# ASX Trader Service Installation

This directory contains configuration files and scripts to run ASX Trader as a system service.

## Quick Installation

To install ASX Trader as a system service, run:

```bash
./install-service.sh
This will:

Copy the service file to /etc/systemd/system/
Set up log rotation
Create a management script in your home directory

Starting the Service
After installation, start the service with:
bashCopysudo systemctl enable asx-trader
sudo systemctl start asx-trader
Managing the Service
Use the management script to control the service:
bashCopy~/manage-asx-trader.sh start    # Start the service
~/manage-asx-trader.sh stop     # Stop the service
~/manage-asx-trader.sh restart  # Restart the service
~/manage-asx-trader.sh status   # Check service status
~/manage-asx-trader.sh logs     # View logs
~/manage-asx-trader.sh tail     # Follow logs in real-time
~/manage-asx-trader.sh update   # Update from git and restart
~/manage-asx-trader.sh backup   # Backup the database
Customizing the Service
You can customize the service by editing /etc/systemd/system/asx-trader.service and then running:
bashCopysudo systemctl daemon-reload
sudo systemctl restart asx-trader
Common customizations:

Change the number of symbols to analyze: Edit --max-symbols value
Change memory limits: Uncomment and adjust MemoryLimit=2G
Add environment variables: Add Environment=KEY=value lines

Log Rotation
Logs are automatically rotated daily. You can find old logs in your project directory with the .gz extension.
Checking Service Health
To check if the service is running properly:
bashCopysudo systemctl status asx-trader
journalctl -u asx-trader -n 50
Troubleshooting
If the service fails to start:

Check logs: journalctl -u asx-trader -n 100
Verify paths in service file
Check permissions: Make sure your user can access all required files
Check for Python errors: python run_curl.py --run-once --force-run
EOF

Copy
## Step 4: Update the Main README with Service Information

Let's update the main README file to include information about the service:

```bash
# Create a backup of the current README
cp README.md README.md.bak

# Add service information to the README
cat > README.md << 'EOF'
# ASX Trader

A GPT-enhanced trading system that monitors ASX stocks, analyzes news, and generates trading signals.

## Features

- **Real-time Market Data**: Fetches real ASX stock data from Yahoo Finance and other sources
- **News Analysis**: Collects financial news and company announcements
- **GPT-Enhanced Analysis**: Uses OpenAI's GPT models to analyze news and generate trading signals  
- **ASX Market Hours**: Operates on Australian market hours (10 AM - 4 PM AEST/AEDT)
- **Live Symbol Detection**: Identifies ASX stock symbols mentioned in news
- **System Service**: Can run as a background service with auto-restart capability

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Git

### Basic Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ASX-Auto-Trader.git
cd ASX-Auto-Trader

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env to add your OpenAI API key
Running as a System Service
ASX Trader can be installed as a system service that starts automatically at boot:
bashCopy# Install as a service
./service-config/install-service.sh

# Enable and start the service
sudo systemctl enable asx-trader
sudo systemctl start asx-trader
For more details on service installation and management, see service-config/README.md.
Usage
Running Manually
bashCopy# Run with default settings
python run_curl.py

# Run once with specific parameters
python run_curl.py --max-symbols 10 --news-limit 20 --run-once

# Force run (even outside market hours)
python run_curl.py --force-run
Managing as a Service
If running as a service, use the management script:
bashCopy# Check status
~/manage-asx-trader.sh status

# View logs
~/manage-asx-trader.sh logs

# Restart service
~/manage-asx-trader.sh restart
Configuration
Edit your .env file to customize behavior:
Copy# API Key (required)
OPENAI_API_KEY=your-key-here

# Market Configuration
MARKET_SCAN_MODE=full
MAX_STOCKS_TO_ANALYZE=20
CYCLE_INTERVAL_MINUTES=90

# Database
DB_PATH=data/asx_trader.db
Architecture
The system consists of several components:

Market Scanner: Fetches stock data from Yahoo Finance
News Collector: Gathers news from multiple sources
Prediction Engine: Analyzes news with GPT-o4
Database: Stores signals and analysis history

License
This project is licensed under the MIT License - see the LICENSE file for details.
