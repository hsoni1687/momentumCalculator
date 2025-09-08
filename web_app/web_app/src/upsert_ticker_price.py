#!/usr/bin/env python3
"""
Ticker Price Upsert Script
Handles upsert operations for ticker price data
"""

import sys
import os
import sqlite3
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, date

# Add paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TickerPriceUpserter:
    def __init__(self, db_path: str = 'data/stock_data.db'):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Ensure database and tables exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create tickerPrice table if it doesn't exist
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
            
            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ticker_price_stock 
                ON tickerPrice(stock)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ticker_price_date 
                ON tickerPrice(date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ticker_price_stock_date 
                ON tickerPrice(stock, date)
            ''')
            
            conn.commit()
            logger.info("Database and tickerPrice table ensured")
    
    def upsert_price_data(self, stock: str, price_data: pd.DataFrame) -> Dict[str, int]:
        """
        Upsert price data for a single stock
        price_data should have columns: Date, Open, High, Low, Close, Volume
        """
        success_count = 0
        failed_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Ensure we have the required columns
                required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                if not all(col in price_data.columns for col in required_columns):
                    logger.error(f"Missing required columns in price data for {stock}")
                    return {'success': 0, 'failed': len(price_data)}
                
                # Process each row
                for index, row in price_data.iterrows():
                    try:
                        # Convert date to string if it's a datetime
                        date_str = row['Date']
                        if isinstance(date_str, (datetime, date)):
                            date_str = date_str.strftime('%Y-%m-%d')
                        elif hasattr(date_str, 'date'):
                            date_str = date_str.date().strftime('%Y-%m-%d')
                        else:
                            date_str = str(date_str)
                        
                        # Use INSERT OR REPLACE for upsert functionality
                        cursor.execute('''
                            INSERT OR REPLACE INTO tickerPrice 
                            (stock, date, open, high, low, close, volume, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (
                            stock,
                            date_str,
                            row['Open'] if pd.notna(row['Open']) else None,
                            row['High'] if pd.notna(row['High']) else None,
                            row['Low'] if pd.notna(row['Low']) else None,
                            row['Close'] if pd.notna(row['Close']) else None,
                            int(row['Volume']) if pd.notna(row['Volume']) else None
                        ))
                        
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error upserting price data for {stock} on {row.get('Date', 'unknown date')}: {e}")
                        failed_count += 1
                
                conn.commit()
                logger.info(f"Upserted price data for {stock}: {success_count} success, {failed_count} failed")
                
        except Exception as e:
            logger.error(f"Error upserting price data for {stock}: {e}")
            failed_count += len(price_data)
            success_count = 0
        
        return {'success': success_count, 'failed': failed_count}
    
    def upsert_batch_price_data(self, price_data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Upsert price data for multiple stocks
        price_data_dict: {stock_symbol: price_dataframe}
        """
        total_success = 0
        total_failed = 0
        stock_results = {}
        
        for stock, price_data in price_data_dict.items():
            logger.info(f"Processing price data for {stock} ({len(price_data)} records)")
            result = self.upsert_price_data(stock, price_data)
            stock_results[stock] = result
            total_success += result['success']
            total_failed += result['failed']
        
        logger.info(f"Batch upsert completed: {total_success} total success, {total_failed} total failed")
        
        return {
            'total_success': total_success,
            'total_failed': total_failed,
            'stock_results': stock_results
        }
    
    def upsert_single_price_record(self, stock: str, date: str, open_price: float = None, 
                                 high_price: float = None, low_price: float = None, 
                                 close_price: float = None, volume: int = None) -> bool:
        """
        Upsert a single price record
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO tickerPrice 
                    (stock, date, open, high, low, close, volume, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (stock, date, open_price, high_price, low_price, close_price, volume))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error upserting single price record for {stock} on {date}: {e}")
            return False
    
    def get_price_data_stats(self) -> Dict[str, Any]:
        """Get statistics about the price data table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute('SELECT COUNT(*) FROM tickerPrice')
                total_records = cursor.fetchone()[0]
                
                # Unique stocks
                cursor.execute('SELECT COUNT(DISTINCT stock) FROM tickerPrice')
                unique_stocks = cursor.fetchone()[0]
                
                # Date range
                cursor.execute('SELECT MIN(date), MAX(date) FROM tickerPrice')
                date_range = cursor.fetchone()
                
                # Records by stock (top 10)
                cursor.execute('''
                    SELECT stock, COUNT(*) as record_count 
                    FROM tickerPrice 
                    GROUP BY stock 
                    ORDER BY record_count DESC 
                    LIMIT 10
                ''')
                top_stocks = dict(cursor.fetchall())
                
                return {
                    'total_records': total_records,
                    'unique_stocks': unique_stocks,
                    'date_range': date_range,
                    'top_stocks_by_records': top_stocks
                }
                
        except Exception as e:
            logger.error(f"Error getting price data stats: {e}")
            return {}
    
    def get_stock_price_range(self, stock: str) -> Optional[Dict[str, Any]]:
        """Get price data range for a specific stock"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as record_count,
                        MIN(date) as first_date,
                        MAX(date) as last_date,
                        MIN(close) as min_price,
                        MAX(close) as max_price,
                        AVG(close) as avg_price
                    FROM tickerPrice 
                    WHERE stock = ?
                ''', (stock,))
                
                result = cursor.fetchone()
                if result and result[0] > 0:
                    return {
                        'record_count': result[0],
                        'first_date': result[1],
                        'last_date': result[2],
                        'min_price': result[3],
                        'max_price': result[4],
                        'avg_price': result[5]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting price range for {stock}: {e}")
            return None
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """
        Clean up old price data (optional maintenance function)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM tickerPrice 
                    WHERE date < date('now', '-{} days')
                '''.format(days_to_keep))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old price records")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0

def main():
    """Main function for testing"""
    upserter = TickerPriceUpserter()
    
    print("🔄 Ticker Price Upserter initialized")
    
    # Show current stats
    stats = upserter.get_price_data_stats()
    if stats:
        print(f"\n📊 Current Price Data Stats:")
        print(f"   Total Records: {stats['total_records']:,}")
        print(f"   Unique Stocks: {stats['unique_stocks']}")
        print(f"   Date Range: {stats['date_range'][0]} to {stats['date_range'][1]}")
        print(f"   Top Stocks by Records: {stats['top_stocks_by_records']}")
    
    # Test single record upsert
    print(f"\n🧪 Testing single record upsert...")
    success = upserter.upsert_single_price_record(
        stock='TEST',
        date='2024-01-01',
        open_price=100.0,
        high_price=105.0,
        low_price=95.0,
        close_price=102.0,
        volume=1000000
    )
    print(f"   Single record upsert: {'✅ Success' if success else '❌ Failed'}")

if __name__ == "__main__":
    main()
