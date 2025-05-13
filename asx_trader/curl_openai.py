"""
Curl-based OpenAI API client.
This module uses the subprocess module to call curl directly instead of using the OpenAI Python SDK.
"""
import os
import json
import logging
import subprocess
import tempfile
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class CurlOpenAIClient:
    """
    A simple OpenAI client that uses curl instead of the Python SDK.
    This avoids any compatibility issues with the OpenAI Python package.
    """
    
    def __init__(self, api_key=None):
        """Initialize the client with API key"""
        self.api_key = api_key or Config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    def chat_completion(self, model, messages, max_tokens=None, temperature=None, response_format=None):
        """
        Create a chat completion using curl.
        
        Args:
            model: The model to use (e.g., "o4-mini")
            messages: List of message objects with role and content
            max_tokens: Maximum number of tokens to generate (renamed to max_completion_tokens for o4)
            temperature: Sampling temperature (omitted for o4 models)
            response_format: Optional format specification (e.g., {"type": "json_object"})
            
        Returns:
            dict: The parsed JSON response from OpenAI
        """
        # Check if using an o4 model
        is_o4_model = model and model.startswith("o4")
        
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": messages
        }
        
        # Only add temperature if not using o4 models
        if temperature is not None and not is_o4_model:
            payload["temperature"] = temperature
        
        # Use the correct parameter name for tokens
        if max_tokens is not None:
            # o4 models use max_completion_tokens instead of max_tokens
            if is_o4_model:
                payload["max_completion_tokens"] = max_tokens
            else:
                payload["max_tokens"] = max_tokens
            
        if response_format is not None:
            payload["response_format"] = response_format
        
        # Log the payload for debugging
        logger.debug(f"OpenAI API payload: {json.dumps(payload)}")
        
        # Convert payload to JSON and save to a temporary file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp:
            json.dump(payload, temp)
            temp_path = temp.name
        
        try:
            # Prepare curl command
            curl_cmd = [
                'curl',
                '-s',  # Silent mode
                'https://api.openai.com/v1/chat/completions',
                '-H', f'Authorization: Bearer {self.api_key}',
                '-H', 'Content-Type: application/json',
                '-d', f'@{temp_path}'
            ]
            
            # Execute curl command
            logger.debug(f"Executing curl command: {' '.join(curl_cmd)}")
            process = subprocess.run(
                curl_cmd,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )
            
            # Check for errors
            if process.returncode != 0:
                error_msg = process.stderr.strip()
                logger.error(f"Curl command failed with exit code {process.returncode}: {error_msg}")
                return {"error": {"message": error_msg}, "content": None}
            
            # Parse the response
            response_text = process.stdout.strip()
            
            # Try to parse JSON response
            try:
                response = json.loads(response_text)
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {e}"
                logger.error(error_msg)
                logger.error(f"Raw response: {response_text}")
                return {"error": {"message": error_msg}, "content": None}
            
            # Check for API errors
            if "error" in response:
                logger.error(f"API error: {response['error']}")
                return {"error": response["error"], "content": None}
            
            # Extract message content similar to the Python SDK format
            if "choices" in response and len(response["choices"]) > 0:
                if "message" in response["choices"][0] and "content" in response["choices"][0]["message"]:
                    content = response["choices"][0]["message"]["content"]
                else:
                    content = None
            else:
                content = None
            
            # Create a simplified result format
            result = {
                "id": response.get("id"),
                "model": response.get("model"),
                "usage": response.get("usage", {}),
                "content": content
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Error in chat completion: {e}"
            logger.error(error_msg)
            return {"error": {"message": error_msg}, "content": None}
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {e}")

# Create a singleton instance for easy importing
openai_client = CurlOpenAIClient()
