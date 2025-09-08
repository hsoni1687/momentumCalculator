"""
PostgreSQL Database module for Momentum Calculator
Supports both SQLite (fallback) and PostgreSQL (primary)
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
import sqlite3

# PostgreSQL imports
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import sqlalchemy
    from sqlalchemy import create_engine, text
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logging.warning("PostgreSQL libraries not available, falling back to SQLite")

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager that supports both PostgreSQL and SQLite"""
    
    def __init__(self, db_path=None, database_url=None):
        self.db_type = os.getenv('DB_TYPE', 'sqlite')
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.db_path = db_path
        
        if self.db_type == 'postgresql' and self.database_url and POSTGRES_AVAILABLE:
            self.use_postgres = True
            self.engine = create_engine(self.database_url)
            logger.info("Using PostgreSQL database")
        else:
            self.use_postgres = False
            if not self.db_path:
                import os
                current_dir = os.path.dirname(os.path.dirname(__file__))
                self.db_path = os.path.join(current_dir, 'data', 'stock_data.db')
            logger.info(f"Using SQLite database: {self.db_path}")
    
    def get_connection(self):
        """Get database connection"""
        if self.use_postgres:
            return self.engine.connect()
        else:
            return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        try:
            if self.use_postgres:
                with self.get_connection() as conn:
                    if params:
                        result = pd.read_sql_query(text(query), conn, params=params)
                    else:
                        result = pd.read_sql_query(text(query), conn)
                    return result
            else:
                with self.get_connection() as conn:
                    if params:
                        result = pd.read_sql_query(query, conn, params=params)
                    else:
                        result = pd.read_sql_query(query, conn)
                    return result
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return pd.DataFrame()
    
    def execute_insert(self, query: str, params: tuple = None) -> bool:
        """Execute insert/update query"""
        try:
            if self.use_postgres:
                with self.get_connection() as conn:
                    if params:
                        conn.execute(text(query), params)
                    else:
                        conn.execute(text(query))
                    conn.commit()
                    return True
            else:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error executing insert: {e}")
            return False
    
    def execute_many(self, query: str, params_list: List[tuple]) -> bool:
        """Execute batch insert/update"""
        try:
            if self.use_postgres:
                with self.get_connection() as conn:
                    conn.executemany(text(query), params_list)
                    conn.commit()
                    return True
            else:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.executemany(query, params_list)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error executing batch insert: {e}")
            return False
    
    def get_stock_metadata(self) -> pd.DataFrame:
        """Get stock metadata"""
        query = "SELECT * FROM stockMetadata ORDER BY market_cap DESC"
        return self.execute_query(query)
    
    def store_stock_metadata(self, metadata_df: pd.DataFrame) -> bool:
        """Store stock metadata"""
        if metadata_df.empty:
            return False
        
        # Convert DataFrame to list of tuples
        data = []
        for _, row in metadata_df.iterrows():
            data.append((
                row.get('stock', ''),
                row.get('name', ''),
                row.get('industry', ''),
                row.get('sector', ''),
                row.get('market_cap', 0),
                row.get('exchange', 'NSE')
            ))
        
        if self.use_postgres:
            query = """
                INSERT INTO stockMetadata (stock, name, industry, sector, market_cap, exchange)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (stock) DO UPDATE SET
                    name = EXCLUDED.name,
                    industry = EXCLUDED.industry,
                    sector = EXCLUDED.sector,
                    market_cap = EXCLUDED.market_cap,
                    exchange = EXCLUDED.exchange,
                    last_updated = CURRENT_TIMESTAMP
            """
        else:
            query = """
                INSERT OR REPLACE INTO stockMetadata 
                (stock, name, industry, sector, market_cap, exchange, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
        
        return self.execute_many(query, data)
    
    def store_price_data(self, stock: str, price_df: pd.DataFrame) -> bool:
        """Store price data for a stock"""
        if price_df.empty:
            return False
        
        # Prepare data for insertion
        data = []
        for date, row in price_df.iterrows():
            # Handle timezone-aware datetime
            if hasattr(date, 'date'):
                date_str = date.date()
            else:
                date_str = date
            
            data.append((
                stock,
                date_str,
                float(row.get('Open', 0)),
                float(row.get('High', 0)),
                float(row.get('Low', 0)),
                float(row.get('Close', 0)),
                int(row.get('Volume', 0))
            ))
        
        if self.use_postgres:
            query = """
                INSERT INTO tickerPrice (stock, date, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (stock, date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    created_at = CURRENT_TIMESTAMP
            """
        else:
            query = """
                INSERT OR REPLACE INTO tickerPrice 
                (stock, date, open, high, low, close, volume, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
        
        return self.execute_many(query, data)
    
    def get_price_data(self, stock: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get price data for a stock"""
        query = "SELECT * FROM tickerPrice WHERE stock = %s" if self.use_postgres else "SELECT * FROM tickerPrice WHERE stock = ?"
        params = [stock]
        
        if start_date:
            query += " AND date >= %s" if self.use_postgres else " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s" if self.use_postgres else " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        return self.execute_query(query, tuple(params))
    
    def get_all_price_data(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get all price data"""
        query = "SELECT * FROM tickerPrice WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= %s" if self.use_postgres else " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s" if self.use_postgres else " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY stock, date"
        
        return self.execute_query(query, tuple(params))
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            
            # Get table counts
            if self.use_postgres:
                tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                tables = self.execute_query(tables_query)['table_name'].tolist()
            else:
                tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
                tables = self.execute_query(tables_query)['name'].tolist()
            
            stats['tables'] = tables
            
            # Get record counts
            record_counts = {}
            for table in tables:
                count_query = f"SELECT COUNT(*) as count FROM {table}"
                result = self.execute_query(count_query)
                if not result.empty:
                    record_counts[table] = result['count'].iloc[0]
            
            stats['record_counts'] = record_counts
            
            # Get unique stocks with price data
            unique_stocks_query = "SELECT COUNT(DISTINCT stock) as count FROM tickerPrice"
            result = self.execute_query(unique_stocks_query)
            if not result.empty:
                stats['unique_stocks_with_price'] = result['count'].iloc[0]
            
            # Get date range
            date_range_query = "SELECT MIN(date) as min_date, MAX(date) as max_date FROM tickerPrice"
            result = self.execute_query(date_range_query)
            if not result.empty:
                stats['date_range'] = f"{result['min_date'].iloc[0]} to {result['max_date'].iloc[0]}"
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def close(self):
        """Close database connections"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
