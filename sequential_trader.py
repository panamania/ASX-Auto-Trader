#!/usr/bin/env python3
"""
Sequential ASX Trader following the specific workflow:
1. Look at trending news to identify ASX listed symbols to assess
2. Use OpenAI to check if symbols fall under buy/sell/hold 
3. Use FinnHub to get realtime market quotes
4. IG to complete trading action determined by OpenAI
"""
import os
import sys
import time
import logging
import datetime
import argparse
import traceback
import json
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("sequential_trader.log")
    ]
)
logger = logging.getLogger(__name__)

# Import modules
try:
    from asx_trader.config import Config
    from asx_trader.news import ASXNewsCollector
    from asx_trader.market import MarketScanner
    from asx_trader.openai_client import create_openai_client
    from asx_trader.broker import BrokerFactory
    from asx_trader.database import Database
except Exception as e:
    logger.error(f"Error importing modules: {e}")
    traceback.print_exc()
    sys.exit(1)

class SequentialTradingSystem:
    """Sequential trading system following the specified workflow"""
    
    def __init__(self):
        """Initialize the sequential trading system"""
        self.news_collector = ASXNewsCollector()
        self.market_scanner = MarketScanner()
        self.openai_client = create_openai_client(Config.OPENAI_API_KEY)
        self.broker = BrokerFactory.get_broker()
        self.database = Database()
        
        logger.info("Sequential trading system initialized")
    
    def step1_analyze_trending_news(self, limit: int = 20) -> List[str]:
        """
        Step 1: Look at trending news to identify ASX listed symbols to assess
        
        Args:
            limit: Maximum number of news items to analyze
            
        Returns:
            List of unique ASX symbols mentioned in trending news
        """
        logger.info("STEP 1: Analyzing trending news to identify ASX symbols")
        
        try:
            # Fetch latest market-wide news
            news_items = self.news_collector.fetch_latest_news(
                symbols=None, 
                limit=limit, 
                market_wide=True
            )
            
            if not news_items:
                logger.warning("No news items found")
                return []
            
            logger.info(f"Retrieved {len(news_items)} news items")
            
            # Extract symbols mentioned in news
            symbols_from_news = set()
            
            for news_item in news_items:
                # Get symbols directly mentioned in the news
                news_symbols = news_item.get('symbols', [])
                symbols_from_news.update(news_symbols)
                
                # Also extract symbols from headline and content using basic pattern matching
                text = f"{news_item.get('headline', '')} {news_item.get('content', '')}"
                extracted_symbols = self._extract_asx_symbols_from_text(text)
                symbols_from_news.update(extracted_symbols)
            
            # Filter to valid ASX symbols and remove duplicates
            valid_symbols = self._filter_valid_asx_symbols(list(symbols_from_news))
            
            logger.info(f"Identified {len(valid_symbols)} unique ASX symbols from trending news: {valid_symbols}")
            
            # Save news analysis to database
            self.database.save_news_analysis({
                'timestamp': datetime.datetime.now().isoformat(),
                'news_items_analyzed': len(news_items),
                'symbols_identified': valid_symbols,
                'news_sources': list(set([item.get('source', 'Unknown') for item in news_items]))
            })
            
            return valid_symbols
            
        except Exception as e:
            logger.error(f"Error in step 1 (news analysis): {e}")
            traceback.print_exc()
            return []
    
    def step2_openai_analysis(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Step 2: Use OpenAI to check if symbols fall under buy/sell/hold
        
        Args:
            symbols: List of ASX symbols to analyze
            
        Returns:
            Dictionary mapping symbols to their OpenAI analysis results
        """
        logger.info(f"STEP 2: Using OpenAI to analyze {len(symbols)} symbols for buy/sell/hold recommendations")
        
        if not symbols:
            logger.warning("No symbols provided for OpenAI analysis")
            return {}
        
        try:
            # Prepare the prompt for OpenAI
            symbols_text = ", ".join(symbols)
            
            prompt = f"""
You are an expert ASX (Australian Stock Exchange) trader and analyst. Analyze the following ASX-listed symbols and provide trading recommendations.

Symbols to analyze: {symbols_text}

For each symbol, provide:
1. Trading recommendation: BUY, SELL, or HOLD
2. Confidence level: HIGH, MEDIUM, or LOW
3. Brief reasoning (1-2 sentences)
4. Risk level: LOW, MEDIUM, HIGH, or EXTREME

Consider current market conditions, recent news sentiment, and general market trends for ASX stocks.

Respond in the following JSON format:
{{
    "analysis": {{
        "SYMBOL1": {{
            "recommendation": "BUY|SELL|HOLD",
            "confidence": "HIGH|MEDIUM|LOW",
            "reasoning": "Brief explanation",
            "risk_level": "LOW|MEDIUM|HIGH|EXTREME"
        }},
        "SYMBOL2": {{
            "recommendation": "BUY|SELL|HOLD",
            "confidence": "HIGH|MEDIUM|LOW", 
            "reasoning": "Brief explanation",
            "risk_level": "LOW|MEDIUM|HIGH|EXTREME"
        }}
    }},
    "market_sentiment": "Overall market sentiment assessment",
    "timestamp": "{datetime.datetime.now().isoformat()}"
}}

Only analyze symbols that are valid ASX-listed companies. If a symbol is not a valid ASX stock, exclude it from the analysis.
"""

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert ASX trader and financial analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response received: {len(response_text)} characters")
            
            # Try to parse JSON response
            try:
                analysis_result = json.loads(response_text)
                analysis_data = analysis_result.get('analysis', {})
                
                logger.info(f"OpenAI analysis completed for {len(analysis_data)} symbols")
                
                # Log individual recommendations
                for symbol, data in analysis_data.items():
                    recommendation = data.get('recommendation', 'UNKNOWN')
                    confidence = data.get('confidence', 'UNKNOWN')
                    reasoning = data.get('reasoning', 'No reasoning provided')
                    logger.info(f"  {symbol}: {recommendation} ({confidence} confidence) - {reasoning}")
                
                # Save OpenAI analysis to database
                self.database.save_openai_analysis({
                    'timestamp': datetime.datetime.now().isoformat(),
                    'symbols_analyzed': list(analysis_data.keys()),
                    'analysis_result': analysis_result,
                    'tokens_used': response.usage.total_tokens if response.usage else 0
                })
                
                return analysis_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI JSON response: {e}")
                logger.error(f"Raw response: {response_text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error in step 2 (OpenAI analysis): {e}")
            traceback.print_exc()
            return {}
    
    def step3_get_market_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Step 3: Use FinnHub to get realtime market quotes
        
        Args:
            symbols: List of symbols to get quotes for
            
        Returns:
            Dictionary mapping symbols to their market data
        """
        logger.info(f"STEP 3: Getting real-time market quotes from FinnHub for {len(symbols)} symbols")
        
        if not symbols:
            logger.warning("No symbols provided for market quotes")
            return {}
        
        try:
            # Get market data using the market scanner
            market_data = self.market_scanner.get_market_data(symbols)
            
            logger.info(f"Retrieved market data for {len(market_data)} symbols")
            
            # Log market data for each symbol
            for symbol, data in market_data.items():
                price = data.get('current_price', 0)
                volume = data.get('volume', 0)
                change_pct = data.get('price_change_pct', 0)
                source = data.get('source', 'Unknown')
                
                logger.info(f"  {symbol}: ${price:.2f} (Volume: {volume:,}, Change: {change_pct*100:.2f}%) - Source: {source}")
            
            # Save market data to database
            for symbol, data in market_data.items():
                self.database.save_market_data(symbol, data)
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error in step 3 (market quotes): {e}")
            traceback.print_exc()
            return {}
    
    def step4_execute_trades(self, openai_analysis: Dict[str, Dict], market_data: Dict[str, Dict], 
                           execute_trades: bool = False) -> List[Dict]:
        """
        Step 4: Use IG to complete trading action determined by OpenAI
        
        Args:
            openai_analysis: OpenAI analysis results from step 2
            market_data: Market data from step 3
            execute_trades: Whether to actually execute trades or just simulate
            
        Returns:
            List of trade execution results
        """
        logger.info(f"STEP 4: Executing trades based on OpenAI recommendations")
        
        if not openai_analysis or not market_data:
            logger.warning("No analysis or market data available for trade execution")
            return []
        
        trade_results = []
        
        try:
            # Process each symbol with a trading recommendation
            for symbol, analysis in openai_analysis.items():
                try:
                    recommendation = analysis.get('recommendation', '').upper()
                    confidence = analysis.get('confidence', '').upper()
                    risk_level = analysis.get('risk_level', '').upper()
                    reasoning = analysis.get('reasoning', '')
                    
                    # Skip if not a buy/sell recommendation
                    if recommendation not in ['BUY', 'SELL']:
                        logger.info(f"Skipping {symbol}: recommendation is {recommendation}")
                        continue
                    
                    # Skip if no market data available
                    if symbol not in market_data:
                        logger.warning(f"Skipping {symbol}: no market data available")
                        continue
                    
                    # Skip high-risk trades unless high confidence
                    if risk_level == 'EXTREME':
                        logger.warning(f"Skipping {symbol}: extreme risk level")
                        continue
                    
                    if risk_level == 'HIGH' and confidence != 'HIGH':
                        logger.warning(f"Skipping {symbol}: high risk with {confidence} confidence")
                        continue
                    
                    # Get current market price
                    current_price = market_data[symbol].get('current_price', 0)
                    if current_price <= 0:
                        logger.warning(f"Skipping {symbol}: invalid price {current_price}")
                        continue
                    
                    # Calculate position size based on confidence and risk
                    position_size = self._calculate_position_size(
                        current_price, confidence, risk_level
                    )
                    
                    if position_size <= 0:
                        logger.info(f"Skipping {symbol}: calculated position size is 0")
                        continue
                    
                    # Prepare trade parameters
                    trade_params = {
                        'symbol': symbol,
                        'direction': recommendation,
                        'quantity': position_size,
                        'order_type': 'MARKET',
                        'current_price': current_price,
                        'confidence': confidence,
                        'risk_level': risk_level,
                        'reasoning': reasoning
                    }
                    
                    logger.info(f"Preparing trade: {recommendation} {position_size} {symbol} @ ${current_price:.2f}")
                    logger.info(f"  Confidence: {confidence}, Risk: {risk_level}")
                    logger.info(f"  Reasoning: {reasoning}")
                    
                    # Execute the trade
                    if execute_trades and Config.TRADING_ENABLED:
                        logger.info(f"Executing trade for {symbol}")
                        trade_result = self.broker.execute_trade(
                            symbol=symbol,
                            direction=recommendation,
                            quantity=position_size,
                            order_type='MARKET'
                        )
                    else:
                        logger.info(f"Simulating trade for {symbol} (execute_trades={execute_trades}, TRADING_ENABLED={Config.TRADING_ENABLED})")
                        trade_result = {
                            'status': 'SIMULATED',
                            'dealReference': f'SIM-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}-{symbol}',
                            'details': f'Simulated {recommendation} {position_size} {symbol} @ ${current_price:.2f}'
                        }
                    
                    # Add trade parameters to result
                    trade_result.update(trade_params)
                    trade_results.append(trade_result)
                    
                    # Log trade result
                    status = trade_result.get('status', 'UNKNOWN')
                    deal_ref = trade_result.get('dealReference', 'N/A')
                    logger.info(f"Trade result for {symbol}: {status} (Reference: {deal_ref})")
                    
                    # Save trade to database
                    self.database.save_trade_execution({
                        'timestamp': datetime.datetime.now().isoformat(),
                        'symbol': symbol,
                        'direction': recommendation,
                        'quantity': position_size,
                        'price': current_price,
                        'status': status,
                        'deal_reference': deal_ref,
                        'confidence': confidence,
                        'risk_level': risk_level,
                        'reasoning': reasoning,
                        'executed': execute_trades and Config.TRADING_ENABLED
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing trade for {symbol}: {e}")
                    continue
            
            logger.info(f"Trade execution completed: {len(trade_results)} trades processed")
            return trade_results
            
        except Exception as e:
            logger.error(f"Error in step 4 (trade execution): {e}")
            traceback.print_exc()
            return []
    
    def run_sequential_cycle(self, news_limit: int = 20, execute_trades: bool = False) -> Dict:
        """
        Run the complete sequential trading cycle
        
        Args:
            news_limit: Maximum number of news items to analyze
            execute_trades: Whether to actually execute trades
            
        Returns:
            Dictionary with cycle results
        """
        start_time = datetime.datetime.now()
        logger.info(f"Starting sequential trading cycle at {start_time}")
        
        cycle_results = {
            'start_time': start_time.isoformat(),
            'step1_symbols': [],
            'step2_analysis': {},
            'step3_market_data': {},
            'step4_trades': [],
            'status': 'completed',
            'error': None
        }
        
        try:
            # Step 1: Analyze trending news
            symbols = self.step1_analyze_trending_news(news_limit)
            cycle_results['step1_symbols'] = symbols
            
            if not symbols:
                logger.warning("No symbols identified from news analysis")
                cycle_results['status'] = 'no_symbols_found'
                return cycle_results
            
            # Step 2: OpenAI analysis
            openai_analysis = self.step2_openai_analysis(symbols)
            cycle_results['step2_analysis'] = openai_analysis
            
            if not openai_analysis:
                logger.warning("No OpenAI analysis results")
                cycle_results['status'] = 'openai_analysis_failed'
                return cycle_results
            
            # Step 3: Get market quotes
            market_data = self.step3_get_market_quotes(list(openai_analysis.keys()))
            cycle_results['step3_market_data'] = market_data
            
            if not market_data:
                logger.warning("No market data retrieved")
                cycle_results['status'] = 'market_data_failed'
                return cycle_results
            
            # Step 4: Execute trades
            trade_results = self.step4_execute_trades(openai_analysis, market_data, execute_trades)
            cycle_results['step4_trades'] = trade_results
            
            end_time = datetime.datetime.now()
            cycle_results['end_time'] = end_time.isoformat()
            cycle_results['duration_seconds'] = (end_time - start_time).total_seconds()
            
            logger.info(f"Sequential trading cycle completed successfully in {cycle_results['duration_seconds']:.1f} seconds")
            
        except Exception as e:
            logger.error(f"Error in sequential trading cycle: {e}")
            traceback.print_exc()
            cycle_results['status'] = 'error'
            cycle_results['error'] = str(e)
        
        return cycle_results
    
    def _extract_asx_symbols_from_text(self, text: str) -> List[str]:
        """Extract potential ASX symbols from text"""
        import re
        
        # Pattern for 3-letter uppercase words (potential stock codes)
        pattern = r'\b[A-Z]{3}\b'
        matches = re.findall(pattern, text.upper())
        
        # Exclude common non-stock words
        exclude_words = {
            'THE', 'AND', 'FOR', 'BUT', 'NOT', 'NEW', 'NOW', 'HAS', 'HAD', 
            'WHO', 'WHY', 'HOW', 'ALL', 'ASX', 'CEO', 'CFO', 'USD', 'AUD',
            'GDP', 'RBA', 'ETF', 'IPO', 'AGM', 'EPS', 'ROE', 'ROI', 'ESG'
        }
        
        # Filter out excluded words and return unique symbols
        symbols = [match for match in matches if match not in exclude_words]
        return list(set(symbols))
    
    def _filter_valid_asx_symbols(self, symbols: List[str]) -> List[str]:
        """Filter to valid ASX symbols using known symbol list"""
        # Get known ASX symbols from market scanner
        known_symbols = self.market_scanner._get_asx_symbols()
        
        # Filter to only include known symbols
        valid_symbols = [symbol for symbol in symbols if symbol in known_symbols]
        
        # Limit to reasonable number for analysis
        return valid_symbols[:20]
    
    def _calculate_position_size(self, price: float, confidence: str, risk_level: str) -> int:
        """Calculate position size based on price, confidence, and risk"""
        try:
            # Get account balance
            account_info = self.broker.get_account_info()
            account_balance = 1000  # Default fallback
            
            if account_info and 'accounts' in account_info:
                for account in account_info['accounts']:
                    if account.get('preferred', False):
                        balance_data = account.get('balance', {})
                        account_balance = float(balance_data.get('available', 1000))
                        break
            
            # Base allocation percentage based on confidence and risk
            base_allocation = {
                ('HIGH', 'LOW'): 0.10,      # 10% for high confidence, low risk
                ('HIGH', 'MEDIUM'): 0.08,   # 8% for high confidence, medium risk
                ('HIGH', 'HIGH'): 0.05,     # 5% for high confidence, high risk
                ('MEDIUM', 'LOW'): 0.06,    # 6% for medium confidence, low risk
                ('MEDIUM', 'MEDIUM'): 0.04, # 4% for medium confidence, medium risk
                ('MEDIUM', 'HIGH'): 0.02,   # 2% for medium confidence, high risk
                ('LOW', 'LOW'): 0.03,       # 3% for low confidence, low risk
                ('LOW', 'MEDIUM'): 0.02,    # 2% for low confidence, medium risk
                ('LOW', 'HIGH'): 0.01,      # 1% for low confidence, high risk
            }
            
            allocation_pct = base_allocation.get((confidence, risk_level), 0.02)  # Default 2%
            
            # Calculate position value and size
            position_value = account_balance * allocation_pct
            position_size = int(position_value / price)
            
            # Minimum position size of 1, maximum reasonable limit
            position_size = max(1, min(position_size, 1000))
            
            logger.debug(f"Position size calculation: ${account_balance:.2f} balance, {allocation_pct*100:.1f}% allocation, "
                        f"${price:.2f} price = {position_size} shares")
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def print_cycle_summary(self, cycle_results: Dict):
        """Print a summary of the trading cycle results"""
        print("\n" + "="*80)
        print("SEQUENTIAL ASX TRADER CYCLE RESULTS")
        print("="*80)
        
        print(f"Start Time: {cycle_results.get('start_time', 'Unknown')}")
        print(f"Status: {cycle_results.get('status', 'Unknown')}")
        
        if cycle_results.get('duration_seconds'):
            print(f"Duration: {cycle_results['duration_seconds']:.1f} seconds")
        
        # Step 1 results
        symbols = cycle_results.get('step1_symbols', [])
        print(f"\nSTEP 1 - News Analysis:")
        print(f"  Symbols identified: {len(symbols)}")
        if symbols:
            print(f"  Symbols: {', '.join(symbols)}")
        
        # Step 2 results
        analysis = cycle_results.get('step2_analysis', {})
        print(f"\nSTEP 2 - OpenAI Analysis:")
        print(f"  Symbols analyzed: {len(analysis)}")
        
        if analysis:
            buy_signals = [s for s, a in analysis.items() if a.get('recommendation') == 'BUY']
            sell_signals = [s for s, a in analysis.items() if a.get('recommendation') == 'SELL']
            hold_signals = [s for s, a in analysis.items() if a.get('recommendation') == 'HOLD']
            
            print(f"  BUY recommendations: {len(buy_signals)} - {', '.join(buy_signals)}")
            print(f"  SELL recommendations: {len(sell_signals)} - {', '.join(sell_signals)}")
            print(f"  HOLD recommendations: {len(hold_signals)} - {', '.join(hold_signals)}")
        
        # Step 3 results
        market_data = cycle_results.get('step3_market_data', {})
        print(f"\nSTEP 3 - Market Data:")
        print(f"  Quotes retrieved: {len(market_data)}")
        
        # Step 4 results
        trades = cycle_results.get('step4_trades', [])
        print(f"\nSTEP 4 - Trade Execution:")
        print(f"  Trades processed: {len(trades)}")
        
        if trades:
            executed_trades = [t for t in trades if t.get('status') not in ['SIMULATED', 'ERROR']]
            simulated_trades = [t for t in trades if t.get('status') == 'SIMULATED']
            failed_trades = [t for t in trades if t.get('status') == 'ERROR']
            
            print(f"  Executed: {len(executed_trades)}")
            print(f"  Simulated: {len(simulated_trades)}")
            print(f"  Failed: {len(failed_trades)}")
            
            # Show individual trade details
            for trade in trades:
                symbol = trade.get('symbol', 'Unknown')
                direction = trade.get('direction', 'Unknown')
                quantity = trade.get('quantity', 0)
                price = trade.get('current_price', 0)
                status = trade.get('status', 'Unknown')
                confidence = trade.get('confidence', 'Unknown')
                
                print(f"    {symbol}: {direction} {quantity} @ ${price:.2f} - {status} ({confidence} confidence)")
        
        if cycle_results.get('error'):
            print(f"\nERROR: {cycle_results['error']}")
        
        print("="*80)

def main():
    """Main function for sequential ASX trader"""
    parser = argparse.ArgumentParser(description="Sequential ASX Trader System")
    parser.add_argument("--news-limit", type=int, default=20, help="Maximum number of news items to analyze")
    parser.add_argument("--execute-trades", action="store_true", help="Execute actual trades (requires TRADING_ENABLED=true)")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=90, help="Interval between cycles in minutes (for continuous mode)")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)
    
    logger.info("Starting Sequential ASX Trader System")
    
    # Initialize trading system
    trading_system = SequentialTradingSystem()
    
    try:
        if args.run_once:
            # Run single cycle
            cycle_results = trading_system.run_sequential_cycle(
                news_limit=args.news_limit,
                execute_trades=args.execute_trades
            )
            trading_system.print_cycle_summary(cycle_results)
        else:
            # Continuous operation
            while True:
                try:
                    cycle_results = trading_system.run_sequential_cycle(
                        news_limit=args.news_limit,
                        execute_trades=args.execute_trades
                    )
                    trading_system.print_cycle_summary(cycle_results)
                    
                    # Wait for next cycle
                    wait_seconds = args.interval * 60
                    next_run = datetime.datetime.now() + datetime.timedelta(seconds=wait_seconds)
                    logger.info(f"Next cycle scheduled at {next_run} (waiting {args.interval} minutes)")
                    time.sleep(wait_seconds)
                    
                except KeyboardInterrupt:
                    logger.info("Sequential trading system stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in trading cycle: {e}")
                    traceback.print_exc()
                    # Wait before retrying
                    time.sleep(60)
        
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        traceback.print_exc()
    finally:
        logger.info("Sequential trading system shutdown")

if __name__ == "__main__":
    main()
