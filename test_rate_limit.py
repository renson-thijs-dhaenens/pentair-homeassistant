#!/usr/bin/env python3
"""
Rate limit testing script for Erie Connect API.

This script tests how many requests per minute the API can handle.
Run with: python3 test_rate_limit.py
"""

import getpass
import sys
import time
from datetime import datetime

try:
    from erie_connect.client import ErieConnect
except ImportError:
    print("❌ erie-connect package not installed.")
    print("   Install it with: pip install erie-connect")
    sys.exit(1)


def test_rate_limit():
    """Test API rate limits."""
    print("=" * 70)
    print("Erie Connect API - Rate Limit Test")
    print("=" * 70)
    print()
    
    # Get credentials
    email = input("Enter your Erie Connect email: ").strip()
    password = getpass.getpass("Enter your Erie Connect password: ")
    
    print()
    print("🔄 Connecting to Erie Connect API...")
    
    try:
        # Create API client
        api = ErieConnect(email, password)
        
        # Login
        print("🔄 Logging in...")
        api.login()
        print("✅ Login successful!")
        
        # Select device
        print("🔄 Selecting first active device...")
        api.select_first_active_device()
        
        if api.device is None:
            print("❌ No device found!")
            return False
        
        print(f"✅ Device: {api.device.name} (ID: {api.device.id})")
        print()
        
        # Test different request rates
        test_intervals = [
            (1, "1 request/second (60/min)"),
            (0.5, "2 requests/second (120/min)"),
            (0.2, "5 requests/second (300/min)"),
            (0.1, "10 requests/second (600/min)"),
        ]
        
        for interval, description in test_intervals:
            print("=" * 70)
            print(f"Testing: {description}")
            print("=" * 70)
            
            success_count = 0
            error_count = 0
            total_time = 0
            num_requests = 30  # Test with 30 requests
            
            print(f"Sending {num_requests} requests...")
            
            for i in range(num_requests):
                start = time.time()
                try:
                    # Test the flow endpoint (fastest/simplest)
                    api.flow()
                    elapsed = time.time() - start
                    total_time += elapsed
                    success_count += 1
                    
                    # Show progress
                    if (i + 1) % 10 == 0:
                        print(f"  ✅ {i + 1}/{num_requests} requests completed")
                    
                    # Wait for the interval
                    if i < num_requests - 1:  # Don't wait after last request
                        time.sleep(max(0, interval - elapsed))
                        
                except Exception as e:
                    error_count += 1
                    print(f"  ❌ Request {i + 1} failed: {e}")
                    
                    # If we get errors, stop this test
                    if error_count >= 3:
                        print(f"  ⚠️  Too many errors, stopping this test")
                        break
            
            # Results
            print()
            if error_count > 0:
                print(f"❌ FAILED - {error_count} errors out of {success_count + error_count} requests")
                print(f"   This rate is TOO FAST for the API")
                print()
                print("=" * 70)
                print("🎯 RECOMMENDATION:")
                print(f"   Maximum safe rate appears to be less than {description}")
                if interval > 0.5:
                    print(f"   Suggest using 5-10 second intervals for production")
                print("=" * 70)
                return
            else:
                avg_response = total_time / success_count if success_count > 0 else 0
                print(f"✅ SUCCESS - All {success_count} requests completed")
                print(f"   Average response time: {avg_response:.3f}s")
                print()
        
        # If we got here, all tests passed
        print()
        print("=" * 70)
        print("🎯 RECOMMENDATION:")
        print("   API can handle very high request rates!")
        print("   Your 5-second polling for flow is MORE than safe.")
        print("   Even 1-second polling would work fine.")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rate_limit()
    sys.exit(0 if success else 1)
