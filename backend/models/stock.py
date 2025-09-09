"""
Stock service for backend
"""

import pandas as pd
import logging
from typing import Dict, List, Optional
from .database import DatabaseService

logger = logging.getLogger(__name__)

class StockService:
    """Stock service for backend operations"""
    
    def __init__(self, database_service: DatabaseService):
        """Initialize with database service"""
        self.db_service = database_service
        self.cache = {}
        logger.info("Stock service initialized")
    
    def get_stocks(self, limit: int = 50, industry: Optional[str] = None, 
                   sector: Optional[str] = None) -> pd.DataFrame:
        """Get stocks with optional filtering"""
        cache_key = f"stocks_{limit}_{industry}_{sector}"
        
        if cache_key in self.cache:
            logger.info(f"Returning cached stocks data: {cache_key}")
            return self.cache[cache_key]
        
        try:
            # Get ALL stock metadata first (no limit)
            all_stocks_df = self.db_service.get_stock_metadata()
            
            if all_stocks_df.empty:
                logger.warning("No stock data found in database")
                return pd.DataFrame()
            
            # Apply filters
            if industry:
                all_stocks_df = all_stocks_df[all_stocks_df['industry'].str.contains(industry, case=False, na=False)]
                logger.info(f"Filtered by industry '{industry}': {len(all_stocks_df)} stocks")
            
            if sector:
                all_stocks_df = all_stocks_df[all_stocks_df['sector'].str.contains(sector, case=False, na=False)]
                logger.info(f"Filtered by sector '{sector}': {len(all_stocks_df)} stocks")
            
            # Apply limit after filtering
            if limit and len(all_stocks_df) > limit:
                stocks_df = all_stocks_df.head(limit)
            else:
                stocks_df = all_stocks_df
            
            # Cache the result
            self.cache[cache_key] = stocks_df
            logger.info(f"Retrieved {len(stocks_df)} stocks")
            return stocks_df
            
        except Exception as e:
            logger.error(f"Error getting stocks: {e}")
            return pd.DataFrame()
    
    def get_historical_data(self, stocks_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Get historical data for stocks"""
        symbols = stocks_df['stock'].tolist()
        return self.db_service.get_historical_data(symbols)
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed information for a specific stock"""
        try:
            stocks_df = self.db_service.get_stock_metadata()
            stock_info = stocks_df[stocks_df['stock'] == symbol]
            
            if not stock_info.empty:
                return stock_info.iloc[0].to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error getting stock info for {symbol}: {e}")
            return None
    
    def get_unique_industries(self) -> List[str]:
        """Get list of unique industries"""
        try:
            industries_df = self.db_service.get_unique_industries()
            industries = industries_df['industry'].dropna().unique().tolist()
            industries.sort()
            logger.info(f"Retrieved {len(industries)} unique industries")
            return industries
        except Exception as e:
            logger.error(f"Error getting unique industries: {e}")
            return []
    
    def get_unique_sectors(self) -> List[str]:
        """Get list of unique sectors"""
        try:
            sectors_df = self.db_service.get_unique_sectors()
            sectors = sectors_df['sector'].dropna().unique().tolist()
            sectors.sort()
            logger.info(f"Retrieved {len(sectors)} unique sectors")
            return sectors
        except Exception as e:
            logger.error(f"Error getting unique sectors: {e}")
            return []
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        logger.info("Stock service cache cleared")
