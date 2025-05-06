"""
GPT-enhanced prediction engine for news analysis.
"""
import json
import logging
from datetime import datetime
from openai import OpenAI
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class GPTEnhancedPredictionEngine:
    """Analyzes news and generates trading signals using GPT"""
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
    def analyze_news(self, news_items):
        """Analyze news items and return trading signals"""
        results = []
        
        for news in news_items:
            try:
                # Format the news for analysis
                prompt = f"""
                Please analyze this financial news and provide a trading signal (BUY, SELL, or HOLD):
                
                Headline: {news.get('headline', '')}
                Date: {news.get('published_date', '')}
                Content: {news.get('content', '')}
                Related Stocks: {', '.join(news.get('symbols', []))}
                
                Include reasoning and confidence level (low, medium, high) for your decision.
                Format response as JSON with fields: signal, confidence, reasoning
                """
                
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                # Parse the response
                analysis = json.loads(response.choices[0].message.content)
                
                # Add to results
                results.append({
                    "news_id": news.get("id"),
                    "headline": news.get("headline"),
                    "symbols": news.get("symbols", []),
                    "signal": analysis.get("signal"),
                    "confidence": analysis.get("confidence"),
                    "reasoning": analysis.get("reasoning"),
                    "analysis_time": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error analyzing news item: {e}")
                
        return results