"""
Enhanced database module with position and alert tracking.
"""
import os
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class EnhancedDatabase:
    """Enhanced SQLite database for the trading system with position and alert tracking"""
    
    def __init__(self, db_path=None):
        """Initialize the database connection"""
        self.db_path = db_path or Config.DB_PATH
        self.conn = None
        self.initialize()
        
    def initialize(self):
        """Initialize the database tables if they don't exist"""
        try:
            # Create the database directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect to the database
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Create tables
            with self.conn:
                # API Usage tracking
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    endpoint TEXT,
                    tokens_used INTEGER,
                    success BOOLEAN
                )
                ''')
                
                # Trading signals
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    news_id TEXT,
                    symbol TEXT,
                    signal TEXT,
                    confidence TEXT,
                    reasoning TEXT
                )
                ''')
                
                # Trading orders
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS trading_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    action TEXT,
                    quantity INTEGER,
                    estimated_price REAL,
                    status TEXT
                )
                ''')
                
                # Run history
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS run_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT,
                    end_time TEXT,
                    status TEXT,
                    symbols_analyzed INTEGER,
                    signals_generated INTEGER,
                    orders_created INTEGER,
                    next_scheduled_run TEXT
                )
                ''')
                
                # Positions tracking
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    quantity INTEGER,
                    entry_price REAL,
                    entry_date TEXT,
                    position_type TEXT,
                    stop_loss REAL,
                    take_profit REAL,
                    current_price REAL,
                    unrealized_pnl REAL,
                    realized_pnl REAL,
                    status TEXT,
                    deal_reference TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(symbol, position_type, deal_reference)
                )
                ''')
                
                # Market alerts
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS market_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    alert_type TEXT,
                    message TEXT,
                    severity TEXT,
                    timestamp TEXT,
                    current_price REAL,
                    trigger_value REAL,
                    acknowledged BOOLEAN DEFAULT 0
                )
                ''')
                
                # Portfolio performance tracking
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    total_value REAL,
                    total_exposure REAL,
                    unrealized_pnl REAL,
                    realized_pnl REAL,
                    cash_balance REAL,
                    position_count INTEGER
                )
                ''')
                
                # Market data history
                self.conn.execute('''
                CREATE TABLE IF NOT EXISTS market_data_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    timestamp TEXT,
                    current_price REAL,
                    volume INTEGER,
                    price_change_pct REAL,
                    market_cap REAL,
                    high_52w REAL,
                    low_52w REAL
                )
                ''')
                
            logger.info("Enhanced database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            
    def record_api_usage(self, endpoint, tokens_used, success=True):
        """Record API usage for tracking and monitoring"""
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO api_usage (timestamp, endpoint, tokens_used, success) VALUES (?, ?, ?, ?)",
                    (datetime.now().isoformat(), endpoint, tokens_used, success)
                )
        except Exception as e:
            logger.error(f"Error recording API usage: {e}")
            
    def save_trading_signals(self, signals):
        """Save trading signals to the database"""
        try:
            with self.conn:
                for signal in signals:
                    for symbol in signal.get("symbols", []):
                        self.conn.execute(
                            '''INSERT INTO trading_signals 
                               (timestamp, news_id, symbol, signal, confidence, reasoning) 
                               VALUES (?, ?, ?, ?, ?, ?)''',
                            (
                                datetime.now().isoformat(),
                                signal.get("news_id", ""),
                                symbol,
                                signal.get("signal", ""),
                                signal.get("confidence", ""),
                                signal.get("reasoning", "")
                            )
                        )
            logger.info(f"Saved {len(signals)} trading signals to database")
        except Exception as e:
            logger.error(f"Error saving trading signals: {e}")
            
    def save_trading_orders(self, orders):
        """Save trading orders to the database"""
        try:
            with self.conn:
                for order in orders:
                    self.conn.execute(
                        '''INSERT INTO trading_orders 
                           (timestamp, symbol, action, quantity, estimated_price, status) 
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        (
                            datetime.now().isoformat(),
                            order.get("symbol", ""),
                            order.get("action", ""),
                            order.get("quantity", 0),
                            order.get("estimated_cost", 0) / order.get("quantity", 1),
                            "simulated" if not order.get("execution_result", {}).get("order_id", "").startswith("sim-") else "executed"
                        )
                    )
            logger.info(f"Saved {len(orders)} trading orders to database")
        except Exception as e:
            logger.error(f"Error saving trading orders: {e}")
    
    def record_run(self, start_time, end_time, status, symbols_analyzed, signals_generated, orders_created, next_run):
        """Record details about a trading system run"""
        try:
            with self.conn:
                self.conn.execute(
                    '''INSERT INTO run_history 
                       (start_time, end_time, status, symbols_analyzed, signals_generated, 
                        orders_created, next_scheduled_run) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        start_time.isoformat(),
                        end_time.isoformat(),
                        status,
                        symbols_analyzed,
                        signals_generated,
                        orders_created,
                        next_run.isoformat()
                    )
                )
            logger.info(f"Recorded run history. Next run scheduled at {next_run}")
        except Exception as e:
            logger.error(f"Error recording run history: {e}")
    
    def save_position(self, position_data: Dict):
        """Save a new position to the database"""
        try:
            with self.conn:
                self.conn.execute(
                    '''INSERT OR REPLACE INTO positions 
                       (symbol, quantity, entry_price, entry_date, position_type, 
                        stop_loss, take_profit, current_price, unrealized_pnl, 
                        realized_pnl, status, deal_reference, created_at, updated_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        position_data.get('symbol'),
                        position_data.get('quantity'),
                        position_data.get('entry_price'),
                        position_data.get('entry_date'),
                        position_data.get('position_type'),
                        position_data.get('stop_loss'),
                        position_data.get('take_profit'),
                        position_data.get('current_price'),
                        position_data.get('unrealized_pnl'),
                        position_data.get('realized_pnl'),
                        position_data.get('status'),
                        position_data.get('deal_reference'),
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
            logger.debug(f"Saved position for {position_data.get('symbol')}")
        except Exception as e:
            logger.error(f"Error saving position: {e}")
    
    def update_position(self, position_data: Dict):
        """Update an existing position in the database"""
        try:
            with self.conn:
                self.conn.execute(
                    '''UPDATE positions SET 
                       quantity=?, current_price=?, unrealized_pnl=?, realized_pnl=?, 
                       status=?, updated_at=?
                       WHERE symbol=? AND position_type=? AND deal_reference=?''',
                    (
                        position_data.get('quantity'),
                        position_data.get('current_price'),
                        position_data.get('unrealized_pnl'),
                        position_data.get('realized_pnl'),
                        position_data.get('status'),
                        datetime.now().isoformat(),
                        position_data.get('symbol'),
                        position_data.get('position_type'),
                        position_data.get('deal_reference')
                    )
                )
            logger.debug(f"Updated position for {position_data.get('symbol')}")
        except Exception as e:
            logger.error(f"Error updating position: {e}")
    
    def get_positions(self, status: str = 'OPEN') -> List[Dict]:
        """Get positions from database"""
        try:
            cursor = self.conn.execute(
                "SELECT * FROM positions WHERE status = ? ORDER BY created_at DESC",
                (status,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def save_alert(self, alert_data: Dict):
        """Save a market alert to the database"""
        try:
            with self.conn:
                self.conn.execute(
                    '''INSERT INTO market_alerts 
                       (symbol, alert_type, message, severity, timestamp, 
                        current_price, trigger_value, acknowledged) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        alert_data.get('symbol'),
                        alert_data.get('alert_type'),
                        alert_data.get('message'),
                        alert_data.get('severity'),
                        alert_data.get('timestamp'),
                        alert_data.get('current_price'),
                        alert_data.get('trigger_value'),
                        False
                    )
                )
            logger.debug(f"Saved alert for {alert_data.get('symbol')}")
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
    
    def get_alerts(self, hours: int = 24, acknowledged: bool = False) -> List[Dict]:
        """Get recent alerts from database"""
        try:
            cutoff_time = datetime.now() - datetime.timedelta(hours=hours)
            cursor = self.conn.execute(
                '''SELECT * FROM market_alerts 
                   WHERE timestamp >= ? AND acknowledged = ? 
                   ORDER BY timestamp DESC''',
                (cutoff_time.isoformat(), acknowledged)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: int):
        """Mark an alert as acknowledged"""
        try:
            with self.conn:
                self.conn.execute(
                    "UPDATE market_alerts SET acknowledged = 1 WHERE id = ?",
                    (alert_id,)
                )
            logger.debug(f"Acknowledged alert {alert_id}")
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
    
    def save_portfolio_snapshot(self, snapshot_data: Dict):
        """Save a portfolio performance snapshot"""
        try:
            with self.conn:
                self.conn.execute(
                    '''INSERT INTO portfolio_snapshots 
                       (timestamp, total_value, total_exposure, unrealized_pnl, 
                        realized_pnl, cash_balance, position_count) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        datetime.now().isoformat(),
                        snapshot_data.get('total_value'),
                        snapshot_data.get('total_exposure'),
                        snapshot_data.get('unrealized_pnl'),
                        snapshot_data.get('realized_pnl'),
                        snapshot_data.get('cash_balance'),
                        snapshot_data.get('position_count')
                    )
                )
            logger.debug("Saved portfolio snapshot")
        except Exception as e:
            logger.error(f"Error saving portfolio snapshot: {e}")
    
    def get_portfolio_history(self, days: int = 30) -> List[Dict]:
        """Get portfolio performance history"""
        try:
            cutoff_time = datetime.now() - datetime.timedelta(days=days)
            cursor = self.conn.execute(
                '''SELECT * FROM portfolio_snapshots 
                   WHERE timestamp >= ? 
                   ORDER BY timestamp ASC''',
                (cutoff_time.isoformat(),)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting portfolio history: {e}")
            return []
    
    def save_market_data(self, symbol: str, market_data: Dict):
        """Save market data for historical analysis"""
        try:
            with self.conn:
                self.conn.execute(
                    '''INSERT INTO market_data_history 
                       (symbol, timestamp, current_price, volume, price_change_pct, 
                        market_cap, high_52w, low_52w) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        symbol,
                        datetime.now().isoformat(),
                        market_data.get('current_price'),
                        market_data.get('volume'),
                        market_data.get('price_change_pct'),
                        market_data.get('market_cap'),
                        market_data.get('52w_high'),
                        market_data.get('52w_low')
                    )
                )
        except Exception as e:
            logger.error(f"Error saving market data for {symbol}: {e}")
    
    def get_market_data_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get historical market data for a symbol"""
        try:
            cutoff_time = datetime.now() - datetime.timedelta(days=days)
            cursor = self.conn.execute(
                '''SELECT * FROM market_data_history 
                   WHERE symbol = ? AND timestamp >= ? 
                   ORDER BY timestamp ASC''',
                (symbol, cutoff_time.isoformat())
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting market data history for {symbol}: {e}")
            return []
    
    def get_trading_performance(self, days: int = 30) -> Dict:
        """Get trading performance statistics"""
        try:
            cutoff_time = datetime.now() - datetime.timedelta(days=days)
            
            # Get closed positions
            cursor = self.conn.execute(
                '''SELECT * FROM positions 
                   WHERE status = 'CLOSED' AND updated_at >= ?''',
                (cutoff_time.isoformat(),)
            )
            closed_positions = [dict(row) for row in cursor.fetchall()]
            
            # Calculate statistics
            total_trades = len(closed_positions)
            winning_trades = len([p for p in closed_positions if p['realized_pnl'] > 0])
            losing_trades = len([p for p in closed_positions if p['realized_pnl'] < 0])
            total_pnl = sum(p['realized_pnl'] for p in closed_positions)
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'average_pnl_per_trade': total_pnl / total_trades if total_trades > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting trading performance: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old data to keep database size manageable"""
        try:
            cutoff_time = datetime.now() - datetime.timedelta(days=days)
            
            with self.conn:
                # Clean up old market data
                self.conn.execute(
                    "DELETE FROM market_data_history WHERE timestamp < ?",
                    (cutoff_time.isoformat(),)
                )
                
                # Clean up old acknowledged alerts
                self.conn.execute(
                    "DELETE FROM market_alerts WHERE timestamp < ? AND acknowledged = 1",
                    (cutoff_time.isoformat(),)
                )
                
                # Clean up old API usage records
                self.conn.execute(
                    "DELETE FROM api_usage WHERE timestamp < ?",
                    (cutoff_time.isoformat(),)
                )
                
            logger.info(f"Cleaned up data older than {days} days")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
