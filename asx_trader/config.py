"""
Configuration module for the trading system.
"""
import os
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

class Config:
    """Configuration container for trading system settings."""
    
    # API Keys
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    ASX_API_KEY = os.environ.get("ASX_API_KEY")
    BROKER_API_KEY = os.environ.get("BROKER_API_KEY")
    
    # AWS Configuration
    AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
    
    # Market Scanning Configuration
    MARKET_SCAN_MODE = os.environ.get("MARKET_SCAN_MODE", "full")
    MARKET_SECTOR_FOCUS = os.environ.get("MARKET_SECTOR_FOCUS", "")
    MAX_STOCKS_TO_ANALYZE = int(os.environ.get("MAX_STOCKS_TO_ANALYZE", "100"))
    MIN_MARKET_CAP = float(os.environ.get("MIN_MARKET_CAP", "1000000"))
    
    # Trading Configuration
    MAX_POSITION_SIZE = float(os.environ.get("MAX_POSITION_SIZE", "10000"))
    TRADING_ENABLED = os.environ.get("TRADING_ENABLED", "false").lower() == "true"
    CYCLE_INTERVAL_SECONDS = int(os.environ.get("CYCLE_INTERVAL_SECONDS", "3600"))
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        missing = []
        
        # Critical settings that must be present
        critical = [
            "OPENAI_API_KEY",
            "AWS_ACCESS_KEY",
            "AWS_SECRET_KEY",
            "S3_BUCKET_NAME",
        ]
        
        # Add trading-specific critical settings if trading is enabled
        if cls.TRADING_ENABLED:
            critical.extend([
                "BROKER_API_KEY",
                "ASX_API_KEY",
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
        
        return True