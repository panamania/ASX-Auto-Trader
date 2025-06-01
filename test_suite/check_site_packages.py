#!/usr/bin/env python3
"""
Script to check for potential conflicts in site-packages
"""
import os
import sys
import site
import importlib
import pkgutil

def check_openai_related_packages():
    print("Checking for OpenAI-related packages...")
    
    # Get the site-packages directory
    site_packages = site.getsitepackages()[0]
    print(f"Site-packages directory: {site_packages}")
    
    # List installed modules
    installed_modules = [name for _, name, ispkg in pkgutil.iter_modules() 
                        if 'openai' in name.lower() or 'gpt' in name.lower()]
    
    if installed_modules:
        print(f"Found potentially relevant modules: {', '.join(installed_modules)}")
    else:
        print("No OpenAI-related modules found.")
    
    # Check specifically for openai
    try:
        import openai
        print(f"OpenAI module location: {openai.__file__}")
        print(f"OpenAI module version: {openai.__version__}")
        
        # Check if OpenAI client is patched or monkey-patched
        from openai import OpenAI
        import inspect
        
        # Check the initialization signature
        sig = inspect.signature(OpenAI.__init__)
        print(f"OpenAI.__init__ parameters: {list(sig.parameters.keys())}")
        
        # Check the source file
        print(f"OpenAI class defined in: {inspect.getfile(OpenAI)}")
        
    except ImportError:
        print("OpenAI module is not installed!")
    except Exception as e:
        print(f"Error checking OpenAI module: {e}")

    # Check for packages that might patch or modify requests (which OpenAI uses)
    requests_related = ['requests', 'urllib3', 'aiohttp', 'httpx']
    for module_name in requests_related:
        try:
            module = importlib.import_module(module_name)
            print(f"{module_name} version: {getattr(module, '__version__', 'unknown')}")
        except ImportError:
            print(f"{module_name} is not installed.")
        except Exception as e:
            print(f"Error checking {module_name}: {e}")

if __name__ == "__main__":
    check_openai_related_packages()
    
    # Print the Python path
    print("\nPython path:")
    for path in sys.path:
        print(f"  {path}")
