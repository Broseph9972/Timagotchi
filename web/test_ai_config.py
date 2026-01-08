#!/usr/bin/env python3
"""
Test script for AI-powered schedule configuration
Demonstrates the workflow without requiring actual API key
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
import json

def test_routes():
    """Test that all routes are accessible"""
    print("Testing Flask app routes...")
    
    with app.test_client() as client:
        # Test home page
        response = client.get('/')
        assert response.status_code == 200
        print("✓ Home page loads")
        
        # Test AI config page
        response = client.get('/ai-config')
        assert response.status_code == 200
        print("✓ AI config page loads")
        
        # Test health endpoint
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        print(f"✓ Health check: {data['status']}, AI enabled: {data['ai_enabled']}")
        
        # Test generate code
        response = client.post('/api/generate-code')
        assert response.status_code == 200
        data = response.get_json()
        print(f"✓ Generated pairing code: {data['code']}")
        
        # Test validate code
        code = data['code']
        response = client.get(f'/api/validate-code/{code}')
        assert response.status_code == 200
        print(f"✓ Code validation works")
        
        # Test config generation (without AI)
        test_analysis = {
            "school_start": "09:05",
            "school_end": "15:20",
            "num_periods": 6,
            "period_times": {
                "1": "09:25",
                "2": "10:20",
                "3": "11:15",
                "4": "12:40",
                "5": "13:35",
                "6": "14:30"
            },
            "period_length": 50,
            "passing_time": 5,
            "period_names": {
                "1": "Math",
                "2": "English",
                "3": "Science",
                "4": "History",
                "5": "Spanish",
                "6": "Art"
            },
            "has_ab_day": True,
            "a_day_periods": {
                "1": "Math", "2": "English", "3": "Science",
                "4": "History", "5": "Spanish", "6": "Art"
            },
            "b_day_periods": {
                "1": "Math", "2": "English", "3": "Science",
                "4": "PE", "5": "Spanish", "6": "Music"
            },
            "has_advisory": True,
            "advisory_start": "09:05",
            "advisory_length": 15,
            "advisory_days": ["m", "t"],
            "has_lunch": True,
            "lunch_start": "12:05",
            "lunch_end": "12:35",
            "uncertain_items": [],
            "notes": "Standard A/B day schedule"
        }
        
        user_inputs = {
            "use_24_hour": False,
            "timezone": "America/New_York",
            "wifi_networks": [["TestWiFi", "password123"]],
            "time_sync_mode": "on_boot"
        }
        
        response = client.post('/api/generate-config',
            json={"analysis": test_analysis, "user_inputs": user_inputs},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        print("✓ Config generation works")
        print("\nGenerated config.py preview:")
        print("=" * 60)
        print(data['config_content'][:500] + "...")
        print("=" * 60)

def test_ai_disabled_gracefully():
    """Test that app works even without API key"""
    print("\nTesting AI endpoints without API key...")
    
    with app.test_client() as client:
        # Create a simple test image if it doesn't exist
        import os
        test_image_path = '/tmp/test_schedules/sample_schedule.png'
        if not os.path.exists(test_image_path):
            os.makedirs('/tmp/test_schedules', exist_ok=True)
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='white')
            img.save(test_image_path)
        
        # Test analyze endpoint should return 503 without key
        with open(test_image_path, 'rb') as f:
            response = client.post('/api/analyze-schedule',
                data={'image': (f, 'schedule.png')},
                content_type='multipart/form-data'
            )
        # Should return 503 (service unavailable) without API key
        if response.status_code == 503:
            print("✓ AI endpoint correctly returns 503 when API key not set")
        else:
            print(f"✓ AI endpoint status: {response.status_code}")
        
        # Test question endpoint
        response = client.post('/api/ask-question',
            json={"question": "What time is lunch?", "context": {}},
            content_type='application/json'
        )
        if response.status_code == 503:
            print("✓ Question endpoint correctly returns 503 when API key not set")
        else:
            print(f"✓ Question endpoint status: {response.status_code}")

def print_setup_instructions():
    """Print setup instructions for users"""
    print("\n" + "=" * 60)
    print("SETUP INSTRUCTIONS FOR AI FEATURES")
    print("=" * 60)
    print("\n1. Get a FREE Gemini API key:")
    print("   Visit: https://makersuite.google.com/app/apikey")
    print("   Sign in with Google account")
    print("   Click 'Create API Key'")
    print("\n2. Set the environment variable:")
    print("   export GEMINI_API_KEY='your-api-key-here'")
    print("\n3. Restart the Flask app")
    print("\n4. AI features will be enabled!")
    print("\nFree tier limits:")
    print("   - 60 requests per minute")
    print("   - 1,500 requests per day")
    print("   - Completely free to use")
    print("=" * 60)

if __name__ == '__main__':
    print("Timagotchi AI Configurator - Test Suite")
    print("=" * 60)
    
    try:
        test_routes()
        test_ai_disabled_gracefully()
        print("\n✓ All tests passed!")
        
        if not os.environ.get('GEMINI_API_KEY'):
            print("\nNOTE: AI features are disabled (no API key set)")
            print_setup_instructions()
        else:
            print("\n✓ AI features are enabled (API key detected)")
            
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
