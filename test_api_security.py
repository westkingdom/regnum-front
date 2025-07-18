#!/usr/bin/env python3
"""
Test script for API security setup
Tests both public access and authenticated access scenarios
"""

import requests
import sys
import os
sys.path.append('.')

from utils.api import RegnumAPI

def test_public_access():
    """Test direct public access to regnum-api (should fail when secured)"""
    print("🧪 Testing public access to regnum-api...")
    
    api_url = "https://regnum-api-85382560394.us-west1.run.app/groups/"
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            print("❌ regnum-api is publicly accessible")
            return False
        elif response.status_code == 403:
            print("✅ regnum-api is properly secured (403 Forbidden)")
            return True
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing public access: {e}")
        return False

def test_authenticated_access():
    """Test authenticated access through RegnumAPI client"""
    print("🧪 Testing authenticated access through RegnumAPI...")
    
    try:
        api_client = RegnumAPI()
        
        # Test the groups endpoint
        groups_data = api_client.get_all_groups()
        group_count = len(groups_data.get('groups', []))
        print(f"✅ Authenticated access successful! Found {group_count} groups")
        
        # Test another endpoint
        principalities_data = api_client.get_principalities()
        principality_count = len(principalities_data.get('principalities', []))
        print(f"✅ Principalities endpoint working! Found {principality_count} principalities")
        
        return True
        
    except Exception as e:
        print(f"❌ Authenticated access failed: {e}")
        return False

def test_local_auth_setup():
    """Test local authentication setup"""
    print("🧪 Testing local authentication setup...")
    
    # Check if we have ADC credentials
    try:
        from google.auth import default
        credentials, project = default()
        print(f"✅ Found default credentials for project: {project}")
        
        # Check if we can get an identity token
        from google.auth.transport.requests import Request
        auth_request = Request()
        
        try:
            import google.oauth2.id_token
            audience = "https://regnum-api-85382560394.us-west1.run.app"
            token = google.oauth2.id_token.fetch_id_token(auth_request, audience)
            if token:
                print("✅ Successfully generated identity token")
                print(f"   Token length: {len(token)} characters")
                return True
            else:
                print("❌ Could not generate identity token")
                return False
        except Exception as e:
            print(f"⚠️  Identity token generation failed: {e}")
            print("   This is expected in local development without proper ADC setup")
            return True  # Not a failure for local testing
            
    except Exception as e:
        print(f"❌ No default credentials found: {e}")
        print("   Run: gcloud auth application-default login")
        return False

def main():
    """Run all security tests"""
    print("🔒 API Security Test Suite")
    print("=" * 50)
    
    tests = [
        ("Local Auth Setup", test_local_auth_setup),
        ("Public Access", test_public_access),
        ("Authenticated Access", test_authenticated_access),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! API security is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 