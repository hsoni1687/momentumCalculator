#!/usr/bin/env python3
"""
Load CSV data into Supabase database
This script loads the generated CSV data into your Supabase database
"""

import os
import sys
import pandas as pd
import logging
from datetime import datetime

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database_supabase import SupabaseDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_stock_metadata(db, csv_file):
    """Load stock metadata from CSV"""
    try:
        logger.info(f"Loading stock metadata from {csv_file}")
        
        # Read CSV
        df = pd.read_csv(csv_file)
        logger.info(f"Read {len(df)} records from {csv_file}")
        
        # Convert to list of dictionaries for Supabase
        records = df.to_dict('records')
        
        # Insert into database
        result = db.supabase.table('stockMetadata').upsert(records).execute()
        
        logger.info(f"Successfully loaded {len(records)} stock metadata records")
        return True
        
    except Exception as e:
        logger.error(f"Error loading stock metadata: {e}")
        return False

def load_ticker_price(db, csv_file):
    """Load ticker price data from CSV"""
    try:
        logger.info(f"Loading ticker price data from {csv_file}")
        
        # Read CSV in chunks to handle large files
        chunk_size = 1000
        total_loaded = 0
        
        for chunk in pd.read_csv(csv_file, chunksize=chunk_size):
            # Convert to list of dictionaries
            records = chunk.to_dict('records')
            
            # Insert into database
            result = db.supabase.table('tickerPrice').upsert(records).execute()
            total_loaded += len(records)
            
            if total_loaded % 10000 == 0:
                logger.info(f"Loaded {total_loaded} price records...")
        
        logger.info(f"Successfully loaded {total_loaded} ticker price records")
        return True
        
    except Exception as e:
        logger.error(f"Error loading ticker price data: {e}")
        return False

def load_momentum_scores(db, csv_file):
    """Load momentum scores from CSV"""
    try:
        logger.info(f"Loading momentum scores from {csv_file}")
        
        # Read CSV
        df = pd.read_csv(csv_file)
        logger.info(f"Read {len(df)} records from {csv_file}")
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        
        # Insert into database
        result = db.supabase.table('momentumScores').upsert(records).execute()
        
        logger.info(f"Successfully loaded {len(records)} momentum score records")
        return True
        
    except Exception as e:
        logger.error(f"Error loading momentum scores: {e}")
        return False

def main():
    """Main function to load all data"""
    print("🚀 Starting data loading to Supabase...")
    
    # Check if data files exist
    data_dir = "data"
    required_files = [
        "stock_metadata.csv",
        "ticker_price.csv", 
        "momentum_scores.csv"
    ]
    
    for file in required_files:
        file_path = os.path.join(data_dir, file)
        if not os.path.exists(file_path):
            print(f"❌ Error: {file_path} not found!")
            return
    
    # Initialize database
    try:
        db = SupabaseDatabase()
        print("✅ Connected to Supabase database")
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return
    
    # Load data
    success_count = 0
    
    # Load stock metadata
    if load_stock_metadata(db, os.path.join(data_dir, "stock_metadata.csv")):
        success_count += 1
    
    # Load ticker price data
    if load_ticker_price(db, os.path.join(data_dir, "ticker_price.csv")):
        success_count += 1
    
    # Load momentum scores
    if load_momentum_scores(db, os.path.join(data_dir, "momentum_scores.csv")):
        success_count += 1
    
    # Summary
    if success_count == 3:
        print("🎉 All data loaded successfully!")
        
        # Show database stats
        try:
            stats = db.get_database_stats()
            if stats:
                print("\n📊 Database Summary:")
                print(f"Total Stocks: {stats.get('unique_stocks_with_price', 0)}")
                print(f"Price Records: {stats.get('record_counts', {}).get('tickerprice', 0)}")
                print(f"Momentum Scores: {stats.get('momentum_scores_count', 0)}")
        except Exception as e:
            print(f"Warning: Could not get database stats: {e}")
    else:
        print(f"⚠️ Only {success_count}/3 data files loaded successfully")

if __name__ == "__main__":
    main()

