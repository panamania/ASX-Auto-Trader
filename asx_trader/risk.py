"""
Risk management module for trading system.
"""
import json
import logging
from datetime import datetime
from openai import OpenAI
from trading.config import Config
from trading.utils import openai_rate_limiter

logger = logging.getLogger(__name__)

class RiskManagement:
    """Assesses market conditions and generates risk summaries"""
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
    def assess_market_risk(self, symbols, signals, market_data=None):
        """
        Assess market conditions and potential risks.
        
        Args:
            symbols: List of symbols to assess risk for
            signals: Trading signals generated for these symbols
            market_data: Optional pre-loaded market data dictionary
            
        Returns:
            dict: Risk assessment results
        """
        # Only process a limited number of symbols for POC
        max_symbols = min(20, len(symbols))
        if len(symbols) > max_symbols:
            logger.info(f"Limiting risk assessment to {max_symbols} symbols for POC")
            symbols = symbols[:max_symbols]
        
        # Get market data if not provided
        if market_data is None:
            market_data = self._get_market_data(symbols)
        else:
            # Filter to only the symbols we need to assess
            filtered_market_data = {}
            for symbol in symbols:
                if symbol in market_data:
                    filtered_market_data[symbol] = market_data[symbol]
            market_data = filtered_market_data
        
        # Calculate overall market metrics
        market_metrics = self._calculate_market_metrics(market_data)
        
        # For POC, only analyze a subset of signals
        max_signals = min(10, len(signals))
        if len(signals) > max_signals:
            logger.info(f"Limiting risk assessment to {max_signals} signals for POC")
            signals = signals[:max_signals]
        
        # Perform the risk assessment
        return self._perform_risk_assessment(market_data, signals, market_metrics)
    
    @openai_rate_limiter
    def _perform_risk_assessment(self, market_data, signals, market_metrics):
        """Perform risk assessment with rate limiting applied"""
        try:
            prompt = f"""
            Please analyze the following market data and trading signals to provide a risk assessment:
            
            Market Overview:
            {json.dumps(market_metrics, indent=2)}
            
            Market Data for Specific Symbols:
            {json.dumps(market_data, indent=2)}
            
            Trading Signals:
            {json.dumps(signals, indent=2)}
            
            Provide a concise risk assessment including:
            1. Overall market risk level (Low, Medium, High, Extreme)
            2. Specific risks for each symbol with signals
            3. Recommended position sizes based on risk level
            
            Format the response as JSON.
            """
            
            response = self.client.chat.completions.create(
                model="o4-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            risk_assessment = json.loads(response.choices[0].message.content)
            
            # Add the market data we used
            risk_assessment["market_data"] = market_data
            risk_assessment["market_metrics"] = market_metrics
            
            return risk_assessment
        except Exception as e:
            logger.error(f"Error during risk assessment: {e}")
            return {"error": str(e), "risk_level": "unknown"}
    
    def _calculate_market_metrics(self, market_data):
        """Calculate overall market metrics from individual stock data."""
        # Simplified metrics calculation for POC
        metrics = {
            "total_symbols": len(market_data),
            "average_price": 0,
            "symbols_up": 0,
            "symbols_down": 0
        }
        
        if not market_data:
            return metrics
            
        # Calculate simple averages
        total_price = 0
        for symbol, data in market_data.items():
            total_price += data.get("current_price", 0)
            
            # Count up/down based on price_change_pct
            if data.get("price_change_pct", 0) > 0:
                metrics["symbols_up"] += 1
            else:
                metrics["symbols_down"] += 1
        
        if len(market_data) > 0:
            metrics["average_price"] = total_price / len(market_data)
            
        return metrics
            
    def _get_market_data(self, symbols):
        """Helper method to get market data for symbols"""
        # Simplified mock data for POC
        market_data = {}
        for symbol in symbols:
            market_data[symbol] = {
                "current_price": round(100 * (1 + 0.1 * (hash(symbol) % 10)), 2),
                "volume": int(1000000 * (1 + 0.2 * (hash(symbol) % 5))),
                "price_change_pct": round((hash(symbol) % 21 - 10) / 100, 4),  # -10% to +10%
            }
        
        return market_data