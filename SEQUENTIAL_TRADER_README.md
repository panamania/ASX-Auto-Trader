# Sequential ASX Trader

This document describes the new Sequential ASX Trader that follows a specific 4-step workflow for automated trading decisions.

## Workflow Overview

The Sequential ASX Trader follows this exact sequence:

1. **News Analysis** → Identify ASX symbols from trending news
2. **OpenAI Analysis** → Get buy/sell/hold recommendations 
3. **FinnHub Market Data** → Retrieve real-time quotes
4. **IG Trading** → Execute trades based on AI recommendations

## Step-by-Step Process

### Step 1: News Analysis
- Fetches trending news from multiple sources (Google News RSS, NewsData.io, ASX announcements)
- Extracts ASX stock symbols mentioned in news headlines and content
- Filters to valid ASX-listed companies
- Returns a list of symbols that are currently in the news

### Step 2: OpenAI Analysis
- Sends the identified symbols to OpenAI GPT-4 for analysis
- Receives structured recommendations for each symbol:
  - **Recommendation**: BUY, SELL, or HOLD
  - **Confidence**: HIGH, MEDIUM, or LOW
  - **Risk Level**: LOW, MEDIUM, HIGH, or EXTREME
  - **Reasoning**: Brief explanation for the recommendation

### Step 3: Market Data Retrieval
- Uses FinnHub API to get real-time market quotes for recommended symbols
- Retrieves current price, volume, price changes, and other market data
- Saves historical market data for analysis and tracking

### Step 4: Trade Execution
- Processes OpenAI recommendations and executes trades via IG Markets API
- Applies risk management rules:
  - Skips EXTREME risk trades
  - Requires HIGH confidence for HIGH risk trades
  - Calculates position sizes based on confidence and risk levels
- Supports both live trading and simulation modes

## Installation and Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file with the following variables:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional (system will use fallbacks if not provided)
FINNHUB_API_KEY=your-finnhub-api-key
NEWSDATA_API_KEY=your-newsdata-api-key

# For live trading (optional - will use simulation if not provided)
BROKER_API_KEY=your-ig-api-key
BROKER_USERNAME=your-ig-username
BROKER_PASSWORD=your-ig-password
BROKER_TYPE=IG
BROKER_ACCOUNT_TYPE=DEMO  # or LIVE for real trading

# Trading configuration
TRADING_ENABLED=false  # Set to true for live trading
MAX_POSITION_SIZE=10000
CYCLE_INTERVAL_MINUTES=90

# Database
DB_PATH=data/asx_trader.db
```

### 3. Test the System
```bash
python test_sequential_trader.py
```

## Usage

### Run Once (Single Cycle)
```bash
# Simulation mode (default)
python sequential_trader.py --run-once

# With trade execution (requires TRADING_ENABLED=true)
python sequential_trader.py --run-once --execute-trades
```

### Continuous Operation
```bash
# Run continuously with 90-minute intervals
python sequential_trader.py

# Custom interval (in minutes)
python sequential_trader.py --interval 60

