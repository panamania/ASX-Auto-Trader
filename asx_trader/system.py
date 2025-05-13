
"""
Main trading system module that orchestrates all components.
"""
import logging
from datetime import datetime
from asx_trader.config import Config
from asx_trader.news import ASXNewsCollector
from asx_trader.market import MarketScanner
from asx_trader.prediction import GPTEnhancedPredictionEngine
from asx_trader.risk import RiskManagement
from asx_trader.utils import is_market_open, get_next_run_time

logger = logging.getLogger(__name__)

class TradingSystem:
    """Main system that orchestrates the entire trading pipeline"""
    def __init__(self):
        # Validate configuration
        Config.validate()
        
        # Initialize components
        self.news_collector = ASXNewsCollector()
        self.market_scanner = MarketScanner()
        self.prediction_engine = GPTEnhancedPredictionEngine()
        self.risk_management = RiskManagement()
        
        # Trading configuration
        self.max_position_size = Config.MAX_POSITION_SIZE
        self.trading_enabled = Config.TRADING_ENABLED
        
        logger.info(f"Trading system initialized with trading {'enabled' if self.trading_enabled else 'disabled'}")
        logger.info(f"Market scan mode: {Config.MARKET_SCAN_MODE}")
        
    def execute_trading_cycle(self, max_symbols=20, news_limit=50):
        """Execute a complete trading cycle"""
        try:
            cycle_start_time = datetime.now()
            logger.info(f"Starting trading cycle at {cycle_start_time}")
            
            # 1. Scan market for symbols
            all_symbols = self.market_scanner.get_market_symbols()
            symbols = all_symbols[:max_symbols]
            logger.info(f"Scanning {len(symbols)} symbols in the market")
            
            # 2. Collect market data
            market_data = self.market_scanner.get_market_data(symbols)
            
            # 3. Find potential opportunities (pre-filtering)
            opportunity_symbols = self.market_scanner.find_opportunities(market_data)
            logger.info(f"Found {len(opportunity_symbols)} potential opportunities")
            
            # 4. Collect news for the whole market and specific opportunities
            news_items = self.news_collector.fetch_latest_news(symbols=opportunity_symbols, limit=news_limit)
            logger.info(f"Collected {len(news_items)} news items")
                
            if not news_items:
                logger.info("No news items found, skipping cycle")
                return {"status": "skipped", "reason": "no news", "symbols": len(symbols), "signals": 0, "orders": 0}
                
            # 5. Analyze news and generate signals
            signals = self.prediction_engine.analyze_news(news_items)
            logger.info(f"Generated {len(signals)} trading signals")
            
            # Extract symbols from signals
            signal_symbols = set()
            for signal in signals:
                signal_symbols.update(signal.get("symbols", []))
                
            logger.info(f"Signals reference {len(signal_symbols)} unique symbols")
            
            # 6. Perform risk assessment on symbols with signals
            risk_assessment = self.risk_management.assess_market_risk(
                list(signal_symbols), signals, market_data
            )
            
            return {
                "status": "success",
                "scanned_symbols": len(symbols),
                "signals": len(signals),
                "orders": 0,  # No orders for POC
                "risk_level": risk_assessment.get("overall_risk_level", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            return {"status": "error", "message": str(e), "symbols": 0, "signals": 0, "orders": 0}
    
    def get_next_scheduled_run(self):
        """Get the next scheduled run time based on the 90-minute interval"""
        return get_next_run_time(Config.CYCLE_INTERVAL_MINUTES)
    
    def is_market_currently_open(self):
        """Check if the market is currently open"""
        return is_market_open()

