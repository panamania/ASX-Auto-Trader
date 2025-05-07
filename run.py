#!/usr/bin/env python3
"""
Main entry point for the ASX-Auto-Trader system.
"""
import os
import sys
import time
import logging
from dotenv import load_dotenv
from asx_trader.system import TradingSystem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("trading.log")
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the trading system"""
    # Load environment variables
    load_dotenv()
    
    # Initialize trading system
    trading_system = TradingSystem()
    
    # Check if running in one-time mode
    one_time = os.environ.get("ONE_TIME_RUN", "false").lower() == "true"
    
    if one_time:
        logger.info("Running in one-time mode...")
        result = trading_system.execute_trading_cycle()
        logger.info(f"Trading cycle completed: {result}")
        return
    
    # Run in continuous mode
    logger.info("Starting ASX-Auto-Trader in continuous mode...")
    
    try:
        while True:
            logger.info("Starting trading cycle...")
            result = trading_system.execute_trading_cycle()
            logger.info(f"Trading cycle completed: {result}")
            
            # Wait for next cycle
            interval = int(os.environ.get("CYCLE_INTERVAL_SECONDS", "3600"))
            logger.info(f"Waiting {interval} seconds until next cycle...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("Trading system stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        raise

if __name__ == "__main__":
    main()