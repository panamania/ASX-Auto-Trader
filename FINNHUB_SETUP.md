# Finnhub API Integration Setup

This document explains how to set up and use the Finnhub API integration for getting ASX stock data.

## Setup Instructions

### 1. Get a Free Finnhub API Key

1. Visit [https://finnhub.io/](https://finnhub.io/)
2. Sign up for a free account
3. Go to your dashboard and copy your API key
4. The free tier includes:
   - 60 API calls/minute
   - Real-time data for US markets
   - Basic data for international markets (including ASX)

### 2. Configure the API Key

1. Open the `.env` file in the project root
2. Replace `your-finnhub-key-here` with your actual API key:
   ```
   FINNHUB_API_KEY=your_actual_api_key_here
   ```

### 3. Test the Integration

Run the test script to verify everything works:
```bash
python test_finnhub_integration.py
```

## How It Works

The `MarketScanner` class in `asx_trader/market.py` now supports multiple data sources:

### 1. **Finnhub Python Library** (Primary)
- Uses the official `finnhub-python` library
- Cleaner API calls with better error handling
- Automatic retry and rate limiting

### 2. **Direct API Calls** (Fallback)
- Direct HTTP requests to Finnhub REST API
- Used when the library fails or is unavailable

### 3. **Hardcoded Symbol List** (Ultimate Fallback)
- Pre-defined list of top 100 ASX stocks
- Ensures the system always works, even without API access

## Available Methods

### Getting Stock Symbols
```python
from asx_trader.market import MarketScanner

scanner = MarketScanner()

# Get symbols based on scan mode (full, sector, filtered, trending)
symbols = scanner.get_market_symbols()
```

### Getting Market Data
```python
# Get data for specific symbols
market_data = scanner.get_market_data(["BHP", "CBA", "NAB"])

# Get data for all configured symbols
market_data = scanner.get_market_data()
```

### Getting Company News
```python
# Get recent news for a company (requires valid API key)
news = scanner.get_company_news("BHP", days_back=7)
```

### Finding Opportunities
```python
# Scan for trading opportunities
opportunities = scanner.find_opportunities()
```

## Data Sources and Fallbacks

| Feature | With Valid API Key | Without API Key |
|---------|-------------------|-----------------|
| Stock Symbols | Finnhub API → Hardcoded list | Hardcoded list |
| Market Data | Finnhub API → Dummy data | Dummy data |
| Company News | Finnhub API | Not available |
| Trending Symbols | Finnhub API → Default list | Default list |

## API Rate Limits

The free Finnhub tier has these limits:
- **60 calls per minute**
- **30 calls per second**

The implementation includes:
- Automatic rate limiting through the library
- ThreadPoolExecutor with limited workers (max 20)
- Graceful fallbacks when limits are exceeded

## Error Handling

The system handles various error scenarios:

1. **Invalid/Missing API Key**: Falls back to hardcoded data
2. **Rate Limit Exceeded**: Uses cached data or dummy data
3. **Network Issues**: Retries with exponential backoff
4. **API Downtime**: Falls back to alternative data sources

## Example Output

With a valid API key, you'll see:
```
=== Testing Finnhub Integration ===

Finnhub API Key configured: Yes
Finnhub client initialized: Yes
Scan mode: full
Max stocks to analyze: 20

1. Testing get_market_symbols()...
   Retrieved 20 symbols: ['BHP', 'CBA', 'CSL', 'NAB', 'WBC', 'ANZ', 'FMG', 'WES', 'TLS', 'RIO']...

2. Testing get_market_data() with sample symbols...
   BHP:
     Price: $45.23
     Volume: 12,345,678
     Change: 1.25%
     Source: Finnhub Library

   CBA:
     Price: $102.45
     Volume: 8,765,432
     Change: -0.75%
     Source: Finnhub Library
```

Without a valid API key:
```
=== Testing Finnhub Integration ===

Finnhub API Key configured: No
Finnhub client initialized: No
Scan mode: full
Max stocks to analyze: 20

1. Testing get_market_symbols()...
   Retrieved 20 symbols: ['BHP', 'CBA', 'CSL', 'NAB', 'WBC', 'ANZ', 'FMG', 'WES', 'TLS', 'RIO']...

2. Testing get_market_data() with sample symbols...
   BHP:
     Price: $67.89
     Volume: 543,210
     Change: 2.15%
     Source: Generated
```

## Troubleshooting

### Common Issues

1. **401 Authentication Error**
   - Check that your API key is correct in the `.env` file
   - Ensure there are no extra spaces or quotes around the key

2. **429 Rate Limit Error**
   - Reduce `MAX_STOCKS_TO_ANALYZE` in `.env`
   - Add delays between API calls if needed

3. **No Data Returned**
   - Check if the stock symbol exists on Finnhub
   - ASX symbols should be in format "SYMBOL.AX" (handled automatically)

### Getting Help

- Finnhub API Documentation: [https://finnhub.io/docs/api](https://finnhub.io/docs/api)
- Python Library Documentation: [https://github.com/Finnhub-Stock-API/finnhub-python](https://github.com/Finnhub-Stock-API/finnhub-python)

## Next Steps

1. **Get a paid Finnhub plan** for higher rate limits and more features
2. **Add other data sources** like Alpha Vantage or Yahoo Finance as additional fallbacks
3. **Implement caching** to reduce API calls and improve performance
4. **Add real-time WebSocket feeds** for live market data
