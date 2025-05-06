# ASX-Auto-Trader

An automated trading system that uses GPT to analyze ASX news, generate trading signals, manage risk, and execute trades.

## Features

- **ASX News Integration**: Automatically fetches the latest news from the Australian Securities Exchange
- **GPT-Enhanced Analysis**: Uses OpenAI's GPT models to analyze news and generate trading signals
- **Risk Management**: Assesses market conditions and adjusts position sizes accordingly
- **Automated Trading**: Can execute trades through broker APIs based on AI-generated signals
- **Cloud Deployment**: AWS integration for storage, monitoring, and notifications
- **Alert System**: Monitors trading activity and sends notifications for critical events

## Architecture

![Architecture Diagram](docs/architecture.html)

The system consists of several components:
1. **News Collector**: Fetches latest ASX news input
2. **Prediction Engine**: GPT-enhanced analysis of news to provide BUY/SELL/HOLD signals
3. **Risk Management**: Assesses market conditions to generate risk summaries
4. **Broker API**: Places trades via broker API
5. **Monitoring System**: Tracks trading activity and sends notifications
6. **AWS Cloud Deployment**: Handles storage and cloud resources

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API account
- AWS account
- ASX data provider subscription
- Broker account with API access

### Setup

1. Clone the repository:

git clone https://github.com/yourusername/ASX-Auto-Trader.git
cd ASX-Auto-Trader

2. Create a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:

pip install -r requirements.txt

4. Create a `.env` file:

cp .env.example .env

Then edit the `.env` file with your actual credentials and settings.

5. Run the system:

python run.py

## Configuration

The system can be configured through environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `ASX_API_KEY`: API key for ASX data provider
- `BROKER_API_KEY`: Your broker API key
- `WATCH_SYMBOLS`: Comma-separated list of stock symbols to monitor
- `MAX_POSITION_SIZE`: Maximum position size in dollars
- `TRADING_ENABLED`: Set to "true" to enable actual trading, "false" for simulation
- `CYCLE_INTERVAL_SECONDS`: Time between trading cycles

## Testing

Run the test suite:

python -m unittest discover tests

## Deployment

### Local Deployment

For a local deployment, set up a scheduled task or service to run the system at regular intervals.

### AWS Deployment

For production, we recommend deploying on AWS:
- EC2 instance for continuous operation
- S3 for data storage
- SNS for notifications
- CloudWatch for monitoring

## Security Considerations

- Never commit your `.env` file
- Use AWS IAM roles with minimal permissions
- Implement circuit breakers for trading safety
- Start with simulation mode before enabling real trading

## License

This project is licensed under the MIT License - see the LICENSE file for details.
