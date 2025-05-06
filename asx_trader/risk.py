"""
Risk management module for trading system.
"""
import json
import logging
from datetime import datetime
from openai import OpenAI
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class RiskManagement:
    """Assesses market conditions and generates risk summaries"""
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
    def assess_market_risk(self, symbols, signals):
        """Assess market conditions and potential risks"""
        
        # Collect market data for the symbols
        market_data = self._get_market_data(symbols)
        
        # Prepare context for GPT
        context = {
            "market_data": market_data,
            "trading_signals": signals,
            "timestamp": datetime.now().isoformat()
        }
        
        prompt = f"""
        Please analyze the following market data and trading signals to provide a risk assessment:
        
        Market Data:
        {json.dumps(market_data, indent=2)}
        
        Trading Signals:
        {json.dumps(signals, indent=2)}
        
        Provide a comprehensive risk assessment including:
        1. Overall market risk level (Low, Medium, High, Extreme)
        2. Specific risks for each symbol with signals
        3. Volatility assessment
        4. Recommended position sizes based on risk level
        5. Stop-loss recommendations
        
        Format the response as JSON.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            risk_assessment = json.loads(response.choices[0].message.content)
            
            return risk_assessment
        except Exception as e:
            logger.error(f"Error during risk assessment: {e}")
            return {"error": str(e), "risk_level": "unknown"}
            
    def _get_market_data(self, symbols):
        """Helper method to get market data for symbols"""
        # This would normally fetch real market data
        # For demonstration, return mock data
        
        market_data = {}
        for symbol in symbols:
            market_data[symbol] = {
                "current_price": round(100 * (1 + 0.1 * (hash(symbol) % 10)), 2),
                "volume": int(1000000 * (1 + 0.2 * (hash(symbol) % 5))),
                "52w_high": round(120 * (1 + 0.1 * (hash(symbol) % 10)), 2),
                "52w_low": round(80 * (1 + 0.1 * (hash(symbol) % 10)), 2),
                "pe_ratio": round(15 * (1 + 0.3 * (hash(symbol) % 3)), 1),
                "market_cap": int(1000000000 * (1 + 0.5 * (hash(symbol) % 20))),
            }
        
        return market_data