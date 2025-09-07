#!/usr/bin/env python3
"""
Database Test Script
Test the database preparation system
"""

import sys
import os
import sqlite3
import tempfile
import shutil

# Add paths
sys.path.append('src')
sys.path.append('config')

from database_preparation import DatabasePreparation

def test_database_preparation():
    """Test database preparation in a temporary directory"""
    print("🧪 Testing Database Preparation System")
    print("=" * 50)
    
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, 'test_stock_data.db')
    
    try:
        print(f"📁 Test directory: {temp_dir}")
        print(f"🗄️ Test database: {test_db_path}")
        
        # Create database preparation instance
        db_prep = DatabasePreparation(test_db_path)
        
        # Test database preparation
        print("\n🚀 Testing database preparation...")
        success = db_prep.prepare_database()
        
        if success:
            print("✅ Database preparation successful!")
            
            # Verify database
            print("\n🔍 Verifying database...")
            verification = db_prep.verify_database()
            
            if verification:
                print("✅ Database verification successful!")
                print(f"\n📊 Database Statistics:")
                print(f"   Tables: {verification['tables_created']}")
                print(f"   Record Counts: {verification['record_counts']}")
                print(f"   Unique Stocks with Price Data: {verification['unique_stocks_with_price']}")
                print(f"   Date Range: {verification['date_range']}")
                print(f"   Database Size: {verification['database_size_mb']:.2f} MB")
                
                # Test some queries
                print(f"\n🔍 Testing queries...")
                with sqlite3.connect(test_db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Test stock metadata query
                    cursor.execute("SELECT COUNT(*) FROM stockMetadata")
                    stock_count = cursor.fetchone()[0]
                    print(f"   Stock metadata records: {stock_count}")
                    
                    # Test price data query
                    cursor.execute("SELECT COUNT(*) FROM tickerPrice")
                    price_count = cursor.fetchone()[0]
                    print(f"   Price data records: {price_count}")
                    
                    # Test sample data
                    cursor.execute("SELECT stock, COUNT(*) FROM tickerPrice GROUP BY stock LIMIT 5")
                    sample_stocks = cursor.fetchall()
                    print(f"   Sample stocks with price data: {sample_stocks}")
                
                print(f"\n🎉 All tests passed!")
                return True
            else:
                print("❌ Database verification failed")
                return False
        else:
            print("❌ Database preparation failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up test directory: {temp_dir}")
        except:
            pass

def test_existing_database():
    """Test with existing database"""
    print("\n🧪 Testing with Existing Database")
    print("=" * 50)
    
    db_path = 'data/stock_data.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        db_prep = DatabasePreparation(db_path)
        verification = db_prep.verify_database()
        
        if verification:
            print("✅ Existing database verification successful!")
            print(f"📊 Current Statistics:")
            print(f"   Tables: {verification['tables_created']}")
            print(f"   Record Counts: {verification['record_counts']}")
            print(f"   Unique Stocks with Price Data: {verification['unique_stocks_with_price']}")
            print(f"   Date Range: {verification['date_range']}")
            print(f"   Database Size: {verification['database_size_mb']:.2f} MB")
            return True
        else:
            print("❌ Existing database verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing existing database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Preparation Test Suite")
    print("=" * 60)
    
    # Test 1: Fresh database preparation
    test1_success = test_database_preparation()
    
    # Test 2: Existing database verification
    test2_success = test_existing_database()
    
    print(f"\n📊 Test Results:")
    print(f"   Fresh Database Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"   Existing Database Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print(f"\n🎉 All tests passed! Database preparation system is working correctly.")
    else:
        print(f"\n⚠️ Some tests failed. Please check the logs for details.")
