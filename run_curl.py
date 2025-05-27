#!/usr/bin/env python3
"""
Curl-based main script for the ASX Trader system.
This version uses curl to interact with OpenAI API instead of the Python SDK.
"""
import os
import sys
import time
import logging
import datetime
import argparse
import traceback
from dotenv import load_dotenv

# Set up logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("asx_trader.log")
    ]
)
logger = logging.getLogger(__name__)

# Now import modules
try:
    from asx_trader.config import Config
    from asx_trader.news import ASXNewsCollector
    from asx_trader.market import MarketScanner
    from asx_trader.prediction import GPTEnhancedPredictionEngine
    from asx_trader.risk import RiskManagement
    from asx_trader.database import Database
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

def run_trading_cycle(args, db):
    """Run a single trading cycle"""
    start_time = datetime.datetime.now()
    logger.info(f"Starting trading cycle at {start_time}")
    
    status = "completed"
    symbols_analyzed = 0
    signals_generated = 0
    orders_created = 0
    
    try:
        # Initialize components with minimal configuration
        news_collector = ASXNewsCollector()
        logger.info("Created news collector")
        
        market_scanner = MarketScanner()
        logger.info("Created market scanner")
        
        prediction_engine = GPTEnhancedPredictionEngine()
        logger.info("Created prediction engine")
        
        risk_management = RiskManagement()
        logger.info("Created risk management")
        
        # 1. Get symbols to analyze (either from args or market scan)
        if args.symbols:
            symbols = args.symbols.split(",")
            logger.info(f"Using provided symbols: {symbols}")
        else:
            # Get symbols from the market scanner
            all_symbols = market_scanner.get_market_symbols()
            logger.info(f"Retrieved {len(all_symbols)} ASX symbols")
            symbols = all_symbols[:args.max_symbols]
            logger.info(f"Using {len(symbols)} symbols from market scan")
        
        symbols_analyzed = len(symbols)
        
        # 2. Collect market data
        market_data = market_scanner.get_market_data(symbols)
        logger.info(f"Collected market data for {len(market_data)} symbols")
        
        # 3. Collect news
        news_items = news_collector.fetch_latest_news(symbols, limit=args.news_limit)
        logger.info(f"Collected {len(news_items)} news items")
        
        if not news_items:
            logger.warning("No news items found, skipping cycle")
            status = "skipped:no_news"
            return status, symbols_analyzed, signals_generated, orders_created
            
        # 4. Analyze news and generate signals (rate limited)
        signals = prediction_engine.analyze_news(news_items)
        logger.info(f"Generated {len(signals)} trading signals")
        signals_generated = len(signals)
        
        # Save signals to database
        db.save_trading_signals(signals)
        
        # Extract symbols from signals
        signal_symbols = set()
        for signal in signals:
            signal_symbols.update(signal.get("symbols", []))
        
        # 5. Perform risk assessment (rate limited)
        risk_assessment = risk_management.assess_market_risk(
            list(signal_symbols), signals, market_data
        )
        logger.info(f"Completed risk assessment: {risk_assessment.get('overall_risk_level', 'unknown')} risk")
        
        # 6. Generate orders based on signals
        orders = []
        executed_orders = []
        
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
            
            # Calculate quantity
            quantity = calculate_position_size(
                symbol, 
                signal_type, 
                symbol_risk, 
                market_data, 
                Config.MAX_POSITION_SIZE
            )
            
            if quantity > 0:
                # Create order object
                order = {
                    "symbol": symbol,
                    "action": signal_type,
                    "quantity": quantity,
                    "risk_level": symbol_risk,
                    "estimated_cost": quantity * market_data.get(symbol, {}).get("current_price", 0),
                    "news_id": signal.get("news_id")
                }
                
                orders.append(order)
                
                # Execute the order if trading is enabled
                if Config.TRADING_ENABLED and not args.simulate:
                    try:
                        # Execute through broker API
                        execution_result = broker.execute_trade(
                            symbol=symbol,
                            direction=signal_type,
                            quantity=quantity
                        )
                        
                        # Add execution result to order
                        order["execution_result"] = execution_result
                        executed_orders.append(order)
                        
                        logger.info(f"Order executed: {signal_type} {quantity} {symbol} - Result: {execution_result['status']}")
                    except Exception as e:
                        logger.error(f"Error executing order: {e}")
                        order["execution_result"] = {"status": "ERROR", "reason": str(e)}
                        executed_orders.append(order)
                else:
                    # Simulated execution
                    order["execution_result"] = {
                        "status": "SIMULATED",
                        "dealReference": f"SIM-{len(executed_orders)}",
                        "details": "Trading disabled or simulation mode"
                    }
                    executed_orders.append(order)
                    logger.info(f"Order simulated: {signal_type} {quantity} {symbol}")
        
        logger.info(f"Generated {len(orders)} trading orders")
        orders_created = len(orders)
        
        # Save orders to database
        if executed_orders:
            db.save_trading_orders(executed_orders)
        
        # 7. Print summary of results
        print("\n===== ASX Trader Results (Curl Version) =====")
        print(f"Analyzed {len(news_items)} news items for {len(symbols)} symbols")
        print(f"Generated {len(signals)} trading signals")
        print(f"Created {len(orders)} trading orders")
        print(f"Overall market risk: {risk_assessment.get('overall_risk_level', 'unknown')}")
        
        print("\nTop Trading Signals:")
        for i, signal in enumerate(signals[:5], 1):
            symbol = signal.get("symbols", ["MARKET"])[0] if signal.get("symbols") else "MARKET"
            signal_type = signal.get("signal", "NONE")
            confidence = signal.get("confidence", "NONE")
            reason = signal.get("reasoning", "")[:150] + "..." if signal.get("reasoning", "") else "No reasoning provided"
            
            print(f"{i}. {symbol} - {signal_type} ({confidence})")
            print(f"   News: {signal.get('headline', '')[:80]}...")
            print(f"   Reason: {reason}")
            print()
        
        if executed_orders:
            print("\nTrading Orders:")
            for i, order in enumerate(executed_orders[:5], 1):
                price = market_data.get(order["symbol"], {}).get("current_price", 0)
                total = order["quantity"] * price
                status = order["execution_result"]["status"]
                print(f"{i}. {order['action']} {order['quantity']} {order['symbol']} @ ${price:.2f} = ${total:.2f}")
                print(f"   Risk Level: {order['risk_level']}")
                print(f"   Status: {status}")
                if "dealReference" in order["execution_result"]:
                    print(f"   Reference: {order['execution_result']['dealReference']}")
                print()
        
    except Exception as e:
        logger.error(f"Error in trading cycle: {e}")
        traceback.print_exc()  # Print full stack trace
        status = f"error:{str(e)}"
    
    end_time = datetime.datetime.now()
    logger.info(f"Trading cycle completed at {end_time} (duration: {end_time - start_time})")
    
    return status, symbols_analyzed, signals_generated, orders_created

