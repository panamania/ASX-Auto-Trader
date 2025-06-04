# Enhanced ASX Auto Trader - Market Monitoring & Position Management

This document describes the enhanced features added to the ASX Auto Trader system, including comprehensive position management and real-time market monitoring capabilities.

## 🚀 New Features Overview

### 1. Position Management System (`position_manager.py`)
- **Automated Position Tracking**: Tracks all open positions with real-time P&L calculations
- **Risk-Based Position Sizing**: Calculates optimal position sizes based on account balance and risk tolerance
- **Stop Loss & Take Profit**: Automatic execution of stop loss and take profit orders
- **Portfolio Exposure Management**: Prevents over-exposure with configurable limits
- **Position Lifecycle Management**: Complete tracking from entry to exit

### 2. Enhanced Market Monitoring (`enhanced_monitoring.py`)
- **Real-Time Alerts**: Price movements, volume spikes, technical levels
- **Position-Specific Alerts**: P&L thresholds, stop loss proximity, take profit alerts
- **Customizable Thresholds**: Configurable alert sensitivity
- **Alert History**: Complete audit trail of all market alerts
- **Watchlist Management**: Dynamic symbol monitoring

### 3. Enhanced Database (`enhanced_database.py`)
- **Position Tracking**: Complete position history and performance
- **Alert Storage**: Historical alert data with acknowledgment system
- **Portfolio Snapshots**: Regular portfolio performance captures
- **Market Data History**: Historical price and volume data
- **Performance Analytics**: Trading statistics and win/loss ratios

### 4. Integrated Trading System (`enhanced_run.py`)
- **Unified Operation**: All components working together seamlessly
- **Multiple Operation Modes**: Single run, continuous, monitoring-only
- **Comprehensive Reporting**: Detailed performance and status reports
- **Risk-Aware Trading**: Signals filtered by market risk assessment

## 📊 Key Improvements

### Market Monitoring Logic Enhancements

#### Before:
- Basic notification system via AWS SNS
- Limited to trade execution alerts
- No real-time monitoring
- Manual position tracking

#### After:
- **Real-time monitoring** with configurable intervals
- **Multi-level alert system** (LOW, MEDIUM, HIGH, CRITICAL)
- **Automated position updates** with current market prices
- **Technical analysis alerts** (52-week highs/lows, volume spikes)
- **Portfolio risk monitoring** with exposure limits

### Position Management Improvements

#### Before:
- No position tracking after execution
- Manual risk management
- No stop loss automation
- Limited portfolio oversight

#### After:
- **Complete position lifecycle tracking**
- **Automated risk management** with stop loss/take profit
- **Portfolio-level risk controls** (max exposure, position limits)
- **Real-time P&L calculations**
- **Position sizing based on risk tolerance**

## 🛠️ Usage Examples

### 1. Run Enhanced Trading Cycle
```bash
# Run once with enhanced features
python enhanced_run.py --run-once --symbols "BHP,CBA,CSL" --execute-trades

# Continuous operation with monitoring
python enhanced_run.py --symbols "BHP,CBA,CSL,NAB,WBC" --execute-trades
```

### 2. Start Real-Time Monitoring
```bash
# Monitor specific symbols
python enhanced_run.py --start-monitoring --symbols "BHP,CBA,CSL"

# Monitor all positions automatically
python enhanced_run.py --start-monitoring
```

### 3. Generate Comprehensive Reports
```bash
# Generate detailed performance report
python enhanced_run.py --generate-report
```

## 📈 Position Management Features

### Risk-Based Position Sizing
```python
# Automatic calculation based on:
# - Account balance
# - Risk tolerance (2% max risk per position)
# - Stop loss distance
# - Maximum position size limits

position_size = position_manager.calculate_position_size(
    symbol="BHP", 
    entry_price=45.50, 
    stop_loss=43.00, 
    account_balance=10000
)
```

### Automated Stop Loss & Take Profit
```python
# Positions automatically include risk management
position_manager.open_position(
    symbol="BHP",
    signal="BUY",
    quantity=100,
    entry_price=45.50,
    stop_loss=43.00,    # 5.5% stop loss
    take_profit=52.00   # 14.3% take profit
)
```

### Portfolio Exposure Controls
- **Maximum position size**: Configurable per-position limit
- **Total portfolio exposure**: Maximum 20% of account value
- **Risk per position**: Maximum 2% account risk per trade
- **Position limits**: Prevents duplicate positions

## 🔔 Alert System

