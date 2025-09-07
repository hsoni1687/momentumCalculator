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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/database_preparation.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class DatabasePreparation:
    def __init__(self, db_path: str = 'data/stock_data.db'):
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
    
    def populate_sample_price_data(self) -> Dict[str, int]:
        """Populate sample price data for testing"""
        try:
            logger.info("📈 Populating sample price data...")
            
            # Get a few sample stocks
            sample_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR']
            
            success_count = 0
            failed_count = 0
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Generate sample price data for the last 30 days
                from datetime import timedelta
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)
                
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
            
            # Step 3: Populate sample price data
            price_result = self.populate_sample_price_data()
            if price_result['success'] == 0:
                logger.warning("⚠️ No sample price data populated")
            
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
