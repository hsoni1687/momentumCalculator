#!/usr/bin/env python3
"""
Debug environment detection
"""

import os
import sys

print("🔍 Environment Debug Information")
print("=" * 50)

# Check environment variables
print("Environment Variables:")
print(f"  STREAMLIT_SHARING_MODE: {os.getenv('STREAMLIT_SHARING_MODE', 'Not set')}")
print(f"  SUPABASE_URL: {os.getenv('SUPABASE_URL', 'Not set')}")
print(f"  SUPABASE_ANON_KEY: {'Set' if os.getenv('SUPABASE_ANON_KEY') else 'Not set'}")
print(f"  MOMENTUM_ENV: {os.getenv('MOMENTUM_ENV', 'Not set')}")

# Check Streamlit secrets
try:
    import streamlit as st
    print("\nStreamlit Secrets:")
    if hasattr(st, 'secrets'):
        print(f"  SUPABASE_URL: {st.secrets.get('SUPABASE_URL', 'Not set')}")
        print(f"  SUPABASE_ANON_KEY: {'Set' if st.secrets.get('SUPABASE_ANON_KEY') else 'Not set'}")
    else:
        print("  Streamlit secrets not available")
except Exception as e:
    print(f"  Streamlit secrets error: {e}")

# Test database adapter
print("\nDatabase Adapter Test:")
try:
    sys.path.append('src')
    from database_smart import SmartDatabase
    db = SmartDatabase()
    print(f"  Database type: {db.db_type}")
    print(f"  Database class: {type(db.db).__name__}")
except Exception as e:
    print(f"  Database adapter error: {e}")
    import traceback
    traceback.print_exc()
