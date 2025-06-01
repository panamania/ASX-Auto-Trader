# ASX Auto Trader

A GPT-enhanced automated trading system that monitors the Australian Securities Exchange (ASX), analyzes financial news, and generates intelligent trading signals using OpenAI's GPT models.

## 🚀 Features

- **Intelligent Market Scanning**: Scans the entire ASX market or focuses on specific sectors
- **Real-time News Analysis**: Fetches and analyzes financial news from multiple sources
- **GPT-Enhanced Predictions**: Uses OpenAI GPT models to generate BUY/SELL/HOLD signals
- **Risk Management**: Assesses market conditions and adjusts position sizes accordingly
- **Multiple Data Sources**: Integrates with Finnhub, NewsData.io, and other financial APIs
- **Flexible Deployment**: Run manually, as a scheduled task, or as a system service
- **Database Tracking**: SQLite database for storing signals, analysis history, and performance metrics
- **AWS Integration**: Optional cloud deployment with S3 storage and SNS notifications
- **Rate Limiting**: Built-in API rate limiting to respect service quotas
- **Market Hours Awareness**: Operates during ASX trading hours (10 AM - 4 PM AEST/AEDT)

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key (required)
- Finnhub API key (optional, for enhanced market data)
- NewsData.io API key (optional, for news feeds)
- AWS account (optional, for cloud features)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ASX-Auto-Trader.git
cd ASX-Auto-Trader
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit the `.env` file with your API keys and configuration:

```env
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional - Enhanced market data
FINNHUB_API_KEY=your-finnhub-api-key
NEWSDATA_API_KEY=your-newsdata-api-key

# Market Configuration
MARKET_SCAN_MODE=full
MAX_STOCKS_TO_ANALYZE=20
CYCLE_INTERVAL_MINUTES=90

# Trading Configuration (DEMO mode by default)
TRADING_ENABLED=false
MAX_POSITION_SIZE=10000
```

## 🚀 Usage

### Manual Execution

```bash
# Run with default settings
python run.py

# Run once and exit
python run.py --run-once

# Analyze specific symbols
python run.py --symbols "BHP,CBA,NAB" --run-once

# Force run outside market hours
python run.py --force-run --run-once

# Limit analysis scope
python run.py --max-symbols 10 --news-limit 20 --run-once
```

### System Service Installation

For production deployment, install as a system service:

```bash
# Install service
sudo ./service-config/install-service.sh

# Enable and start
sudo systemctl enable asx-trader
sudo systemctl start asx-trader

# Manage service
~/manage-asx-trader.sh status   # Check status
~/manage-asx-trader.sh logs     # View logs
~/manage-asx-trader.sh restart  # Restart service
```

## ⚙️ Configuration

### Market Scanning Modes

- **`full`**: Scan the entire ASX market
- **`sector`**: Focus on a specific sector (requires `MARKET_SECTOR_FOCUS`)
- **`filtered`**: Apply market cap and other filters

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `MARKET_SCAN_MODE` | Scanning strategy | `full` |
| `MAX_STOCKS_TO_ANALYZE` | Maximum symbols per cycle | `20` |
| `CYCLE_INTERVAL_MINUTES` | Time between cycles | `90` |
| `MIN_MARKET_CAP` | Minimum market cap filter | `1000000` |
| `TRADING_ENABLED` | Enable actual trading | `false` |
| `BROKER_ACCOUNT_TYPE` | `DEMO` or `LIVE` | `DEMO` |

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Market        │    │   News          │    │   Prediction    │
│   Scanner       │───▶│   Collector     │───▶│   Engine        │
│                 │    │                 │    │   (GPT)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Risk          │    │   Monitoring    │
│   Storage       │    │   Management    │    │   & Alerts      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

1. **Market Scanner** (`asx_trader/market.py`)
   - Fetches ASX stock symbols and market data
   - Supports multiple data sources with fallbacks
   - Handles rate limiting and error recovery

2. **News Collector** (`asx_trader/news.py`)
   - Gathers financial news from multiple sources
   - Filters news relevant to analyzed stocks
   - Extracts company mentions and sentiment

3. **Prediction Engine** (`asx_trader/prediction.py`)
   - Analyzes news using OpenAI GPT models
   - Generates BUY/SELL/HOLD signals with confidence scores
   - Provides detailed reasoning for each recommendation

4. **Risk Management** (`asx_trader/risk.py`)
   - Assesses overall market risk levels
   - Adjusts position sizes based on volatility
   - Implements safety checks and circuit breakers

5. **Database** (`asx_trader/database.py`)
   - SQLite database for persistent storage
   - Tracks trading signals and performance
   - Maintains analysis history and metrics

## 🧪 Testing

### Run Test Suite

```bash
# Basic functionality tests
python -m unittest discover tests

# Environment validation
python test_suite/check_env.py

# API integration tests
python test_finnhub_integration.py

# OpenAI connectivity
python test_suite/tests_openai_simple.py
```

### Development Testing

```bash
# Test with minimal setup
python test_suite/openapi_minimal.py

# Check package dependencies
python test_suite/check_site_packages.py
```

## 📊 Sample Output

```
===== ASX Trader Results =====
Analyzed 45 news items for 20 symbols
Generated 8 trading signals
Overall market risk: moderate

Top Trading Signals:
1. BHP, RIO - BUY (85%)
   Reason: Strong iron ore demand outlook and positive earnings guidance...

2. CBA - HOLD (72%)
   Reason: Mixed signals from interest rate environment and housing market...

3. CSL - SELL (68%)
   Reason: Regulatory concerns and increased competition in plasma market...
```

## 🔒 Security & Safety

### Trading Safety

- **Demo Mode**: Default configuration uses simulation mode
- **Position Limits**: Configurable maximum position sizes
- **Risk Assessment**: Continuous market risk monitoring
- **Circuit Breakers**: Automatic trading halts during high volatility

### API Security

- **Environment Variables**: Sensitive data stored in `.env` file
- **Rate Limiting**: Respects API quotas and limits
- **Error Handling**: Graceful degradation when services are unavailable
- **Logging**: Comprehensive audit trail of all activities

## 🌐 Deployment Options

### Local Development

```bash
python run.py --run-once --force-run
```

### Production Service

```bash
sudo systemctl start asx-trader
```

### AWS Cloud Deployment

Configure AWS credentials in `.env`:

```env
AWS_ACCESS_KEY=your-access-key
AWS_SECRET_KEY=your-secret-key
AWS_REGION=ap-southeast-2
S3_BUCKET_NAME=your-bucket
SNS_TOPIC_ARN=your-sns-topic
```

## 📝 Logging

Logs are written to:
- Console output (when running manually)
- `asx_trader.log` (main log file)
- System journal (when running as service)

Log rotation is automatically configured for the service installation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading financial instruments involves substantial risk of loss. The authors are not responsible for any financial losses incurred through the use of this software.

**Always test thoroughly in demo mode before considering live trading.**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Documentation

- [Finnhub Setup Guide](FINNHUB_SETUP.md)
- [Service Configuration](service-config/README.md)
- [Test Suite Documentation](test_suite/README.md)
- [Architecture Overview](docs/architecture.html)
