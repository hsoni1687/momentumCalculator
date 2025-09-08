#!/usr/bin/env python3
"""
Test Database Connection
Simple test to verify which database is being used
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_connection():
    """Test database connection"""
    print("🧪 Testing Database Connection...")
    print("=" * 50)
    
    # Test environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SUPABASE_ANON_KEY: {supabase_key[:20] if supabase_key else 'None'}...")
    
    # Test Supabase connection
    try:
        from database_supabase import SupabaseDatabase
        print("\n🔄 Testing SupabaseDatabase...")
        db = SupabaseDatabase()
        print("✅ SupabaseDatabase imported and initialized successfully")
        
        # Test database stats
        stats = db.get_database_stats()
        print(f"📊 Database stats: {stats}")
        
        if stats and stats.get('unique_stocks_with_price', 0) > 0:
            print("🎉 Supabase connection working with data!")
            return True
        else:
            print("⚠️ Supabase connected but no data found")
            return False
            
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
