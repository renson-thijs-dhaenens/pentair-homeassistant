#!/usr/bin/env python3
"""
Test script for Pentair Water Softener integration.

This script tests the Erie Connect API connection without needing Home Assistant.
Run with: python3 test_connection.py

You'll be prompted for your Erie Connect email and password.
"""

import getpass
import json
import sys

try:
    from erie_connect.client import ErieConnect
except ImportError:
    print("❌ erie-connect package not installed.")
    print("   Install it with: pip install erie-connect")
    sys.exit(1)


def pretty_print_dict(d, indent=3):
    """Pretty print a dictionary."""
    for key, value in d.items():
        if isinstance(value, dict):
            print(" " * indent + f"{key}:")
            pretty_print_dict(value, indent + 3)
        elif isinstance(value, list):
            print(" " * indent + f"{key}: [")
            for item in value:
                if isinstance(item, dict):
                    pretty_print_dict(item, indent + 6)
                else:
                    print(" " * (indent + 6) + str(item))
            print(" " * indent + "]")
        else:
            print(" " * indent + f"{key}: {value}")


def test_connection():
    """Test connection to Erie Connect API."""
    print("=" * 70)
    print("Pentair Water Softener - Full API Data Dump")
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
        
        # ===== INFO ENDPOINT =====
        print()
        print("=" * 70)
        print("📊 INFO ENDPOINT (api.info())")
        print("=" * 70)
        info = api.info()
        print("RAW DATA:")
        pretty_print_dict(info.content)
        
        # ===== DASHBOARD ENDPOINT =====
        print()
        print("=" * 70)
        print("📊 DASHBOARD ENDPOINT (api.dashboard())")
        print("=" * 70)
        dashboard = api.dashboard()
        print("RAW DATA:")
        pretty_print_dict(dashboard.content)
        
        # ===== SETTINGS ENDPOINT =====
        print()
        print("=" * 70)
        print("📊 SETTINGS ENDPOINT (api.settings())")
        print("=" * 70)
        settings = api.settings()
        print("RAW DATA:")
        pretty_print_dict(settings.content)
        
        # ===== FLOW ENDPOINT =====
        print()
        print("=" * 70)
        print("📊 FLOW ENDPOINT (api.flow())")
        print("=" * 70)
        flow = api.flow()
        print("RAW DATA:")
        pretty_print_dict(flow.content)
        
        # ===== FEATURES ENDPOINT =====
        print()
        print("=" * 70)
        print("📊 FEATURES ENDPOINT (api.features())")
        print("=" * 70)
        try:
            features = api.features()
            print("RAW DATA:")
            pretty_print_dict(features.content)
        except Exception as e:
            print(f"   Not available or error: {e}")
        
        # ===== STATISTICS ENDPOINT (if available) =====
        print()
        print("=" * 70)
        print("📊 STATISTICS ENDPOINT (api.statistics() - if available)")
        print("=" * 70)
        try:
            statistics = api.statistics()
            print("RAW DATA:")
            pretty_print_dict(statistics.content)
        except Exception as e:
            print(f"   Not available or error: {e}")
        
        # ===== STATUS ENDPOINT (if available) =====
        print()
        print("=" * 70)
        print("📊 STATUS ENDPOINT (api.status() - if available)")
        print("=" * 70)
        try:
            status = api.status()
            print("RAW DATA:")
            pretty_print_dict(status.content)
        except Exception as e:
            print(f"   Not available or error: {e}")
        
        print()
        print("=" * 70)
        print("✅ All API data retrieved successfully!")
        print("=" * 70)
        print()
        
        return True
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
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
