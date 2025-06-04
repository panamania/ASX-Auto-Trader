#!/usr/bin/env python3
"""
Enhanced ASX Trader system with comprehensive position management, monitoring, and curl-based OpenAI integration.
This version combines the enhanced features with curl-based API calls for better reliability.
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
        logging.FileHandler("asx_trader_enhanced.log")
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
    from asx_trader.curl_openai import openai_client
    from asx_trader.broker import broker
except Exception as e:
    logger.error(f"Error importing modules: {e}")
    traceback.print_exc()
    sys.exit(1)

def calculate_position_size(symbol, signal, risk_level, market_data, max_position=Config.MAX_POSITION_SIZE):
    """
    Calculate appropriate position size based on signal and risk level.
    
    Args:
        symbol: Stock symbol
        signal: Trading signal (BUY, SELL, HOLD)
        risk_level: Risk assessment level (Low, Medium, High, Extreme)
        market_data: Market data dictionary
        max_position: Maximum position size in dollars
        
    Returns:
        int: Quantity of shares to trade
    """
    # Default to 0 if not a BUY or SELL signal
    if signal not in ["BUY", "SELL"]:
        return 0
    
    # Get current price from market data
    price = 0
    if symbol in market_data:
        price = market_data[symbol].get("current_price", 0)
    
    # If we couldn't get a price, we can't calculate quantity
    if price <= 0:
        return 0
    
    # Adjust position size based on risk level
    risk_factor = {
        "Low": 1.0,
        "Medium": 0.7, 
        "High": 0.4,
        "Extreme": 0.2
    }.get(risk_level, 0.5)
    
    # Calculate dollar amount
    position_dollars = max_position * risk_factor
    
    # Calculate quantity (round down to nearest whole share)
    quantity = int(position_dollars / price)
    
    return quantity

class EnhancedTradingSystemCurl:
    """Enhanced trading system with position management, monitoring, and curl-based API calls"""
    
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
        
        # Test curl-based OpenAI client
        self._test_openai_client()
        
        logger.info("Enhanced trading system with curl integration initialized")
    
    def _test_openai_client(self):
        """Test the curl-based OpenAI client"""
        try:
            test_response = openai_client.chat_completion(
                model="o4-mini",
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=10
            )
            if test_response.get('content'):
                logger.info(f"OpenAI curl client test successful: {test_response.get('content', '')}")
            else:
                logger.warning(f"OpenAI curl client test returned no content: {test_response}")
        except Exception as e:
            logger.error(f"OpenAI curl client test failed: {e}")
            raise
    
    def run_enhanced_trading_cycle(self, args):
        """Run an enhanced trading cycle with position management and curl-based API calls"""
        start_time = datetime.datetime.now()
        logger.info(f"Starting enhanced trading cycle at {start_time}")
        
        status = "completed"
        symbols_analyzed = 0
        signals_generated = 0
        orders_created = 0
        positions_updated = 0
        
        try:
            # 1. Get symbols to analyze
            if args.symbols:
                symbols = args.symbols.split(",")
                logger.info(f"Using provided symbols: {symbols}")
            else:
                all_symbols = self.market_scanner.get_market_symbols()
                symbols = all_symbols[:args.max_symbols]
                logger.info(f"Using {len(symbols)} symbols from market scan")
            
            symbols_analyzed = len(symbols)
            
            # 2. Collect market data
            market_data = self.market_scanner.get_market_data(symbols)
            logger.info(f"Collected market data for {len(market_data)} symbols")
            
            # Save market data to database for historical analysis
            for symbol, data in market_data.items():
                self.db.save_market_data(symbol, data)
            
            # 3. Update existing positions with current market data
            if market_data:
                self.position_manager.update_positions(market_data)
                positions_updated = len(self.position_manager.positions)
                logger.info(f"Updated {positions_updated} existing positions")
            
            # 4. Collect news
            news_items = self.news_collector.fetch_latest_news(symbols, limit=args.news_limit)
            logger.info(f"Collected {len(news_items)} news items")
            
            if not news_items:
                logger.warning("No news items found, skipping signal generation")
                status = "skipped:no_news"
            else:
                # 5. Analyze news and generate signals using curl-based API
                signals = self.prediction_engine.analyze_news(news_items)
                logger.info(f"Generated {len(signals)} trading signals using curl-based API")
                signals_generated = len(signals)
                
                # Save signals to database
                self.db.save_trading_signals(signals)
                
                # 6. Perform risk assessment using curl-based API
                signal_symbols = set()
                for signal in signals:
                    signal_symbols.update(signal.get("symbols", []))
                
                risk_assessment = self.risk_management.assess_market_risk(
                    list(signal_symbols), signals, market_data
                )
                logger.info(f"Risk assessment: {risk_assessment.get('overall_risk_level', 'unknown')} risk")
                
                # 7. Process trading signals (if trading is enabled)
                if Config.TRADING_ENABLED and args.execute_trades:
                    orders_created = self._process_trading_signals_enhanced(signals, market_data, risk_assessment)
                elif args.simulate:
                    orders_created = self._simulate_trading_signals(signals, market_data, risk_assessment)
                else:
                    logger.info("Trading disabled or --execute-trades not specified - signals generated but no trades executed")
            
            # 8. Generate and save portfolio snapshot
            self._save_portfolio_snapshot()
            
            # 9. Print comprehensive summary
            self._print_enhanced_summary(
                symbols_analyzed, signals_generated, orders_created, 
                positions_updated, market_data, risk_assessment if 'risk_assessment' in locals() else None
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced trading cycle: {e}")
            traceback.print_exc()
            status = f"error:{str(e)}"
        
        end_time = datetime.datetime.now()
        logger.info(f"Enhanced trading cycle completed at {end_time} (duration: {end_time - start_time})")
        
        return status, symbols_analyzed, signals_generated, orders_created
    
    def _process_trading_signals_enhanced(self, signals, market_data, risk_assessment):
        """Process trading signals with enhanced position management"""
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
            
            for signal in signals:
                try:
                    signal_symbols = signal.get('symbols', [])
                    signal_action = signal.get('signal', '').upper()
                    confidence = signal.get('confidence', '').lower()
                    
                    # Skip non-actionable signals
                    if signal_action not in ['BUY', 'SELL'] or not signal_symbols:
                        continue
                    
                    # Process each symbol in the signal
                    for symbol in signal_symbols:
                        if symbol not in market_data:
                            logger.warning(f"No market data for {symbol}, skipping")
                            continue
                        
                        current_price = market_data[symbol].get('current_price', 0)
                        if current_price <= 0:
                            logger.warning(f"Invalid price for {symbol}, skipping")
                            continue
                        
                        # Calculate position size and risk parameters
                        stop_loss_pct = 0.05 if confidence == 'high' else 0.03  # 5% or 3% stop loss
                        take_profit_pct = 0.15 if confidence == 'high' else 0.10  # 15% or 10% take profit
                        
                        if signal_action == 'BUY':
                            stop_loss = current_price * (1 - stop_loss_pct)
                            take_profit = current_price * (1 + take_profit_pct)
                        else:  # SELL
                            stop_loss = current_price * (1 + stop_loss_pct)
                            take_profit = current_price * (1 - take_profit_pct)
                        
                        # Get account balance for position sizing
                        account_info = self.position_manager.broker.get_account_info()
                        account_balance = 1000  # Default fallback
                        
                        if account_info and 'accounts' in account_info:
                            for account in account_info['accounts']:
                                if account.get('preferred', False):
                                    balance_data = account.get('balance', {})
                                    account_balance = float(balance_data.get('available', 1000))
                                    break
                        
                        # Calculate optimal position size
                        position_size = self.position_manager.calculate_position_size(
                            symbol, current_price, stop_loss, account_balance
                        )
                        
                        if position_size <= 0:
                            logger.info(f"Position size calculation resulted in 0 shares for {symbol}")
                            continue
                        
                        # Check if we can open the position
                        can_open, reason = self.position_manager.can_open_position(
                            symbol, position_size, current_price
                        )
                        
                        if not can_open:
                            logger.info(f"Cannot open position for {symbol}: {reason}")
                            continue
                        
                        # Open the position
                        success, message = self.position_manager.open_position(
                            symbol=symbol,
                            signal=signal_action,
                            quantity=position_size,
                            entry_price=current_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit
                        )
                        
                        if success:
                            orders_created += 1
                            logger.info(f"Successfully opened position: {signal_action} {position_size} {symbol} @ ${current_price}")
                        else:
                            logger.error(f"Failed to open position for {symbol}: {message}")
                
                except Exception as e:
                    logger.error(f"Error processing signal: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in signal processing: {e}")
        
        return orders_created
    
    def _simulate_trading_signals(self, signals, market_data, risk_assessment):
        """Simulate trading signals for testing purposes"""
        orders_created = 0
        executed_orders = []
        
        try:
            for signal in signals:
                symbol = signal.get("symbols", ["MARKET"])[0] if signal.get("symbols") else "MARKET"
                signal_type = signal.get("signal", "NONE")
                
                # Skip if not an actionable symbol or signal
                if symbol == "MARKET" or signal_type not in ["BUY", "SELL"]:
                    continue
                    
                # Get risk level for this symbol
                symbol_risks = risk_assessment.get("symbol_risks", [])
                symbol_risk = "Medium"  # Default
                for risk in symbol_risks:
                    if risk.get("symbol") == symbol:
                        symbol_risk = risk.get("risk_level", "Medium")
                        break
                
                # Calculate quantity using the helper function
                quantity = calculate_position_size(
                    symbol, 
                    signal_type, 
                    symbol_risk, 
                    market_data, 
                    Config.MAX_POSITION_SIZE
                )
                
                if quantity > 0:
                    # Create simulated order
                    order = {
                        "symbol": symbol,
                        "action": signal_type,
                        "quantity": quantity,
                        "risk_level": symbol_risk,
                        "estimated_cost": quantity * market_data.get(symbol, {}).get("current_price", 0),
                        "news_id": signal.get("news_id"),
                        "execution_result": {
                            "status": "SIMULATED",
                            "dealReference": f"SIM-{len(executed_orders)}",
                            "details": "Simulation mode"
                        }
                    }
                    
                    executed_orders.append(order)
                    orders_created += 1
                    logger.info(f"Order simulated: {signal_type} {quantity} {symbol}")
            
            # Save simulated orders to database
            if executed_orders:
                self.db.save_trading_orders(executed_orders)
        
        except Exception as e:
            logger.error(f"Error in signal simulation: {e}")
        
        return orders_created
    
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
    
    def _print_enhanced_summary(self, symbols_analyzed, signals_generated, orders_created, 
                              positions_updated, market_data, risk_assessment):
        """Print comprehensive trading summary"""
        print("\n" + "="*60)
        print("ENHANCED ASX TRADER RESULTS (CURL VERSION)")
        print("="*60)
        
        # Basic statistics
        print(f"Symbols Analyzed: {symbols_analyzed}")
        print(f"Signals Generated: {signals_generated}")
        print(f"Orders Created: {orders_created}")
        print(f"Positions Updated: {positions_updated}")
        
        # Risk assessment
        if risk_assessment:
            print(f"Market Risk Level: {risk_assessment.get('overall_risk_level', 'Unknown')}")
        
        # Show top signals
        if signals_generated > 0:
            print(f"\nTOP TRADING SIGNALS:")
            # This would need access to the signals list - we'll add it as a parameter if needed
            print("  (Signal details would be shown here)")
        
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
        
        # Market monitoring summary
        if self.market_monitor:
            monitoring_summary = self.market_monitor.get_monitoring_summary()
            recent_alerts = self.market_monitor.get_recent_alerts(24)
            
            print(f"\nMONITORING STATUS:")
            print(f"  Active: {'Yes' if monitoring_summary.get('monitoring_active') else 'No'}")
            print(f"  Watchlist: {monitoring_summary.get('watchlist_size', 0)} symbols")
            print(f"  Recent Alerts (24h): {len(recent_alerts)}")
            
            # Show recent high-priority alerts
            high_priority = [a for a in recent_alerts if a.severity in ['HIGH', 'CRITICAL']]
            if high_priority:
                print(f"\nRECENT HIGH PRIORITY ALERTS:")
                for alert in high_priority[-5:]:  # Last 5
                    print(f"  [{alert.severity}] {alert.symbol}: {alert.message}")
        
        print("="*60)
    
    def start_monitoring(self, symbols=None):
        """Start enhanced market monitoring"""
        try:
            # Add position symbols to watchlist
            if self.position_manager:
                position_symbols = [pos.symbol for pos in self.position_manager.positions.values()]
                if position_symbols:
                    self.market_monitor.add_to_watchlist(position_symbols)
            
            # Add provided symbols
            if symbols:
                self.market_monitor.add_to_watchlist(symbols)
            
            # Start monitoring
            self.market_monitor.start_monitoring()
            logger.info("Enhanced market monitoring started")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop market monitoring"""
        try:
            self.market_monitor.stop_monitoring()
            logger.info("Enhanced market monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
    
    def generate_report(self):
        """Generate comprehensive trading report"""
        try:
            report = self.market_monitor.generate_monitoring_report()
            
            # Add trading performance
            performance = self.db.get_trading_performance(30)
            if performance:
                report += "\n\nTRADING PERFORMANCE (30 days):\n"
                report += f"  Total Trades: {performance.get('total_trades', 0)}\n"
                report += f"  Win Rate: {performance.get('win_rate', 0):.1f}%\n"
                report += f"  Total P&L: ${performance.get('total_pnl', 0):,.2f}\n"
                report += f"  Average P&L per Trade: ${performance.get('average_pnl_per_trade', 0):,.2f}\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {str(e)}"
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_monitoring()
            self.db.close()
            logger.info("Enhanced trading system cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main function for enhanced ASX trader with curl integration"""
    parser = argparse.ArgumentParser(description="Enhanced ASX Trader System with Curl Integration")
    parser.add_argument("--symbols", type=str, help="Comma-separated list of symbols to analyze")
    parser.add_argument("--max-symbols", type=int, default=20, help="Maximum number of symbols to analyze")
    parser.add_argument("--news-limit", type=int, default=50, help="Maximum number of news items to fetch")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--force-run", action="store_true", help="Force run even if market is closed")
    parser.add_argument("--execute-trades", action="store_true", help="Execute actual trades (requires TRADING_ENABLED=true)")
    parser.add_argument("--simulate", action="store_true", help="Simulate trades without execution")
    parser.add_argument("--start-monitoring", action="store_true", help="Start continuous market monitoring")
    parser.add_argument("--generate-report", action="store_true", help="Generate and display comprehensive report")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting Enhanced ASX Trader System with Curl Integration")
    
    # Initialize enhanced trading system
    trading_system = EnhancedTradingSystemCurl()
    
    try:
        # Check if trading is enabled
        if Config.TRADING_ENABLED:
            if Config.BROKER_ACCOUNT_TYPE == "LIVE":
                logger.warning("⚠️ TRADING IS ENABLED WITH A LIVE ACCOUNT - REAL MONEY WILL BE USED ⚠️")
            else:
                logger.info("Trading is enabled with a DEMO account")
        else:
            logger.info("Trading is disabled, orders will be simulated")
        
        # Generate report if requested
        if args.generate_report:
            report = trading_system.generate_report()
            print(report)
            return
        
        # Start monitoring if requested
        if args.start_monitoring:
            symbols = args.symbols.split(",") if args.symbols else None
            trading_system.start_monitoring(symbols)
            
            try:
                print("Enhanced market monitoring started. Press Ctrl+C to stop.")
                while True:
                    time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                trading_system.stop_monitoring()
            return
        
        # Run trading cycle
        if args.run_once:
            status, symbols_analyzed, signals_generated, orders_created = trading_system.run_enhanced_trading_cycle(args)
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
                status, symbols_analyzed, signals_generated, orders_created = trading_system.run_enhanced_trading_cycle(args)
                
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
        logger.info("Enhanced trading system stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        traceback.print_exc()
    finally:
        trading_system.cleanup()

if __name__ == "__main__":
    main()
