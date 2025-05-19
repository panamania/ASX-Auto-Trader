
"""
Market scanning and data aggregation functions using FinanceAPI.net.
"""
import logging
import requests
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class MarketScanner:
    """Scans the market for opportunities and gathers market data using FinanceAPI.net."""
    
    def __init__(self):
        self.finance_api_key = Config.FINANCE_API_KEY
        self.use_finance_api = bool(self.finance_api_key)
        
        self.scan_mode = Config.MARKET_SCAN_MODE
        self.sector_focus = Config.MARKET_SECTOR_FOCUS
        self.min_market_cap = Config.MIN_MARKET_CAP
        self.max_stocks = Config.MAX_STOCKS_TO_ANALYZE
        
        # FinanceAPI.net endpoints
        self.base_url = "https://yfapi.net"
        
        # Cache for market data to reduce API calls
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(minutes=60)  # Cache for 60 minutes
        
    def get_market_symbols(self):
        """
        Get the list of ASX stock symbols to analyze based on configuration.
        
        Returns:
            list: List of stock symbols meeting the criteria
        """
        logger.info(f"Getting ASX market symbols with scan mode: {self.scan_mode}")
        
        # Cache key for symbols
        cache_key = f"symbols_{self.scan_mode}_{self.sector_focus}"
        
        # Check cache first
        if cache_key in self.cache and datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
            logger.info(f"Using cached symbols for {self.scan_mode}")
            return self.cache[cache_key]
        
        try:
            symbols = []
            
            if self.use_finance_api:
                if self.scan_mode == "sector" and self.sector_focus:
                    symbols = self._get_sector_symbols_via_api(self.sector_focus)
                else:
                    # For "full" or "filtered" mode, get ASX indices and popular stocks
                    symbols = self._get_asx_symbols_via_api()
            
            # If we couldn't get symbols via API or not enough, add default ASX symbols
            if len(symbols) < 5:
                default_symbols = self._get_default_asx_symbols()
                symbols.extend([s for s in default_symbols if s not in symbols])
            
            # Limit to max_stocks
            symbols = symbols[:self.max_stocks]
            
            # Cache the results
            self.cache[cache_key] = symbols
            self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
            
            logger.info(f"Retrieved {len(symbols)} ASX symbols")
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting market symbols: {e}")
            # Return default ASX symbols as fallback
            return self._get_default_asx_symbols()
    
    def _get_asx_symbols_via_api(self):
        """Get ASX symbols using FinanceAPI.net"""
        try:
            # Get the ASX 200 components
            endpoint = "/v6/finance/quote"
            params = {
                "symbols": "^AXJO",  # ASX 200 index
                "modules": "components"
            }
            
            headers = {
                "x-api-key": self.finance_api_key,
                "Accept": "application/json"
            }
            
            response = requests.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract component symbols
            symbols = []
            if "quoteResponse" in data and "result" in data["quoteResponse"]:
                if "components" in data["quoteResponse"]["result"][0]:
                    components = data["quoteResponse"]["result"][0]["components"]
                    for component in components:
                        # Extract symbol and remove .AX suffix
                        symbol = component.get("symbol", "")
                        if symbol.endswith(".AX"):
                            symbols.append(symbol[:-3])
            
            if not symbols:
                # Fallback to default symbols
                symbols = self._get_default_asx_symbols()
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error fetching ASX symbols via API: {e}")
            return self._get_default_asx_symbols()
    
    def _get_sector_symbols_via_api(self, sector):
        """
        Retrieve ASX symbols for a specific sector using the FinanceAPI.net screener endpoint.
        """
        try:
            # Map sector names to API-recognized sector IDs
            sector_map = {
                "financial": "financials",
                "technology": "technology",
                "healthcare": "healthcare",
                "energy": "energy",
                "materials": "materials",
                "consumer": "consumer_cyclical",
                "industrial": "industrials",
                "utilities": "utilities",
                "real_estate": "real_estate",
                "communication": "communication_services"
            }

            api_sector = sector_map.get(sector.lower(), sector.lower())

            endpoint = "/v6/finance/screener"
            params = {
                "region": "AU",
                "sector": api_sector,
                "exchange": "ASX"
            }

            headers = {
                "x-api-key": self.finance_api_key,
                "Accept": "application/json"
            }

            response = requests.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
            response.raise_for_status()

            data = response.json()

            # Extract stock symbols
            symbols = []
            if "finance" in data and "result" in data["finance"]:
                for result in data["finance"]["result"]:
                    if "quotes" in result:
                        for quote in result["quotes"]:
                            symbol = quote.get("symbol", "")
                            if symbol.endswith(".AX"):
                                symbols.append(symbol[:-3])

            # Fallback to default sector symbols if none found
            if not symbols:
                symbols = self._get_default_sector_symbols(sector)

            return symbols

        except Exception as e:
            logger.error(f"Error fetching sector symbols via API: {e}")
            return self._get_default_sector_symbols(sector)

    
    def _get_default_asx_symbols(self):
        """Get default ASX symbols for testing"""
        return [
            "BHP", "CBA", "NAB", "WBC", "ANZ", "RIO", "CSL", "WES", "TLS", "FMG",
            "GMG", "MQG", "TCL", "WOW", "NCM", "STO", "AMC", "S32", "QBE", "BXB",
            "ALL", "SUN", "RMD", "ORG", "SHL", "AMP", "CCL", "OSH", "FPH", "SGP"
        ]
    
    def _get_default_sector_symbols(self, sector):
        """Get default symbols for a specific sector"""
        sector_symbols = {
            "financial": ["CBA", "NAB", "WBC", "ANZ", "MQG", "SUN", "QBE", "AMP", "BEN", "BOQ"],
            "technology": ["WTC", "XRO", "APX", "ALU", "MP1", "TNE", "APT", "PME", "CPU", "NXT"],
            "healthcare": ["CSL", "RMD", "COH", "SHL", "RHC", "FPH", "MSB", "PRN", "NAN", "SIG"],
            "energy": ["WPL", "STO", "OSH", "ORG", "WHC", "WOR", "BPT", "KAR", "NHC", "KOV"],
            "materials": ["BHP", "RIO", "FMG", "NCM", "S32", "MIN", "LYC", "OZL", "IGO", "SFR"],
            "consumer": ["WOW", "WES", "COL", "DMP", "JBH", "HVN", "MTS", "LOV", "BKL", "TWE"],
            "industrial": ["TCL", "SYD", "QAN", "AZJ", "DOW", "SEK", "SVW", "CIM", "BWP", "GMG"],
            "utilities": ["AGL", "APA", "ORG", "SKI", "AST", "ALX", "CPU", "IRE", "MCY", "URW"],
            "real_estate": ["GMG", "SGP", "DXS", "MGR", "GPT", "CLW", "CHC", "ABP", "NSR", "GOZ"],
            "communication": ["TLS", "TPG", "REA", "CAR", "DHG", "SEK", "NWS", "NXT", "SXL", "PRT"]
        }
        
        return sector_symbols.get(sector.lower(), ["BHP", "CBA", "NAB", "WBC", "ANZ"])
            
    def get_market_data(self, symbols=None):
        """
        Get market data for given symbols or all scanned symbols using FinanceAPI.net.
        
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
        
        # Use ThreadPoolExecutor for parallel requests to improve performance
        market_data = {}
        
        # Define the max number of workers (limit concurrent API calls)
        max_workers = min(10, len(symbols))  # Limit to 10 concurrent requests
        
        # Use batching to reduce API calls (5 symbols per call)
        batched_symbols = [symbols[i:i+5] for i in range(0, len(symbols), 5)]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a map of futures to symbol batches
            future_to_batch = {
                executor.submit(self._get_batch_data, batch): batch
                for batch in batched_symbols
            }
            
            # Process results as they complete
            for future in future_to_batch:
                batch = future_to_batch[future]
                try:
                    batch_data = future.result()
                    if batch_data:
                        market_data.update(batch_data)
                except Exception as e:
                    logger.error(f"Error getting data for batch {batch}: {e}")
        
        logger.info(f"Retrieved market data for {len(market_data)} symbols")
        return market_data
    
    def _get_batch_data(self, symbols):
        """
        Retrieve market data for a batch of symbols using the FinanceAPI.net quote endpoint.
        """
        batch_data = {}
        symbols_to_fetch = []

        for symbol in symbols:
            cache_key = f"market_data_{symbol}"
            if cache_key in self.cache and datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
                batch_data[symbol] = self.cache[cache_key]
            else:
                symbols_to_fetch.append(symbol)

        if not symbols_to_fetch:
            return batch_data

        yahoo_symbols = [f"{s}.AX" for s in symbols_to_fetch]

        try:
            if self.use_finance_api:
                endpoint = "/v6/finance/quote"
                params = {
                    "symbols": ",".join(yahoo_symbols),
                    "modules": "summaryDetail,price,financialData,defaultKeyStatistics"
                }

                headers = {
                    "x-api-key": self.finance_api_key,
                    "Accept": "application/json"
                }

                response = requests.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
                response.raise_for_status()

                data = response.json()

                if "quoteResponse" in data and "result" in data["quoteResponse"]:
                    quotes = data["quoteResponse"]["result"]
                    for quote in quotes:
                        symbol = quote.get("symbol", "").replace(".AX", "")
                        market_cap = quote.get("marketCap", 0)

                        if market_cap < self.min_market_cap:
                            continue

                        price = quote.get("regularMarketPrice", 0)
                        price_change = quote.get("regularMarketChange", 0)
                        price_change_pct = quote.get("regularMarketChangePercent", 0) / 100
                        volume = quote.get("regularMarketVolume", 0)

                        summary = quote.get("summaryDetail", {})
                        high_52w = summary.get("fiftyTwoWeekHigh", {}).get("raw", 0)
                        low_52w = summary.get("fiftyTwoWeekLow", {}).get("raw", 0)
                        avg_volume = summary.get("averageVolume", {}).get("raw", 0)
                        pe_ratio = summary.get("trailingPE", {}).get("raw", 0)

                        market_data = {
                            "symbol": symbol,
                            "current_price": price,
                            "price_change": price_change,
                            "price_change_pct": price_change_pct,
                            "volume": volume,
                            "avg_volume": avg_volume,
                            "market_cap": market_cap,
                            "52w_high": high_52w,
                            "52w_low": low_52w,
                            "pe_ratio": pe_ratio,
                            "data_source": "FinanceAPI.net",
                            "timestamp": datetime.now().isoformat()
                        }

                        cache_key = f"market_data_{symbol}"
                        self.cache[cache_key] = market_data
                        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration

                        batch_data[symbol] = market_data
            else:
                for symbol in symbols_to_fetch:
                    mock_data = self._generate_mock_data(symbol)
                    cache_key = f"market_data_{symbol}"
                    self.cache[cache_key] = mock_data
                    self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
                    batch_data[symbol] = mock_data

            return batch_data

        except Exception as e:
            logger.error(f"Error fetching market data via API for {symbols_to_fetch}: {e}")
            for symbol in symbols_to_fetch:
                mock_data = self._generate_mock_data(symbol)
                batch_data[symbol] = mock_data

            return batch_data

    
    def _generate_mock_data(self, symbol):
        """Generate mock market data for testing"""
        import random
        
        # Seed random with symbol to get consistent data for the same symbol
        random.seed(hash(symbol))
        
        price = round(10 + random.random() * 90, 2)
        price_change_pct = round((random.random() * 0.1) - 0.05, 4)  # -5% to +5%
        price_change = round(price * price_change_pct, 2)
        volume = int(random.random() * 1000000)
        
        return {
            "symbol": symbol,
            "current_price": price,
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "volume": volume,
            "avg_volume": int(volume * 0.8),
            "market_cap": int(price * 10000000),
            "52w_high": round(price * 1.2, 2),
            "52w_low": round(price * 0.8, 2),
            "pe_ratio": round(15 * (1 + 0.3 * random.random()), 1),
            "data_source": "Generated",
            "timestamp": datetime.now().isoformat()
        }
            
    def find_opportunities(self, market_data=None):
        """
        Scan the market to find trading opportunities.
        
        This is a pre-filtering step before detailed GPT analysis.
        
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
        opportunities = []
        
        try:
            # Manual filtering based on technical indicators
            for symbol, data in market_data.items():
                # Get all relevant data with defaults if missing
                volume = data.get('volume', 0)
                avg_volume = data.get('avg_volume', volume / 2)  # If no avg, assume current is 2x
                price = data.get('current_price', 0)
                high = data.get('52w_high', 0)
                low = data.get('52w_low', 0)
                price_change_pct = data.get('price_change_pct', 0)
                
                # Opportunity filters
                
                # 1. Significant volume increase (1.5x average)
                if volume > avg_volume * 1.5:
                    opportunities.append(symbol)
                    continue
                    
                # 2. Near 52-week high (within 5%)
                if high > 0 and price >= high * 0.95:
                    opportunities.append(symbol)
                    continue
                    
                # 3. Near 52-week low (within 5%)
                if low > 0 and price <= low * 1.05:
                    opportunities.append(symbol)
                    continue
                    
                # 4. Significant price movement (>3%)
                if abs(price_change_pct) >= 0.03:
                    opportunities.append(symbol)
                    continue
            
            # De-duplicate
            opportunities = list(set(opportunities))
            
            logger.info(f"Found {len(opportunities)} potential opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error finding opportunities: {e}")
            return list(market_data.keys())[:5]  # Return first 5 symbols as fallback

