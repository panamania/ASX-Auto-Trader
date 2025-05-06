"""
Main trading system module that orchestrates all components.
"""
import logging
from datetime import datetime
from asx_trader.config import Config
from asx_trader.news import ASXNewsCollector
from asx_trader.prediction import GPTEnhancedPredictionEngine
from asx_trader.risk import RiskManagement
from asx_trader.broker import BrokerAPI
from asx_trader.monitoring import MonitoringSystem
from asx_trader.aws import AWSDeployment

logger = logging.getLogger(__name__)

class TradingSystem:
    """Main system that orchestrates the entire trading pipeline"""
    def __init__(self):
        # Validate configuration
        Config.validate()
        
        # Initialize components
        self.news_collector = ASXNewsCollector()
        self.prediction_engine = GPTEnhancedPredictionEngine()
        self.risk_management = RiskManagement()
        self.broker_api = BrokerAPI()
        self.monitoring = MonitoringSystem()
        self.cloud = AWSDeployment()
        
        # Trading configuration
        self.watch_symbols = Config.WATCH_SYMBOLS
        self.max_position_size = Config.MAX_POSITION_SIZE
        self.trading_enabled = Config.TRADING_ENABLED
        
        logger.info(f"Trading system initialized with trading {'enabled' if self.trading_enabled else 'disabled'}")
        
    def execute_trading_cycle(self):
        """Execute a complete trading cycle"""
        try:
            # 1. Collect news
            news_items = self.news_collector.fetch_latest_news(self.watch_symbols)
            if not news_items:
                logger.info("No news items found, skipping cycle")
                return {"status": "skipped", "reason": "no news"}
                
            # 2. Analyze news and generate signals
            signals = self.prediction_engine.analyze_news(news_items)
            
            # Extract symbols from signals
            signal_symbols = set()
            for signal in signals:
                signal_symbols.update(signal.get("symbols", []))
                
            # 3. Perform risk assessment
            risk_assessment = self.risk_management.assess_market_risk(
                list(signal_symbols), signals
            )
            
            # 4. Make trading decisions
            orders = self._make_trading_decisions(signals, risk_assessment)
            
            # 5. Execute trades if enabled
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
                
            # 6. Monitor and notify
            self.monitoring.track_trading_activity(
                executed_orders, signals, risk_assessment
            )
            
            # 7. Save results to cloud
            self.cloud.save_trading_results({
                "cycle_time": datetime.now().isoformat(),
                "news_count": len(news_items),
                "signals": signals,
                "risk_assessment": risk_assessment,
                "orders": executed_orders,
                "trading_enabled": self.trading_enabled
            }, "trading_cycle")
            
            return {
                "status": "success",
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
    
    def _make_trading_decisions(self, signals, risk_assessment):
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
                
                # Get current price from risk assessment
                current_price = next(
                    (data.get("current_price", 100) 
                     for s, data in risk_assessment.get("market_data", {}).items() 
                     if s == symbol),
                    100  # Default price if not found
                )
                
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
                        "news_id": signal.get("news_id")
                    })
        
        return orders