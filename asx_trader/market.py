"""
Market scanning and data aggregation functions.
"""
import logging
import requests
import random
import json
import finnhub
from concurrent.futures import ThreadPoolExecutor
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class MarketScanner:
    """Scans the market for opportunities and gathers market data."""

    def __init__(self):
        self.finnhub_api_key = Config.FINNHUB_API_KEY
        
        # Initialize Finnhub client
        self.finnhub_client = None
        if self.finnhub_api_key:
            try:
                self.finnhub_client = finnhub.Client(api_key=self.finnhub_api_key)
                logger.info("Finnhub client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Finnhub client: {e}")
                self.finnhub_client = None

        # Use basic web scraping if API not configured
        self.use_scraping = True if not self.finnhub_api_key else False
        self.base_url = "https://finnhub.io/api/v1"
        self.scan_mode = Config.MARKET_SCAN_MODE
        self.sector_focus = Config.MARKET_SECTOR_FOCUS
        self.min_market_cap = Config.MIN_MARKET_CAP
        self.max_stocks = Config.MAX_STOCKS_TO_ANALYZE

    def get_market_symbols(self):
        """
        Get the list of stock symbols to analyze based on configuration.

        Returns:
            list: List of stock symbols meeting the criteria
        """

        logger.info(f"Getting ASX market symbols with scan mode: {self.scan_mode}")
        
        try:
            # Get ASX stock list via Finnhub or default list
            all_symbols = self._get_asx_symbols()
            
            # Filter based on scan mode
            if self.scan_mode == "sector":
                return self._get_sector_symbols(self.sector_focus, all_symbols)
            elif self.scan_mode == "filtered":
                return self._get_filtered_symbols(all_symbols)
            elif self.scan_mode == "trending":
                return self._get_trending_symbols()
            else:
                # Default to all symbols (full scan mode)
                return all_symbols[:self.max_stocks]
                
        except Exception as e:
            logger.error(f"Error getting market symbols: {e}")
            # Return some default ASX symbols for testing
            logger.info("Using default ASX symbols")
            return ["BHP", "CBA", "NAB", "WBC", "ANZ", "RIO", "CSL", "WES", "TLS", "FMG"]
    
    def _get_asx_symbols(self):
        """Get ASX stock symbols using Finnhub API or fallback to hardcoded list"""
        if self.finnhub_client:
            try:
                # Try to get ASX symbols from Finnhub
                symbols = self.finnhub_client.stock_symbols('AU')
                asx_symbols = [s['symbol'].replace('.AX', '') for s in symbols if s['symbol'].endswith('.AX')]
                if asx_symbols:
                    logger.info(f"Retrieved {len(asx_symbols)} ASX symbols from Finnhub API")
                    return asx_symbols[:100]  # Limit to top 100
            except Exception as e:
                logger.warning(f"Failed to get symbols from Finnhub API: {e}")
        
        # Fallback to hardcoded list
        asx_symbols = [
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
        
        logger.info(f"Using fallback list of {len(asx_symbols)} ASX symbols")
        return asx_symbols
            
    def _get_sector_symbols(self, sector, all_symbols=None):
        """Get symbols for a specific sector."""
        # Pre-defined sector groupings
        sector_symbols = {
            "financial": ["CBA", "NAB", "WBC", "ANZ", "MQG", "SUN", "QBE", "AMP", "BEN", "BOQ"],
            "mining": ["BHP", "RIO", "FMG", "NCM", "S32", "MIN", "LYC", "OZL", "IGO", "SFR"],
            "tech": ["WTC", "XRO", "APX", "ALU", "MP1", "TNE", "APT", "PME", "CPU", "NXT"],
            "healthcare": ["CSL", "RMD", "COH", "SHL", "RHC", "FPH", "MSB", "PRN", "NAN", "SIG"],
            "energy": ["WPL", "STO", "OSH", "ORG", "WHC", "WOR", "BPT", "KAR", "NHC", "KOV"],
            "consumer": ["WOW", "WES", "COL", "DMP", "JBH", "HVN", "MTS", "LOV", "BKL", "TWE"]
        }
        
        logger.info(f"Getting symbols for sector: {sector}")
        # Return sector symbols or default to financial if sector not found
        return sector_symbols.get(sector.lower(), sector_symbols["financial"])
            
    def _get_filtered_symbols(self, all_symbols=None):
        """Get symbols based on custom filters."""
        logger.info("Getting filtered symbols based on market cap and volume")
        # For now, just return a selection of high-cap ASX symbols
        return ["BHP", "CBA", "CSL", "NAB", "WBC", "ANZ", "RIO", "WES", "TLS", "FMG"]

    def _get_trending_symbols(self):
        """Get trending symbols using Finnhub API."""
        if not self.finnhub_client:
            logger.warning("Finnhub client not available for trending symbols")
            return self._get_asx_symbols()[:10]
            
        try:
            # Get general market news
            news_data = self.finnhub_client.general_news('general')
            
            # Extract symbols from news articles
            symbols = []
            for article in news_data[:10]:  # Get first 10 articles
                if 'related' in article and article['related']:
                    symbols.extend(article['related'].split(',')[:2])
            
            # Filter for ASX symbols and return unique ones
            asx_symbols = [s.strip() for s in symbols if s.strip() in self._get_asx_symbols()]
            if asx_symbols:
                logger.info(f"Found {len(asx_symbols)} trending ASX symbols")
                return list(set(asx_symbols))[:self.max_stocks]
            else:
                logger.info("No trending ASX symbols found, using default list")
                return self._get_asx_symbols()[:10]  # Fallback to default symbols
                
        except Exception as e:
            logger.error(f"Error fetching trending symbols: {e}")
            return self._get_asx_symbols()[:10]  # Fallback to default symbols

    def get_market_data(self, symbols=None):
        """
        Get market data for given symbols or all scanned symbols.

        Args:
            symbols: Optional list of symbols to get data for.
                    If None, uses the configured scan method.

        Returns:
            dict: Dictionary of market data keyed by symbol
        """
        if not symbols:
            symbols = self.get_market_symbols()

        if not symbols:
            logger.warning("No symbols found for market data retrieval")
            return {}

        logger.info(f"Getting market data for {len(symbols)} symbols")

        market_data = {}
        max_workers = min(20, len(symbols))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(self._get_symbol_data, symbol): symbol
                for symbol in symbols
            }
            for future in future_to_symbol:
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if data:
                        market_data[symbol] = data
                except Exception as e:
                    logger.error(f"Error getting data for {symbol}: {e}")

        logger.info(f"Retrieved market data for {len(market_data)} symbols")
        return market_data

    def _get_symbol_data(self, symbol):
        """Get market data for a single symbol using Finnhub library."""
        try:
            # Use Finnhub library if available, otherwise fallback to direct API
            if self.finnhub_client:
                return self._get_finnhub_library_data(symbol)
            else:
                return self._get_finnhub_direct_api_data(symbol)
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            # Return dummy data for testing
            return self._generate_dummy_data(symbol)
    
    def _get_finnhub_library_data(self, symbol):
        """Get market data using the Finnhub Python library."""
        try:
            finnhub_symbol = f"{symbol}.AX"  # ASX stocks on Finnhub have .AX suffix
            
            # Get quote data
            quote_data = self.finnhub_client.quote(finnhub_symbol)
            
            # Get company profile for additional data
            try:
                profile_data = self.finnhub_client.company_profile2(symbol=finnhub_symbol)
                market_cap = profile_data.get('marketCapitalization', 0) * 1000000  # Convert from millions
            except:
                market_cap = 0
            
            current_price = quote_data.get("c", 0)
            previous_close = quote_data.get("pc", 0)
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "volume": quote_data.get("v", 0),
                "price_change_pct": ((current_price - previous_close) / previous_close) if previous_close > 0 else 0,
                "market_cap": market_cap,
                "52w_high": quote_data.get("h", 0),  # This is daily high, not 52-week
                "52w_low": quote_data.get("l", 0),   # This is daily low, not 52-week
                "pe_ratio": 0,  # Would need separate API call
                "avg_volume": 0,  # Not available in basic quote
                "source": "Finnhub Library"
            }
            
        except Exception as e:
            logger.error(f"Error fetching Finnhub library data for {symbol}: {e}")
            return self._generate_dummy_data(symbol)
    
    def _get_finnhub_direct_api_data(self, symbol):
        """Get market data for a single symbol from Finnhub API using direct requests."""
        try:
            finnhub_symbol = f"{symbol}.AX"  # ASX stocks on Finnhub have .AX suffix
            quote_url = f"{self.base_url}/quote"
            
            params = {
                'symbol': finnhub_symbol,
                'token': self.finnhub_api_key
            }
            
            response = requests.get(quote_url, params=params)
            response.raise_for_status()
            quote_data = response.json()
            
            # Finnhub quote response format: {"c": current, "h": high, "l": low, "o": open, "pc": previous_close, "t": timestamp, "v": volume}
            current_price = quote_data.get("c", 0)
            previous_close = quote_data.get("pc", 0)
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "volume": quote_data.get("v", 0),
                "price_change_pct": ((current_price - previous_close) / previous_close) if previous_close > 0 else 0,
                "market_cap": 0,  # Requires separate API call to /stock/profile2
                "52w_high": quote_data.get("h", 0),  # This is daily high, not 52-week
                "52w_low": quote_data.get("l", 0),   # This is daily low, not 52-week
                "pe_ratio": 0,  # Requires separate API call
                "avg_volume": 0,  # Not available in basic quote
                "source": "Finnhub Direct API"
            }
            
        except Exception as e:
            logger.error(f"Error fetching Finnhub direct API data for {symbol}: {e}")
            return self._generate_dummy_data(symbol)
    
    def _generate_dummy_data(self, symbol):
        """Generate dummy market data for testing."""
        import random
        price = round(10 + random.random() * 90, 2)
        return {
            "symbol": symbol,
            "current_price": price,
            "volume": int(random.random() * 1000000),
            "price_change_pct": round((random.random() * 0.1) - 0.05, 4),  # -5% to +5%
            "market_cap": int(price * 10000000),
            "52w_high": round(price * 1.2, 2),
            "52w_low": round(price * 0.8, 2),
            "pe_ratio": round(10 + random.random() * 20, 2),
            "avg_volume": int(random.random() * 500000),
            "source": "Generated"
        }

    def get_company_news(self, symbol, days_back=7):
        """Get company news using Finnhub library."""
        if not self.finnhub_client:
            logger.warning("Finnhub client not available for company news")
            return []
            
        try:
            import datetime
            to_date = datetime.datetime.now()
            from_date = to_date - datetime.timedelta(days=days_back)
            
            finnhub_symbol = f"{symbol}.AX"
            news = self.finnhub_client.company_news(
                finnhub_symbol, 
                _from=from_date.strftime('%Y-%m-%d'), 
                to=to_date.strftime('%Y-%m-%d')
            )
            
            logger.info(f"Retrieved {len(news)} news articles for {symbol}")
            return news
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    def find_opportunities(self, market_data=None):
        """
        Scan the market to find trading opportunities.

        Args:
            market_data: Optional pre-loaded market data. If None, fetches new data.

        Returns:
            list: List of symbols that represent potential opportunities
        """
        if not market_data:
            market_data = self.get_market_data()

        if not market_data:
            return []

        logger.info(f"Scanning {len(market_data)} stocks for opportunities")

        opportunities = []

        try:
            # Manual filtering
            for symbol, data in market_data.items():
                # Get all relevant data with defaults if missing
                volume = data.get('volume', 0)
                avg_volume = data.get('avg_volume', volume / 2)  # If no avg, assume current is 2x
                price = data.get('current_price', 0)
                high = data.get('52w_high', 0)
                low = data.get('52w_low', 0)
                price_change = data.get('price_change_pct', 0)
                
                # Significant volume increase
                if volume > avg_volume * 1.5:
                    opportunities.append(symbol)
                    continue
                    
                # Price near 52-week high/low
                if high > 0 and price >= high * 0.95:  # Within 5% of high
                    opportunities.append(symbol)
                    continue
                    
                if low > 0 and price <= low * 1.05:  # Within 5% of low
                    opportunities.append(symbol)
                    continue
                    
                # Unusual price movement
                if abs(price_change) >= 0.03:  # 3% or more
                    opportunities.append(symbol)
                    continue
            
            # De-duplicate
            opportunities = list(set(opportunities))
            logger.info(f"Found {len(opportunities)} potential opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error finding opportunities: {e}")
            return list(market_data.keys())[:5]  # Return first 5 symbols as fallback
