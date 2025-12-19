#!/usr/bin/env python3
"""
Test script for Pentair Water Softener integration.

This script tests the Erie Connect API connection without needing Home Assistant.
Run with: python3 test_connection.py

You'll be prompted for your Erie Connect email and password.
"""

import getpass
import sys

try:
    from erie_connect.client import ErieConnect
except ImportError:
    print("❌ erie-connect package not installed.")
    print("   Install it with: pip install erie-connect")
    sys.exit(1)


def test_connection():
    """Test connection to Erie Connect API."""
    print("=" * 60)
    print("Pentair Water Softener - Connection Test")
    print("=" * 60)
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
        
        # Get auth info
        print()
        print("📋 Authentication Info:")
        print(f"   Access Token: {api.auth.access_token[:20]}...")
        print(f"   Client ID: {api.auth.client}")
        print(f"   UID: {api.auth.uid}")
        print(f"   Expiry: {api.auth.expiry}")
        
        # Select device
        print()
        print("🔄 Selecting first active device...")
        api.select_first_active_device()
        
        if api.device is None:
            print("❌ No device found!")
            return False
        
        print("✅ Device found!")
        print()
        print("📋 Device Info:")
        print(f"   Device ID: {api.device.id}")
        print(f"   Device Name: {api.device.name}")
        
        # Get device info
        print()
        print("🔄 Fetching device data...")
        info = api.info()
        
        print("✅ Device data retrieved!")
        print()
        print("📊 Device Statistics:")
        print(f"   Last Regeneration: {info.content.get('last_regeneration', 'N/A')}")
        print(f"   Number of Regenerations: {info.content.get('nr_regenerations', 'N/A')}")
        print(f"   Last Maintenance: {info.content.get('last_maintenance', 'N/A')}")
        print(f"   Total Volume: {info.content.get('total_volume', 'N/A')}")
        
        # Get dashboard
        print()
        print("🔄 Fetching dashboard data...")
        dashboard = api.dashboard()
        
        print("✅ Dashboard data retrieved!")
        warnings = dashboard.content.get('warnings', [])
        
        if warnings:
            print()
            print("⚠️  Warnings:")
            for warning in warnings:
                print(f"   - {warning.get('description', 'Unknown warning')}")
        else:
            print("   No warnings")
        
        print()
        print("=" * 60)
        print("✅ All tests passed! Your device is compatible.")
        print("=" * 60)
        print()
        print("You can now install the integration in Home Assistant.")
        print()
        
        return True
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        print()
        print("Possible causes:")
        print("  - Invalid email or password")
        print("  - No internet connection")
        print("  - Erie Connect API is down")
        print("  - No device linked to your account")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
