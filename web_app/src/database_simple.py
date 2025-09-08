"""
Simple database adapter for PostgreSQL
"""

import os
import pandas as pd
import logging
from typing import Dict, List, Any, Optional

# PostgreSQL imports
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import sqlalchemy
    from sqlalchemy import create_engine, text
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logging.warning("PostgreSQL libraries not available")

logger = logging.getLogger(__name__)

class SimpleDatabase:
    """Simple database manager for PostgreSQL"""
    
    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.engine = None
        
        if self.database_url and POSTGRES_AVAILABLE:
            try:
                self.engine = create_engine(self.database_url)
                logger.info("Connected to PostgreSQL database")
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                self.engine = None
        else:
            logger.warning("No PostgreSQL connection available")
    
    def get_connection(self):
        """Get database connection"""
        if self.engine:
            return self.engine.connect()
        else:
            raise Exception("No database connection available")
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        try:
            with self.get_connection() as conn:
                if params:
                    # Replace %s with :param0, :param1, etc.
                    param_query = query
                    for i, param in enumerate(params):
                        param_query = param_query.replace('%s', f':param{i}', 1)
                    
                    param_dict = {f'param{i}': param for i, param in enumerate(params)}
                    result = pd.read_sql_query(text(param_query), conn, params=param_dict)
                else:
                    result = pd.read_sql_query(text(query), conn)
                return result
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return pd.DataFrame()
    
    def get_stock_metadata(self) -> pd.DataFrame:
        """Get stock metadata"""
        query = "SELECT * FROM stockMetadata ORDER BY market_cap DESC"
        return self.execute_query(query)
    
    def get_price_data(self, stock: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get price data for a stock"""
        query = "SELECT * FROM tickerPrice WHERE stock = %s"
        params = [stock]
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        return self.execute_query(query, tuple(params))
    
    def get_all_price_data(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get all price data"""
        query = "SELECT * FROM tickerPrice WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY stock, date"
        
        return self.execute_query(query, tuple(params))
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            
            # Get table counts
            tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            tables = self.execute_query(tables_query)['table_name'].tolist()
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
    
    def get_momentum_scores_today(self):
        """Get momentum scores calculated today or most recent"""
        try:
            # First try to get today's scores
            query = "SELECT * FROM momentumScores WHERE DATE(calculated_at) = CURRENT_DATE"
            result = self.execute_query(query)
            
            # If no scores for today, get the most recent scores
            if result.empty:
                query = "SELECT * FROM momentumScores ORDER BY calculated_at DESC"
                result = self.execute_query(query)
            
            return result
        except Exception as e:
            logger.error(f"Error getting momentum scores: {e}")
            return pd.DataFrame()
    
    def store_momentum_scores(self, stock, momentum_score):
        """Store momentum scores for a stock"""
        try:
            query = """
                INSERT INTO momentumScores 
                (stock, total_score, raw_momentum_6m, raw_momentum_3m, raw_momentum_1m, 
                 volatility_adjusted_6m, volatility_adjusted_3m, volatility_adjusted_1m,
                 relative_strength_6m, relative_strength_3m, relative_strength_1m,
                 trend_score, volume_score, calculated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (stock) DO UPDATE SET
                    total_score = EXCLUDED.total_score,
                    raw_momentum_6m = EXCLUDED.raw_momentum_6m,
                    raw_momentum_3m = EXCLUDED.raw_momentum_3m,
                    raw_momentum_1m = EXCLUDED.raw_momentum_1m,
                    volatility_adjusted_6m = EXCLUDED.volatility_adjusted_6m,
                    volatility_adjusted_3m = EXCLUDED.volatility_adjusted_3m,
                    volatility_adjusted_1m = EXCLUDED.volatility_adjusted_1m,
                    relative_strength_6m = EXCLUDED.relative_strength_6m,
                    relative_strength_3m = EXCLUDED.relative_strength_3m,
                    relative_strength_1m = EXCLUDED.relative_strength_1m,
                    trend_score = EXCLUDED.trend_score,
                    volume_score = EXCLUDED.volume_score,
                    calculated_at = EXCLUDED.calculated_at
            """
            
            params = (
                stock,
                momentum_score.get('total_score', 0),
                momentum_score.get('raw_momentum_6m', 0),
                momentum_score.get('raw_momentum_3m', 0),
                momentum_score.get('raw_momentum_1m', 0),
                momentum_score.get('volatility_adjusted_6m', 0),
                momentum_score.get('volatility_adjusted_3m', 0),
                momentum_score.get('volatility_adjusted_1m', 0),
                momentum_score.get('relative_strength_6m', 0),
                momentum_score.get('relative_strength_3m', 0),
                momentum_score.get('relative_strength_1m', 0),
                momentum_score.get('trend_score', 0),
                momentum_score.get('volume_score', 0)
            )
            
            return self.execute_insert(query, params)
        except Exception as e:
            logger.error(f"Error storing momentum scores: {e}")
            return False

    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
