#!/usr/bin/env python3
"""
Test script for curl-based OpenAI client
"""
import sys
import logging
from dotenv import load_dotenv
from asx_trader.curl_openai import CurlOpenAIClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    logger.info("Testing curl-based OpenAI client")
    
    try:
        # Create client
        client = CurlOpenAIClient()
        
        # Make a simple test request without temperature parameter
        response = client.chat_completion(
            model="o4-mini",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=20  # This should be converted to max_completion_tokens
            # No temperature parameter
        )
        
        # Log the response
        logger.info(f"Response: {response}")
        
        if "content" in response:
            logger.info(f"Content: {response['content']}")
            logger.info("Test successful!")
        else:
            logger.error("No content in response")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        logger.exception("Exception details:")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
