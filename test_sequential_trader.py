#!/usr/bin/env python3
"""
Test script for the Sequential ASX Trader to verify the workflow.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_sequential_trader():
    """Test the sequential trader workflow"""
    print("="*60)
    print("TESTING SEQUENTIAL ASX TRADER")
    print("="*60)
    
    try:
        from sequential_trader import SequentialTradingSystem
        
        # Initialize the trading system
        print("1. Initializing Sequential Trading System...")
        trading_system = SequentialTradingSystem()
        print("   ✓ Trading system initialized successfully")
        
        # Test each step individually
        print("\n2. Testing Step 1: News Analysis...")
        symbols = trading_system.step1_analyze_trending_news(limit=10)
        print(f"   ✓ Found {len(symbols)} symbols from news: {symbols}")
        
        if symbols:
            print("\n3. Testing Step 2: OpenAI Analysis...")
            # Test with a smaller subset for faster testing
            test_symbols = symbols[:3] if len(symbols) > 3 else symbols
            openai_analysis = trading_system.step2_openai_analysis(test_symbols)
            print(f"   ✓ OpenAI analyzed {len(openai_analysis)} symbols")
            
            for symbol, analysis in openai_analysis.items():
                recommendation = analysis.get('recommendation', 'UNKNOWN')
                confidence = analysis.get('confidence', 'UNKNOWN')
                print(f"     {symbol}: {recommendation} ({confidence} confidence)")
            
            if openai_analysis:
                print("\n4. Testing Step 3: Market Data...")
                market_data = trading_system.step3_get_market_quotes(list(openai_analysis.keys()))
                print(f"   ✓ Retrieved market data for {len(market_data)} symbols")
                
                for symbol, data in market_data.items():
                    price = data.get('current_price', 0)
                    source = data.get('source', 'Unknown')
                    print(f"     {symbol}: ${price:.2f} (Source: {source})")
                
                print("\n5. Testing Step 4: Trade Execution (Simulation)...")
                trade_results = trading_system.step4_execute_trades(
                    openai_analysis, market_data, execute_trades=False
                )
                print(f"   ✓ Processed {len(trade_results)} trades")
                
                for trade in trade_results:
                    symbol = trade.get('symbol', 'Unknown')
                    direction = trade.get('direction', 'Unknown')
                    quantity = trade.get('quantity', 0)
                    status = trade.get('status', 'Unknown')
                    print(f"     {symbol}: {direction} {quantity} shares - {status}")
            else:
                print("   ⚠ No OpenAI analysis results, skipping remaining steps")
        else:
            print("   ⚠ No symbols found from news, skipping remaining steps")
        
        print("\n6. Testing Full Cycle...")
        cycle_results = trading_system.run_sequential_cycle(news_limit=10, execute_trades=False)
        print(f"   ✓ Full cycle completed with status: {cycle_results.get('status')}")
        
        # Print summary
        trading_system.print_cycle_summary(cycle_results)
        
        print("\n" + "="*60)
        print("SEQUENTIAL TRADER TEST COMPLETED SUCCESSFULLY")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_configuration():
    """Check if required configuration is present"""
    print("Checking configuration...")
    
    required_vars = ['OPENAI_API_KEY']
    optional_vars = ['FINNHUB_API_KEY', 'BROKER_API_KEY', 'NEWSDATA_API_KEY']
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_required.append(var)
        else:
            print(f"   ✓ {var} is configured")
    
    for var in optional_vars:
        if not os.environ.get(var):
            missing_optional.append(var)
        else:
            print(f"   ✓ {var} is configured")
    
    if missing_required:
        print(f"   ❌ Missing required variables: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"   ⚠ Missing optional variables: {', '.join(missing_optional)}")
        print("     (System will use fallback methods)")
    
    return True

if __name__ == "__main__":
    print("Sequential ASX Trader Test")
    print("=" * 40)
    
    # Check configuration first
    if not check_configuration():
        print("\n❌ Configuration check failed. Please set up your .env file with required API keys.")
        sys.exit(1)
    
    print("\nStarting test...")
    success = test_sequential_trader()
    
    if success:
        print("\n🎉 All tests passed! The sequential trader is ready to use.")
        print("\nTo run the sequential trader:")
        print("  python sequential_trader.py --run-once")
        print("  python sequential_trader.py --run-once --execute-trades  # For real trading")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
        sys.exit(1)
