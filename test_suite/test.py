#try:
from openai import OpenAI
        
        # Try basic initialization
client = OpenAI(api_key="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")
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
        

