"""
GPT-enhanced prediction engine for news analysis.
"""
import json
import logging
import re
from datetime import datetime
from asx_trader.utils import openai_rate_limiter
from asx_trader.curl_openai import openai_client

logger = logging.getLogger(__name__)

class GPTEnhancedPredictionEngine:
    """Analyzes news and generates trading signals using GPT"""
    def __init__(self):
        self.client = openai_client

        self.asx_symbols = self._load_top_asx_symbols()
        
    def _load_top_asx_symbols(self):
        """Load a list of common ASX symbols for reference"""
        # Top 100 ASX symbols - this helps identify stocks mentioned in news
        return [
            "BHP", "CBA", "CSL", "NAB", "WBC", "ANZ", "FMG", "WES", "TLS", "RIO",
            "MQG", "NCM", "WOW", "GMG", "TCL", "STO", "WDS", "COL", "S32", "ALL",
            "AMC", "QBE", "RMD", "ASX", "ORG", "SHL", "MIN", "JHX", "REA", "CPU",
            "IAG", "FBU", "SGP", "AMP", "TWE", "OSH", "VCX", "CWY", "LLC", "AZJ",
            "DXS", "BOQ", "CTX", "GPT", "ORI", "AGL", "MGR", "BXB", "CCL", "DOW",
            "SCG", "JHG", "APA", "CAR", "SUN", "SEK", "NHF", "IGO", "BSL", "NST",
            "QAN", "MPL", "EVN", "BEN", "ALX", "HVN", "BWP", "CIM", "ALQ", "IPL",
            "SBM", "XRO", "CHC", "GNC", "SGR", "GWA", "OZL", "ANN", "LYC", "CNU",
            "GUD", "TAH", "RHC", "CGF", "ORA", "HLS", "NEC", "SKC", "ILU", "ABP",
            "BKW", "ELD", "JBH", "ALD", "SDF", "DMP", "ARB", "CCP", "FLT", "ABC"
        ]
        
    def analyze_news(self, news_items):
        """Analyze news items and return trading signals"""
        results = []
        
        for i, news in enumerate(news_items):
            try:
                logger.info(f"Analyzing news item {i+1}/{len(news_items)}: {news.get('headline', '')[:50]}...")
                
                # Enhance news with identified stock symbols
                enhanced_news = self._enhance_news_with_symbols(news)
                
                # Analyze the enhanced news
                analysis = self._analyze_single_news_item(enhanced_news)
                if analysis:
                    results.append(analysis)
                    
            except Exception as e:
                logger.error(f"Error analyzing news item: {e}")
                
        return results
    
    def _enhance_news_with_symbols(self, news):
        """
        Enhance news item by identifying potential ASX stock symbols 
        that might be mentioned in the content.
        """
        # Make a copy of the news item
        enhanced_news = dict(news)
        
        # Get content and headline
        content = news.get('content', '')
        headline = news.get('headline', '')
        
        # Existing symbols
        existing_symbols = set(news.get('symbols', []))
        
        # Find potential stock symbols in content and headline
        found_symbols = set()
        
        # Check each known ASX symbol
        for symbol in self.asx_symbols:
            # Check if symbol appears as a word in content or headline
            symbol_pattern = r'\b' + symbol + r'\b'
            if re.search(symbol_pattern, content) or re.search(symbol_pattern, headline):
                found_symbols.add(symbol)
                
        # Check for company name mentions that can be mapped to symbols
        company_to_symbol = {
            "Commonwealth Bank": "CBA",
            "BHP Group": "BHP",
            "CSL Limited": "CSL",
            "National Australia Bank": "NAB",
            "Westpac": "WBC",
            "ANZ Bank": "ANZ",
            "Fortescue Metals": "FMG",
            "Wesfarmers": "WES",
            "Telstra": "TLS",
            "Rio Tinto": "RIO",
            "Macquarie Group": "MQG",
            "Newcrest Mining": "NCM",
            "Woolworths": "WOW"
        }
        
        for company, symbol in company_to_symbol.items():
            if company in content or company in headline:
                found_symbols.add(symbol)
        
        # Combine existing and found symbols
        all_symbols = list(existing_symbols.union(found_symbols))
        
        # Update the news item with enhanced symbols
        enhanced_news['symbols'] = all_symbols
        
        return enhanced_news
    
    @openai_rate_limiter
    def _analyze_single_news_item(self, news):
        """Analyze a single news item with rate limiting applied"""
        try:
            # Get the symbols as a comma-separated string
            symbols_str = ', '.join(news.get('symbols', []))
            
            # Format the news for analysis
            prompt = f"""
            Please analyze this financial news and provide a trading signal (BUY, SELL, or HOLD):
            
            Headline: {news.get('headline', '')}
            Date: {news.get('published_date', '')}
            Content: {news.get('content', '')}
            Related Stocks: {symbols_str}
            
            First, identify any ASX-listed stocks that might be affected by this news.
            Then provide a trading signal (BUY, SELL, or HOLD) for the most relevant stock,
            with reasoning and confidence level (low, medium, high).
            
            Format response as JSON with fields: 
            - symbol (the most relevant stock code, or "MARKET" if it's general market news)
            - signal (BUY, SELL, or HOLD)
            - confidence (low, medium, or high)
            - reasoning (brief explanation)
            """
            
            response = self.client.chat_completion(
                model="o4-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
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
                    analysis = {
                        "symbol": news.get("symbols", ["MARKET"])[0] if news.get("symbols") else "MARKET",
                        "signal": "HOLD", 
                        "confidence": "low", 
                        "reasoning": "No analysis available due to empty API response"
                    }
                    analysis = {"signal": "HOLD", "confidence": "low", "reasoning": "No analysis available due to empty API response"}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw content: {content}")
                # Create a default analysis
                analysis = {
                    "symbol": news.get("symbols", ["MARKET"])[0] if news.get("symbols") else "MARKET",
                    "signal": "HOLD", 
                    "confidence": "low",
                    "reasoning": f"Error parsing response: {str(e)}. Raw content: {content[:100]}"
                }
            
            # Add to results
            result = {
                "news_id": news.get("id"),
                "headline": news.get("headline"),
                "symbols": [analysis.get("symbol")] if analysis.get("symbol") != "MARKET" else [],
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
                "symbols": news.get("symbols", [])[:1] if news.get("symbols") else [],
                "symbols": news.get("symbols", []),
                "signal": "ERROR",
                "confidence": "none",
                "reasoning": f"API error: {str(e)}",
                "analysis_time": datetime.now().isoformat()
            }
