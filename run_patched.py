
#!/usr/bin/env python3
"""
Patched main script for the ASX Trader system.
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

# Apply patch before importing any other modules
logger.info("Applying OpenAI client patch...")
from asx_trader.patch import patch_openai_client

# Now import other modules
try:
    from asx_trader.config import Config
    from asx_trader.news import ASXNewsCollector
    from asx_trader.market import MarketScanner
    from asx_trader.prediction import GPTEnhancedPredictionEngine
    from asx_trader.risk import RiskManagement
    from asx_trader.database import Database
    from asx_trader.utils import is_market_open, get_next_run_time
except Exception as e:
    logger.error(f"Error importing modules: {e}")
    traceback.print_exc()
    sys.exit(1)

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
            # Limit number of symbols for POC
            all_symbols = market_scanner.get_market_symbols()
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
        
        # 6. Print summary of results
        print("\n===== ASX Trader Results =====")
        print(f"Analyzed {len(news_items)} news items for {len(symbols)} symbols")
        print(f"Generated {len(signals)} trading signals")
        print(f"Overall market risk: {risk_assessment.get('overall_risk_level', 'unknown')}")
        
        print("\nTop Trading Signals:")
        for i, signal in enumerate(signals[:5], 1):
            print(f"{i}. {', '.join(signal.get('symbols', []))} - {signal.get('signal')} "
                  f"({signal.get('confidence')})")
            print(f"   Reason: {signal.get('reasoning', '')[:100]}...")
        
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
    parser = argparse.ArgumentParser(description="ASX Trader System (Patched)")
    parser.add_argument("--symbols", type=str, help="Comma-separated list of symbols to analyze")
    parser.add_argument("--max-symbols", type=int, default=5, help="Maximum number of symbols to analyze")
    parser.add_argument("--news-limit", type=int, default=10, help="Maximum number of news items to fetch")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--force-run", action="store_true", help="Force run even if market is closed")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting ASX Trader System (Patched Version)")
    
    # Initialize database
    db = Database()
    
    try:
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

