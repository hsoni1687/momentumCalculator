#!/usr/bin/env python3
"""
Data Export Script for Momentum Calculator
Run this in your cloud VS Code to export data in various formats
"""

import sys
import os
import pandas as pd
import sqlite3
from datetime import datetime

# Add paths
sys.path.append('src')
sys.path.append('config')

def export_all_data():
    """Export all data from the database to CSV files"""
    
    db_path = 'data/stock_data.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    print("📊 Exporting data from Momentum Calculator Database...")
    print(f"Database: {db_path}")
    print(f"Size: {os.path.getsize(db_path) / (1024*1024):.1f} MB")
    
    # Create exports directory
    os.makedirs('exports', exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        # Export stock metadata
        print("\n1. Exporting Stock Metadata...")
        metadata_df = pd.read_sql_query("SELECT * FROM stockMetadata", conn)
        metadata_df.to_csv('exports/stock_metadata.csv', index=False)
        print(f"   ✅ Exported {len(metadata_df)} stocks to exports/stock_metadata.csv")
        
        # Export price data summary
        print("\n2. Exporting Price Data Summary...")
        price_summary = pd.read_sql_query("""
            SELECT 
                stock,
                COUNT(*) as price_records,
                MIN(date) as first_date,
                MAX(date) as last_date,
                AVG(close) as avg_price
            FROM tickerPrice 
            GROUP BY stock
            ORDER BY price_records DESC
        """, conn)
        price_summary.to_csv('exports/price_data_summary.csv', index=False)
        print(f"   ✅ Exported price summary for {len(price_summary)} stocks")
        
        # Export momentum scores (if available)
        print("\n3. Checking for Momentum Scores...")
        try:
            momentum_df = pd.read_sql_query("SELECT * FROM momentumScores", conn)
            momentum_df.to_csv('exports/momentum_scores.csv', index=False)
            print(f"   ✅ Exported momentum scores for {len(momentum_df)} stocks")
        except:
            print("   ⚠️  No momentum scores found in database")
        
        # Export industry/sector breakdown
        print("\n4. Exporting Industry/Sector Breakdown...")
        industry_breakdown = pd.read_sql_query("""
            SELECT 
                industry,
                sector,
                COUNT(*) as stock_count,
                AVG(market_cap) as avg_market_cap
            FROM stockMetadata 
            WHERE industry IS NOT NULL AND industry != ''
            GROUP BY industry, sector
            ORDER BY stock_count DESC
        """, conn)
        industry_breakdown.to_csv('exports/industry_sector_breakdown.csv', index=False)
        print(f"   ✅ Exported breakdown for {len(industry_breakdown)} industry/sector combinations")
        
        # Export top stocks by market cap
        print("\n5. Exporting Top Stocks by Market Cap...")
        top_stocks = pd.read_sql_query("""
            SELECT 
                symbol,
                company_name,
                market_cap,
                sector,
                industry,
                exchange
            FROM stockMetadata 
            WHERE market_cap IS NOT NULL
            ORDER BY market_cap DESC
            LIMIT 100
        """, conn)
        top_stocks.to_csv('exports/top_100_stocks_by_market_cap.csv', index=False)
        print(f"   ✅ Exported top 100 stocks by market cap")
        
        # Export sample price data for a few stocks
        print("\n6. Exporting Sample Price Data...")
        sample_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR']
        for stock in sample_stocks:
            try:
                sample_data = pd.read_sql_query(f"""
                    SELECT * FROM tickerPrice 
                    WHERE stock = '{stock}' 
                    ORDER BY date DESC 
                    LIMIT 100
                """, conn)
                if not sample_data.empty:
                    sample_data.to_csv(f'exports/sample_price_data_{stock}.csv', index=False)
                    print(f"   ✅ Exported sample data for {stock} ({len(sample_data)} records)")
            except:
                print(f"   ⚠️  No data found for {stock}")
    
    print(f"\n🎉 Export completed! Check the 'exports' folder for all CSV files.")
    print(f"📁 Files created:")
    for file in os.listdir('exports'):
        if file.endswith('.csv'):
            size = os.path.getsize(f'exports/{file}') / 1024
            print(f"   - {file} ({size:.1f} KB)")

def export_specific_stock_data(symbol):
    """Export detailed data for a specific stock"""
    
    db_path = 'data/stock_data.db'
    
    with sqlite3.connect(db_path) as conn:
        # Get stock metadata
        metadata = pd.read_sql_query(f"""
            SELECT * FROM stockMetadata 
            WHERE symbol = '{symbol}'
        """, conn)
        
        if metadata.empty:
            print(f"Stock {symbol} not found in metadata")
            return
        
        # Get price data
        price_data = pd.read_sql_query(f"""
            SELECT * FROM tickerPrice 
            WHERE stock = '{symbol}'
            ORDER BY date
        """, conn)
        
        # Get momentum scores
        try:
            momentum_data = pd.read_sql_query(f"""
                SELECT * FROM momentumScores 
                WHERE symbol = '{symbol}'
            """, conn)
        except:
            momentum_data = pd.DataFrame()
        
        # Export
        os.makedirs('exports', exist_ok=True)
        metadata.to_csv(f'exports/{symbol}_metadata.csv', index=False)
        price_data.to_csv(f'exports/{symbol}_price_data.csv', index=False)
        
        if not momentum_data.empty:
            momentum_data.to_csv(f'exports/{symbol}_momentum.csv', index=False)
        
        print(f"✅ Exported data for {symbol}")
        print(f"   - Metadata: {len(metadata)} records")
        print(f"   - Price data: {len(price_data)} records")
        if not momentum_data.empty:
            print(f"   - Momentum scores: {len(momentum_data)} records")

if __name__ == "__main__":
    print("🚀 Momentum Calculator Data Exporter")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Export specific stock
        symbol = sys.argv[1].upper()
        export_specific_stock_data(symbol)
    else:
        # Export all data
        export_all_data()
