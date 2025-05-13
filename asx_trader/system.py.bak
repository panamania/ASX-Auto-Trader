"""
Main trading system module that orchestrates all components.
"""
import logging
from datetime import datetime
from trading.config import Config
from trading.news import ASXNewsCollector
from trading.market import MarketScanner
from trading.prediction import GPTEnhancedPredictionEngine
from trading.risk import RiskManagement
from trading.broker import BrokerAPI
from trading.monitoring import MonitoringSystem
from trading.aws import AWSDeployment

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
        self.broker_api = BrokerAPI()
        self.monitoring = MonitoringSystem()
        self.cloud = AWSDeployment()
        
        # Trading configuration
        self.max_position_size = Config.MAX_POSITION_SIZE
        self.trading_enabled = Config.TRADING_ENABLED
        
        logger.info(f"Trading system initialized with trading {'enabled' if self.trading_enabled else 'disabled'}")
        logger.info(f"Market scan mode: {Config.MARKET_SCAN_MODE}")
        
    def execute_trading_cycle(self):
        """Execute a complete trading cycle"""
        try:
            cycle_start_time = datetime.now()
            logger.info(f"Starting trading cycle at {cycle_start_time}")
            
            # 1. Scan market for symbols
            all_symbols = self.market_scanner.get_market_symbols()
            logger.info(f"Scanning {len(all_symbols)} symbols in the market")
            
            # 2. Collect market data
            market_data = self.market_scanner.get_market_data(all_symbols)
            
            # 3. Find potential opportunities (pre-filtering)
            opportunity_symbols = self.market_scanner.find_opportunities(market_data)
            logger.info(f"Found {len(opportunity_symbols)} potential opportunities")
            
            # 4. Collect news for the whole market and specific opportunities
            market_news = self.news_collector.fetch_latest_news(market_wide=True)
            
            # Also get specific news for opportunity symbols if we have a reasonable number
            symbol_specific_news = []
            if opportunity_symbols and len(opportunity_symbols) <= 50:
                symbol_specific_news = self.news_collector.fetch_latest_news(
                    symbols=opportunity_symbols, 
                    market_wide=False
                )
            
            # Combine all news
            all_news = market_news + symbol_specific_news
            logger.info(f"Collected {len(all_news)} news items")
                
            if not all_news:
                logger.info("No news items found, skipping cycle")
                return {"status": "skipped", "reason": "no news"}
                
            # 5. Analyze news and generate signals
            signals = self.prediction_engine.analyze_news(all_news)
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
            
            # 7. Make trading decisions
            orders = self._make_trading_decisions(signals, risk_assessment, market_data)
            logger.info(f"Generated {len(orders)} order recommendations")
            
            # 8. Execute trades if enabled
            executed_orders = []
            if self.trading_enabled:
                for order in orders:
                    result = self.broker_api.place_trade(
                        order["symbol"], 
                        order["action"], 
                        order["quantity"]
                    )
                    executed_orders.append({**order, "execution_result": result})
            else:
                logger.info("Trading is disabled, skipping order execution")
                executed_orders = [
                    {**order, "execution_result": {"status": "simulated", "order_id": f"sim-{idx}"}} 
                    for idx, order in enumerate(orders)
                ]
                
            # 9. Monitor and notify
            self.monitoring.track_trading_activity(
                executed_orders, signals, risk_assessment
            )
            
            # 10. Save results to cloud
            cycle_data = {
                "cycle_time": cycle_start_time.isoformat(),
                "completion_time": datetime.now().isoformat(),
                "scan_mode": Config.MARKET_SCAN_MODE,
                "scanned_symbols": len(all_symbols),
                "opportunity_symbols": len(opportunity_symbols),
                "news_count": len(all_news),
                "signals": signals,
                "risk_assessment": risk_assessment,
                "orders": executed_orders,
                "trading_enabled": self.trading_enabled
            }
            
            self.cloud.save_trading_results(cycle_data, "trading_cycle")
            
            return {
                "status": "success",
                "scanned_symbols": len(all_symbols),
                "signals": len(signals),
                "orders": len(executed_orders)
            }
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            self.monitoring.send_notification(
                "TRADING CYCLE ERROR",
                f"Error occurred during trading cycle: {str(e)}"
            )
            return {"status": "error", "message": str(e)}
    
    def _make_trading_decisions(self, signals, risk_assessment, market_data=None):
        """Translate signals into actionable orders with risk management applied"""
        orders = []
        
        # Get overall risk factor
        overall_risk = risk_assessment.get("overall_risk_level", "Medium")
        risk_factor = {
            "Low": 1.0,
            "Medium": 0.7,
            "High": 0.3,
            "Extreme": 0.1
        }.get(overall_risk, 0.5)
        
        # Process each signal
        for signal in signals:
            signal_action = signal.get("signal")
            if signal_action not in ["BUY", "SELL"]:
                continue  # Skip HOLD signals
                
            for symbol in signal.get("symbols", []):
                # Check symbol-specific risk
                symbol_risk = next(
                    (r.get("risk_level", "Medium") 
                     for r in risk_assessment.get("symbol_risks", []) 
                     if r.get("symbol") == symbol),
                    "Medium"
                )
                
                symbol_risk_factor = {
                    "Low": 1.0,
                    "Medium": 0.7,
                    "High": 0.3,
                    "Extreme": 0.1
                }.get(symbol_risk, 0.5)
                
                # Adjust position size based on confidence and risk
                confidence_factor = {
                    "high": 1.0,
                    "medium": 0.7,
                    "low": 0.3
                }.get(signal.get("confidence", "").lower(), 0.5)
                
                # Calculate position size
                position_size = self.max_position_size * risk_factor * symbol_risk_factor * confidence_factor
                
                # Get current price from market data or risk assessment
                current_price = None
                
                # First try to get from market data
                if market_data and symbol in market_data:
                    current_price = market_data[symbol].get("price", None)
                
                # If not found, try risk assessment
                if current_price is None:
                    current_price = next(
                        (data.get("current_price", None) 
                         for s, data in risk_assessment.get("market_data", {}).items() 
                         if s == symbol),
                        None  
                    )
                
                # Default price if still not found
                if current_price is None:
                    current_price = 100
                    logger.warning(f"No price data found for {symbol}, using default price of {current_price}")
                
                # Calculate quantity
                quantity = int(position_size / current_price)
                
                if quantity > 0:
                    orders.append({
                        "symbol": symbol,
                        "action": signal_action,
                        "quantity": quantity,
                        "estimated_cost": quantity * current_price,
                        "confidence": signal.get("confidence"),
                        "risk_level": symbol_risk,
                        "news_id": signal.get("news_id"),
                        "reasoning": signal.get("reasoning", "")
                    })
        
        return orders