### Alert Types
1. **PRICE_MOVE**: Significant price changes (>5% default)
2. **VOLUME_SPIKE**: Unusual volume activity (>2x average)
3. **TECHNICAL**: Near 52-week highs/lows
4. **POSITION_LOSS**: Position losses exceeding threshold
5. **POSITION_GAIN**: Significant position gains
6. **STOP_LOSS_NEAR**: Approaching stop loss levels
7. **TAKE_PROFIT_NEAR**: Approaching take profit targets

### Alert Severity Levels
- **LOW**: Minor price movements (5-7%)
- **MEDIUM**: Moderate movements (7-10%) or volume spikes
- **HIGH**: Significant movements (10-15%) or position alerts
- **CRITICAL**: Extreme movements (>15%)

### Customizable Thresholds
```python
# Adjust alert sensitivity
market_monitor.set_alert_thresholds(
    price_change=0.03,      # 3% price change threshold
    volume_spike=1.5,       # 1.5x volume spike threshold
    position_loss=-0.08     # 8% position loss threshold
)
```

## 📊 Database Schema Enhancements

### New Tables
1. **positions**: Complete position tracking
2. **market_alerts**: Alert history and management
3. **portfolio_snapshots**: Regular portfolio performance
4. **market_data_history**: Historical market data

### Performance Analytics
- Win/loss ratios
- Average P&L per trade
- Portfolio value tracking
- Risk-adjusted returns

## 🔧 Configuration

### Environment Variables
```bash
# Position Management
MAX_POSITION_SIZE=10000          # Maximum position value
TRADING_ENABLED=true             # Enable actual trading

# Monitoring
PRICE_CHANGE_THRESHOLD=0.05      # 5% price change alert
VOLUME_SPIKE_THRESHOLD=2.0       # 2x volume spike alert
POSITION_LOSS_THRESHOLD=-0.10    # 10% position loss alert

# Risk Management
MAX_PORTFOLIO_RISK=0.02          # 2% max risk per position
MAX_TOTAL_EXPOSURE=0.20          # 20% max portfolio exposure
```

## 📋 Monitoring Dashboard

### Real-Time Status
- Active positions with current P&L
- Recent alerts by severity
- Portfolio exposure and risk metrics
- Market monitoring status

### Performance Metrics
- Total portfolio value
- Unrealized/realized P&L
- Win rate and trade statistics
- Risk-adjusted performance

## 🚨 Risk Management

### Position-Level Controls
- **Stop Loss**: Automatic exit on adverse moves
- **Take Profit**: Automatic profit-taking
- **Position Sizing**: Risk-based quantity calculation
- **Exposure Limits**: Maximum position value controls

### Portfolio-Level Controls
- **Total Exposure**: Maximum percentage of account
- **Risk Budget**: Maximum risk per position
- **Correlation Limits**: Prevent over-concentration
- **Drawdown Protection**: Portfolio-level stop loss

## 🔄 Integration with Existing System

The enhanced features are designed to work seamlessly with the existing ASX Auto Trader:

1. **Backward Compatibility**: Original `run.py` continues to work
2. **Gradual Migration**: Can use enhanced features incrementally
3. **Configuration Driven**: Enable/disable features via environment variables
4. **Database Migration**: Enhanced database extends existing schema

## 📝 Logging and Monitoring

### Enhanced Logging
- Position lifecycle events
- Alert generation and processing
- Risk management decisions
- Portfolio performance snapshots

### Monitoring Integration
- AWS SNS notifications for critical alerts
- Database logging for audit trails
- Real-time status updates
- Performance tracking

## 🎯 Benefits

1. **Reduced Risk**: Automated stop losses and position sizing
2. **Better Oversight**: Real-time monitoring and alerts
3. **Improved Performance**: Risk-adjusted position sizing
4. **Complete Tracking**: Full audit trail of all activities
5. **Scalability**: Handle multiple positions efficiently
6. **Professional Features**: Institution-grade risk management

## 🔮 Future Enhancements

1. **Advanced Analytics**: Machine learning for position sizing
2. **Multi-Asset Support**: Extend beyond ASX stocks
3. **Options Trading**: Support for derivatives
4. **Backtesting**: Historical strategy validation
5. **Web Dashboard**: Real-time web interface
6. **Mobile Alerts**: Push notifications to mobile devices

---

This enhanced system transforms the ASX Auto Trader from a basic signal generator into a comprehensive trading platform with professional-grade risk management and monitoring capabilities.
