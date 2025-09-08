#!/usr/bin/env python3
"""
Setup Supabase database tables
This script creates the required tables in your Supabase database
"""

import os
import sys
import logging

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database_supabase import SupabaseDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_tables(db):
    """Create database tables"""
    try:
        logger.info("Creating database tables...")
        
        # Create stockMetadata table
        stock_metadata_sql = """
        CREATE TABLE IF NOT EXISTS stockMetadata (
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
        
        # Create tickerPrice table
        ticker_price_sql = """
        CREATE TABLE IF NOT EXISTS tickerPrice (
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
        
        # Create momentumScores table
        momentum_scores_sql = """
        CREATE TABLE IF NOT EXISTS momentumScores (
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
        db.supabase.rpc('exec_sql', {'sql': stock_metadata_sql}).execute()
        logger.info("✅ Created stockMetadata table")
        
        db.supabase.rpc('exec_sql', {'sql': ticker_price_sql}).execute()
        logger.info("✅ Created tickerPrice table")
        
        db.supabase.rpc('exec_sql', {'sql': momentum_scores_sql}).execute()
        logger.info("✅ Created momentumScores table")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Setting up Supabase database tables...")
    
    # Initialize database
    try:
        db = SupabaseDatabase()
        print("✅ Connected to Supabase database")
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return
    
    # Create tables
    if create_tables(db):
        print("🎉 Database tables created successfully!")
    else:
        print("❌ Failed to create database tables")

if __name__ == "__main__":
    main()

