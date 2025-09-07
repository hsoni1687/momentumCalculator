#!/usr/bin/env python3
"""
Database Preparation System
Comprehensive database initialization and data population
"""

import sys
import os
import sqlite3
import logging
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import pandas as pd

# Add paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

from stock_lists import get_all_stocks
from database_postgres import DatabaseManager

# Configure logging
import os

# Create logs directory if it doesn't exist
try:
    os.makedirs('logs', exist_ok=True)
    log_file = 'logs/database_preparation.log'
except (OSError, PermissionError):
    # If we can't create logs directory, just use console logging
    log_file = None

# Configure logging
handlers = [logging.StreamHandler()]
if log_file:
    try:
        handlers.append(logging.FileHandler(log_file, mode='a'))
    except (OSError, PermissionError):
        # If we can't create log file, just use console logging
        pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

class DatabasePreparation:
    def __init__(self, db_path: str = 'data/stock_data.db', database_url: str = None):
        self.db_manager = DatabaseManager(db_path=db_path, database_url=database_url)
        self.db_path = db_path
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        logger.info(f"Directories ensured for database: {self.db_path}")
    
    def create_tables(self) -> bool:
        """Create all required database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                logger.info("Creating database tables...")
                
                # 1. Create stockMetadata table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS stockMetadata (
                        stock TEXT PRIMARY KEY,
                        company_name TEXT,
                        market_cap REAL,
                        sector TEXT,
                        industry TEXT,
                        exchange TEXT,
                        dividend_yield REAL,
                        roce REAL,
                        roe REAL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                logger.info("✅ Created stockMetadata table")
                
                # 2. Create tickerPrice table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tickerPrice (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stock TEXT NOT NULL,
                        date DATE NOT NULL,
                        open REAL,
                        high REAL,
                        low REAL,
                        close REAL,
                        volume INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(stock, date)
                    )
                ''')
                logger.info("✅ Created tickerPrice table")
                
                # 3. Create momentumScores table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS momentumScores (
                        stock TEXT PRIMARY KEY,
                        total_score REAL,
                        raw_momentum_6m REAL,
                        raw_momentum_3m REAL,
                        raw_momentum_1m REAL,
                        volatility_adjusted REAL,
                        smooth_momentum REAL,
                        consistency_score REAL,
                        trend_strength REAL,
                        calculated_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        momentum_12_2 REAL,
                        fip_quality REAL
                    )
                ''')
                logger.info("✅ Created momentumScores table")
                
                # 4. Create indexes for better performance
                indexes = [
                    ('idx_stock_metadata_sector', 'stockMetadata', 'sector'),
                    ('idx_stock_metadata_industry', 'stockMetadata', 'industry'),
                    ('idx_ticker_price_stock', 'tickerPrice', 'stock'),
                    ('idx_ticker_price_date', 'tickerPrice', 'date'),
                    ('idx_ticker_price_stock_date', 'tickerPrice', 'stock, date')
                ]
                
                for index_name, table, columns in indexes:
                    cursor.execute(f'''
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table}({columns})
                    ''')
                
                logger.info("✅ Created database indexes")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            return False
    
    def populate_stock_metadata(self) -> Dict[str, int]:
        """Populate stock metadata table with initial data"""
        try:
            logger.info("📋 Populating stock metadata...")
            
            # Get all stocks from stock lists
            all_stocks = get_all_stocks()
            logger.info(f"Retrieved {len(all_stocks)} stocks from stock lists")
            
            success_count = 0
            failed_count = 0
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for stock in all_stocks:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO stockMetadata 
                            (stock, company_name, market_cap, sector, industry, exchange, 
                             dividend_yield, roce, roe, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (
                            stock.get('symbol'),
                            stock.get('company_name', ''),
                            stock.get('market_cap'),
                            stock.get('sector', 'Unknown'),
                            stock.get('industry', 'Unknown'),
                            stock.get('exchange', 'NSE'),
                            stock.get('dividend_yield'),
                            stock.get('roce'),
                            stock.get('roe')
                        ))
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error inserting stock {stock.get('symbol', 'unknown')}: {e}")
                        failed_count += 1
                
                conn.commit()
            
            logger.info(f"✅ Stock metadata populated: {success_count} success, {failed_count} failed")
            return {'success': success_count, 'failed': failed_count}
            
        except Exception as e:
            logger.error(f"❌ Error populating stock metadata: {e}")
            return {'success': 0, 'failed': 0}
    
    def populate_real_price_data(self) -> Dict[str, int]:
        """Populate real price data for all stocks"""
        try:
            logger.info("📈 Populating real price data for all stocks...")
            
            # Import data fetcher
            from data_fetcher import IndianStockDataFetcher
            
            # Initialize data fetcher
            fetcher = IndianStockDataFetcher(self.db_path)
            
            # Get all stocks from metadata
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT stock FROM stockMetadata')
                stocks = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Found {len(stocks)} stocks to populate with price data")
            
            success_count = 0
            failed_count = 0
            
            # Process stocks in batches to avoid overwhelming the API
            batch_size = 10
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(stocks) + batch_size - 1)//batch_size}")
                
                for stock in batch:
                    try:
                        # Fetch historical data for the stock using the public method
                        hist_data = fetcher._fetch_from_api(stock, period='2y')
                        
                        if hist_data is not None and not hist_data.empty:
                            success_count += 1
                            logger.info(f"✅ Populated price data for {stock}")
                        else:
                            failed_count += 1
                            logger.warning(f"⚠️ No price data available for {stock}")
                            
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"❌ Error populating price data for {stock}: {e}")
                
                # Small delay between batches to be respectful to the API
                import time
                time.sleep(1)
            
            logger.info(f"✅ Real price data populated: {success_count} stocks, {failed_count} failed")
            
            return {
                'success': success_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f"Error populating real price data: {e}")
            return {'success': 0, 'failed': 1}

    def populate_sample_price_data(self) -> Dict[str, int]:
        """Populate sample price data for testing"""
        try:
            logger.info("📈 Populating sample price data...")
            
            # Get a broader set of sample stocks for better testing
            sample_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ITC', 'WIPRO', 'BHARTIARTL', 'SBIN', 'KOTAKBANK', 'LT', 'MARUTI', 'ASIANPAINT', 'NESTLEIND', 'BAJFINANCE']
            
            success_count = 0
            failed_count = 0
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Generate sample price data for the last 2 years
                from datetime import timedelta
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=730)  # 2 years
                
                for stock in sample_stocks:
                    current_date = start_date
                    while current_date <= end_date:
                        try:
                            # Generate sample price data
                            base_price = 100.0 + hash(stock) % 1000  # Consistent base price per stock
                            daily_variation = (hash(f"{stock}{current_date}") % 20) - 10  # ±10 variation
                            price = base_price + daily_variation
                            
                            cursor.execute('''
                                INSERT OR REPLACE INTO tickerPrice 
                                (stock, date, open, high, low, close, volume, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            ''', (
                                stock,
                                current_date.strftime('%Y-%m-%d'),
                                price,
                                price + 2,
                                price - 2,
                                price,
                                1000000 + (hash(f"{stock}{current_date}") % 500000)
                            ))
                            success_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error inserting price data for {stock} on {current_date}: {e}")
                            failed_count += 1
                        
                        current_date += timedelta(days=1)
                
                conn.commit()
            
            logger.info(f"✅ Sample price data populated: {success_count} records, {failed_count} failed")
            return {'success': success_count, 'failed': failed_count}
            
        except Exception as e:
            logger.error(f"❌ Error populating sample price data: {e}")
            return {'success': 0, 'failed': 0}
    
    def verify_database(self) -> Dict[str, Any]:
        """Verify database integrity and return statistics"""
        try:
            logger.info("🔍 Verifying database...")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check table existence
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get record counts
                stats = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[table] = count
                
                # Get unique stocks in price data
                cursor.execute("SELECT COUNT(DISTINCT stock) FROM tickerPrice")
                unique_stocks_with_price = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute("SELECT MIN(date), MAX(date) FROM tickerPrice")
                date_range = cursor.fetchone()
                
                verification_result = {
                    'tables_created': tables,
                    'record_counts': stats,
                    'unique_stocks_with_price': unique_stocks_with_price,
                    'date_range': date_range,
                    'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
                }
                
                logger.info("✅ Database verification completed")
                return verification_result
                
        except Exception as e:
            logger.error(f"❌ Error verifying database: {e}")
            return {}
    
    def prepare_database(self) -> bool:
        """Complete database preparation process"""
        try:
            logger.info("🚀 Starting comprehensive database preparation...")
            
            # Step 1: Create tables
            if not self.create_tables():
                logger.error("❌ Failed to create tables")
                return False
            
            # Step 2: Populate stock metadata
            metadata_result = self.populate_stock_metadata()
            if metadata_result['success'] == 0:
                logger.error("❌ Failed to populate stock metadata")
                return False
            
            # Step 3: Populate real price data (with fallback to sample data)
            try:
                price_result = self.populate_real_price_data()
                if price_result['success'] == 0:
                    logger.warning("⚠️ No real price data populated, falling back to sample data")
                    # Fallback to sample data if real data fails
                    price_result = self.populate_sample_price_data()
            except Exception as e:
                logger.error(f"❌ Error during price data population: {e}")
                logger.info("📈 Falling back to sample data...")
                price_result = self.populate_sample_price_data()
            
            # Step 4: Verify database
            verification = self.verify_database()
            if not verification:
                logger.error("❌ Database verification failed")
                return False
            
            # Log final statistics
            logger.info("🎉 Database preparation completed successfully!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   Tables: {verification['tables_created']}")
            logger.info(f"   Record Counts: {verification['record_counts']}")
            logger.info(f"   Unique Stocks with Price Data: {verification['unique_stocks_with_price']}")
            logger.info(f"   Date Range: {verification['date_range']}")
            logger.info(f"   Database Size: {verification['database_size_mb']:.2f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database preparation failed: {e}")
            return False
    
    def reset_database(self) -> bool:
        """Reset database by dropping all tables and recreating"""
        try:
            logger.info("🔄 Resetting database...")
            
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                logger.info("✅ Existing database removed")
            
            return self.prepare_database()
            
        except Exception as e:
            logger.error(f"❌ Error resetting database: {e}")
            return False

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Database Preparation System')
    parser.add_argument('--prepare-database', action='store_true', 
                       help='Prepare database with all tables and sample data')
    parser.add_argument('--reset-database', action='store_true',
                       help='Reset database (drop all tables and recreate)')
    parser.add_argument('--verify-database', action='store_true',
                       help='Verify database integrity')
    parser.add_argument('--db-path', default='data/stock_data.db',
                       help='Database file path')
    
    args = parser.parse_args()
    
    # Create database preparation instance
    db_prep = DatabasePreparation(args.db_path)
    
    if args.reset_database:
        print("🔄 Resetting database...")
        success = db_prep.reset_database()
        print(f"Database reset: {'✅ Success' if success else '❌ Failed'}")
        
    elif args.prepare_database:
        print("🚀 Preparing database...")
        success = db_prep.prepare_database()
        print(f"Database preparation: {'✅ Success' if success else '❌ Failed'}")
        
    elif args.verify_database:
        print("🔍 Verifying database...")
        verification = db_prep.verify_database()
        if verification:
            print("✅ Database verification completed")
            print(f"📊 Statistics: {verification}")
        else:
            print("❌ Database verification failed")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
