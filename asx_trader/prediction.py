"""
GPT-enhanced prediction engine for news analysis.
"""
import json
import logging
from datetime import datetime
from asx_trader.utils import openai_rate_limiter
from asx_trader.curl_openai import openai_client

logger = logging.getLogger(__name__)

class GPTEnhancedPredictionEngine:
    """Analyzes news and generates trading signals using GPT"""
    def __init__(self):
        self.client = openai_client
        
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
            
            response = self.client.chat_completion(
                model="o4-mini",  # Using o4-mini as specified
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                # Note: removing temperature parameter to use default (1)
            )
            
            # Get the content
            content = response.get("content", "")
            logger.debug(f"Raw response content: {content}")
            
            # Parse the response with error handling
            try:
                if content and content.strip():
                    analysis = json.loads(content)
                else:
                    logger.warning("Empty response content from API")
                    analysis = {"signal": "HOLD", "confidence": "low", "reasoning": "No analysis available due to empty API response"}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw content: {content}")
                # Create a default analysis
                analysis = {
                    "signal": "HOLD", 
                    "confidence": "low",
                    "reasoning": f"Error parsing response: {str(e)}. Raw content: {content[:100]}"
                }
            
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
            # Return a minimal valid result instead of None
            return {
                "news_id": news.get("id", "unknown"),
                "headline": news.get("headline", "unknown"),
                "symbols": news.get("symbols", []),
                "signal": "ERROR",
                "confidence": "none",
                "reasoning": f"API error: {str(e)}",
                "analysis_time": datetime.now().isoformat()
            }
