
"""
Utility functions including rate limiting for API calls.
"""
import time
import logging
import functools
import datetime
import pytz

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls_per_minute=20):
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute
        self.last_call_time = 0
        self.call_count = 0
        
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Calculate time since last call
            current_time = time.time()
            time_since_last = current_time - self.last_call_time
            
            # If not enough time has passed, sleep
            if time_since_last < self.interval:
                sleep_time = self.interval - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            # Make the API call
            result = func(*args, **kwargs)
            
            # Update state
            self.last_call_time = time.time()
            self.call_count += 1
            
            return result
        return wrapper

# Create a global rate limiter for OpenAI API calls
# Set to 20 calls per minute as a conservative default
openai_rate_limiter = RateLimiter(calls_per_minute=20)

def get_sydney_time():
    """Get the current time in Sydney timezone"""
    sydney_tz = pytz.timezone('Australia/Sydney')
    return datetime.datetime.now(sydney_tz)

def is_market_open():
    """
    Determine if the Australian market is currently open.
    ASX trading hours are typically 10:00 AM to 4:00 PM AEST/AEDT Monday to Friday.
    
    Returns:
        bool: True if market is open, False otherwise
    """
    # Get current Sydney time
    now = get_sydney_time()
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    is_weekday = now.weekday() < 5
    
    # Check if it's a holiday (simplified, add actual ASX holidays)
    holidays = [
        # 2023-2024 ASX holidays
        datetime.date(2023, 12, 25),  # Christmas Day
        datetime.date(2023, 12, 26),  # Boxing Day
        datetime.date(2024, 1, 1),    # New Year's Day
        datetime.date(2024, 1, 26),   # Australia Day
        datetime.date(2024, 3, 29),   # Good Friday
        datetime.date(2024, 4, 1),    # Easter Monday
        datetime.date(2024, 4, 25),   # Anzac Day
        datetime.date(2024, 6, 10),   # King's Birthday
        datetime.date(2024, 12, 25),  # Christmas Day
        datetime.date(2024, 12, 26),  # Boxing Day
    ]
    is_holiday = now.date() in holidays
    
    # Australian market hours
    # ASX trading hours are 10:00 AM to 4:00 PM AEST/AEDT
    is_trading_hours = 10 <= now.hour < 16
    
    # Check if the market is open
    market_open = is_weekday and not is_holiday and is_trading_hours
    
    # Log the current Sydney time and market status
    status = "Open" if market_open else "Closed"
    reason = ""
    if not is_weekday:
        reason = " (Weekend)"
    elif is_holiday:
        reason = " (Holiday)"
    elif not is_trading_hours:
        reason = " (Outside trading hours)"
    
    logger.info(f"Current Sydney time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}. Market status: {status}{reason}")
    
    # DEBUG: For testing, let's always return True
    # In production, remove this line and let real logic work
    return True
    
    # Return True if the market is open
    #return market_open

def get_next_run_time(interval_minutes=90):
    """
    Calculate the next run time based on the specified interval.
    If the market will be closed at that time, adjust to the next market open time.
    
    Args:
        interval_minutes: Number of minutes between runs (default: 90)
        
    Returns:
        datetime: The next scheduled run time
    """
    # Get current time in Sydney timezone
    sydney_tz = pytz.timezone('Australia/Sydney')
    now = datetime.datetime.now(sydney_tz)
    
    # Calculate next run time based on interval
    next_run = now + datetime.timedelta(minutes=interval_minutes)
    
    # If next run is on a weekend, move to Monday
    if next_run.weekday() >= 5:  # Saturday or Sunday
        days_to_monday = 7 - next_run.weekday() + 0  # Days until Monday
        next_run = next_run.replace(hour=10, minute=0) + datetime.timedelta(days=days_to_monday)
    
    # If next run is outside trading hours on a weekday
    elif next_run.hour < 10 or next_run.hour >= 16:
        if next_run.hour < 10:
            # If before market opens, set to market open time
            next_run = next_run.replace(hour=10, minute=0)
        else:
            # If after market closes, set to next day's market open
            next_run = (next_run + datetime.timedelta(days=1)).replace(hour=10, minute=0)
            
            # If next day is weekend, move to Monday
            if next_run.weekday() >= 5:
                days_to_monday = 7 - next_run.weekday() + 0  # Days until Monday
                next_run = next_run + datetime.timedelta(days=days_to_monday)
    
    logger.info(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    return next_run

