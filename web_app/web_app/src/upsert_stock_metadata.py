#!/usr/bin/env python3
"""
Stock Metadata Upsert Script
Handles upsert operations for stock metadata table
"""

import sys
import os
import sqlite3
import logging
from typing import List, Dict, Any

# Add paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

from stock_lists import get_all_stocks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockMetadataUpserter:
    def __init__(self, db_path: str = 'data/stock_data.db'):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Ensure database and tables exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create stockMetadata table if it doesn't exist
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
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stock_metadata_sector 
                ON stockMetadata(sector)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stock_metadata_industry 
                ON stockMetadata(industry)
            ''')
            
            conn.commit()
            logger.info("Database and stockMetadata table ensured")
    
    def upsert_stock_metadata(self, stock_data: Dict[str, Any]) -> bool:
        """
        Upsert a single stock's metadata
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Use INSERT OR REPLACE for upsert functionality
                cursor.execute('''
                    INSERT OR REPLACE INTO stockMetadata 
                    (stock, company_name, market_cap, sector, industry, exchange, 
                     dividend_yield, roce, roe, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    stock_data.get('symbol'),
                    stock_data.get('company_name'),
                    stock_data.get('market_cap'),
                    stock_data.get('sector'),
                    stock_data.get('industry'),
                    stock_data.get('exchange'),
                    stock_data.get('dividend_yield'),
                    stock_data.get('roce'),
                    stock_data.get('roe')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error upserting stock metadata for {stock_data.get('symbol', 'unknown')}: {e}")
            return False
    
    def upsert_batch_stock_metadata(self, stocks_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Upsert multiple stocks' metadata in batch
        Returns: {'success': count, 'failed': count}
        """
        success_count = 0
        failed_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for stock_data in stocks_data:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO stockMetadata 
                            (stock, company_name, market_cap, sector, industry, exchange, 
                             dividend_yield, roce, roe, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (
                            stock_data.get('symbol'),
                            stock_data.get('company_name'),
                            stock_data.get('market_cap'),
                            stock_data.get('sector'),
                            stock_data.get('industry'),
                            stock_data.get('exchange'),
                            stock_data.get('dividend_yield'),
                            stock_data.get('roce'),
                            stock_data.get('roe')
                        ))
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error upserting stock {stock_data.get('symbol', 'unknown')}: {e}")
                        failed_count += 1
                
                conn.commit()
                logger.info(f"Batch upsert completed: {success_count} success, {failed_count} failed")
                
        except Exception as e:
            logger.error(f"Error in batch upsert: {e}")
            failed_count += len(stocks_data)
            success_count = 0
        
        return {'success': success_count, 'failed': failed_count}
    
    def upsert_all_stocks_from_lists(self) -> Dict[str, int]:
        """
        Upsert all stocks from the stock lists
        """
        logger.info("Starting upsert of all stocks from stock lists...")
        
        try:
            # Get all stocks from stock lists
            all_stocks = get_all_stocks()
            logger.info(f"Retrieved {len(all_stocks)} stocks from stock lists")
            
            # Convert to the format expected by upsert
            stocks_data = []
            for stock in all_stocks:
                stock_data = {
                    'symbol': stock.get('symbol'),
                    'company_name': stock.get('company_name', ''),
                    'market_cap': stock.get('market_cap'),
                    'sector': stock.get('sector', 'Unknown'),
                    'industry': stock.get('industry', 'Unknown'),
                    'exchange': stock.get('exchange', 'NSE'),
                    'dividend_yield': stock.get('dividend_yield'),
                    'roce': stock.get('roce'),
                    'roe': stock.get('roe')
                }
                stocks_data.append(stock_data)
            
            # Perform batch upsert
            result = self.upsert_batch_stock_metadata(stocks_data)
            
            logger.info(f"Upsert completed: {result['success']} stocks processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in upsert_all_stocks_from_lists: {e}")
            return {'success': 0, 'failed': 0}
    
    def get_stock_count(self) -> int:
        """Get total number of stocks in metadata table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM stockMetadata')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting stock count: {e}")
            return 0
    
    def get_metadata_stats(self) -> Dict[str, Any]:
        """Get statistics about the metadata table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total stocks
                cursor.execute('SELECT COUNT(*) FROM stockMetadata')
                total_stocks = cursor.fetchone()[0]
                
                # Stocks by exchange
                cursor.execute('''
                    SELECT exchange, COUNT(*) 
                    FROM stockMetadata 
                    GROUP BY exchange
                ''')
                exchange_counts = dict(cursor.fetchall())
                
                # Stocks by sector
                cursor.execute('''
                    SELECT sector, COUNT(*) 
                    FROM stockMetadata 
                    GROUP BY sector 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 10
                ''')
                sector_counts = dict(cursor.fetchall())
                
                return {
                    'total_stocks': total_stocks,
                    'exchange_counts': exchange_counts,
                    'top_sectors': sector_counts
                }
                
        except Exception as e:
            logger.error(f"Error getting metadata stats: {e}")
            return {}

def main():
    """Main function for testing"""
    upserter = StockMetadataUpserter()
    
    print("🔄 Starting Stock Metadata Upsert...")
    result = upserter.upsert_all_stocks_from_lists()
    
    print(f"✅ Upsert completed:")
    print(f"   Success: {result['success']}")
    print(f"   Failed: {result['failed']}")
    
    # Show stats
    stats = upserter.get_metadata_stats()
    if stats:
        print(f"\n📊 Database Stats:")
        print(f"   Total Stocks: {stats['total_stocks']}")
        print(f"   Exchange Distribution: {stats['exchange_counts']}")
        print(f"   Top Sectors: {stats['top_sectors']}")

if __name__ == "__main__":
    main()
