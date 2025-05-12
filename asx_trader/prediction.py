"""
GPT-enhanced prediction engine for news analysis.
"""
import json
import logging
from datetime import datetime
from openai import OpenAI
from asx_trader.config import Config
from asx_trader.utils import openai_rate_limiter

logger = logging.getLogger(__name__)

class GPTEnhancedPredictionEngine:
    """Analyzes news and generates trading signals using GPT"""
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
    def analyze_news(self, news_items):
        """Analyze news items and return trading signals"""
        results = []
        
        for i, news in enumerate(news_items):
            try:
                logger.info(f"Analyzing news item {i+1}/{len(news_items)}: {news.get('headline', '')[:50]}...")
                analysis = self._analyze_single_news_item(news)
                if analysis:
                    results.append(analysis)
                    
            except Exception as e:
                logger.error(f"Error analyzing news item: {e}")
                
        return results
    
    @openai_rate_limiter
    def _analyze_single_news_item(self, news):
        """Analyze a single news item with rate limiting applied"""
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
                model="o4-mini",  # Using o4-mini as specified
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2  # Lower temperature for more consistent results
            )
            
            # Parse the response
            analysis = json.loads(response.choices[0].message.content)
            
            # Add to results
            result = {
                "news_id": news.get("id"),
                "headline": news.get("headline"),
                "symbols": news.get("symbols", []),
                "signal": analysis.get("signal"),
                "confidence": analysis.get("confidence"),
                "reasoning": analysis.get("reasoning"),
                "analysis_time": datetime.now().isoformat()
            }
            
            return result
                
        except Exception as e:
            logger.error(f"Error in API call to analyze news: {e}")
            return None