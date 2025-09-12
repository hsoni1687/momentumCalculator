"""
Local database implementation for strategy service
"""

import pandas as pd
import psycopg2
import logging
from typing import Dict, List, Optional, Any
from config.settings import settings
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

class LocalDatabase:
    """Local database connection for strategy service"""
    
    def __init__(self):
        """Initialize database connection"""
        self.connection_params = {
            'host': settings.database_host,
            'port': settings.database_port,
            'database': settings.database_name,
            'user': settings.database_user,
            'password': settings.database_password
        }
        
        # Create SQLAlchemy engine for compatibility
        connection_string = f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"
        self.engine = create_engine(connection_string)
        
        logger.info("Local database initialized")
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.connection_params)
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return pd.DataFrame()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute update query and return number of affected rows"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Error executing update: {e}")
            return 0
    
    def get_stock_metadata(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get stock metadata from database"""
        query = """
        SELECT stock, company_name, sector, industry, market_cap, market_cap_rank, 
               current_price, last_price_date
        FROM stockmetadata 
        ORDER BY market_cap_rank
        """
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query)
    
    def get_price_data(self, symbol: str) -> pd.DataFrame:
        """Get price data for a specific stock symbol"""
        query = """
        SELECT stock, date, open, high, low, close, volume
        FROM tickerprice 
        WHERE stock = %s
        ORDER BY date
        """
        return self.execute_query(query, (symbol,))
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
