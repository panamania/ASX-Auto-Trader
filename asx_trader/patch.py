"""
Module to apply monkey patches to fix compatibility issues.
"""
import logging
import inspect
from functools import wraps

logger = logging.getLogger(__name__)

def patch_openai_client():
    """
    Apply monkey patch to OpenAI client to handle 'proxies' parameter.
    This should be called before any other imports.
    """
    try:
        # Import OpenAI
        from openai import OpenAI
        original_init = OpenAI.__init__
        
        @wraps(original_init)
        def patched_init(self, *args, **kwargs):
            # Remove proxies parameter if present
            if 'proxies' in kwargs:
                logger.warning("Removed 'proxies' parameter from OpenAI client initialization")
                kwargs.pop('proxies')
            
            # Call original init
            return original_init(self, *args, **kwargs)
        
        # Apply the patch
        OpenAI.__init__ = patched_init
        logger.info("Successfully patched OpenAI client")
        
    except ImportError:
        logger.warning("Could not patch OpenAI client: module not found")
    except Exception as e:
        logger.error(f"Error patching OpenAI client: {e}")

# Apply the patch immediately when this module is imported
patch_openai_client()
