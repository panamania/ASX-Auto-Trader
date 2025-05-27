
"""
News collector module for ASX stock news using Google News RSS.
"""
import logging
import requests
import json
import random
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class ASXNewsCollector:
    """Collects news from ASX"""
    def __init__(self):
        self.newsdata_api_key = Config.NEWSDATA_API_KEY
        
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
        
        try:
            # Set default limit based on whether we're doing market-wide or specific symbols
            if limit is None:
                limit = 20 if market_wide else 10
            
            # Try to get real news first
            news_items = []
            
            # First try Google News RSS for specified symbols
            if symbols:
                for symbol in symbols[:min(5, len(symbols))]:  # Limit to 5 symbols to avoid too many requests
                    symbol_news = self._fetch_google_news_rss(symbol, limit=5)
                    news_items.extend(symbol_news)
                    
                logger.info(f"Retrieved {len(news_items)} news items from Google News RSS")
            
            # Add market-wide news if requested
            if market_wide:
                market_news = self._fetch_google_news_rss("ASX", limit=limit)
                news_items.extend(market_news)
                logger.info(f"Added {len(market_news)} market-wide news items from Google News RSS")
            
            # Then try NewsData.io as backup
            if self.newsdata_api_key and len(news_items) < limit:
                try:
                    if market_wide:
                        newsdata_news = self._fetch_newsdata_market_news(limit=limit)
                        news_items.extend(newsdata_news)
                        logger.info(f"Retrieved {len(newsdata_news)} news items from NewsData.io market news")
                    
                    # If we have specific symbols, get company news for each
                    if symbols and len(symbols) > 0:
                        company_news = self._fetch_newsdata_company_news(symbols, limit=limit)
                        news_items.extend(company_news)
                        logger.info(f"Retrieved company news from NewsData.io")
                except Exception as e:
                    logger.error(f"Error fetching news from NewsData.io: {e}")
            
            # If we don't have enough news, try ASX announcements
            if len(news_items) < limit:
                try:
                    if market_wide or not symbols:
                        asx_news = self._fetch_asx_announcements(limit=limit)
                        news_items.extend(asx_news)
                    else:
                        for symbol in symbols[:10]:  # Limit to 10 symbols for specific fetches
                            symbol_news = self._fetch_asx_announcements(symbol=symbol, limit=5)
                            news_items.extend(symbol_news)
                except Exception as e:
                    logger.error(f"Error fetching ASX announcements: {e}")
            
            # If we still don't have enough news, generate mock data
            if len(news_items) < limit / 2:
                mock_news = self._generate_mock_news(symbols, limit - len(news_items), market_wide)
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
            
            logger.info(f"Fetched {len(unique_news)} news items")
            return unique_news
            
        except Exception as e:
            logger.error(f"Error fetching ASX news: {e}")
            # Fall back to mock data
            return self._generate_mock_news(symbols, limit, market_wide)
    
    def _fetch_google_news_rss(self, symbol, limit=10):
        """Fetch news from Google News RSS for ASX symbols"""
        try:
            # Format the URL to search for ASX:SYMBOL format
            url = f"https://news.google.com/rss/search?q=ASX:{symbol}&hl=en-AU&gl=AU&ceid=AU:en"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch Google News RSS: {response.status_code}")
                return []
            
            # Parse XML
            try:
                root = ET.fromstring(response.content)
                items = root.findall('.//item')
                
                news_items = []
                for i, item in enumerate(items[:limit]):
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    date_elem = item.find('pubDate')
                    description_elem = item.find('description')
                    
                    if title_elem is None:
                        continue
                        
                    title = title_elem.text
                    link = link_elem.text if link_elem is not None else ""
                    date_str = date_elem.text if date_elem is not None else ""
                    description = description_elem.text if description_elem is not None else ""
                    
                    # Clean the title and description
                    title = html.unescape(title) if title else ""
                    description = html.unescape(description) if description else ""
                    
                    # Create a unique ID
                    news_id = f"google-{symbol}-{i}-{hash(title)}"
                    
                    # Convert date if possible
                    published_date = date_str
                    try:
                        if date_str:
                            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                            published_date = dt.isoformat()
                    except Exception:
                        pass
                    
                    # Create news item
                    news_item = {
                        "id": news_id,
                        "headline": title,
                        "content": description,
                        "symbols": [symbol],
                        "published_date": published_date,
                        "source": "Google News",
                        "url": link,
                        "category": "stock"
                    }
                    
                    news_items.append(news_item)
                
                return news_items
                
            except ET.ParseError as e:
                logger.error(f"Error parsing Google News RSS XML: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching Google News RSS for {symbol}: {e}")
            return []
    
    def _fetch_newsdata_market_news(self, limit=10):
        """Fetch market news from NewsData.io API"""
        try:
            if not self.newsdata_api_key:
                return []
                
            url = f"https://newsdata.io/api/1/news"
            params = {
                "apikey": self.newsdata_api_key,
                "country": "au",  # Australia
                "category": "business",  # Business category
                "language": "en",   # English
                "size": min(limit, 20)  # Maximum allowed is 20 for free tier
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch NewsData.io market news: {response.status_code} - {response.text}")
                return []
            
            news_data = response.json()
            if not news_data or "results" not in news_data or not news_data["results"]:
                logger.warning("Invalid response from NewsData.io API")
                return []
                
            # Process news items
            news_items = []
            for idx, item in enumerate(news_data["results"][:limit]):
                # Extract potential ASX symbols from content
                symbols = self._extract_asx_symbols_from_text(item.get("title", "") + " " + item.get("description", ""))
                
                # Skip news items without publication date
                if not item.get("pubDate"):
                    continue
                
                news_items.append({
                    "id": f"newsdata-{item.get('article_id', idx)}",
                    "headline": item.get("title", ""),
                    "content": item.get("description", ""),
                    "symbols": symbols,
                    "published_date": item.get("pubDate", ""),
                    "source": item.get("source_id", "NewsData"),
                    "url": item.get("link", ""),
                    "category": "business"
                })
                
            return news_items
                
        except Exception as e:
            logger.error(f"Error fetching NewsData.io market news: {e}")
            return []
    
    def _fetch_newsdata_company_news(self, symbols, limit=10):
        """Fetch company-specific news from NewsData.io API"""
        try:
            if not self.newsdata_api_key or not symbols:
                return []
            
            # Create keywords for the symbols
            # Convert ["BHP", "CBA"] to "(BHP OR CBA)"
            keywords = " OR ".join(symbols)
            keywords = f"({keywords})"
            
            url = f"https://newsdata.io/api/1/news"
            params = {
                "apikey": self.newsdata_api_key,
                "country": "au",  # Australia
                "category": "business",  # Business category
                "language": "en",   # English
                "q": keywords,      # Search query for the symbols
                "size": min(limit, 20)  # Maximum allowed is 20 for free tier
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch NewsData.io company news: {response.status_code} - {response.text}")
                return []
            
            news_data = response.json()
            if not news_data or "results" not in news_data or not news_data["results"]:
                logger.warning("No company news found from NewsData.io API")
                return []
                
            # Process news items
            news_items = []
            for idx, item in enumerate(news_data["results"][:limit]):
                # Find which symbols are mentioned
                mentioned_symbols = []
                text = (item.get("title", "") + " " + item.get("description", "")).upper()
                for symbol in symbols:
                    if symbol in text:
                        mentioned_symbols.append(symbol)
                
                # If no symbols found, try to extract them
                if not mentioned_symbols:
                    mentioned_symbols = self._extract_asx_symbols_from_text(text)
                    # Filter to only include symbols from our list
                    mentioned_symbols = [s for s in mentioned_symbols if s in symbols]
                
                # Skip news without any symbols or publication date
                if not mentioned_symbols or not item.get("pubDate"):
                    continue
                
                news_items.append({
                    "id": f"newsdata-company-{item.get('article_id', idx)}",
                    "headline": item.get("title", ""),
                    "content": item.get("description", ""),
                    "symbols": mentioned_symbols,
                    "published_date": item.get("pubDate", ""),
                    "source": item.get("source_id", "NewsData"),
                    "url": item.get("link", ""),
                    "category": "company"
                })
                
            return news_items
                
        except Exception as e:
            logger.error(f"Error fetching NewsData.io company news: {e}")
            return []
    
    def _extract_asx_symbols_from_text(self, text):
        """Extract potential ASX stock symbols from text."""
        # Basic pattern: look for 3-letter uppercase words that might be stock codes
        # This is a simple approach - more sophisticated methods could be used
        pattern = r'\b[A-Z]{3}\b'
        matches = re.findall(pattern, text)
        
        # Exclude common non-stock 3-letter words
        exclude_words = {'THE', 'AND', 'FOR', 'BUT', 'NOT', 'NEW', 'NOW', 'HAS', 'HAD', 'WHO', 'WHY', 'HOW', 'ALL'}
        
        # Filter out excluded words
        symbols = [match for match in matches if match not in exclude_words]
        
        # Remove duplicates
        symbols = list(set(symbols))
        
        return symbols
    
    def _fetch_asx_announcements(self, symbol=None, limit=10):
        """Fetch company announcements from ASX"""
        try:
            url = "https://www.asx.com.au/asx/1/company/announcements"
            params = {
                "count": limit,
                "market_sensitive": "true"  # Focus on market-sensitive announcements
            }
            
            if symbol:
                params["code"] = symbol
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch ASX announcements, status code: {response.status_code}")
                return []
            
            try:
                data = response.json()
                if "data" not in data:
                    return []
                
                announcements = data["data"]
                result = []
                
                for idx, announcement in enumerate(announcements):
                    # Extract relevant fields
                    news_id = announcement.get("id", f"asx-{idx}")
                    headline = announcement.get("headline", "")
                    ticker = announcement.get("ticker", "")
                    published_date = announcement.get("date", "")
                    
                    # Try to get the announcement text if available
                    content = announcement.get("text", "")
                    if not content:
                        content = f"ASX announcement from {ticker}: {headline}"
                    
                    # Create a news item
                    news_item = {
                        "id": news_id,
                        "headline": headline,
                        "content": content,
                        "symbols": [ticker] if ticker else [],
                        "published_date": published_date,
                        "source": "ASX Announcements",
                        "url": announcement.get("url", ""),
                        "category": "announcement"
                    }
                    
                    result.append(news_item)
                
                return result
            except json.JSONDecodeError:
                logger.warning("Failed to parse ASX announcement JSON")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching ASX announcements: {e}")
            return []
    
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
                    "id": f"news-{base_id + i}",
                    "headline": headline,
                    "content": content,
                    "symbols": news_symbols,
                    "published_date": published_date,
                    "source": random.choice(["ASX Announcements", "Financial Review", "The Australian", "Bloomberg", "Reuters"]),
                    "sentiment": template["sentiment"],
                    "type": template["type"],
                    "category": template["type"],
                    "generated": True
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
        
        # First try Google News RSS
        try:
            google_news = self._fetch_google_news_rss(symbol, limit=limit)
            if google_news:
                return google_news
        except Exception as e:
            logger.error(f"Error fetching Google News RSS for {symbol}: {e}")
        
        # Then try NewsData.io for company news
        if self.newsdata_api_key:
            try:
                newsdata_news = self._fetch_newsdata_company_news([symbol], limit=limit)
                if newsdata_news:
                    return newsdata_news
            except Exception as e:
                logger.error(f"Error fetching NewsData.io company news for {symbol}: {e}")
        
        # Then try ASX announcements
        try:
            announcements = self._fetch_asx_announcements(symbol=symbol, limit=limit)
            if announcements:
                return announcements
        except Exception as e:
            logger.error(f"Error fetching ASX announcements for {symbol}: {e}")
        
        # Fall back to generated news
        return self._generate_mock_news(symbols=[symbol], limit=limit, market_wide=False)
            
    def fetch_market_summaries(self):
        """
        Fetch market summary news and reports.
        
        Returns:
            list: List of market summary news items
        """
        logger.info("Fetching market summaries")
        
        # Try Google News RSS for ASX
        try:
            google_news = self._fetch_google_news_rss("ASX", limit=10)
            if google_news:
                return google_news
        except Exception as e:
            logger.error(f"Error fetching Google News RSS for market summaries: {e}")
        
        # Then try NewsData.io for market news
        if self.newsdata_api_key:
            try:
                newsdata_news = self._fetch_newsdata_market_news(limit=5)
                if newsdata_news:
                    return newsdata_news
            except Exception as e:
                logger.error(f"Error fetching NewsData.io market news: {e}")
        
        # Fall back to generated news
        return self._generate_mock_news(limit=5, market_wide=True)

