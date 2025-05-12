"""
Simple database module for POC using SQLite.
"""
import os
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    """Simple SQLite database for the trading system POC"""
    
    def __init__(self, db_path="trading.db"):
        """Initialize the database connection"""
        self.db_path = db_path
        self.conn = None
        self.initialize()
        
    def initialize(self):
        """Initialize the database tables if they don't exist"""
        try:
            # Create the database directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect to the database
            self.conn = sqlite3.connect(self.db_path)
            
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
                
            logger.info("Database initialized successfully")
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
            
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()