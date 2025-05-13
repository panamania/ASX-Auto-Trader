#!/usr/bin/env python3
"""
Simple test script for OpenAI API
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    logger.info("OpenAI Simple Test")
    
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check OpenAI module
    try:
        import openai
        logger.info(f"OpenAI module version: {openai.__version__}")
    except ImportError:
        logger.error("OpenAI module not found. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai==1.3.7"])
        import openai
        logger.info(f"OpenAI module installed. Version: {openai.__version__}")
    
    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OPENAI_API_KEY found in environment!")
        return
    
    # Import OpenAI client class
    logger.info("Testing OpenAI initialization...")
    try:
        from openai import OpenAI
        
        # Try basic initialization
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully!")
        
        # Try a simple API call
        logger.info("Making a test API call...")
        response = client.chat.completions.create(
            model="o4-mini",
            messages=[{"role": "user", "content": "Say hi"}],
            max_tokens=10
        )
        
        logger.info(f"API Response: {response.choices[0].message.content}")
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
