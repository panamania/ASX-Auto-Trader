"""
Position management module for tracking and managing trading positions.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from asx_trader.config import Config
from asx_trader.broker import BrokerFactory

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    quantity: int
    entry_price: float
    entry_date: datetime
    position_type: str  # 'LONG' or 'SHORT'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: float = 0.0
    status: str = 'OPEN'  # 'OPEN', 'CLOSED', 'PARTIAL'
    deal_reference: Optional[str] = None
    
    def update_current_price(self, price: float):
        """Update current price and calculate unrealized P&L"""
        self.current_price = price
        if self.position_type == 'LONG':
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
        else:  # SHORT
            self.unrealized_pnl = (self.entry_price - price) * self.quantity
    
    def get_position_value(self) -> float:
        """Get current position value"""
        if self.current_price:
            return self.current_price * abs(self.quantity)
        return self.entry_price * abs(self.quantity)
    
    def get_pnl_percentage(self) -> float:
        """Get P&L as percentage of entry value"""
        if self.unrealized_pnl is None:
            return 0.0
        entry_value = self.entry_price * abs(self.quantity)
        return (self.unrealized_pnl / entry_value) * 100 if entry_value > 0 else 0.0

class PositionManager:
    """Manages trading positions with risk controls"""
    
    def __init__(self, database=None):
        self.broker = BrokerFactory.get_broker()
        self.database = database
        self.positions: Dict[str, Position] = {}
        self.max_position_size = Config.MAX_POSITION_SIZE
        self.max_portfolio_risk = 0.02  # 2% max risk per position
        self.max_total_exposure = 0.20  # 20% max total portfolio exposure
        
        # Load existing positions
        self._load_positions()
    
    def _load_positions(self):
        """Load existing positions from broker and database"""
        try:
            # Get positions from broker
            broker_positions = self.broker.get_positions()
            if broker_positions and 'positions' in broker_positions:
                for pos_data in broker_positions['positions']:
                    position = self._convert_broker_position(pos_data)
                    if position:
                        self.positions[f"{position.symbol}_{position.position_type}"] = position
            
            logger.info(f"Loaded {len(self.positions)} existing positions")
            
        except Exception as e:
            logger.error(f"Error loading positions: {e}")
    
    def _convert_broker_position(self, broker_data: dict) -> Optional[Position]:
        """Convert broker position data to Position object"""
        try:
            # This will vary based on broker API format
            # Example for IG Markets format
            market = broker_data.get('market', {})
            position_data = broker_data.get('position', {})
            
            symbol = market.get('epic', '').replace('.AU', '').replace('AU.', '')
            if not symbol:
                return None
            
            quantity = int(position_data.get('size', 0))
            direction = position_data.get('direction', 'BUY')
            position_type = 'LONG' if direction == 'BUY' else 'SHORT'
            
            # Adjust quantity for short positions
            if position_type == 'SHORT':
                quantity = -quantity
            
            return Position(
                symbol=symbol,
                quantity=quantity,
                entry_price=float(position_data.get('level', 0)),
                entry_date=datetime.now(),  # Would need to parse from broker data
                position_type=position_type,
                current_price=float(market.get('bid', 0)),
                deal_reference=position_data.get('dealId')
            )
            
        except Exception as e:
            logger.error(f"Error converting broker position: {e}")
            return None
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                             stop_loss: float, account_balance: float) -> int:
        """Calculate optimal position size based on risk management"""
        try:
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss)
            
            # Calculate maximum risk amount (2% of account)
            max_risk_amount = account_balance * self.max_portfolio_risk
            
            # Calculate position size based on risk
            risk_based_size = int(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0
            
            # Apply maximum position size limit
            max_size_limit = int(self.max_position_size / entry_price)
            
            # Take the smaller of the two
            position_size = min(risk_based_size, max_size_limit)
            
            logger.info(f"Position size calculation for {symbol}: "
                       f"Risk-based: {risk_based_size}, Max-size: {max_size_limit}, "
                       f"Final: {position_size}")
            
            return max(position_size, 0)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def can_open_position(self, symbol: str, position_size: int, 
                         entry_price: float) -> Tuple[bool, str]:
        """Check if a new position can be opened"""
        try:
            # Check if position already exists
            position_key = f"{symbol}_LONG"  # Assuming long positions for now
            if position_key in self.positions:
                return False, f"Position already exists for {symbol}"
            
            # Check total portfolio exposure
            current_exposure = self.get_total_exposure()
            new_position_value = position_size * entry_price
            
            # Get account balance
            account_info = self.broker.get_account_info()
            if not account_info or 'accounts' not in account_info:
                return False, "Cannot retrieve account information"
            
            account_balance = 0
            for account in account_info['accounts']:
                if account.get('preferred', False):
                    balance_data = account.get('balance', {})
                    account_balance = float(balance_data.get('available', 0))
                    break
            
            if account_balance <= 0:
                return False, "Insufficient account balance"
            
            # Check if new position would exceed exposure limits
            total_exposure_ratio = (current_exposure + new_position_value) / account_balance
            if total_exposure_ratio > self.max_total_exposure:
                return False, f"Would exceed maximum portfolio exposure ({self.max_total_exposure*100}%)"
            
            # Check position size limits
            if new_position_value > self.max_position_size:
                return False, f"Position size exceeds maximum limit (${self.max_position_size})"
            
            return True, "Position can be opened"
            
        except Exception as e:
            logger.error(f"Error checking position eligibility: {e}")
            return False, f"Error: {str(e)}"
    
    def open_position(self, symbol: str, signal: str, quantity: int, 
                     entry_price: float, stop_loss: float = None, 
                     take_profit: float = None) -> Tuple[bool, str]:
        """Open a new trading position"""
        try:
            # Validate inputs
            if quantity <= 0:
                return False, "Invalid quantity"
            
            direction = "BUY" if signal.upper() in ["BUY", "LONG"] else "SELL"
            position_type = "LONG" if direction == "BUY" else "SHORT"
            
            # Check if position can be opened
            can_open, reason = self.can_open_position(symbol, quantity, entry_price)
            if not can_open:
                return False, reason
            
            # Execute trade through broker
            trade_result = self.broker.execute_trade(
                symbol=symbol,
                direction=direction,
                quantity=quantity,
                order_type="MARKET"
            )
            
            if trade_result.get('status') not in ['SUCCESS', 'SIMULATED']:
                return False, f"Trade execution failed: {trade_result.get('reason', 'Unknown error')}"
            
            # Create position object
            position = Position(
                symbol=symbol,
                quantity=quantity if direction == "BUY" else -quantity,
                entry_price=entry_price,
                entry_date=datetime.now(),
                position_type=position_type,
                stop_loss=stop_loss,
                take_profit=take_profit,
                deal_reference=trade_result.get('dealReference')
            )
            
            # Store position
            position_key = f"{symbol}_{position_type}"
            self.positions[position_key] = position
            
            # Save to database if available
            if self.database:
                self._save_position_to_db(position)
            
            logger.info(f"Opened {position_type} position: {quantity} {symbol} @ ${entry_price}")
            return True, f"Position opened successfully: {trade_result.get('dealReference')}"
            
        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return False, f"Error: {str(e)}"
    
    def close_position(self, symbol: str, position_type: str = "LONG", 
                      quantity: int = None) -> Tuple[bool, str]:
        """Close an existing position"""
        try:
            position_key = f"{symbol}_{position_type}"
            if position_key not in self.positions:
                return False, f"No {position_type} position found for {symbol}"
            
            position = self.positions[position_key]
            
            # Determine quantity to close
            close_quantity = quantity if quantity else abs(position.quantity)
            
            # Determine direction for closing trade
            close_direction = "SELL" if position.position_type == "LONG" else "BUY"
            
            # Execute closing trade
            trade_result = self.broker.execute_trade(
                symbol=symbol,
                direction=close_direction,
                quantity=close_quantity,
                order_type="MARKET"
            )
            
            if trade_result.get('status') not in ['SUCCESS', 'SIMULATED']:
                return False, f"Failed to close position: {trade_result.get('reason', 'Unknown error')}"
            
            # Update position
            if quantity and quantity < abs(position.quantity):
                # Partial close
                if position.quantity > 0:
                    position.quantity -= quantity
                else:
                    position.quantity += quantity
                position.status = 'PARTIAL'
            else:
                # Full close
                position.quantity = 0
                position.status = 'CLOSED'
                # Calculate realized P&L
                if position.current_price:
                    position.realized_pnl = position.unrealized_pnl or 0
                
                # Remove from active positions
                del self.positions[position_key]
            
            # Update database
            if self.database:
                self._update_position_in_db(position)
            
            logger.info(f"Closed position: {close_quantity} {symbol} - Reference: {trade_result.get('dealReference')}")
            return True, f"Position closed successfully: {trade_result.get('dealReference')}"
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False, f"Error: {str(e)}"
    
    def update_positions(self, market_data: Dict[str, dict]):
        """Update all positions with current market data"""
        try:
            for position_key, position in self.positions.items():
                if position.symbol in market_data:
                    current_price = market_data[position.symbol].get('current_price')
                    if current_price:
                        position.update_current_price(current_price)
                        
                        # Check stop loss and take profit
                        self._check_exit_conditions(position)
            
            logger.debug(f"Updated {len(self.positions)} positions with market data")
            
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
    
    def _check_exit_conditions(self, position: Position):
        """Check if position should be closed based on stop loss or take profit"""
        try:
            if not position.current_price:
                return
            
            should_close = False
            reason = ""
            
            # Check stop loss
            if position.stop_loss:
                if position.position_type == "LONG" and position.current_price <= position.stop_loss:
                    should_close = True
                    reason = f"Stop loss triggered at ${position.current_price}"
                elif position.position_type == "SHORT" and position.current_price >= position.stop_loss:
                    should_close = True
                    reason = f"Stop loss triggered at ${position.current_price}"
            
            # Check take profit
            if position.take_profit and not should_close:
                if position.position_type == "LONG" and position.current_price >= position.take_profit:
                    should_close = True
                    reason = f"Take profit triggered at ${position.current_price}"
                elif position.position_type == "SHORT" and position.current_price <= position.take_profit:
                    should_close = True
                    reason = f"Take profit triggered at ${position.current_price}"
            
            if should_close:
                logger.info(f"Auto-closing position {position.symbol}: {reason}")
                success, message = self.close_position(position.symbol, position.position_type)
                if not success:
                    logger.error(f"Failed to auto-close position: {message}")
                    
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}")
    
    def get_total_exposure(self) -> float:
        """Calculate total portfolio exposure"""
        total_exposure = 0
        for position in self.positions.values():
            total_exposure += position.get_position_value()
        return total_exposure
    
    def get_total_pnl(self) -> Tuple[float, float]:
        """Get total unrealized and realized P&L"""
        unrealized_pnl = sum(pos.unrealized_pnl or 0 for pos in self.positions.values())
        realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
        return unrealized_pnl, realized_pnl
    
    def get_position_summary(self) -> Dict:
        """Get summary of all positions"""
        try:
            unrealized_pnl, realized_pnl = self.get_total_pnl()
            total_exposure = self.get_total_exposure()
            
            positions_data = []
            for position in self.positions.values():
                positions_data.append({
                    'symbol': position.symbol,
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'current_price': position.current_price,
                    'unrealized_pnl': position.unrealized_pnl,
                    'pnl_percentage': position.get_pnl_percentage(),
                    'position_value': position.get_position_value(),
                    'position_type': position.position_type,
                    'status': position.status
                })
            
            return {
                'total_positions': len(self.positions),
                'total_exposure': total_exposure,
                'unrealized_pnl': unrealized_pnl,
                'realized_pnl': realized_pnl,
                'total_pnl': unrealized_pnl + realized_pnl,
                'positions': positions_data
            }
            
        except Exception as e:
            logger.error(f"Error getting position summary: {e}")
            return {'error': str(e)}
    
    def _save_position_to_db(self, position: Position):
        """Save position to database"""
        try:
            if self.database:
                self.database.save_position(asdict(position))
        except Exception as e:
            logger.error(f"Error saving position to database: {e}")
    
    def _update_position_in_db(self, position: Position):
        """Update position in database"""
        try:
            if self.database:
                self.database.update_position(asdict(position))
        except Exception as e:
            logger.error(f"Error updating position in database: {e}")
