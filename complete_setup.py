#!/usr/bin/env python3
"""
Complete Setup Script for Momentum Calculator
This script sets up everything: Supabase database, loads data, and prepares for deployment
"""

import os
import sys
import pandas as pd
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if environment variables are set"""
    print("🔍 Checking environment setup...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found!")
        print("\nPlease set up your Supabase credentials:")
        print("1. Go to https://supabase.com")
        print("2. Create a new project")
        print("3. Go to Settings → API")
        print("4. Copy your Project URL and anon key")
        print("5. Run: python setup_env.py")
        return False
    
    print(f"✅ SUPABASE_URL: {supabase_url}")
    print(f"✅ SUPABASE_ANON_KEY: {supabase_key[:20]}...")
    return True

def create_tables_simple():
    """Create tables using simple SQL execution"""
    try:
        from database_supabase import SupabaseDatabase
        db = SupabaseDatabase()
        
        print("🏗️ Creating database tables...")
        
        # Create stockmetadata table
        stock_metadata_sql = """
        CREATE TABLE IF NOT EXISTS stockmetadata (
            stock VARCHAR(20) PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            market_cap BIGINT,
            industry VARCHAR(100),
            sector VARCHAR(100),
            dividend_yield DECIMAL(5,2),
            roce DECIMAL(5,2),
            roe DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Create tickerprice table
        ticker_price_sql = """
        CREATE TABLE IF NOT EXISTS tickerprice (
            id SERIAL PRIMARY KEY,
            stock VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            open DECIMAL(10,2),
            high DECIMAL(10,2),
            low DECIMAL(10,2),
            close DECIMAL(10,2),
            volume BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock, date)
        );
        """
        
        # Create momentumscores table
        momentum_scores_sql = """
        CREATE TABLE IF NOT EXISTS momentumscores (
            id SERIAL PRIMARY KEY,
            stock VARCHAR(20) NOT NULL,
            total_score DECIMAL(8,4),
            raw_momentum_6m DECIMAL(8,4),
            raw_momentum_3m DECIMAL(8,4),
            raw_momentum_1m DECIMAL(8,4),
            volatility_adjusted_6m DECIMAL(8,4),
            volatility_adjusted_3m DECIMAL(8,4),
            volatility_adjusted_1m DECIMAL(8,4),
            relative_strength_6m DECIMAL(8,4),
            relative_strength_3m DECIMAL(8,4),
            relative_strength_1m DECIMAL(8,4),
            trend_score DECIMAL(8,4),
            volume_score DECIMAL(8,4),
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock, calculated_at)
        );
        """
        
        # Execute SQL statements
        try:
            db.client.rpc('exec_sql', {'sql': stock_metadata_sql}).execute()
            print("✅ Created stockmetadata table")
        except:
            print("⚠️ stockmetadata table might already exist")
        
        try:
            db.client.rpc('exec_sql', {'sql': ticker_price_sql}).execute()
            print("✅ Created tickerprice table")
        except:
            print("⚠️ tickerprice table might already exist")
        
        try:
            db.client.rpc('exec_sql', {'sql': momentum_scores_sql}).execute()
            print("✅ Created momentumscores table")
        except:
            print("⚠️ momentumscores table might already exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def load_data_simple():
    """Load data using simple insert operations"""
    try:
        from database_supabase import SupabaseDatabase
        db = SupabaseDatabase()
        
        print("📊 Loading data into Supabase...")
        
        # Load stock metadata
        print("Loading stock metadata...")
        df_metadata = pd.read_csv('data/stock_metadata.csv')
        records_metadata = df_metadata.to_dict('records')
        
        try:
            db.client.table('stockmetadata').upsert(records_metadata).execute()
            print(f"✅ Loaded {len(records_metadata)} stock metadata records")
        except Exception as e:
            print(f"⚠️ Error loading metadata: {e}")
        
        # Load momentum scores
        print("Loading momentum scores...")
        df_scores = pd.read_csv('data/momentum_scores.csv')
        records_scores = df_scores.to_dict('records')
        
        try:
            db.client.table('momentumscores').upsert(records_scores).execute()
            print(f"✅ Loaded {len(records_scores)} momentum score records")
        except Exception as e:
            print(f"⚠️ Error loading scores: {e}")
        
        # Load ticker price data in chunks
        print("Loading ticker price data (this may take a few minutes)...")
        chunk_size = 1000
        total_loaded = 0
        
        try:
            for chunk in pd.read_csv('data/ticker_price.csv', chunksize=chunk_size):
                records_price = chunk.to_dict('records')
                db.client.table('tickerprice').upsert(records_price).execute()
                total_loaded += len(records_price)
                
                if total_loaded % 10000 == 0:
                    print(f"Loaded {total_loaded} price records...")
            
            print(f"✅ Loaded {total_loaded} ticker price records")
        except Exception as e:
            print(f"⚠️ Error loading price data: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False

def test_database():
    """Test database connection and show stats"""
    try:
        from database_supabase import SupabaseDatabase
        db = SupabaseDatabase()
        
        print("🧪 Testing database connection...")
        stats = db.get_database_stats()
        
        if stats:
            print("\n📊 Database Summary:")
            print(f"Total Stocks: {stats.get('unique_stocks_with_price', 0)}")
            print(f"Price Records: {stats.get('record_counts', {}).get('tickerprice', 0)}")
            print(f"Momentum Scores: {stats.get('momentum_scores_count', 0)}")
            
            if stats.get('unique_stocks_with_price', 0) > 0:
                print("🎉 Database is ready with data!")
                return True
            else:
                print("⚠️ Database is empty")
                return False
        else:
            print("❌ Could not retrieve database stats")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Complete Momentum Calculator Setup")
    print("=" * 50)
    
    # Step 1: Check environment
    if not check_environment():
        return
    
    # Step 2: Create tables
    if not create_tables_simple():
        print("❌ Failed to create tables")
        return
    
    # Step 3: Load data
    if not load_data_simple():
        print("❌ Failed to load data")
        return
    
    # Step 4: Test database
    if not test_database():
        print("❌ Database test failed")
        return
    
    print("\n🎉 Setup Complete!")
    print("\nNext steps:")
    print("1. Test your app locally: streamlit run app_supabase.py")
    print("2. Deploy to Vercel: Follow DEPLOY_TO_VERCEL.md")
    print("3. Your app will be live and free!")

if __name__ == "__main__":
    main()
