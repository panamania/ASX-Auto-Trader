"""
Risk management module for trading system.
"""
import json
import logging
from datetime import datetime
from openai import OpenAI
from trading.config import Config

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
        
        # Prepare context for GPT
        context = {
            "market_data": market_data,
            "trading_signals": signals,
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate overall market metrics
        market_metrics = self._calculate_market_metrics(market_data)
        
        prompt = f"""
        Please analyze the following market data and trading signals to provide a risk assessment:
        
        Market Overview:
        {json.dumps(market_metrics, indent=2)}
        
        Market Data for Specific Symbols:
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
            
            # Add the market data we used
            risk_assessment["market_data"] = market_data
            risk_assessment["market_metrics"] = market_metrics
            
            return risk_assessment
        except Exception as e:
            logger.error(f"Error during risk assessment: {e}")
            return {"error": str(e), "risk_level": "unknown"}
    
    def _calculate_market_metrics(self, market_data):
        """Calculate overall market metrics from individual stock data."""
        try:
            metrics = {
                "avg_pe_ratio": 0,
                "avg_volume": 0,
                "avg_price_change_pct": 0,
                "symbols_up": 0,
                "symbols_down": 0,
                "symbols_flat": 0,
                "total_symbols": len(market_data),
            }
            
            if not market_data:
                return metrics
                
            # Calculate averages and counts
            pe_ratios = []
            volumes = []
            price_changes = []
            
            for symbol, data in market_data.items():
                # PE Ratio
                if "pe_ratio" in data and data["pe_ratio"] is not None and data["pe_ratio"] > 0:
                    pe_ratios.append(data["pe_ratio"])
                    
                # Volume
                if "volume" in data and data["volume"] is not None:
                    volumes.append(data["volume"])
                    
                # Price change
                if "price_change_pct" in data and data["price_change_pct"] is not None:
                    change = data["price_change_pct"]
                    price_changes.append(change)
                    
                    # Count up/down/flat
                    if change > 0.005:  # 0.5% up
                        metrics["symbols_up"] += 1
                    elif change < -0.005:  # 0.5% down
                        metrics["symbols_down"] += 1
                    else:
                        metrics["symbols_flat"] += 1
            
            # Calculate averages
            if pe_ratios:
                metrics["avg_pe_ratio"] = sum(pe_ratios) / len(pe_ratios)
                
            if volumes:
                metrics["avg_volume"] = sum(volumes) / len(volumes)
                
            if price_changes:
                metrics["avg_price_change_pct"] = sum(price_changes) / len(price_changes)
                metrics["market_direction"] = "up" if metrics["avg_price_change_pct"] > 0 else "down"
                
            return metrics
        except Exception as e:
            logger.error(f"Error calculating market metrics: {e}")
            return {}
            
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
                "price_change_pct": round((hash(symbol) % 21 - 10) / 100, 4),  # -10% to +10%
            }
        
        return market_data