def main():
    """Main function to run the ASX Trader system"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="ASX Trader System (Curl Version)")
    parser.add_argument("--symbols", type=str, help="Comma-separated list of symbols to analyze")
    parser.add_argument("--max-symbols", type=int, default=5, help="Maximum number of symbols to analyze")
    parser.add_argument("--news-limit", type=int, default=10, help="Maximum number of news items to fetch")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--force-run", action="store_true", help="Force run even if market is closed")
    parser.add_argument("--simulate", action="store_true", help="Simulate trades without execution")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting ASX Trader System (Curl Version)")
    
    # Test the OpenAI client
    try:
        test_response = openai_client.chat_completion(
            model="o4-mini",
            messages=[{"role": "user", "content": "Say hello"}]
        )
        logger.info(f"OpenAI curl client test successful: {test_response.get('content', '')}")
    except Exception as e:
        logger.error(f"OpenAI curl client test failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    # Initialize database
    db = Database()
    
    try:
        # Check if trading is enabled
        if Config.TRADING_ENABLED:
            if Config.BROKER_ACCOUNT_TYPE == "LIVE":
                logger.warning("⚠️ TRADING IS ENABLED WITH A LIVE ACCOUNT - REAL MONEY WILL BE USED ⚠️")
            else:
                logger.info("Trading is enabled with a DEMO account")
        else:
            logger.info("Trading is disabled, orders will be simulated")
        
        # Run once if specified
        if args.run_once:
            status, symbols_analyzed, signals_generated, orders_created = run_trading_cycle(args, db)
            next_run = get_next_run_time(Config.CYCLE_INTERVAL_MINUTES)
            db.record_run(
                datetime.datetime.now(), 
                datetime.datetime.now(), 
                status, 
                symbols_analyzed, 
                signals_generated, 
                orders_created, 
                next_run
            )
            return
        
        # Enter the main loop with 90-minute intervals
        while True:
            # Check if market is open or run is forced
            if is_market_open() or args.force_run:
                # Run the trading cycle
                status, symbols_analyzed, signals_generated, orders_created = run_trading_cycle(args, db)
                
                # Calculate next run time (90 minutes from now)
                next_run = get_next_run_time(Config.CYCLE_INTERVAL_MINUTES)
                
                # Record run in database
                db.record_run(
                    datetime.datetime.now(), 
                    datetime.datetime.now(), 
                    status, 
                    symbols_analyzed, 
                    signals_generated, 
                    orders_created, 
                    next_run
                )
                
                # Calculate wait time until next run
                wait_seconds = (next_run - datetime.datetime.now()).total_seconds()
                logger.info(f"Next run scheduled at {next_run} (waiting {wait_seconds/60:.1f} minutes)")
                
                # Wait until next run time
                time.sleep(wait_seconds)
            else:
                logger.info("Market is closed. Checking again in 15 minutes.")
                time.sleep(15 * 60)  # Check again in 15 minutes
        
    except KeyboardInterrupt:
        logger.info("Trading system stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        traceback.print_exc()  # Print full stack trace
    finally:
        # Close database connection
        db.close()

if __name__ == "__main__":
    main()
