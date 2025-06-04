#!/usr/bin/env python3
"""
Intelligent ASX Trader system with smart buy/sell logic based on market predictions and current positions.
"""
import os
import sys
import time
import logging
import datetime
import argparse
import traceback
from dotenv import load_dotenv

# Set up logging before imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("asx_trader_intelligent.log")
    ]
)
logger = logging.getLogger(__name__)

# Import modules
try:
    from asx_trader.config import Config
    from asx_trader.news import ASXNewsCollector
    from asx_trader.market import MarketScanner
    from asx_trader.prediction import GPTEnhancedPredictionEngine
    from asx_trader.risk import RiskManagement
    from asx_trader.enhanced_database import EnhancedDatabase
    from asx_trader.position_manager import PositionManager
    from asx_trader.enhanced_monitoring import EnhancedMarketMonitor
    from asx_trader.utils import is_market_open, get_next_run_time
except Exception as e:
    logger.error(f"Error importing modules: {e}")
    traceback.print_exc()
    sys.exit(1)

class IntelligentTradingSystem:
    """Intelligent trading system with smart buy/sell logic"""
    
    def __init__(self):
        self.db = EnhancedDatabase()
        self.position_manager = PositionManager(database=self.db)
        self.market_monitor = EnhancedMarketMonitor(
            position_manager=self.position_manager, 
            database=self.db
        )
        
        # Initialize other components
        self.news_collector = ASXNewsCollector()
        self.market_scanner = MarketScanner()
        self.prediction_engine = GPTEnhancedPredictionEngine()
        self.risk_management = RiskManagement()
        
        logger.info("Intelligent trading system initialized")
    
    def run_intelligent_trading_cycle(self, args):
        """Run an intelligent trading cycle with smart buy/sell decisions"""
        start_time = datetime.datetime.now()
        logger.info(f"Starting intelligent trading cycle at {start_time}")
        
        status = "completed"
        symbols_analyzed = 0
        signals_generated = 0
        orders_created = 0
        positions_updated = 0
        
        try:
            # 1. Get symbols for analysis - combine market scan with current positions
            market_symbols = self._get_market_symbols_for_analysis(args)
            position_symbols = self._get_position_symbols_for_analysis()
            
            # Combine and deduplicate
            all_symbols = list(set(market_symbols + position_symbols))
            symbols_analyzed = len(all_symbols)
            
            logger.info(f"Analyzing {len(market_symbols)} market symbols and {len(position_symbols)} position symbols")
            logger.info(f"Market symbols: {market_symbols[:10]}...")  # Show first 10
            logger.info(f"Position symbols: {position_symbols}")
            
            # 2. Collect market data for all symbols
            market_data = self.market_scanner.get_market_data(all_symbols)
            logger.info(f"Collected market data for {len(market_data)} symbols")
            
            # Save market data to database for historical analysis
            for symbol, data in market_data.items():
                self.db.save_market_data(symbol, data)
            
            # 3. Update existing positions with current market data
            if market_data:
                self.position_manager.update_positions(market_data)
                positions_updated = len(self.position_manager.positions)
                logger.info(f"Updated {positions_updated} existing positions")
            
            # 4. Collect news for all symbols
            news_items = self.news_collector.fetch_latest_news(all_symbols, limit=args.news_limit)
            logger.info(f"Collected {len(news_items)} news items")
            
            if not news_items:
                logger.warning("No news items found, skipping signal generation")
                status = "skipped:no_news"
            else:
                # 5. Analyze news and generate signals
                signals = self.prediction_engine.analyze_news(news_items)
                logger.info(f"Generated {len(signals)} trading signals")
                signals_generated = len(signals)
                
                # Save signals to database
                self.db.save_trading_signals(signals)
                
                # 6. Perform risk assessment
                signal_symbols = set()
                for signal in signals:
                    signal_symbols.update(signal.get("symbols", []))
                
                risk_assessment = self.risk_management.assess_market_risk(
                    list(signal_symbols), signals, market_data
                )
                logger.info(f"Risk assessment: {risk_assessment.get('overall_risk_level', 'unknown')} risk")
                
                # 7. Process trading signals with intelligent logic (if trading is enabled)
                if Config.TRADING_ENABLED and args.execute_trades:
                    orders_created = self._process_intelligent_trading_signals(signals, market_data, risk_assessment)
                else:
                    logger.info("Trading disabled or --execute-trades not specified - signals generated but no trades executed")
            
            # 8. Generate and save portfolio snapshot
            self._save_portfolio_snapshot()
            
            # 9. Print comprehensive summary
            self._print_intelligent_summary(
                symbols_analyzed, signals_generated, orders_created, 
                positions_updated, market_data, risk_assessment if 'risk_assessment' in locals() else None
            )
            
        except Exception as e:
            logger.error(f"Error in intelligent trading cycle: {e}")
            traceback.print_exc()
            status = f"error:{str(e)}"
        
        end_time = datetime.datetime.now()
        logger.info(f"Intelligent trading cycle completed at {end_time} (duration: {end_time - start_time})")
        
        return status, symbols_analyzed, signals_generated, orders_created
    
    def _get_market_symbols_for_analysis(self, args):
        """Get symbols from market for BUY signal analysis"""
        if args.symbols:
            symbols = args.symbols.split(",")
            logger.info(f"Using provided symbols for market analysis: {symbols}")
            return symbols
        else:
            all_symbols = self.market_scanner.get_market_symbols()
            symbols = all_symbols[:args.max_symbols]
            logger.info(f"Using {len(symbols)} symbols from market scan for BUY opportunities")
            return symbols
    
    def _get_position_symbols_for_analysis(self):
        """Get symbols from current positions for SELL signal analysis"""
        position_symbols = []
        if self.position_manager and self.position_manager.positions:
            position_symbols = [pos.symbol for pos in self.position_manager.positions.values()]
            logger.info(f"Found {len(position_symbols)} symbols in current positions for SELL analysis")
        return position_symbols
    
    def _process_intelligent_trading_signals(self, signals, market_data, risk_assessment):
        """Process trading signals with intelligent buy/sell logic"""
        orders_created = 0
        
        try:
            # Filter signals based on risk assessment
            overall_risk = risk_assessment.get('overall_risk_level', 'Medium')
            
            # Adjust signal processing based on risk level
            if overall_risk == 'Extreme':
                logger.warning("Extreme risk detected - skipping all trades")
                return 0
            elif overall_risk == 'High':
                logger.warning("High risk detected - processing only high-confidence signals")
                signals = [s for s in signals if s.get('confidence', '').lower() == 'high']
            
            # Get current positions for intelligent decision making
            current_positions = {pos.symbol: pos for pos in self.position_manager.positions.values()}
            logger.info(f"Current positions: {list(current_positions.keys())}")
            
            # Separate BUY and SELL signals based on intelligent logic
            buy_candidates = []
            sell_candidates = []
            
            for signal in signals:
                signal_symbols = signal.get('symbols', [])
                signal_action = signal.get('signal', '').upper()
                confidence = signal.get('confidence', '').lower()
                
                if signal_action == 'BUY':
                    # For BUY signals, only consider symbols we don't already own
                    for symbol in signal_symbols:
                        if symbol not in current_positions:
                            buy_candidates.append({
                                'symbol': symbol,
                                'signal': signal,
                                'confidence': confidence,
                                'reasoning': signal.get('reasoning', '')
                            })
                            logger.info(f"BUY candidate: {symbol} (confidence: {confidence})")
                        else:
                            logger.info(f"Already holding {symbol}, skipping BUY signal")
                
                elif signal_action == 'SELL':
                    # For SELL signals, only consider symbols we currently own
                    for symbol in signal_symbols:
                        if symbol in current_positions:
                            sell_candidates.append({
                                'symbol': symbol,
                                'signal': signal,
                                'position': current_positions[symbol],
                                'confidence': confidence,
                                'reasoning': signal.get('reasoning', '')
                            })
                            logger.info(f"SELL candidate: {symbol} (confidence: {confidence})")
                        else:
                            logger.info(f"Not holding {symbol}, skipping SELL signal")
            
            logger.info(f"\n=== INTELLIGENT TRADING DECISIONS ===")
            logger.info(f"BUY candidates (new positions): {len(buy_candidates)}")
            logger.info(f"SELL candidates (existing positions): {len(sell_candidates)}")
            
            # Process SELL signals first (free up capital and manage risk)
            if sell_candidates:
                logger.info(f"\nProcessing {len(sell_candidates)} SELL signals for existing positions...")
                orders_created += self._execute_intelligent_sells(sell_candidates, market_data)
            
            # Process BUY signals (use available capital for new opportunities)
            if buy_candidates:
                logger.info(f"\nProcessing {len(buy_candidates)} BUY signals for new positions...")
                orders_created += self._execute_intelligent_buys(buy_candidates, market_data)
            
        except Exception as e:
            logger.error(f"Error in intelligent signal processing: {e}")
        
        return orders_created
    
    def _execute_intelligent_sells(self, sell_candidates, market_data):
        """Execute SELL orders for existing positions based on signals"""
        orders_created = 0
        
        try:
            for candidate in sell_candidates:
                symbol = candidate['symbol']
                position = candidate['position']
                confidence = candidate['confidence']
                reasoning = candidate['reasoning']
                
                if symbol not in market_data:
                    logger.warning(f"No market data for {symbol}, skipping SELL")
                    continue
                
                current_price = market_data[symbol].get('current_price', 0)
                if current_price <= 0:
                    logger.warning(f"Invalid price for {symbol}, skipping SELL")
                    continue
                
                # Calculate current P&L
                position.update_current_price(current_price)
                pnl_pct = position.get_pnl_percentage()
                pnl_amount = position.unrealized_pnl or 0
                
                # Intelligent sell decision based on multiple factors
                sell_decision = self._make_sell_decision(position, confidence, pnl_pct, reasoning)
                
                if sell_decision['action'] == 'SKIP':
                    logger.info(f"Skipping SELL for {symbol}: {sell_decision['reason']}")
                    continue
                
                sell_quantity = sell_decision['quantity']
                
                logger.info(f"SELLING {symbol}: {sell_decision['reason']}")
                logger.info(f"  Current P&L: {pnl_pct:.1f}% (${pnl_amount:.2f})")
                logger.info(f"  Confidence: {confidence}, Quantity: {sell_quantity}/{abs(position.quantity)}")
                
                # Execute sell order
                success, message = self.position_manager.close_position(
                    symbol=symbol,
                    position_type=position.position_type,
                    quantity=sell_quantity
                )
                
                if success:
                    orders_created += 1
                    logger.info(f"✓ Successfully sold {sell_quantity} {symbol} @ ${current_price}")
                else:
                    logger.error(f"✗ Failed to sell {symbol}: {message}")
        
        except Exception as e:
            logger.error(f"Error executing intelligent sells: {e}")
        
        return orders_created
    
    def _make_sell_decision(self, position, confidence, pnl_pct, reasoning):
        """Make intelligent sell decision based on multiple factors"""
        total_quantity = abs(position.quantity)
        
        # High confidence sell signal - sell entire position
        if confidence == 'high':
            return {
                'action': 'SELL',
                'quantity': total_quantity,
                'reason': f'High confidence SELL signal'
            }
        
        # Significant loss - sell entire position to limit damage
        if pnl_pct < -8:
            return {
                'action': 'SELL',
                'quantity': total_quantity,
                'reason': f'Stop loss triggered at {pnl_pct:.1f}% loss'
            }
        
        # Good profit with medium confidence - sell half to lock in gains
        if pnl_pct > 10 and confidence == 'medium':
            return {
                'action': 'SELL',
                'quantity': total_quantity // 2,
                'reason': f'Taking partial profits at {pnl_pct:.1f}% gain'
            }
        
        # Medium confidence with small loss - sell half to reduce risk
        if confidence == 'medium' and -5 < pnl_pct < 0:
            return {
                'action': 'SELL',
                'quantity': total_quantity // 2,
                'reason': f'Reducing position due to medium confidence signal'
            }
        
        # Low confidence or small movements - hold position
        return {
            'action': 'SKIP',
            'quantity': 0,
            'reason': f'Holding position (confidence: {confidence}, P&L: {pnl_pct:.1f}%)'
        }
    
    def _execute_intelligent_buys(self, buy_candidates, market_data):
        """Execute BUY orders for new positions based on signals"""
        orders_created = 0
        
        try:
            # Get account balance for position sizing
            account_info = self.position_manager.broker.get_account_info()
            account_balance = 1000  # Default fallback
            
            if account_info and 'accounts' in account_info:
                for account in account_info['accounts']:
                    if account.get('preferred', False):
                        balance_data = account.get('balance', {})
                        account_balance = float(balance_data.get('available', 1000))
                        break
            
            logger.info(f"Available account balance: ${account_balance:,.2f}")
            
            # Sort buy candidates by confidence and market attractiveness
            buy_candidates.sort(key=lambda x: (
                0 if x['confidence'] == 'high' else 1 if x['confidence'] == 'medium' else 2,
                -market_data.get(x['symbol'], {}).get('price_change_pct', 0)  # Prefer positive momentum
            ))
            
            for candidate in buy_candidates:
                symbol = candidate['symbol']
                confidence = candidate['confidence']
                reasoning = candidate['reasoning']
                
                if symbol not in market_data:
                    logger.warning(f"No market data for {symbol}, skipping BUY")
                    continue
                
                current_price = market_data[symbol].get('current_price', 0)
                if current_price <= 0:
                    logger.warning(f"Invalid price for {symbol}, skipping BUY")
                    continue
                
                # Calculate position size and risk parameters based on confidence
                position_params = self._calculate_buy_parameters(confidence, current_price, account_balance)
                
                if position_params['size'] <= 0:
                    logger.info(f"Position size calculation resulted in 0 shares for {symbol}")
                    continue
                
                # Check if we can open the position
                can_open, reason = self.position_manager.can_open_position(
                    symbol, position_params['size'], current_price
                )
                
                if not can_open:
                    logger.info(f"Cannot open position for {symbol}: {reason}")
                    continue
                
                logger.info(f"BUYING {symbol}: {reasoning[:100]}...")
                logger.info(f"  Confidence: {confidence}, Price: ${current_price}")
                logger.info(f"  Position size: {position_params['size']}, Stop loss: ${position_params['stop_loss']:.2f}")
                
                # Open the position
                success, message = self.position_manager.open_position(
                    symbol=symbol,
                    signal="BUY",
                    quantity=position_params['size'],
                    entry_price=current_price,
                    stop_loss=position_params['stop_loss'],
                    take_profit=position_params['take_profit']
                )
                
                if success:
                    orders_created += 1
                    position_value = position_params['size'] * current_price
                    logger.info(f"✓ Successfully bought {position_params['size']} {symbol} @ ${current_price} (${position_value:,.2f})")
                    
                    # Update account balance for next calculation
                    account_balance -= position_value
                    
                    # Stop if we're running low on capital
                    if account_balance < 1000:
                        logger.info("Low account balance, stopping further BUY orders")
                        break
                else:
                    logger.error(f"✗ Failed to buy {symbol}: {message}")
        
        except Exception as e:
            logger.error(f"Error executing intelligent buys: {e}")
        
        return orders_created
    
    def _calculate_buy_parameters(self, confidence, current_price, account_balance):
        """Calculate position parameters based on confidence level"""
        # Adjust risk parameters based on confidence
        if confidence == 'high':
            stop_loss_pct = 0.05  # 5% stop loss
            take_profit_pct = 0.15  # 15% take profit
            risk_pct = 0.03  # 3% of account at risk
        elif confidence == 'medium':
            stop_loss_pct = 0.03  # 3% stop loss
            take_profit_pct = 0.10  # 10% take profit
            risk_pct = 0.02  # 2% of account at risk
        else:  # low confidence
            stop_loss_pct = 0.02  # 2% stop loss
            take_profit_pct = 0.08  # 8% take profit
            risk_pct = 0.01  # 1% of account at risk
        
        stop_loss = current_price * (1 - stop_loss_pct)
        take_profit = current_price * (1 + take_profit_pct)
        
        # Calculate position size based on risk
        risk_amount = account_balance * risk_pct
        risk_per_share = current_price - stop_loss
        position_size = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
        
        # Apply maximum position size limit
        max_position_value = min(account_balance * 0.1, Config.MAX_POSITION_SIZE)  # 10% of account or config limit
        max_shares = int(max_position_value / current_price)
        position_size = min(position_size, max_shares)
        
        return {
            'size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
    
    def _save_portfolio_snapshot(self):
        """Save current portfolio performance snapshot"""
        try:
            if not self.position_manager:
                return
            
            # Get position summary
            position_summary = self.position_manager.get_position_summary()
            
            # Get account balance
            account_info = self.position_manager.broker.get_account_info()
            cash_balance = 0
            
            if account_info and 'accounts' in account_info:
                for account in account_info['accounts']:
                    if account.get('preferred', False):
                        balance_data = account.get('balance', {})
                        cash_balance = float(balance_data.get('available', 0))
                        break
            
            # Calculate total portfolio value
            total_exposure = position_summary.get('total_exposure', 0)
            total_value = cash_balance + total_exposure
            
            snapshot_data = {
                'total_value': total_value,
                'total_exposure': total_exposure,
                'unrealized_pnl': position_summary.get('unrealized_pnl', 0),
                'realized_pnl': position_summary.get('realized_pnl', 0),
                'cash_balance': cash_balance,
                'position_count': position_summary.get('total_positions', 0)
            }
            
            self.db.save_portfolio_snapshot(snapshot_data)
            logger.debug("Saved portfolio snapshot")
            
        except Exception as e:
            logger.error(f"Error saving portfolio snapshot: {e}")
    
    def _print_intelligent_summary(self, symbols_analyzed, signals_generated, orders_created, 
                                 positions_updated, market_data, risk_assessment):
        """Print comprehensive intelligent trading summary"""
        print("\n" + "="*70)
        print("INTELLIGENT ASX TRADER RESULTS")
        print("="*70)
        
        # Basic statistics
        print(f"Symbols Analyzed: {symbols_analyzed}")
        print(f"Signals Generated: {signals_generated}")
        print(f"Orders Created: {orders_created}")
        print(f"Positions Updated: {positions_updated}")
        
        # Risk assessment
        if risk_assessment:
            print(f"Market Risk Level: {risk_assessment.get('overall_risk_level', 'Unknown')}")
        
        # Position summary
        if self.position_manager:
            position_summary = self.position_manager.get_position_summary()
            print(f"\nPORTFOLIO SUMMARY:")
            print(f"  Active Positions: {position_summary.get('total_positions', 0)}")
            print(f"  Total Exposure: ${position_summary.get('total_exposure', 0):,.2f}")
            print(f"  Unrealized P&L: ${position_summary.get('unrealized_pnl', 0):,.2f}")
            print(f"  Realized P&L: ${position_summary.get('realized_pnl', 0):,.2f}")
            
            # Show individual positions
            positions = position_summary.get('positions', [])
            if positions:
                print(f"\nACTIVE POSITIONS:")
                for pos in positions[:10]:  # Show top 10
                    pnl_str = f"${pos.get('unrealized_pnl', 0):,.2f}" if pos.get('unrealized_pnl') else "N/A"
                    pnl_pct_str = f"{pos.get('pnl_percentage', 0):.1f}%" if pos.get('pnl_percentage') else "N/A"
                    print(f"  {pos.get('symbol')}: {pos.get('quantity')} @ ${pos.get('entry_price', 0):.2f} "
                          f"(Current: ${pos.get('current_price', 0):.2f}, P&L: {pnl_str} / {pnl_pct_str})")
        
        print("="*70)
        print("INTELLIGENT TRADING LOGIC:")
        print("• BUY signals: Only for symbols NOT currently held")
        print("• SELL signals: Only for symbols currently held")
        print("• Position sizing: Risk-based (1-3% account risk)")
        print("• Confidence-based parameters: High/Medium/Low confidence levels")
        print("="*70)
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'market_monitor'):
                self.market_monitor.stop_monitoring()
            self.db.close()
            logger.info("Intelligent trading system cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main function for intelligent ASX trader"""
    parser = argparse.ArgumentParser(description="Intelligent ASX Trader System")
    parser.add_argument("--symbols", type=str, help="Comma-separated list of symbols to analyze for BUY opportunities")
    parser.add_argument("--max-symbols", type=int, default=20, help="Maximum number of market symbols to analyze for BUY")
    parser.add_argument("--news-limit", type=int, default=50, help="Maximum number of news items to fetch")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--force-run", action="store_true", help="Force run even if market is closed")
    parser.add_argument("--execute-trades", action="store_true", help="Execute actual trades (requires TRADING_ENABLED=true)")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting Intelligent ASX Trader System")
    logger.info("=== INTELLIGENT TRADING LOGIC ===")
    logger.info("• BUY signals: Analyzed from market symbols (new opportunities)")
    logger.info("• SELL signals: Analyzed from current positions (exit decisions)")
    logger.info("• Risk-based position sizing with confidence-adjusted parameters")
    logger.info("=======================================")
    
    # Initialize intelligent trading system
    trading_system = IntelligentTradingSystem()
    
    try:
        # Run trading cycle
        if args.run_once:
            status, symbols_analyzed, signals_generated, orders_created = trading_system.run_intelligent_trading_cycle(args)
            next_run = get_next_run_time(Config.CYCLE_INTERVAL_MINUTES)
            trading_system.db.record_run(
                datetime.datetime.now(), 
                datetime.datetime.now(), 
                status, 
                symbols_analyzed, 
                signals_generated, 
                orders_created, 
                next_run
            )
            return
        
        # Continuous operation
        while True:
            if is_market_open() or args.force_run:
                status, symbols_analyzed, signals_generated, orders_created = trading_system.run_intelligent_trading_cycle(args)
                
                next_run = get_next_run_time(Config.CYCLE_INTERVAL_MINUTES)
                trading_system.db.record_run(
                    datetime.datetime.now(), 
                    datetime.datetime.now(), 
                    status, 
                    symbols_analyzed, 
                    signals_generated, 
                    orders_created, 
                    next_run
                )
                
                wait_seconds = (next_run - datetime.datetime.now()).total_seconds()
                logger.info(f"Next run scheduled at {next_run} (waiting {wait_seconds/60:.1f} minutes)")
                time.sleep(wait_seconds)
            else:
                logger.info("Market is closed. Checking again in 15 minutes.")
                time.sleep(15 * 60)
        
    except KeyboardInterrupt:
        logger.info("Intelligent trading system stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        traceback.print_exc()
    finally:
        trading_system.cleanup()

if __name__ == "__main__":
    main()
