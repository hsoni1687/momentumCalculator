#!/usr/bin/env python3
"""
Extract clean data from SQLite database and generate CSV files for Supabase
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def extract_clean_data():
    """Extract data from SQLite and create clean CSV files"""
    
    print("🔄 Extracting clean data from SQLite database...")
    print("=" * 60)
    
    # Path to SQLite database
    db_path = "../stock_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ SQLite database not found at: {db_path}")
        return False
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        print(f"✅ Connected to SQLite database: {db_path}")
        
        # 1. Extract stock metadata
        print("\n📊 Extracting stock metadata...")
        metadata_query = """
        SELECT 
            stock,
            company_name,
            market_cap,
            sector,
            industry,
            exchange,
            dividend_yield,
            roce,
            roe,
            last_updated
        FROM stockMetadata
        ORDER BY market_cap DESC
        """
        
        metadata_df = pd.read_sql_query(metadata_query, conn)
        print(f"✅ Extracted {len(metadata_df)} stock records")
        
        # Clean and format metadata
        metadata_df['market_cap'] = metadata_df['market_cap'].fillna(0).astype('int64')
        metadata_df['dividend_yield'] = metadata_df['dividend_yield'].fillna(0.0)
        metadata_df['roce'] = metadata_df['roce'].fillna(0.0)
        metadata_df['roe'] = metadata_df['roe'].fillna(0.0)
        metadata_df['last_updated'] = pd.to_datetime(metadata_df['last_updated']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Save to CSV
        metadata_csv = "data/clean_stock_metadata.csv"
        metadata_df.to_csv(metadata_csv, index=False)
        print(f"✅ Saved stock metadata to: {metadata_csv}")
        
        # 2. Extract price data (sample recent data to avoid huge files)
        print("\n📈 Extracting recent price data...")
        price_query = """
        SELECT 
            stock,
            date,
            open,
            high,
            low,
            close,
            volume
        FROM tickerPrice
        WHERE date >= date('now', '-2 years')
        ORDER BY stock, date
        """
        
        price_df = pd.read_sql_query(price_query, conn)
        print(f"✅ Extracted {len(price_df)} recent price records")
        
        # Clean and format price data
        price_df['date'] = pd.to_datetime(price_df['date']).dt.strftime('%Y-%m-%d')
        price_df['open'] = price_df['open'].fillna(0.0)
        price_df['high'] = price_df['high'].fillna(0.0)
        price_df['low'] = price_df['low'].fillna(0.0)
        price_df['close'] = price_df['close'].fillna(0.0)
        
        # Handle volume data - convert to numeric first, then to int
        price_df['volume'] = pd.to_numeric(price_df['volume'], errors='coerce').fillna(0).astype('int64')
        
        # Save to CSV
        price_csv = "data/clean_ticker_price.csv"
        price_df.to_csv(price_csv, index=False)
        print(f"✅ Saved price data to: {price_csv}")
        
        # 3. Extract momentum scores
        print("\n⚡ Extracting momentum scores...")
        momentum_query = """
        SELECT 
            stock,
            total_score,
            raw_momentum_6m,
            raw_momentum_3m,
            raw_momentum_1m,
            volatility_adjusted,
            smooth_momentum,
            consistency_score,
            trend_strength,
            momentum_12_2,
            fip_quality,
            calculated_date,
            created_at
        FROM momentumScores
        ORDER BY total_score DESC
        """
        
        momentum_df = pd.read_sql_query(momentum_query, conn)
        print(f"✅ Extracted {len(momentum_df)} momentum score records")
        
        # Clean and format momentum data
        momentum_df['calculated_date'] = pd.to_datetime(momentum_df['calculated_date']).dt.strftime('%Y-%m-%d')
        momentum_df['created_at'] = pd.to_datetime(momentum_df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Fill NaN values with 0
        numeric_columns = ['total_score', 'raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m', 
                          'volatility_adjusted', 'smooth_momentum', 'consistency_score', 
                          'trend_strength', 'momentum_12_2', 'fip_quality']
        for col in numeric_columns:
            momentum_df[col] = momentum_df[col].fillna(0.0)
        
        # Save to CSV
        momentum_csv = "data/clean_momentum_scores.csv"
        momentum_df.to_csv(momentum_csv, index=False)
        print(f"✅ Saved momentum scores to: {momentum_csv}")
        
        # Close connection
        conn.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 DATA EXTRACTION COMPLETE!")
        print("=" * 60)
        print(f"📊 Stock Metadata: {len(metadata_df):,} records")
        print(f"📈 Price Data: {len(price_df):,} records (last 2 years)")
        print(f"⚡ Momentum Scores: {len(momentum_df):,} records")
        print("\n📁 Generated CSV files:")
        print(f"   • {metadata_csv}")
        print(f"   • {price_csv}")
        print(f"   • {momentum_csv}")
        print("\n🚀 Ready to upload to Supabase!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        return False

if __name__ == "__main__":
    extract_clean_data()
