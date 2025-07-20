#!/usr/bin/env python3
"""
Simple Runway API test
"""

import requests
import json

# Import API configuration
try:
    from config import RUNWAY_API_KEY
except ImportError:
    RUNWAY_API_KEY = "key_536cfd03902f0448624e34cddf7be4cfaf04ca75f5920ac5098fef3fd158cb1deb1cf1e4fef7e73c6f18faf74b3c0c1b218af61a607c1b0813c3039dda886330"

def test_runway():
    """Test Runway API with a simple prompt"""
    
    print("🧪 Testing Runway API...")
    print(f"API Key: {RUNWAY_API_KEY[:20]}...")
    
    # Simple test prompt
    test_prompt = "Korean romance manga, soft anime style, young man cooking in kitchen"
    
    headers = {
        "Authorization": f"Bearer {RUNWAY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "promptText": test_prompt,
        "aspectRatio": "3:4",
        "motion": "none",
        "seed": 0,
        "negativePrompt": "low quality, blurry, distorted, ugly, bad anatomy"
    }
    
    try:
        print("📡 Sending request to Runway API...")
        print(f"URL: https://api.runwayml.com/v1/inference")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            "https://api.runwayml.com/v1/inference",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📝 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Runway API call successful!")
            print(f"📝 Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Runway API error: {response.status_code}")
            print(f"📝 Error response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Runway API Test")
    print("=" * 50)
    
    success = test_runway()
    
    if success:
        print("\n✅ Runway API is working!")
        print("You can now run manga_framer.py with Runway generation.")
    else:
        print("\n❌ Runway API test failed.")
        print("Please check your API key and try again.") 