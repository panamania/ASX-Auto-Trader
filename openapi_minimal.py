
#!/usr/bin/env python3
"""
Minimal script to test OpenAI API
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai():
    print("Testing OpenAI API with minimal configuration...")
    
    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("No OPENAI_API_KEY found in environment!")
        return
    
    try:
        # Initialize with just the API key
        client = OpenAI(api_key=api_key)
        
        # Make a simple test request
        response = client.chat.completions.create(
            model="o4-mini",
            messages=[{"role": "user", "content": "Say 'Hello ASX Trader'"}],
            max_tokens=20
        )
        
        print("OpenAI response:")
        print(response.choices[0].message.content)
        print("\nAPI call successful!")
        
    except Exception as e:
        print(f"Error with OpenAI API: {e}")

if __name__ == "__main__":
    test_openai()

