#!/usr/bin/env python3
"""
Test script to verify environment detection
"""

import os
import sys

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

def test_environment_detection():
    """Test environment detection logic"""
    print("🧪 Testing Environment Detection")
    print("=" * 40)
    
    # Test current environment variables
    print("Current Environment Variables:")
    print(f"  STREAMLIT_SHARING_MODE: {os.getenv('STREAMLIT_SHARING_MODE', 'Not set')}")
    print(f"  SUPABASE_URL: {os.getenv('SUPABASE_URL', 'Not set')}")
    print(f"  SUPABASE_ANON_KEY: {'Set' if os.getenv('SUPABASE_ANON_KEY') else 'Not set'}")
    print(f"  DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
    print(f"  POSTGRES_HOST: {os.getenv('POSTGRES_HOST', 'Not set')}")
    print(f"  MOMENTUM_ENV: {os.getenv('MOMENTUM_ENV', 'Not set')}")
    
    # Test Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            print(f"  Streamlit SUPABASE_URL: {'Set' if st.secrets.get('SUPABASE_URL') else 'Not set'}")
            print(f"  Streamlit SUPABASE_ANON_KEY: {'Set' if st.secrets.get('SUPABASE_ANON_KEY') else 'Not set'}")
        else:
            print("  Streamlit secrets: Not available")
    except Exception as e:
        print(f"  Streamlit secrets: Error - {e}")
    
    # Test configuration system
    try:
        from config.loader import get_config
        config_manager = get_config()
        
        print("\nConfiguration Results:")
        print(f"  Detected Environment: {config_manager.config.environment}")
        print(f"  Database Type: {config_manager.get_database_config().get('type', 'unknown')}")
        print(f"  Database Adapter: {config_manager.get_database_config().get('adapter', 'unknown')}")
        
        # Test database adapter
        from src.database_smart import SmartDatabase
        db = SmartDatabase()
        print(f"  Database Adapter Used: {db.db_type}")
        
    except Exception as e:
        print(f"  Configuration Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_environment_detection()
