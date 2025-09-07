"""
Database module for storing and retrieving stock price data
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

class StockDatabase:
    def __init__(self, db_path="stock_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tickerPrice table
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
                
                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_stock_date 
                    ON tickerPrice(stock, date)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_stock 
                    ON tickerPrice(stock)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_date 
                    ON tickerPrice(date)
                ''')
                
                # Create stock metadata table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS stockMetadata (
                        stock TEXT PRIMARY KEY,
                        company_name TEXT,
                        market_cap REAL,
                        sector TEXT,
                        exchange TEXT,
                        industry TEXT,
                        dividend_yield REAL,
                        roce REAL,
                        roe REAL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create momentum scores table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS momentumScores (
                        stock TEXT PRIMARY KEY,
                        total_score REAL,
                        momentum_12_2 REAL,
                        fip_quality REAL,
                        raw_momentum_6m REAL,
                        raw_momentum_3m REAL,
                        raw_momentum_1m REAL,
                        volatility_adjusted REAL,
                        smooth_momentum REAL,
                        consistency_score REAL,
                        trend_strength REAL,
                        calculated_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Add new columns to existing tables if they don't exist
                self._add_new_columns_if_not_exist()
                self._add_momentum_columns_if_not_exist()
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def store_price_data(self, stock_symbol, price_data):
        """Store price data for a stock"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Prepare data for insertion
                data_to_insert = []
                for date, row in price_data.iterrows():
                    data_to_insert.append((
                        stock_symbol,
                        date.strftime('%Y-%m-%d'),
                        row.get('Open', None),
                        row.get('High', None),
                        row.get('Low', None),
                        row.get('Close', None),
                        row.get('Volume', None)
                    ))
                
                # Insert data (ignore duplicates)
                cursor = conn.cursor()
                cursor.executemany('''
                    INSERT OR IGNORE INTO tickerPrice 
                    (stock, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', data_to_insert)
                
                conn.commit()
                logger.info(f"Stored {len(data_to_insert)} records for {stock_symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing price data for {stock_symbol}: {e}")
            return False
    
    def get_price_data(self, stock_symbol, start_date=None, end_date=None):
        """Retrieve price data for a stock"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT date, open, high, low, close, volume
                    FROM tickerPrice
                    WHERE stock = ?
                '''
                params = [stock_symbol]
                
                if start_date:
                    query += ' AND date >= ?'
                    params.append(start_date.strftime('%Y-%m-%d'))
                
                if end_date:
                    query += ' AND date <= ?'
                    params.append(end_date.strftime('%Y-%m-%d'))
                
                query += ' ORDER BY date'
                
                df = pd.read_sql_query(query, conn, params=params)
                
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    # Convert columns to proper numeric types
                    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                    for col in numeric_columns:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    logger.info(f"Retrieved {len(df)} records for {stock_symbol}")
                else:
                    logger.warning(f"No data found for {stock_symbol}")
                
                return df
                
        except Exception as e:
            logger.error(f"Error retrieving price data for {stock_symbol}: {e}")
            return pd.DataFrame()
    
    def store_stock_metadata(self, stock_data):
        """Store stock metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for _, stock in stock_data.iterrows():
                    cursor.execute('''
                        INSERT OR REPLACE INTO stockMetadata 
                        (stock, company_name, market_cap, sector, exchange)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        stock['symbol'],
                        stock['company_name'],
                        stock['market_cap'],
                        stock['sector'],
                        stock['exchange']
                    ))
                
                conn.commit()
                logger.info(f"Stored metadata for {len(stock_data)} stocks")
                return True
                
        except Exception as e:
            logger.error(f"Error storing stock metadata: {e}")
            return False
    
    def get_stock_metadata(self):
        """Retrieve all stock metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query('''
                    SELECT stock as symbol, company_name, market_cap, sector, exchange,
                           industry, dividend_yield, roce, roe
                    FROM stockMetadata
                    ORDER BY market_cap DESC
                ''', conn)
                
                logger.info(f"Retrieved metadata for {len(df)} stocks")
                return df
                
        except Exception as e:
            logger.error(f"Error retrieving stock metadata: {e}")
            return pd.DataFrame()
    
    def get_latest_date(self, stock_symbol):
        """Get the latest date for which we have data for a stock"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT MAX(date) FROM tickerPrice WHERE stock = ?
                ''', (stock_symbol,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    return datetime.strptime(result[0], '%Y-%m-%d').date()
                return None
                
        except Exception as e:
            logger.error(f"Error getting latest date for {stock_symbol}: {e}")
            return None
    
    def get_stocks_needing_update(self, days_threshold=1):
        """Get stocks that need data updates"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    SELECT s.stock, s.last_updated
                    FROM stockMetadata s
                    LEFT JOIN (
                        SELECT stock, MAX(date) as latest_date
                        FROM tickerPrice
                        GROUP BY stock
                    ) p ON s.stock = p.stock
                    WHERE p.latest_date IS NULL OR p.latest_date < ?
                    ORDER BY s.market_cap DESC
                ''', (cutoff_date,))
                
                results = cursor.fetchall()
                return [row[0] for row in results]
                
        except Exception as e:
            logger.error(f"Error getting stocks needing update: {e}")
            return []
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total records
                cursor.execute('SELECT COUNT(*) FROM tickerPrice')
                total_records = cursor.fetchone()[0]
                
                # Get unique stocks
                cursor.execute('SELECT COUNT(DISTINCT stock) FROM tickerPrice')
                unique_stocks = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute('SELECT MIN(date), MAX(date) FROM tickerPrice')
                date_range = cursor.fetchone()
                
                # Get database size
                db_size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
                
                return {
                    'total_records': total_records,
                    'unique_stocks': unique_stocks,
                    'date_range': date_range,
                    'db_size_mb': round(db_size, 2)
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep=365):
        """Clean up old data beyond specified days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
                
                cursor.execute('DELETE FROM tickerPrice WHERE date < ?', (cutoff_date,))
                deleted_rows = cursor.rowcount
                
                conn.commit()
                logger.info(f"Cleaned up {deleted_rows} old records")
                return deleted_rows
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
    
    def execute_query(self, query, params=None):
        """Execute a custom SQL query and return results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = cursor.fetchall()
                return results
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return None
    
    def store_momentum_scores(self, stock_symbol, momentum_data):
        """Store momentum scores for a stock"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert or replace momentum scores
                cursor.execute('''
                    INSERT OR REPLACE INTO momentumScores 
                    (stock, total_score, momentum_12_2, fip_quality, raw_momentum_6m, raw_momentum_3m, raw_momentum_1m,
                     volatility_adjusted, smooth_momentum, consistency_score, trend_strength, calculated_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock_symbol,
                    momentum_data.get('total_score', 0),
                    momentum_data.get('momentum_12_2', 0),
                    momentum_data.get('fip_quality', 0),
                    momentum_data.get('raw_momentum_6m', 0),
                    momentum_data.get('raw_momentum_3m', 0),
                    momentum_data.get('raw_momentum_1m', 0),
                    momentum_data.get('volatility_adjusted', 0),
                    momentum_data.get('smooth_momentum', 0),
                    momentum_data.get('consistency_score', 0),
                    momentum_data.get('trend_strength', 0),
                    datetime.now().strftime('%Y-%m-%d')
                ))
                
                conn.commit()
                logger.info(f"Stored momentum scores for {stock_symbol}")
                
        except Exception as e:
            logger.error(f"Error storing momentum scores for {stock_symbol}: {e}")
    
    def get_momentum_scores(self, stock_symbol=None):
        """Get momentum scores for a stock or all stocks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if stock_symbol:
                    query = "SELECT * FROM momentumScores WHERE stock = ?"
                    params = (stock_symbol,)
                else:
                    query = "SELECT * FROM momentumScores ORDER BY total_score DESC"
                    params = None
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            logger.error(f"Error getting momentum scores: {e}")
            return pd.DataFrame()
    
    def get_momentum_scores_today(self):
        """Get momentum scores calculated today"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM momentumScores WHERE calculated_date = ? ORDER BY total_score DESC"
                df = pd.read_sql_query(query, conn, params=(today,))
                return df
                
        except Exception as e:
            logger.error(f"Error getting today's momentum scores: {e}")
            return pd.DataFrame()
    
    def get_latest_date_for_stock(self, stock_symbol):
        """Get the latest date for which we have price data for a stock"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT MAX(date) FROM tickerPrice WHERE stock = ?
                ''', (stock_symbol,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    return datetime.strptime(result[0], '%Y-%m-%d').date()
                return None
                
        except Exception as e:
            logger.error(f"Error getting latest date for {stock_symbol}: {e}")
            return None
    
    def _add_new_columns_if_not_exist(self):
        """Add new columns to existing stockMetadata table if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stockMetadata'")
                if not cursor.fetchone():
                    return
                
                # Get existing columns
                cursor.execute("PRAGMA table_info(stockMetadata)")
                existing_columns = [row[1] for row in cursor.fetchall()]
                
                # Add new columns if they don't exist
                new_columns = {
                    'industry': 'TEXT',
                    'dividend_yield': 'REAL',
                    'roce': 'REAL',
                    'roe': 'REAL'
                }
                
                for column_name, column_type in new_columns.items():
                    if column_name not in existing_columns:
                        cursor.execute(f"ALTER TABLE stockMetadata ADD COLUMN {column_name} {column_type}")
                        logger.info(f"Added column {column_name} to stockMetadata table")
                
        except Exception as e:
            logger.error(f"Error adding new columns: {e}")
    
    def _add_momentum_columns_if_not_exist(self):
        """Add new columns to existing momentumScores table if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='momentumScores'")
                if not cursor.fetchone():
                    return
                
                # Get existing columns
                cursor.execute("PRAGMA table_info(momentumScores)")
                existing_columns = [row[1] for row in cursor.fetchall()]
                
                # Add new columns if they don't exist
                new_columns = {
                    'momentum_12_2': 'REAL',
                    'fip_quality': 'REAL'
                }
                
                for column_name, column_type in new_columns.items():
                    if column_name not in existing_columns:
                        cursor.execute(f"ALTER TABLE momentumScores ADD COLUMN {column_name} {column_type}")
                        logger.info(f"Added column {column_name} to momentumScores table")
                
        except Exception as e:
            logger.error(f"Error adding momentum columns: {e}")
    
    def update_stock_metadata(self, stock_symbol, metadata_dict):
        """Update stock metadata with new fields"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                update_fields = []
                values = []
                
                for field, value in metadata_dict.items():
                    if field in ['industry', 'dividend_yield', 'roce', 'roe', 'sector', 'company_name', 'market_cap', 'exchange']:
                        update_fields.append(f"{field} = ?")
                        values.append(value)
                
                if update_fields:
                    values.append(stock_symbol)
                    query = f"UPDATE stockMetadata SET {', '.join(update_fields)}, last_updated = CURRENT_TIMESTAMP WHERE stock = ?"
                    cursor.execute(query, values)
                    conn.commit()
                    logger.info(f"Updated metadata for {stock_symbol}")
                    
        except Exception as e:
            logger.error(f"Error updating metadata for {stock_symbol}: {e}")

if __name__ == "__main__":
    # Test the database
    db = StockDatabase()
    
    # Test storing sample data
    sample_data = pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [105, 106, 107],
        'Low': [99, 100, 101],
        'Close': [104, 105, 106],
        'Volume': [1000, 1100, 1200]
    }, index=pd.date_range('2024-01-01', periods=3))
    
    db.store_price_data('TEST', sample_data)
    
    # Test retrieving data
    retrieved_data = db.get_price_data('TEST')
    print("Retrieved data:")
    print(retrieved_data)
    
    # Get database stats
    stats = db.get_database_stats()
    print("\nDatabase stats:")
    print(stats)
