"""
Momentum Scores Storage Manager
Handles storage and retrieval of pre-calculated momentum scores
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
from sqlalchemy import text
from config.database_queries import DatabaseQueries

logger = logging.getLogger(__name__)

class MomentumStorage:
    """Manages storage and retrieval of pre-calculated momentum scores"""
    
    def __init__(self, database_service):
        """Initialize momentum storage with database service"""
        self.db = database_service
    
    def store_momentum_scores(self, momentum_df: pd.DataFrame, calculation_date: date = None) -> bool:
        """
        Store momentum scores in the database
        
        Args:
            momentum_df: DataFrame with momentum scores
            calculation_date: Date for the calculation (defaults to today)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if calculation_date is None:
            calculation_date = date.today()
        
        try:
            if momentum_df.empty:
                logger.warning("No momentum scores to store")
                return False
            
            # Prepare data for insertion
            records = []
            for _, row in momentum_df.iterrows():
                record = {
                    'stock': row['stock'],
                    'calculation_date': calculation_date,
                    'momentum_score': row.get('momentum_score'),
                    'fip_quality': row.get('fip_quality'),
                    'raw_momentum_12_2': row.get('raw_momentum_12_2'),
                    'true_momentum_6m': row.get('true_momentum_6m'),
                    'true_momentum_3m': row.get('true_momentum_3m'),
                    'true_momentum_1m': row.get('true_momentum_1m'),
                    'raw_return_6m': row.get('raw_return_6m'),
                    'raw_return_3m': row.get('raw_return_3m'),
                    'raw_return_1m': row.get('raw_return_1m'),
                    'raw_momentum_6m': row.get('raw_momentum_6m'),
                    'raw_momentum_3m': row.get('raw_momentum_3m'),
                    'raw_momentum_1m': row.get('raw_momentum_1m')
                }
                records.append(record)
            
            # Insert records using pandas to_sql with if_exists='append'
            # First, create a DataFrame from records
            records_df = pd.DataFrame(records)
            
            # Use the database connection to insert
            with self.db.get_connection().connect() as conn:
                # Use ON CONFLICT to handle duplicates
                for record in records:
                    query = text("""
                        INSERT INTO momentum_scores 
                        (stock, calculation_date, momentum_score, fip_quality, raw_momentum_12_2,
                         true_momentum_6m, true_momentum_3m, true_momentum_1m, raw_return_6m,
                         raw_return_3m, raw_return_1m, raw_momentum_6m, raw_momentum_3m, raw_momentum_1m)
                        VALUES (:stock, :calculation_date, :momentum_score, :fip_quality, :raw_momentum_12_2,
                                :true_momentum_6m, :true_momentum_3m, :true_momentum_1m, :raw_return_6m,
                                :raw_return_3m, :raw_return_1m, :raw_momentum_6m, :raw_momentum_3m, :raw_momentum_1m)
                        ON CONFLICT (stock, calculation_date) 
                        DO UPDATE SET
                            momentum_score = EXCLUDED.momentum_score,
                            fip_quality = EXCLUDED.fip_quality,
                            raw_momentum_12_2 = EXCLUDED.raw_momentum_12_2,
                            true_momentum_6m = EXCLUDED.true_momentum_6m,
                            true_momentum_3m = EXCLUDED.true_momentum_3m,
                            true_momentum_1m = EXCLUDED.true_momentum_1m,
                            raw_return_6m = EXCLUDED.raw_return_6m,
                            raw_return_3m = EXCLUDED.raw_return_3m,
                            raw_return_1m = EXCLUDED.raw_return_1m,
                            raw_momentum_6m = EXCLUDED.raw_momentum_6m,
                            raw_momentum_3m = EXCLUDED.raw_momentum_3m,
                            raw_momentum_1m = EXCLUDED.raw_momentum_1m,
                            created_at = CURRENT_TIMESTAMP
                    """)
                    conn.execute(query, record)
                conn.commit()
            
            logger.info(f"Stored {len(records)} momentum scores for {calculation_date}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing momentum scores: {e}")
            return False
    
    def get_momentum_scores_for_date(self, calculation_date: date = None, limit: int = None, industry: str = None, sector: str = None) -> pd.DataFrame:
        """
        Get momentum scores for a specific date
        
        Args:
            calculation_date: Date to get scores for (defaults to today)
            limit: Maximum number of records to return
        
        Returns:
            pd.DataFrame: Momentum scores for the date
        """
        if calculation_date is None:
            calculation_date = date.today()
        
        try:
            query = """
                SELECT ms.*, sm.company_name, sm.sector, sm.industry, sm.last_price_date, sm.market_cap
                FROM momentum_scores ms
                JOIN stockmetadata sm ON ms.stock = sm.stock
                WHERE ms.calculation_date = %s
            """
            
            params = [calculation_date]
            
            # Add industry filter if specified
            if industry:
                query += " AND sm.industry = %s"
                params.append(industry)
            
            # Add sector filter if specified
            if sector:
                query += " AND sm.sector = %s"
                params.append(sector)
            
            query += " ORDER BY sm.market_cap DESC, ms.momentum_score DESC"
            
            if limit:
                query += " LIMIT %s"
                params.append(limit)
            
            result = self.db.execute_query(query, tuple(params))
            logger.debug(f"Retrieved {len(result)} momentum scores for {calculation_date}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting momentum scores for date {calculation_date}: {e}")
            return pd.DataFrame()
    
    def get_latest_momentum_date(self) -> Optional[date]:
        """
        Get the latest date for which momentum scores are available
        
        Returns:
            Optional[date]: Latest date with momentum scores, or None if none exist
        """
        try:
            query = "SELECT MAX(calculation_date) as latest_date FROM momentum_scores"
            result = self.db.execute_query(query)
            
            if not result.empty and result.iloc[0]['latest_date'] is not None:
                latest_date = result.iloc[0]['latest_date']
                if hasattr(latest_date, 'date'):
                    latest_date = latest_date.date()
                logger.info(f"Latest momentum scores available for date: {latest_date}")
                return latest_date
            else:
                logger.warning("No momentum scores found in database")
                return None
                
        except Exception as e:
            logger.error(f"Error getting latest momentum date: {e}")
            return None
    
    def get_best_momentum_date(self) -> Optional[date]:
        """
        Get the best date for momentum scores (most recent date with most stocks)
        
        Returns:
            Optional[date]: Best date with momentum scores, or None if none exist
        """
        try:
            # Get all dates with their stock counts, ordered by date desc
            query = """
            SELECT calculation_date, COUNT(*) as stock_count 
            FROM momentum_scores 
            GROUP BY calculation_date 
            ORDER BY calculation_date DESC
            """
            result = self.db.execute_query(query)
            
            if result.empty:
                logger.warning("No momentum scores found in database")
                return None
            
            # Find the most recent date with the most stocks
            # Start with the latest date and work backwards
            max_stocks = 0
            best_date = None
            
            for _, row in result.iterrows():
                date_val = row['calculation_date']
                stock_count = row['stock_count']
                
                if hasattr(date_val, 'date'):
                    date_val = date_val.date()
                
                # Use this date if it has more stocks than what we've seen
                if stock_count > max_stocks:
                    max_stocks = stock_count
                    best_date = date_val
                
                # If we have a good number of stocks (e.g., > 1000), use this date
                if stock_count > 1000:
                    logger.info(f"Found good momentum data for {date_val}: {stock_count} stocks")
                    return date_val
            
            if best_date:
                logger.info(f"Using best momentum date: {best_date} with {max_stocks} stocks")
                return best_date
            else:
                logger.warning("No suitable momentum scores found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting best momentum date: {e}")
            return None
    
    def get_stocks_needing_momentum_calculation(self, limit: int, calculation_date: date = None) -> List[str]:
        """
        Get stocks that need momentum calculation (don't have scores for today)
        
        Args:
            limit: Maximum number of stocks to return
            calculation_date: Date to check for (defaults to today)
        
        Returns:
            List[str]: List of stock symbols that need momentum calculation
        """
        if calculation_date is None:
            calculation_date = date.today()
        
        try:
            query = """
                SELECT sm.stock
                FROM stockmetadata sm
                LEFT JOIN momentum_scores ms ON sm.stock = ms.stock AND ms.calculation_date = %s
                WHERE ms.stock IS NULL
                ORDER BY sm.market_cap DESC NULLS LAST
                LIMIT %s
            """
            
            result = self.db.execute_query(query, (calculation_date, limit))
            stocks = result['stock'].tolist() if not result.empty else []
            
            logger.info(f"Found {len(stocks)} stocks needing momentum calculation for {calculation_date}")
            return stocks
            
        except Exception as e:
            logger.error(f"Error getting stocks needing momentum calculation: {e}")
            return []
    
    def get_top_momentum_stocks(self, top_n: int = 10, calculation_date: date = None) -> pd.DataFrame:
        """
        Get top momentum stocks for a specific date
        
        Args:
            top_n: Number of top stocks to return
            calculation_date: Date to get scores for (defaults to today)
        
        Returns:
            pd.DataFrame: Top momentum stocks
        """
        if calculation_date is None:
            calculation_date = date.today()
        
        try:
            query = """
                SELECT ms.*, sm.company_name, sm.sector, sm.industry, sm.last_price_date
                FROM momentum_scores ms
                JOIN stockmetadata sm ON ms.stock = sm.stock
                WHERE ms.calculation_date = %s
                ORDER BY ms.momentum_score DESC
                LIMIT %s
            """
            
            result = self.db.execute_query(query, (calculation_date, top_n))
            logger.info(f"Retrieved top {len(result)} momentum stocks for {calculation_date}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting top momentum stocks: {e}")
            return pd.DataFrame()
    
    def get_momentum_statistics(self, calculation_date: date = None) -> Dict:
        """
        Get statistics about momentum calculations for a date
        
        Args:
            calculation_date: Date to get statistics for (defaults to today)
        
        Returns:
            Dict: Statistics about momentum calculations
        """
        if calculation_date is None:
            calculation_date = date.today()
        
        try:
            query = """
                SELECT 
                    COUNT(*) as total_calculated,
                    AVG(momentum_score) as avg_momentum,
                    MAX(momentum_score) as max_momentum,
                    MIN(momentum_score) as min_momentum
                FROM momentum_scores 
                WHERE calculation_date = %s
            """
            
            result = self.db.execute_query(query, (calculation_date,))
            
            if not result.empty:
                stats = result.iloc[0].to_dict()
                logger.info(f"Momentum statistics for {calculation_date}: {stats}")
                return stats
            else:
                return {"total_calculated": 0, "avg_momentum": 0, "max_momentum": 0, "min_momentum": 0}
                
        except Exception as e:
            logger.error(f"Error getting momentum statistics: {e}")
            return {"total_calculated": 0, "avg_momentum": 0, "max_momentum": 0, "min_momentum": 0}
