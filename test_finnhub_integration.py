#!/usr/bin/env python3
"""
Test script to demonstrate the improved Finnhub integration in market.py
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from asx_trader.market import MarketScanner

def test_finnhub_integration():
    """Test the Finnhub integration with both library and direct API methods."""
    
    print("=== Testing Finnhub Integration ===\n")
    
    # Initialize the market scanner
    scanner = MarketScanner()
    
    print(f"Finnhub API Key configured: {'Yes' if scanner.finnhub_api_key else 'No'}")
    print(f"Finnhub client initialized: {'Yes' if scanner.finnhub_client else 'No'}")
    print(f"Scan mode: {scanner.scan_mode}")
    print(f"Max stocks to analyze: {scanner.max_stocks}")
    print()
    
    # Test getting market symbols
    print("1. Testing get_market_symbols()...")
    symbols = scanner.get_market_symbols()
    print(f"   Retrieved {len(symbols)} symbols: {symbols[:10]}{'...' if len(symbols) > 10 else ''}")
    print()
    
    # Test getting market data for a few symbols
    print("2. Testing get_market_data() with sample symbols...")
    test_symbols = ["BHP", "CBA", "NAB"]
    market_data = scanner.get_market_data(test_symbols)
    
    for symbol, data in market_data.items():
        print(f"   {symbol}:")
        print(f"     Price: ${data.get('current_price', 'N/A')}")
        print(f"     Volume: {data.get('volume', 'N/A'):,}")
        print(f"     Change: {data.get('price_change_pct', 0)*100:.2f}%")
        print(f"     Source: {data.get('source', 'Unknown')}")
        print()
    
    # Test trending symbols if Finnhub client is available
    if scanner.finnhub_client:
        print("3. Testing get_trending_symbols()...")
        try:
            trending = scanner._get_trending_symbols()
            print(f"   Found {len(trending)} trending symbols: {trending[:5]}{'...' if len(trending) > 5 else ''}")
        except Exception as e:
            print(f"   Error getting trending symbols: {e}")
        print()
        
        # Test company news
        print("4. Testing get_company_news()...")
        try:
            news = scanner.get_company_news("BHP", days_back=3)
            print(f"   Found {len(news)} news articles for BHP")
            if news:
                print(f"   Latest headline: {news[0].get('headline', 'N/A')[:100]}...")
        except Exception as e:
            print(f"   Error getting company news: {e}")
        print()
    else:
        print("3. Skipping trending symbols test (Finnhub client not available)")
        print("4. Skipping company news test (Finnhub client not available)")
        print()
    
    # Test opportunity finding
    print("5. Testing find_opportunities()...")
    opportunities = scanner.find_opportunities(market_data)
    print(f"   Found {len(opportunities)} opportunities: {opportunities}")
    print()
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    test_finnhub_integration()
