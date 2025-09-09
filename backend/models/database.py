"""
Database service for backend
"""

import pandas as pd
import logging
from typing import Dict, List, Optional
import sys
import os

from .database_local import LocalDatabase
from config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for backend operations"""
    
    def __init__(self):
        """Initialize database connection"""
        self.db = LocalDatabase()
        logger.info("Database service initialized")
    
    def get_stock_metadata(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get stock metadata from database"""
        try:
            stocks_df = self.db.get_stock_metadata()
            if limit:
                stocks_df = stocks_df.head(limit)
            logger.info(f"Retrieved {len(stocks_df)} stocks metadata")
            return stocks_df
        except Exception as e:
            logger.error(f"Error getting stock metadata: {e}")
            return pd.DataFrame()
    
    def get_price_data(self, symbol: str) -> pd.DataFrame:
        """Get price data for a specific stock symbol"""
        try:
            price_data = self.db.get_price_data(symbol)
            if not price_data.empty:
                # Convert to expected format
                price_data = price_data.sort_values('date')
                price_data = price_data[['open', 'high', 'low', 'close', 'volume']]
                price_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                
                # Calculate Returns column
                price_data['Returns'] = price_data['Close'].pct_change()
                
            logger.info(f"Retrieved price data for {symbol}: {len(price_data)} records")
            return price_data
        except Exception as e:
            logger.error(f"Error getting price data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_historical_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Get historical data for multiple symbols"""
        historical_data = {}
        
        for symbol in symbols:
            price_data = self.get_price_data(symbol)
            if not price_data.empty:
                historical_data[symbol] = price_data
        
        logger.info(f"Retrieved historical data for {len(historical_data)} symbols")
        return historical_data
    
    def get_unique_industries(self) -> pd.DataFrame:
        """Get unique industries that have actual stocks with price data"""
        try:
            query = """
            SELECT DISTINCT sm.industry 
            FROM stockmetadata sm 
            WHERE sm.industry IS NOT NULL 
            AND EXISTS (SELECT 1 FROM tickerprice tp WHERE tp.stock = sm.stock)
            ORDER BY sm.industry
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting unique industries: {e}")
            return pd.DataFrame()
    
    def get_unique_sectors(self) -> pd.DataFrame:
        """Get unique sectors that have actual stocks with price data"""
        try:
            query = """
            SELECT DISTINCT sm.sector 
            FROM stockmetadata sm 
            WHERE sm.sector IS NOT NULL 
            AND EXISTS (SELECT 1 FROM tickerprice tp WHERE tp.stock = sm.stock)
            ORDER BY sm.sector
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting unique sectors: {e}")
            return pd.DataFrame()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            test_data = self.get_stock_metadata(limit=1)
            return not test_data.empty
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Dict = None) -> pd.DataFrame:
        """Execute a SQL query and return DataFrame"""
        try:
            return self.db.execute_query(query, params)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return pd.DataFrame()
    
    def get_connection(self):
        """Get database connection"""
        return self.db.get_connection()
