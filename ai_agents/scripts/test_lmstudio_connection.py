#!/usr/bin/env python3
"""
LM Studio Connection Test for Sanskriti AI Studio AI Agents

This script tests the LM Studio connection by:
1. Connecting to LM Studio
2. Sending a simple text request
3. Printing the response
4. Clearly reporting connection failure if it occurs

IMPORTANT: This test sends TEXT-ONLY requests only.
Never send images to Qwen 3.5 (the coding model).
"""

import sys
import requests


def main():
    """Main entry point for LM Studio connection test."""
    
    print("=" * 70)
    print("LM STUDIO CONNECTION TEST")
    print("=" * 70)
    print()
    
    # Import and validate configuration
    try:
        from config import (
            get_base_url,
            get_coding_model,
            get_vision_model,
            validate_config,
        )
        
        print("[1] Loading Configuration...")
        config = validate_config()
        
        # Check if validation failed
        if not config.get('valid', False):
            print("[ERROR] Configuration validation failed:")
            for issue in config.get('issues', []):
                print(f"         - {issue}")
            return 1
        
        base_url = config['base_url']
        coding_model = config['coding_model']
        vision_model = config['vision_model']
        
        print(f"      Base URL:     {base_url}")
        print(f"      Coding Model: {coding_model or '(using default)'}")
        print(f"      Vision Model: {vision_model or '(not set)'}")
        print()
        
    except ImportError as e:
        print(f"[ERROR] Failed to import config module:")
        print(f"         {e}")
        print()
        print("[TIP] Make sure config.py exists in the same directory.")
        return 1
    
    # Test connection without sending actual model request first
    print("[2] Testing HTTP Connection...")
    try:
        # Try to ping the health endpoint (if available) or chat endpoint
        health_url = f"{base_url}/health"
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            print(f"[OK] Health check passed at {base_url}")
        elif response.status_code == 404:
            print(f"[INFO] No health endpoint at {base_url}")
            print("[INFO] Trying direct chat/completions endpoint...")
            response = requests.get(f"{base_url}/chat/completions", timeout=5)
            if response.status_code in [200, 400]:  # 400 is OK - means model not loaded yet
                print(f"[OK] Chat endpoint accessible at {base_url}")
        else:
            print(f"[ERROR] Connection failed to {base_url}")
            print(f"         Status code: {response.status_code}")
            if response.text:
                print(f"         Response: {response.text[:200]}")
            return 1
        
    except requests.exceptions.ConnectionError as e:
        print("[FAIL] Cannot connect to LM Studio")
        print()
        print("=" * 70)
        print("CONNECTION FAILURE REPORT")
        print("=" * 70)
        print()
        print("PROBLEM:")
        print(f"  Cannot reach LM Studio at {base_url}")
        print()
        print("CAUSES:")
        print("  1. LM Studio is not running")
        print("     -> Start LM Studio and wait for model to load")
        print()
        print("  2. Wrong base URL")
        print("     -> Check that you're using correct port (default: 1234)")
        print()
        print("  3. Firewall blocking local connections")
        print()
        print("  4. Model not loaded yet")
        print("     -> Load a model in LM Studio first")
        print()
        print("SOLUTION:")
        print("  1. Start LM Studio (if not already running)")
        print("  2. Wait for initial setup to complete")
        print("  3. Load a model (e.g., Qwen, Llama, etc.)")
        print("  4. Run this test again")
        print()
        print("=" * 70)
        return 1
    
    except requests.exceptions.Timeout:
        print("[FAIL] Connection timeout to LM Studio")
        print(f"         URL: {base_url}")
        print()
        print("SOLUTION:")
        print("  1. Verify LM Studio is running on the specified port")
        print("  2. Check firewall settings allow localhost connections")
        print("  3. Adjust timeout in config if needed")
        return 1
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during connection test:")
        print(f"         {type(e).__name__}: {e}")
        return 1
    
    # If we get here, connection is working - test with actual chat
    print()
    print("[3] Testing Chat Completion...")
    print()
    
    from lmstudio_client import LMStudioClient
    
    client = LMStudioClient(base_url=base_url)
    
    messages = [
        {
            "role": "system", 
            "content": "You are the Coding Agent for Sanskriti AI Studio."
        },
        {
            "role": "user", 
            "content": "Hello! This is a test connection. Please confirm you received this message."
        }
    ]
    
    # Test text-only validation (should pass)
    try:
        client._validate_text_only(messages)
        print("[OK] Text-only validation passed")
    except ValueError as e:
        print(f"[ERROR] Text-only validation failed:")
        print(f"       {e}")
        return 1
    
    # Send chat request
    result = client.chat_complete(
        messages=messages,
        max_tokens=100,
        temperature=0.7,
    )
    
    if result is None:
        print("[FAIL] Chat completion returned no response")
        return 1
    
    # Extract and print the model's response
    try:
        content = result['choices'][0]['message']['content']
        
        print("=" * 70)
        print("CHAT RESPONSE")
        print("=" * 70)
        print()
        print(content)
        print()
        print("=" * 70)
        
    except (KeyError, IndexError) as e:
        print(f"[ERROR] Failed to extract response from LM Studio:")
        print(f"         {e}")
        if result:
            print(f"         Raw response keys: {list(result.keys())}")
        return 1
    
    # Success report
    print()
    print("=" * 70)
    print("CONNECTION TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - Connection to {base_url}: OK")
    print(f"  - Text-only validation: OK")
    print(f"  - Chat completion: OK")
    print()
    print("You can now use the LM Studio client in your AI agents.")
    print("=" * 70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
