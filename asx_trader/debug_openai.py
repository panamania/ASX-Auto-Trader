#!/usr/bin/env python3
"""
Debug script to find OpenAI initialization issues
"""
import sys
import traceback
from openai import OpenAI

def test_openai_init():
    print("Testing OpenAI client initialization...")
    try:
        # Basic initialization
        client = OpenAI(api_key="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")
        print("✓ Basic initialization works")
        
        # Check what parameters are accepted
        print("\nChecking accepted parameters:")
        import inspect
        sig = inspect.signature(OpenAI.__init__)
        print(f"OpenAI.__init__ accepts these parameters: {list(sig.parameters.keys())}")
        
        # Try to initialize with different parameters
        try:
            client = OpenAI(api_key="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", proxies={"http": "http://proxy"})
            print("✗ Initialization with 'proxies' parameter worked but should not")
        except TypeError as e:
            print(f"✓ Expected error when using 'proxies': {e}")
        
    except Exception as e:
        print(f"Error testing OpenAI: {e}")
        traceback.print_exc()

def check_all_modules():
    print("\nChecking all modules for OpenAI imports...")
    modules_to_check = [
        "asx_trader.prediction",
        "asx_trader.risk",
        "asx_trader.news",
        "asx_trader.system",
        "asx_trader.market",
    ]
    
    for module_name in modules_to_check:
        try:
            print(f"\nChecking {module_name}...")
            module = __import__(module_name, fromlist=["*"])
            
            # Look for classes that might use OpenAI
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if hasattr(attr, "__class__") and attr_name[0].isupper():
                    print(f"  Class: {attr_name}")
                    # Look for __init__ method
                    if hasattr(attr, "__init__"):
                        init_code = inspect.getsource(attr.__init__)
                        if "OpenAI(" in init_code:
                            print(f"    ⚠️ This class initializes OpenAI: {init_code}")
                            if "proxies" in init_code:
                                print(f"    ❌ FOUND PROXIES PARAMETER IN: {module_name}.{attr_name}.__init__")
                        
        except ImportError:
            print(f"  Module {module_name} not found")
        except Exception as e:
            print(f"  Error checking {module_name}: {e}")
    
    print("\nChecking complete!")

if __name__ == "__main__":
    test_openai_init()
    
    try:
        import inspect
        check_all_modules()
    except Exception as e:
        print(f"Error in module checking: {e}")
        traceback.print_exc()
