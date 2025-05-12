"""
Utility functions including rate limiting for API calls.
"""
import time
import logging
import functools

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