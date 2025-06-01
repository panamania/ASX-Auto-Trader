
#!/usr/bin/env python3
"""
Script to check environment for proxy configurations
"""
import os
import sys
import json

def check_env_vars():
    print("Checking environment variables for proxies...")
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'no_proxy', 'NO_PROXY']
    found = False
    
    for var in proxy_vars:
        if var in os.environ:
            print(f"Found proxy environment variable: {var}={os.environ[var]}")
            found = True
    
    if not found:
        print("No proxy environment variables found.")
    
    # Check if OPENAI_API_KEY is set
    if 'OPENAI_API_KEY' in os.environ:
        print("OPENAI_API_KEY is set.")
    else:
        print("OPENAI_API_KEY is not set!")

def check_imported_modules():
    print("\nChecking imported modules related to OpenAI...")
    
    # Check if openai is imported
    try:
        import openai
        print(f"openai version: {openai.__version__}")
        print(f"openai package location: {openai.__file__}")
        
        # Check OpenAI client
        from openai import OpenAI
        print(f"OpenAI client is importable")
        
        # Inspect OpenAI.__init__ parameters
        import inspect
        try:
            sig = inspect.signature(OpenAI.__init__)
            print(f"OpenAI.__init__ parameters: {list(sig.parameters.keys())}")
        except Exception as e:
            print(f"Could not inspect OpenAI.__init__: {e}")
        
    except ImportError:
        print("openai module is not installed!")
    except Exception as e:
        print(f"Error importing openai: {e}")
    
    # Check for potential conflicting modules
    try:
        import requests
        print(f"requests version: {requests.__version__}")
        
        # Check if requests has a session configured with proxies
        session = requests.Session()
        if session.proxies:
            print(f"requests session has proxies: {session.proxies}")
        else:
            print("requests session has no proxies.")
    except ImportError:
        print("requests module is not installed!")
    except Exception as e:
        print(f"Error checking requests: {e}")

if __name__ == "__main__":
    check_env_vars()
    check_imported_modules()
    
    print("\nPython path:")
    for path in sys.path:
        print(f"  {path}")
