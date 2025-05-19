"""
Configuration module for the trading system.
"""
import os
import logging
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

class Config:
    """Configuration container for trading system settings."""
    
    # API Keys
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    FINANCE_API_KEY = os.environ.get("FINANCE_API_KEY")
    NEWSDATA_API_KEY = os.environ.get("NEWSDATA_API_KEY")
    ASX_API_KEY = os.environ.get("ASX_API_KEY")
    BROKER_API_KEY = os.environ.get("BROKER_API_KEY")
    
    # API URLs
    ASX_API_URL = os.environ.get("ASX_API_URL")
    BROKER_API_URL = os.environ.get("BROKER_API_URL")
    
    # AWS Configuration
    AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
    
    # Market Scanning Configuration
    MARKET_SCAN_MODE = os.environ.get("MARKET_SCAN_MODE", "full")
    MARKET_SECTOR_FOCUS = os.environ.get("MARKET_SECTOR_FOCUS", "")
    MAX_STOCKS_TO_ANALYZE = int(os.environ.get("MAX_STOCKS_TO_ANALYZE", "30"))
    MIN_MARKET_CAP = float(os.environ.get("MIN_MARKET_CAP", "1000000"))
    
    # Trading Configuration
    MAX_POSITION_SIZE = float(os.environ.get("MAX_POSITION_SIZE", "10000"))
    TRADING_ENABLED = os.environ.get("TRADING_ENABLED", "false").lower() == "true"
    CYCLE_INTERVAL_MINUTES = int(os.environ.get("CYCLE_INTERVAL_MINUTES", "90"))
    
    # Database Configuration
    DB_PATH = os.environ.get("DB_PATH", "data/asx_trader.db")
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        missing = []
        
        # Critical settings that must be present
        critical = [
            "OPENAI_API_KEY",
        ]
        
        # Add AWS settings if configured
        if cls.AWS_ACCESS_KEY or cls.AWS_SECRET_KEY or cls.S3_BUCKET_NAME:
            critical.extend([
                "AWS_ACCESS_KEY",
                "AWS_SECRET_KEY",
                "AWS_REGION",
                "S3_BUCKET_NAME",
            ])
        
        # Add trading-specific critical settings if trading is enabled
        if cls.TRADING_ENABLED:
            critical.extend([
                "BROKER_API_KEY",
                "SNS_TOPIC_ARN"
            ])
        
        # Check for missing critical settings
        for setting in critical:
            if not getattr(cls, setting):
                missing.append(setting)
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        # Validate scan mode
        if cls.MARKET_SCAN_MODE not in ["full", "sector", "filtered"]:
            raise ValueError(f"Invalid MARKET_SCAN_MODE: {cls.MARKET_SCAN_MODE}. " 
                            "Must be 'full', 'sector', or 'filtered'")
            
        # If sector mode, validate sector
        if cls.MARKET_SCAN_MODE == "sector" and not cls.MARKET_SECTOR_FOCUS:
            raise ValueError("MARKET_SECTOR_FOCUS must be specified when using sector scan mode")
        
        # Log warnings for optional API keys
        if not cls.FINANCE_API_KEY:
            logger.warning("FINANCE_API_KEY not set. Will use mock market data.")
        if not cls.NEWSDATA_API_KEY:
            logger.warning("NEWSDATA_API_KEY not set. Will use mock news data.")
        
        return True