# With trade execution
python sequential_trader.py --execute-trades
```

### Command Line Options
- `--run-once`: Run a single cycle and exit
- `--execute-trades`: Execute actual trades (requires TRADING_ENABLED=true)
- `--news-limit N`: Maximum number of news items to analyze (default: 20)
- `--interval N`: Minutes between cycles for continuous mode (default: 90)

## Risk Management

The system includes multiple layers of risk management:

### Position Sizing
Position sizes are calculated based on confidence and risk levels:

| Confidence | Risk Level | Allocation % |
|------------|------------|--------------|
| HIGH       | LOW        | 10%          |
| HIGH       | MEDIUM     | 8%           |
| HIGH       | HIGH       | 5%           |
| MEDIUM     | LOW        | 6%           |
| MEDIUM     | MEDIUM     | 4%           |
| MEDIUM     | HIGH       | 2%           |
| LOW        | LOW        | 3%           |
| LOW        | MEDIUM     | 2%           |
| LOW        | HIGH       | 1%           |

### Trade Filtering
- EXTREME risk trades are automatically rejected
- HIGH risk trades require HIGH confidence
- Invalid prices or missing market data cause trades to be skipped
- Account balance is checked before executing trades

### Safety Features
- All trades are simulated by default unless explicitly enabled
- Comprehensive logging of all decisions and actions
- Database tracking of all analysis and trade results
- Fallback mechanisms for API failures

## Output and Monitoring

### Console Output
The system provides detailed console output showing:
- Step-by-step progress through the workflow
- Symbols identified from news
- OpenAI recommendations with reasoning
- Market data retrieved
- Trade execution results

### Database Tracking
All activities are logged to an SQLite database:
- News analysis results
- OpenAI analysis and token usage
- Market data history
- Trade executions
- System performance metrics

### Log Files
Detailed logs are written to `sequential_trader.log` including:
- API calls and responses
- Error messages and stack traces
- Timing information
- Decision rationale

## API Integration Details

### News Sources
1. **Google News RSS** (Free)
   - ASX-specific news searches
   - No API key required
   - Primary source for trending news

2. **NewsData.io** (Optional)
   - Australian business news
   - Company-specific news searches
   - Requires API key

3. **ASX Announcements** (Free)
   - Official company announcements
   - Market-sensitive information
   - No API key required

### Market Data
- **FinnHub API**: Real-time ASX stock quotes
- **Fallback**: Generated dummy data for testing
- Supports both library and direct API calls

### AI Analysis
- **OpenAI GPT-4**: Trading recommendations
- Structured JSON responses
- Token usage tracking

### Trading
- **IG Markets API**: Trade execution
- **Simulation Mode**: Safe testing without real trades
- Account balance and position tracking

## Example Output

```
================================================================================
SEQUENTIAL ASX TRADER CYCLE RESULTS
================================================================================
Start Time: 2025-06-04T22:30:00
Status: completed
Duration: 45.2 seconds

STEP 1 - News Analysis:
  Symbols identified: 5
  Symbols: BHP, CBA, RIO, WBC, CSL

STEP 2 - OpenAI Analysis:
  Symbols analyzed: 5
  BUY recommendations: 2 - BHP, RIO
  SELL recommendations: 1 - WBC
  HOLD recommendations: 2 - CBA, CSL

STEP 3 - Market Data:
  Quotes retrieved: 5

STEP 4 - Trade Execution:
  Trades processed: 3
  Executed: 0
  Simulated: 3
  Failed: 0
    BHP: BUY 15 @ $45.23 - SIMULATED (HIGH confidence)
    RIO: BUY 8 @ $125.67 - SIMULATED (MEDIUM confidence)
    WBC: SELL 12 @ $28.45 - SIMULATED (HIGH confidence)
================================================================================
```

## Troubleshooting

### Common Issues

1. **No symbols found from news**
   - Check internet connection
   - Verify news sources are accessible
   - Try increasing `--news-limit`

2. **OpenAI analysis fails**
   - Verify OPENAI_API_KEY is correct
   - Check API quota and billing
   - Ensure sufficient token allowance

3. **No market data retrieved**
   - Check FINNHUB_API_KEY if using FinnHub
   - Verify symbols are valid ASX stocks
   - System will use dummy data as fallback

4. **Trade execution errors**
   - Verify broker credentials
   - Check account balance
   - Ensure TRADING_ENABLED=true for live trading

### Debug Mode
For detailed debugging, check the log file:
```bash
tail -f sequential_trader.log
```

## Safety Considerations

⚠️ **Important Safety Notes:**

1. **Always test in simulation mode first**
2. **Start with small position sizes**
3. **Use DEMO account before LIVE trading**
4. **Monitor the system closely during initial runs**
5. **Set appropriate risk limits in your broker account**
6. **Keep TRADING_ENABLED=false until you're confident**

## Support

For issues or questions:
1. Check the log files for error details
2. Run the test script to verify configuration
3. Review the database for historical data
4. Ensure all API keys are valid and have sufficient quotas

The Sequential ASX Trader is designed to be robust and safe, with multiple fallback mechanisms and comprehensive logging to help you understand and monitor its operation.
