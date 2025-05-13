
"""
Custom OpenAI client wrapper that handles compatibility issues.
"""
import logging
from openai import OpenAI
from asx_trader.config import Config

logger = logging.getLogger(__name__)

def create_openai_client(api_key, **kwargs):
    """
    Create an OpenAI client with compatibility handling.
    
    This function filters out unsupported parameters like 'proxies'
    to ensure compatibility with the latest OpenAI SDK.
    
    Args:
        api_key: OpenAI API key
        **kwargs: Additional arguments for the OpenAI client
        
    Returns:
        OpenAI: An initialized OpenAI client
    """
    # Remove unsupported parameters
    if 'proxies' in kwargs:
        logger.warning("Removing unsupported 'proxies' parameter from OpenAI client")
        kwargs.pop('proxies')
    
    # Initialize only with supported parameters
    try:
        supported_params = {'api_key', 'organization', 'base_url', 'timeout', 'max_retries', 'default_headers'}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params}
        return OpenAI(api_key=Config.OPENAI_API_KEY, **filtered_kwargs)
    except Exception as e:
        logger.error(f"Error creating OpenAI client: {e}")
        # Fallback to simplest initialization
        return OpenAI(api_key=Config.OPENAI_API_KEY)

