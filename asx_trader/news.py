
"""
News collector module for ASX stock news.
"""
import logging
import requests
import json
import random
from datetime import datetime, timedelta
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class ASXNewsCollector:
    """Collects news from ASX"""
    def __init__(self):
        self.api_key = Config.ASX_API_KEY
        self.base_url = "https://asx.api.example.com"  # Replace with actual ASX API endpoint
        
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
            # For POC/testing: Generate mock news data if API not available
            # In production, replace this with actual API call
            
            # Set default limit based on whether we're doing market-wide or specific symbols
            if limit is None:
                limit = 20 if market_wide else 10
            
            # Generate mock news data
            news_items = self._generate_mock_news(symbols, limit, market_wide)
            logger.info(f"Generated {len(news_items)} mock news items")
            return news_items
            
            # Uncomment below for real API integration
            """
            params = {"limit": limit}
            
            # Add symbols parameter if provided and not doing market_wide only
            if symbols and not market_wide:
                params["symbols"] = ",".join(symbols)
                
            # Add market_wide parameter
            params["market_wide"] = "true" if market_wide else "false"
                
            response = requests.get(
                f"{self.base_url}/news", 
                params=params,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            news_items = response.json()
            
            logger.info(f"Fetched {len(news_items)} news items")
            return news_items
            """
            
        except Exception as e:
            logger.error(f"Error fetching ASX news: {e}")
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
                    "type": template["type"]
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
        
        # For POC, reuse the fetch_latest_news method with specific symbol
        return self.fetch_latest_news(symbols=[symbol], limit=limit, market_wide=False)
            
    def fetch_market_summaries(self):
        """
        Fetch market summary news and reports.
        
        Returns:
            list: List of market summary news items
        """
        logger.info("Fetching market summaries")
        
        # For POC, generate market-specific news
        return self.fetch_latest_news(limit=5, market_wide=True)
