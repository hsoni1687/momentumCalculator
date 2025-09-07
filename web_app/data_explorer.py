#!/usr/bin/env python3
"""
Data Explorer Script for Momentum Calculator
This script helps you explore and export data from the stock database
"""

import sys
import os
import pandas as pd
import sqlite3
from datetime import datetime

# Add src and config to path
sys.path.append('src')
sys.path.append('config')

from database import StockDatabase

def explore_database():
    """Explore the database structure and data"""
    db_path = 'data/stock_data.db'
    db = StockDatabase(db_path)
    
    print("🔍 DATABASE EXPLORATION")
    print("=" * 50)
    
    # Get database stats
    stats = db.get_database_stats()
    print(f"📊 Database Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n📈 Stock Metadata Sample:")
    metadata = db.get_stock_metadata()
    print(f"   Total stocks: {len(metadata)}")
    print(f"   Columns: {list(metadata.columns)}")
    print("\n   Sample data:")
    print(metadata.head())
    
    print("\n🏭 Industry Distribution:")
    industry_counts = metadata['industry'].value_counts().head(10)
    for industry, count in industry_counts.items():
        print(f"   {industry}: {count}")
    
    print("\n🏢 Sector Distribution:")
    sector_counts = metadata['sector'].value_counts().head(10)
    for sector, count in sector_counts.items():
        print(f"   {sector}: {count}")
    
    return metadata

def export_data_to_csv():
    """Export data to CSV files"""
    db_path = 'data/stock_data.db'
    db = StockDatabase(db_path)
    
    print("\n📤 EXPORTING DATA TO CSV")
    print("=" * 50)
    
    # Export stock metadata
    metadata = db.get_stock_metadata()
    metadata_file = f"exports/stock_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    os.makedirs("exports", exist_ok=True)
    metadata.to_csv(metadata_file, index=False)
    print(f"✅ Stock metadata exported to: {metadata_file}")
    
    # Export price data sample (last 30 days for top 100 stocks)
    top_stocks = metadata.nlargest(100, 'market_cap')['symbol'].tolist()
    price_data = db.get_historical_data(top_stocks[:10])  # Sample of 10 stocks
    
    if not price_data.empty:
        price_file = f"exports/price_data_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        price_data.to_csv(price_file, index=False)
        print(f"✅ Price data sample exported to: {price_file}")
    
    print(f"\n📁 Files saved in: {os.path.abspath('exports')}")

def query_custom_data():
    """Run custom queries on the database"""
    db_path = 'data/stock_data.db'
    
    print("\n🔍 CUSTOM QUERIES")
    print("=" * 50)
    
    with sqlite3.connect(db_path) as conn:
        # Query 1: Top 20 stocks by market cap
        query1 = """
        SELECT symbol, company_name, market_cap, sector, industry
        FROM stockMetadata 
        ORDER BY market_cap DESC 
        LIMIT 20
        """
        df1 = pd.read_sql_query(query1, conn)
        print("📈 Top 20 stocks by market cap:")
        print(df1.to_string(index=False))
        
        # Query 2: Stocks by sector
        query2 = """
        SELECT sector, COUNT(*) as stock_count, AVG(market_cap) as avg_market_cap
        FROM stockMetadata 
        WHERE sector != 'Unknown'
        GROUP BY sector 
        ORDER BY stock_count DESC
        """
        df2 = pd.read_sql_query(query2, conn)
        print("\n🏢 Stocks by sector:")
        print(df2.to_string(index=False))
        
        # Query 3: Recent price data availability
        query3 = """
        SELECT stock, COUNT(*) as price_records, MIN(date) as first_date, MAX(date) as last_date
        FROM tickerPrice 
        GROUP BY stock 
        ORDER BY price_records DESC 
        LIMIT 10
        """
        df3 = pd.read_sql_query(query3, conn)
        print("\n📊 Price data availability (top 10):")
        print(df3.to_string(index=False))

def main():
    """Main function"""
    print("🚀 MOMENTUM CALCULATOR DATA EXPLORER")
    print("=" * 60)
    
    while True:
        print("\nChoose an option:")
        print("1. Explore database structure")
        print("2. Export data to CSV")
        print("3. Run custom queries")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            explore_database()
        elif choice == '2':
            export_data_to_csv()
        elif choice == '3':
            query_custom_data()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
