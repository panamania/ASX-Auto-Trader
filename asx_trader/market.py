

"""
Market scanning and data aggregation functions.
"""
import logging
import requests
import random
import json
from concurrent.futures import ThreadPoolExecutor
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class MarketScanner:
    """Scans the market for opportunities and gathers market data."""

    def __init__(self):
        self.api_key = Config.ASX_API_KEY

        # Use basic web scraping if API not configured
        self.use_scraping = True if not self.api_key else False
        self.base_url = "https://yfapi.net"
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
            # Get ASX stock list via Yahoo Finance or default list
            all_symbols = self._get_asx_symbols()
            
            # Filter based on scan mode
            if self.scan_mode == "sector":
                return self._get_sector_symbols(self.sector_focus, all_symbols)
            elif self.scan_mode == "filtered":
                return self._get_filtered_symbols(all_symbols)
            else:
                # Default to all symbols (full scan mode)
                return all_symbols[:self.max_stocks]
                
        except Exception as e:
            logger.error(f"Error getting market symbols: {e}")
            # Return some default ASX symbols for testing
            logger.info("Using default ASX symbols")
            return ["BHP", "CBA", "NAB", "WBC", "ANZ", "RIO", "CSL", "WES", "TLS", "FMG"]
    
    def _get_asx_symbols(self):
        """Get ASX stock symbols"""
        # Top ASX stocks by market cap
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
        
        logger.info(f"Retrieved {len(asx_symbols)} ASX symbols")
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
        
        # Return sector symbols or default to financial if sector not found
        return sector_symbols.get(sector.lower(), sector_symbols["financial"])
            
    def _get_filtered_symbols(self, all_symbols=None):
        """Get symbols based on custom filters."""
        # For now, just return a selection of high-cap ASX symbols
        return ["BHP", "CBA", "CSL", "NAB", "WBC", "ANZ", "RIO", "WES", "TLS", "FMG"]
            

        logger.info(f"Getting market symbols with scan mode: {self.scan_mode}")

        try:
            if self.scan_mode == "sector":
                return self._get_sector_symbols(self.sector_focus)
            elif self.scan_mode == "filtered":
                return self._get_filtered_symbols()
            elif self.scan_mode == "trending":
                return self._get_trending_symbols()
            else:
                logger.warning(f"Unknown scan mode '{self.scan_mode}', defaulting to trending symbols.")
                return self._get_trending_symbols()
        except Exception as e:
            logger.error(f"Error getting market symbols: {e}")
            return []

    def _get_trending_symbols(self):
        """Get trending symbols using Yahoo Finance API."""
        try:
            response = requests.get(
                f"{self.base_url}/v1/finance/trending/AU",
                headers={"x-api-key": self.api_key, "accept": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            quotes = data.get("finance", {}).get("result", [])
            if quotes and "quotes" in quotes[0]:
                trending_symbols = [item["symbol"] for item in quotes[0]["quotes"]]
                return trending_symbols[:self.max_stocks]
            return []
        except Exception as e:
            logger.error(f"Error fetching trending symbols: {e}")
            return []

    def _get_sector_symbols(self, sector):
        logger.warning("_get_sector_symbols is not supported by the Yahoo Finance API.")
        return []

    def _get_filtered_symbols(self):
        logger.warning("_get_filtered_symbols is not supported by the Yahoo Finance API.")
        return []


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
        """Get market data for a single symbol using Yahoo Finance API."""
        try:

            # Use Yahoo Finance as a reliable source for stock data
            return self._get_yahoo_symbol_data(symbol)
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            # Return dummy data for testing
            return self._generate_dummy_data(symbol)
    
    def _get_yahoo_symbol_data(self, symbol):
        """Get market data for a single symbol from Yahoo Finance."""
        try:
            yahoo_symbol = f"{symbol}.AX"  # ASX stocks on Yahoo have .AX suffix
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={yahoo_symbol}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "quoteResponse" in data and "result" in data["quoteResponse"] and len(data["quoteResponse"]["result"]) > 0:
                quote = data["quoteResponse"]["result"][0]
                
                # Extract relevant data
                return {
                    "symbol": symbol,
                    "current_price": quote.get("regularMarketPrice", 0),
                    "volume": quote.get("regularMarketVolume", 0),
                    "price_change_pct": quote.get("regularMarketChangePercent", 0) / 100 if "regularMarketChangePercent" in quote else 0,
                    "market_cap": quote.get("marketCap", 0),
                    "52w_high": quote.get("fiftyTwoWeekHigh", 0),
                    "52w_low": quote.get("fiftyTwoWeekLow", 0),
                    "pe_ratio": quote.get("trailingPE", 0),
                    "avg_volume": quote.get("averageDailyVolume3Month", 0),
                    "source": "Yahoo Finance"
                }
            else:
                logger.warning(f"No Yahoo Finance data found for {symbol}")
                return self._generate_dummy_data(symbol)
                
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
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
            "source": "Generated"
        }
            

            response = requests.get(
                f"{self.base_url}/v6/finance/quote",
                params={"symbols": symbol},
                headers={"x-api-key": self.api_key, "accept": "application/json"}
            )
            response.raise_for_status()
            data = response.json().get("quoteResponse", {}).get("result", [])
            return data[0] if data else None
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None


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

        
        # Apply opportunity filters
        # These are example filters - customize based on your strategy

        df = pd.DataFrame.from_dict(market_data, orient='index')

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
            if 'volume' in df.columns and 'averageDailyVolume3Month' in df.columns:
                volume_filter = df['volume'] > df['averageDailyVolume3Month'] * 1.5
                opportunities.extend(df[volume_filter].index.tolist())

            if 'regularMarketPrice' in df.columns and 'fiftyTwoWeekHigh' in df.columns and 'fiftyTwoWeekLow' in df.columns:
                high_filter = df['regularMarketPrice'] >= df['fiftyTwoWeekHigh'] * 0.95
                opportunities.extend(df[high_filter].index.tolist())

                low_filter = df['regularMarketPrice'] <= df['fiftyTwoWeekLow'] * 1.05
                opportunities.extend(df[low_filter].index.tolist())

            if 'regularMarketChangePercent' in df.columns:
                movement_filter = abs(df['regularMarketChangePercent']) >= 3.0
                opportunities.extend(df[movement_filter].index.tolist())


            opportunities = list(set(opportunities))
            logger.info(f"Found {len(opportunities)} potential opportunities")
            return opportunities
        except Exception as e:
            logger.error(f"Error finding opportunities: {e}")

            return list(market_data.keys())[:5]  # Return first 5 symbols as fallback

            return []


