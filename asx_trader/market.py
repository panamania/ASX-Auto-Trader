import logging
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class MarketScanner:
    """Scans the market for opportunities and gathers market data."""

    def __init__(self):
        self.api_key = Config.ASX_API_KEY
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
        df = pd.DataFrame.from_dict(market_data, orient='index')
        opportunities = []

        try:
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
            return []

