#!/usr/bin/env python3
"""
Script to find all OpenAI initializations with proxies parameter
"""
import os
import re

def scan_file(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Look for OpenAI initialization
        client_pattern = re.compile(r'(?:client|self\.client)\s*=\s*OpenAI\((.*?)\)', re.DOTALL)
        matches = client_pattern.findall(content)
        
        for match in matches:
            if 'proxies' in match:
                print(f"Found proxies in OpenAI initialization in {file_path}:")
                print(f"  OpenAI({match})")
                return True
        
        # Also check for other patterns of OpenAI initialization
        init_pattern = re.compile(r'OpenAI\((.*?)\)', re.DOTALL)
        matches = init_pattern.findall(content)
        
        for match in matches:
            if 'proxies' in match:
                print(f"Found proxies in OpenAI initialization in {file_path}:")
                print(f"  OpenAI({match})")
                return True
                
        return False
        
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
        return False

def main():
    root_dir = '.'
    found = False
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(dirpath, filename)
                if scan_file(file_path):
                    found = True
    
    if not found:
        print("No OpenAI initialization with proxies parameter found.")
        print("The issue might be in a third-party module or in a variable.")

if __name__ == "__main__":
    main()
