#!/usr/bin/env python3
"""
Proof of Concept (POC) script for the GPT-enhanced trading system.
This simplified version demonstrates the core functionality with minimal resources.
"""
import os
import sys
import time
import logging
import argparse
from dotenv import load_dotenv

# Set up logging before imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("trading_poc.log")
    ]
)
logger = logging.getLogger(__name__)

# Now import modules
from trading.config import Config
from trading.news import ASXNewsCollector
from trading.market import MarketScanner
from trading.prediction import GPTEnhancedPredictionEngine
from trading.risk import RiskManagement
from trading.database import Database

def main():
    """Main function to run the POC trading system"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="GPT-Enhanced Trading System POC")
    parser.add_argument("--symbols", type=str, help="Comma-separated list of symbols to analyze")
    parser.add_argument("--max-symbols", type=int, default=10, help="Maximum number of symbols to analyze")
    parser.add_argument("--news-limit", type=int, default=20, help="Maximum number of news items to fetch")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting GPT-Enhanced Trading System POC")
    
    # Initialize database
    db = Database("data/trading_poc.db")
    
    try:
        # Initialize components with minimal configuration
        news_collector = ASXNewsCollector()
        market_scanner = MarketScanner()
        prediction_engine = GPTEnhancedPredictionEngine()
        risk_management = RiskManagement()
        
        # 1. Get symbols to analyze (either from args or market scan)
        if args.symbols:
            symbols = args.symbols.split(",")
            logger.info(f"Using provided symbols: {symbols}")
        else:
            # Limit number of symbols for POC
            all_symbols = market_scanner.get_market_symbols()
            symbols = all_symbols[:args.max_symbols]
            logger.info(f"Using {len(symbols)} symbols from market scan")
        
        # 2. Collect market data (simplified)
        market_data = market_scanner.get_market_data(symbols)
        logger.info(f"Collected market data for {len(market_data)} symbols")
        
        # 3. Collect news (limited)
        news_items = news_collector.fetch_latest_news(symbols, limit=args.news_limit)
        logger.info(f"Collected {len(news_items)} news items")
        
        if not news_items:
            logger.warning("No news items found, exiting POC")
            return
            
        # 4. Analyze news and generate signals (rate limited)
        signals = prediction_engine.analyze_news(news_items)
        logger.info(f"Generated {len(signals)} trading signals")
        
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
        print("\n===== GPT-Enhanced Trading System POC Results =====")
        print(f"Analyzed {len(news_items)} news items for {len(symbols)} symbols")
        print(f"Generated {len(signals)} trading signals")
        print(f"Overall market risk: {risk_assessment.get('overall_risk_level', 'unknown')}")
        
        print("\nTop Trading Signals:")
        for i, signal in enumerate(signals[:5], 1):
            print(f"{i}. {', '.join(signal.get('symbols', []))} - {signal.get('signal')} "
                  f"({signal.get('confidence')})")
            print(f"   Reason: {signal.get('reasoning', '')[:100]}...")
        
        print("\nPOC completed successfully. Results saved to database.")
        
    except Exception as e:
        logger.error(f"Error in POC execution: {e}")
    finally:
        # Close database connection
        db.close()

if __name__ == "__main__":
    main()