#!/usr/bin/env python3
"""
Clean and format CSV data for Supabase upload
"""

import pandas as pd
import numpy as np

def clean_csv_data():
    """Clean and format the CSV data for Supabase"""
    
    print("🧹 Cleaning CSV data for Supabase upload...")
    print("=" * 60)
    
    # 1. Clean stock metadata
    print("\n📊 Cleaning stock metadata...")
    metadata_df = pd.read_csv('data/clean_stock_metadata.csv')
    print(f"Original records: {len(metadata_df)}")
    
    # Remove any duplicates
    metadata_df = metadata_df.drop_duplicates(subset=['stock'])
    print(f"After removing duplicates: {len(metadata_df)}")
    
    # Clean company names
    metadata_df['company_name'] = metadata_df['company_name'].fillna('Unknown')
    metadata_df['sector'] = metadata_df['sector'].fillna('Unknown')
    metadata_df['industry'] = metadata_df['industry'].fillna('Unknown')
    metadata_df['exchange'] = metadata_df['exchange'].fillna('NSE')
    
    # Save cleaned metadata
    metadata_df.to_csv('data/clean_stock_metadata.csv', index=False)
    print("✅ Stock metadata cleaned and saved")
    
    # 2. Clean ticker price data
    print("\n📈 Cleaning ticker price data...")
    price_df = pd.read_csv('data/clean_ticker_price.csv', low_memory=False)
    print(f"Original records: {len(price_df)}")
    
    # Remove any duplicates
    price_df = price_df.drop_duplicates(subset=['stock', 'date'])
    print(f"After removing duplicates: {len(price_df)}")
    
    # Clean and format price data
    price_df['open'] = pd.to_numeric(price_df['open'], errors='coerce').round(2)
    price_df['high'] = pd.to_numeric(price_df['high'], errors='coerce').round(2)
    price_df['low'] = pd.to_numeric(price_df['low'], errors='coerce').round(2)
    price_df['close'] = pd.to_numeric(price_df['close'], errors='coerce').round(2)
    price_df['volume'] = pd.to_numeric(price_df['volume'], errors='coerce').fillna(0).astype('int64')
    
    # Remove rows with invalid data
    price_df = price_df.dropna(subset=['open', 'high', 'low', 'close'])
    print(f"After removing invalid data: {len(price_df)}")
    
    # Sort by stock and date
    price_df = price_df.sort_values(['stock', 'date'])
    
    # Save cleaned price data
    price_df.to_csv('data/clean_ticker_price.csv', index=False)
    print("✅ Ticker price data cleaned and saved")
    
    # 3. Clean momentum scores
    print("\n⚡ Cleaning momentum scores...")
    momentum_df = pd.read_csv('data/clean_momentum_scores.csv')
    print(f"Original records: {len(momentum_df)}")
    
    # Remove any duplicates
    momentum_df = momentum_df.drop_duplicates(subset=['stock'])
    print(f"After removing duplicates: {len(momentum_df)}")
    
    # Clean numeric columns
    numeric_columns = ['total_score', 'raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m', 
                      'volatility_adjusted', 'smooth_momentum', 'consistency_score', 
                      'trend_strength', 'momentum_12_2', 'fip_quality']
    
    for col in numeric_columns:
        if col in momentum_df.columns:
            momentum_df[col] = pd.to_numeric(momentum_df[col], errors='coerce').fillna(0.0).round(4)
    
    # Save cleaned momentum data
    momentum_df.to_csv('data/clean_momentum_scores.csv', index=False)
    print("✅ Momentum scores cleaned and saved")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 DATA CLEANING COMPLETE!")
    print("=" * 60)
    print(f"📊 Stock Metadata: {len(metadata_df):,} records")
    print(f"📈 Price Data: {len(price_df):,} records")
    print(f"⚡ Momentum Scores: {len(momentum_df):,} records")
    print("\n✅ All data cleaned and ready for Supabase upload!")
    
    return True

if __name__ == "__main__":
    clean_csv_data()
