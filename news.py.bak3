
"""
News collector module using NewsData.io for ASX stock news.
"""
import logging
import requests
import json
import random
from datetime import datetime, timedelta
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class ASXNewsCollector:
    """Collects news from NewsData.io with focus on ASX stocks"""
    def __init__(self):
        self.newsdata_api_key = Config.NEWSDATA_API_KEY
        self.use_newsdata_api = bool(self.newsdata_api_key)
        
        # Cache for news data to reduce API calls
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=3)  # Cache for 3 hours
        
    def fetch_latest_news(self, symbols=None, limit=None, market_wide=True):
        """
        Fetch latest news for specified stock symbols or market-wide news.
        
        Args:
            symbols: Optional list of symbols to fetch news for.
            limit: Maximum number of news items to return.
            market_wide: Whether to include market-wide news.
            
        Returns:
            list: List of news items
        """
        logger.info(f"Fetching news for {'market-wide' if market_wide else symbols}")
        
        # Set default limit
        if limit is None:
            limit = 20 if market_wide else 10
        
        # Cache key for this request
        cache_key = f"news_{market_wide}_{'-'.join(symbols or [])}"
        
        # Check cache first
        if cache_key in self.cache and datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
            logger.info("Using cached news data")
            return self.cache[cache_key][:limit]
        
        try:
            news_items = []
            
            if self.use_newsdata_api:
                if market_wide:
                    # Fetch market-wide Australian financial news
                    market_news = self._fetch_newsdata_market_news(limit=limit)
                    news_items.extend(market_news)
                
                # Fetch specific news for each symbol if provided
                if symbols:
                    for symbol in symbols[:5]:  # Limit to 5 symbols to avoid too many API calls
                        symbol_news = self._fetch_newsdata_symbol_news(symbol, limit=3)
                        news_items.extend(symbol_news)
            
            # If we couldn't get enough news from the API, generate mock data
            if len(news_items) < limit / 2:
                logger.warning(f"Not enough news from NewsData.io ({len(news_items)}), adding mock news")
                mock_news = self._generate_mock_news(
                    symbols, limit - len(news_items), market_wide
                )
                news_items.extend(mock_news)
            
            # Deduplicate and limit
            unique_news = []
            news_ids = set()
            for news in news_items:
                if news.get("id") not in news_ids:
                    news_ids.add(news.get("id"))
                    unique_news.append(news)
                    if len(unique_news) >= limit:
                        break
            
            # Cache the results
            self.cache[cache_key] = unique_news
            self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
            
            logger.info(f"Fetched {len(unique_news)} news items")
            return unique_news
            
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            # Fall back to mock data
            return self._generate_mock_news(symbols, limit, market_wide)
    
    def _fetch_newsdata_market_news(self, limit=10):
        """
        Fetch financial news from NewsData.io for the Australian market.
        
        Args:
            limit: Maximum number of news items to return.
            
        Returns:
            list: List of news items
        """
        try:
            url = "https://newsdata.io/api/1/news"
            
            params = {
                "apikey": self.newsdata_api_key,
                "country": "au",  # Australia
                "category": "business",  # Business category
                "language": "en",  # English
                "size": limit
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "success":
                logger.warning(f"NewsData.io API returned error: {data.get('results', {}).get('message')}")
                return []
            
            news_items = []
            results = data.get("results", [])
            
            for idx, article in enumerate(results):
                # Extract article data
                news_id = article.get("article_id") or f"newsdata-{idx}"
                title = article.get("title", "")
                description = article.get("description", "")
                content = article.get("content", description)
                source = article.get("source_id", "")
                published = article.get("pubDate", "")
                
                # Extract ASX symbols mentioned in the content
                symbols = self._extract_asx_symbols_from_text(title + " " + content)
                
                # Create news item
                news_item = {
                    "id": news_id,
                    "headline": title,
                    "content": content or description,
                    "symbols": symbols,
                    "published_date": published,
                    "source": source,
                    "url": article.get("link", ""),
                    "data_source": "NewsData.io",
                    "sentiment": self._estimate_sentiment(title + " " + content)
                }
                
                news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching market news from NewsData.io: {e}")
            return []
    
    def _fetch_newsdata_symbol_news(self, symbol, limit=5):
        """
        Fetch news from NewsData.io for a specific ASX symbol.
        
        Args:
            symbol: The stock symbol to fetch news for.
            limit: Maximum number of news items to return.
            
        Returns:
            list: List of news items for the symbol
        """
        try:
            url = "https://newsdata.io/api/1/news"
            
            params = {
                "apikey": self.newsdata_api_key,
                "q": f"ASX {symbol}",  # Search for ASX + symbol
                "country": "au",  # Australia
                "language": "en",  # English
                "size": limit
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "success":
                logger.warning(f"NewsData.io API returned error: {data.get('results', {}).get('message')}")
                return []
            
            news_items = []
            results = data.get("results", [])
            
            for idx, article in enumerate(results):
                # Extract article data
                news_id = article.get("article_id") or f"newsdata-{symbol}-{idx}"
                title = article.get("title", "")
                description = article.get("description", "")
                content = article.get("content", description)
                source = article.get("source_id", "")
                published = article.get("pubDate", "")
                
                # Create news item with the specified symbol
                news_item = {
                    "id": news_id,
                    "headline": title,
                    "content": content or description,
                    "symbols": [symbol],  # Since we searched for this symbol specifically
                    "published_date": published,
                    "source": source,
                    "url": article.get("link", ""),
                    "data_source": "NewsData.io",
                    "sentiment": self._estimate_sentiment(title + " " + content)
                }
                
                news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching symbol news from NewsData.io for {symbol}: {e}")
            return []
    
    def _extract_asx_symbols_from_text(self, text):
        """
        Extract potential ASX stock symbols from text.
        This is a simple heuristic and may not catch all mentions.
        
        Args:
            text: Text to analyze for ASX symbols
            
        Returns:
            list: List of potential ASX symbols
        """
        import re
        
        # Look for patterns like "ASX: BHP" or "BHP.AX" or standalone 3-letter codes
        asx_patterns = [
            r'ASX:\s*([A-Z]{3})',  # ASX: ABC
            r'ASX\.[A-Z]{3}\.([A-Z]{3})',  # ASX.ASX.ABC
            r'([A-Z]{3})\.AX',  # ABC.AX
            r'\b([A-Z]{3})\b'  # Standalone ABC
        ]
        
        # Common ASX symbols to validate matches
        common_asx = set([
            'BHP', 'CBA', 'NAB', 'WBC', 'ANZ', 'RIO', 'CSL', 'WES', 'TLS', 'FMG',
            'GMG', 'MQG', 'TCL', 'WOW', 'NCM', 'STO', 'AMC', 'S32', 'QBE', 'BXB'
        ])
        
        symbols = set()
        
        for pattern in asx_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Prioritize common ASX symbols
                if match in common_asx:
                    symbols.add(match)
                # Otherwise, only add if it looks like an ASX symbol (3 letters)
                elif len(match) == 3 and match.isalpha() and match.isupper():
                    symbols.add(match)
        
        return list(symbols)
    
    def _estimate_sentiment(self, text):
        """
        Estimate the sentiment of a news article based on simple keyword matching.
        
        Args:
            text: The text to analyze
            
        Returns:
            str: "positive", "negative", or "neutral"
        """
        text = text.lower()
        
        positive_words = [
            'gain', 'profit', 'rise', 'up', 'surge', 'jump', 'positive', 'growth',
            'increase', 'higher', 'beat', 'exceed', 'strong', 'success', 'improved',
            'bullish', 'upgrade', 'opportunity'
        ]
        
        negative_words = [
            'loss', 'decline', 'drop', 'down', 'fall', 'negative', 'decrease',
            'lower', 'miss', 'weak', 'poor', 'fail', 'bearish', 'downgrade',
            'risk', 'concern', 'problem', 'trouble', 'challenge'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count * 1.5:
            return "positive"
        elif negative_count > positive_count * 1.5:
            return "negative"
        else:
            return "neutral"
            
    def _generate_mock_news(self, symbols=None, limit=10, market_wide=True):
        """Generate mock news data for testing purposes"""
        news_items = []
        
        # Default symbols if none provided
        if not symbols:
            symbols = ["BHP", "CBA", "NAB", "WBC", "ANZ", "RIO", "CSL", "WES", "TLS", "FMG"]
        
        # News templates
        news_templates = [
            {"type": "earnings", "sentiment": "positive", "headline": "{symbol} Reports Strong Quarterly Earnings", 
             "content": "{symbol} reported quarterly earnings above analyst expectations, with revenue up {percent}% year-over-year. The company cited strong demand for its products and services."},
            
            {"type": "earnings", "sentiment": "negative", "headline": "{symbol} Misses Earnings Expectations", 
             "content": "{symbol} reported disappointing quarterly results, with earnings per share below consensus estimates. Revenue declined {percent}% compared to the same period last year."},
            
            {"type": "acquisition", "sentiment": "positive", "headline": "{symbol} Acquires Competitor to Expand Market Share", 
             "content": "{symbol} announced today it has acquired {target} for ${amount} million, a move expected to expand its market presence and product offerings."},
            
            {"type": "management", "sentiment": "neutral", "headline": "CEO of {symbol} Steps Down", 
             "content": "The Chief Executive Officer of {symbol} has announced plans to step down after {years} years at the helm. The board has initiated a search for a successor."},
            
            {"type": "analyst", "sentiment": "positive", "headline": "Analysts Upgrade {symbol} to Buy", 
             "content": "Analysts at {bank} have upgraded {symbol} from Hold to Buy, citing improved growth prospects and favorable industry conditions. The price target was raised to ${price}."},
            
            {"type": "analyst", "sentiment": "negative", "headline": "Analysts Downgrade {symbol} on Growth Concerns", 
             "content": "Analysts at {bank} have downgraded {symbol} from Buy to Hold, citing concerns about slowing growth and competitive pressures. The price target was lowered to ${price}."},
            
            {"type": "market", "sentiment": "neutral", "headline": "ASX Market Update: Stocks {direction} on Economic Data", 
             "content": "Australian stocks {direction_verb} today as investors digested new economic data showing {economic_indicator}. The ASX 200 {direction_verb} {percent}% in trading."}
        ]
        
        # Banks and target companies for news generation
        banks = ["Goldman Sachs", "Morgan Stanley", "UBS", "JP Morgan", "Macquarie"]
        target_companies = ["TechCorp", "InnovateAU", "Pacific Solutions", "MetalWorks", "DigitalVentures"]
        
        # Generate unique news IDs
        base_id = int(datetime.now().timestamp())
        
        # Generate news items
        for i in range(limit):
            try:
                # Select random template
                template = random.choice(news_templates)
                
                # For market-wide news, use market templates or assign to random symbols
                if market_wide and template["type"] == "market":
                    news_symbols = []
                    direction = random.choice(["Up", "Down", "Mixed"])
                    direction_verb = "gained" if direction == "Up" else "fell" if direction == "Down" else "ended mixed"
                    economic_indicator = random.choice([
                        "stronger than expected GDP growth", 
                        "rising inflation concerns", 
                        "improving employment figures",
                        "weaker consumer confidence",
                        "positive manufacturing data"
                    ])
                    
                    headline = template["headline"].format(direction=direction)
                    content = template["content"].format(
                        direction_verb=direction_verb,
                        economic_indicator=economic_indicator,
                        percent=round(random.uniform(0.1, 2.5), 1)
                    )
                else:
                    # Choose random symbol(s) for the news
                    if market_wide:
                        news_symbols = random.sample(symbols, random.randint(1, min(3, len(symbols))))
                    else:
                        news_symbols = [random.choice(symbols)]
                    
                    symbol = news_symbols[0]
                    percent = round(random.uniform(2, 15), 1)
                    price = round(random.uniform(20, 150), 2)
                    bank = random.choice(banks)
                    target = random.choice(target_companies)
                    amount = random.randint(100, 2000)
                    years = random.randint(3, 10)
                    
                    headline = template["headline"].format(
                        symbol=symbol, 
                        bank=bank, 
                        target=target
                    )
                    content = template["content"].format(
                        symbol=symbol, 
                        percent=percent, 
                        price=price, 
                        bank=bank, 
                        target=target, 
                        amount=amount, 
                        years=years
                    )
                
                # Generate a random timestamp within the last 24 hours
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                published_date = (datetime.now() - timedelta(hours=hours_ago, minutes=minutes_ago)).isoformat()
                
                # Create news item
                news_item = {
                    "id": f"mock-news-{base_id + i}",
                    "headline": headline,
                    "content": content,
                    "symbols": news_symbols,
                    "published_date": published_date,
                    "source": random.choice(["ASX Announcements", "Financial Review", "The Australian", "Bloomberg", "Reuters"]),
                    "sentiment": template["sentiment"],
                    "type": template["type"],
                    "data_source": "Generated"
                }
                
                news_items.append(news_item)
                
            except Exception as e:
                logger.error(f"Error generating mock news item: {e}")
        
        return news_items
            
    def fetch_specific_symbol_news(self, symbol, limit=20):
        """
        Fetch news specifically for a given symbol.
        
        Args:
            symbol: The stock symbol to fetch news for.
            limit: Maximum number of news items to return.
            
        Returns:
            list: List of news items for the symbol
        """
        logger.info(f"Fetching specific news for {symbol}")
        
        # Cache key for this request
        cache_key = f"news_symbol_{symbol}_{limit}"
        
        # Check cache first
        if cache_key in self.cache and datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
            logger.info(f"Using cached news data for {symbol}")
            return self.cache[cache_key]
        
        # First try to get real news for the symbol
        try:
            if self.use_newsdata_api:
                symbol_news = self._fetch_newsdata_symbol_news(symbol, limit=limit)
                if symbol_news:
                    # Cache the results
                    self.cache[cache_key] = symbol_news
                    self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
                    return symbol_news
        except Exception as e:
            logger.error(f"Error fetching NewsData.io news for {symbol}: {e}")
        
        # Fall back to generated news
        mock_news = self._generate_mock_news(symbols=[symbol], limit=limit, market_wide=False)
        
        # Cache the results
        self.cache[cache_key] = mock_news
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
        
        return mock_news
            
    def fetch_market_summaries(self):
        """
        Fetch market summary news and reports.
        
        Returns:
            list: List of market summary news items
        """
        logger.info("Fetching market summaries")
        
        # Cache key for this request
        cache_key = "market_summaries"
        
        # Check cache first
        if cache_key in self.cache and datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
            logger.info("Using cached market summaries")
            return self.cache[cache_key]
        
        # Try to get real market summaries
        try:
            if self.use_newsdata_api:
                # Get market news with a more specific query
                market_news = self._fetch_newsdata_market_news(limit=5)
                if market_news:
                    # Cache the results
                    self.cache[cache_key] = market_news
                    self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
                    return market_news
        except Exception as e:
            logger.error(f"Error fetching market summaries: {e}")
        
        # Fall back to generated news
        mock_news = self._generate_mock_news(limit=5, market_wide=True)
        
        # Cache the results
        self.cache[cache_key] = mock_news
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
        
        return mock_news

