#!/usr/bin/env python3
"""
Local Database Adapter for PostgreSQL
Provides database connectivity and operations for local PostgreSQL development
"""

import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LocalDatabase:
    """Database adapter for local PostgreSQL development"""
    
    def __init__(self):
        """Initialize PostgreSQL connection"""
        # Get database URL from environment
        self.database_url = os.getenv('DATABASE_URL')
        
        if not self.database_url:
            # Fallback to individual components
            host = os.getenv('POSTGRES_HOST', 'localhost')
            port = os.getenv('POSTGRES_PORT', '5432')
            database = os.getenv('POSTGRES_DB', 'momentum_calc')
            username = os.getenv('POSTGRES_USER', 'momentum_user')
            password = os.getenv('POSTGRES_PASSWORD', 'momentum_password')
            
            self.database_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        try:
            self.engine = create_engine(self.database_url)
            logger.info("Connected to local PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def get_connection(self):
        """Get database connection"""
        return self.engine
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        try:
            with self.engine.connect() as conn:
                if params:
                    # Use psycopg2 style parameter binding
                    result = pd.read_sql(query, conn, params=params)
                else:
                    result = pd.read_sql(query, conn)
                return result
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return pd.DataFrame()
    
    def get_stock_metadata(self, industry_filter: str = None, sector_filter: str = None) -> pd.DataFrame:
        """Get stock metadata with optional filters"""
        try:
            query = "SELECT * FROM stockmetadata WHERE 1=1"
            params = []
            
            if industry_filter:
                query += " AND industry = %s"
                params.append(industry_filter)
            if sector_filter:
                query += " AND sector = %s"
                params.append(sector_filter)
            
            query += " ORDER BY market_cap DESC"
            
            return self.execute_query(query, tuple(params))
        except Exception as e:
            logger.error(f"Error getting stock metadata: {e}")
            return pd.DataFrame()
    
    def get_price_data(self, stock_symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get price data for a specific stock"""
        try:
            query = "SELECT * FROM tickerprice WHERE stock = %s"
            params = [stock_symbol]
            
            if start_date:
                query += " AND date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND date <= %s"
                params.append(end_date)
            
            query += " ORDER BY date"
            
            return self.execute_query(query, tuple(params))
        except Exception as e:
            logger.error(f"Error getting price data for {stock_symbol}: {e}")
            return pd.DataFrame()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            
            # Get stock metadata count
            metadata_result = self.execute_query("SELECT COUNT(*) as count FROM stockmetadata")
            stats['unique_stocks_with_price'] = metadata_result['count'].iloc[0] if not metadata_result.empty else 0
            
            # Get price data count
            price_result = self.execute_query("SELECT COUNT(*) as count FROM tickerprice")
            stats['record_counts'] = {'tickerprice': price_result['count'].iloc[0] if not price_result.empty else 0}
            
            # Get momentum scores count
            momentum_result = self.execute_query("SELECT COUNT(*) as count FROM momentumscores")
            stats['momentum_scores_count'] = momentum_result['count'].iloc[0] if not momentum_result.empty else 0
            
            # Get date range
            date_result = self.execute_query("SELECT MIN(date) as min_date, MAX(date) as max_date FROM tickerprice")
            if not date_result.empty:
                min_date = date_result['min_date'].iloc[0]
                max_date = date_result['max_date'].iloc[0]
                stats['date_range'] = f"{min_date} to {max_date}"
            
            stats['tables'] = ['stockmetadata', 'tickerprice', 'momentumscores']
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def get_momentum_scores_today(self) -> pd.DataFrame:
        """Get momentum scores for today"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            query = """
                SELECT ms.*, sm.company_name, sm.market_cap, sm.sector, sm.industry
                FROM momentumscores ms
                JOIN stockmetadata sm ON ms.stock = sm.stock
                WHERE ms.calculated_date = %s
                ORDER BY ms.total_score DESC
            """
            result = self.execute_query(query, (today,))
            
            if result.empty:
                # Fallback to most recent scores
                query = """
                    SELECT ms.*, sm.company_name, sm.market_cap, sm.sector, sm.industry
                    FROM momentumscores ms
                    JOIN stockmetadata sm ON ms.stock = sm.stock
                    ORDER BY ms.calculated_date DESC, ms.total_score DESC
                    LIMIT 1000
                """
                result = self.execute_query(query)
            
            return result
        except Exception as e:
            logger.error(f"Error getting momentum scores: {e}")
            return pd.DataFrame()
    
    def store_momentum_scores(self, stock_symbol: str, momentum_data: Dict[str, Any]) -> bool:
        """Store momentum scores for a stock"""
        try:
            with self.engine.connect() as conn:
                # Prepare data for insertion
                data = {
                    'stock': stock_symbol,
                    'total_score': momentum_data.get('total_score', 0),
                    'momentum_12_2': momentum_data.get('momentum_12_2', 0),
                    'fip_quality': momentum_data.get('fip_quality', 0),
                    'raw_momentum_6m': momentum_data.get('raw_momentum_6m', 0),
                    'raw_momentum_3m': momentum_data.get('raw_momentum_3m', 0),
                    'raw_momentum_1m': momentum_data.get('raw_momentum_1m', 0),
                    'volatility_adjusted': momentum_data.get('volatility_adjusted', 0),
                    'smooth_momentum': momentum_data.get('smooth_momentum', 0),
                    'consistency_score': momentum_data.get('consistency_score', 0),
                    'trend_strength': momentum_data.get('trend_strength', 0),
                    'calculated_date': datetime.now().strftime('%Y-%m-%d')
                }
                
                # Use INSERT ... ON CONFLICT for upsert
                query = """
                    INSERT INTO momentumscores 
                    (stock, total_score, momentum_12_2, fip_quality, raw_momentum_6m, 
                     raw_momentum_3m, raw_momentum_1m, volatility_adjusted, smooth_momentum, 
                     consistency_score, trend_strength, calculated_date)
                    VALUES (%(stock)s, %(total_score)s, %(momentum_12_2)s, %(fip_quality)s, 
                            %(raw_momentum_6m)s, %(raw_momentum_3m)s, %(raw_momentum_1m)s, 
                            %(volatility_adjusted)s, %(smooth_momentum)s, %(consistency_score)s, 
                            %(trend_strength)s, %(calculated_date)s)
                    ON CONFLICT (stock) 
                    DO UPDATE SET
                        total_score = EXCLUDED.total_score,
                        momentum_12_2 = EXCLUDED.momentum_12_2,
                        fip_quality = EXCLUDED.fip_quality,
                        raw_momentum_6m = EXCLUDED.raw_momentum_6m,
                        raw_momentum_3m = EXCLUDED.raw_momentum_3m,
                        raw_momentum_1m = EXCLUDED.raw_momentum_1m,
                        volatility_adjusted = EXCLUDED.volatility_adjusted,
                        smooth_momentum = EXCLUDED.smooth_momentum,
                        consistency_score = EXCLUDED.consistency_score,
                        trend_strength = EXCLUDED.trend_strength,
                        calculated_date = EXCLUDED.calculated_date,
                        created_at = NOW()
                """
                
                conn.execute(text(query), data)
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error storing momentum scores for {stock_symbol}: {e}")
            return False
    
    def get_available_industries(self) -> list:
        """Get list of available industries"""
        try:
            result = self.execute_query("SELECT DISTINCT industry FROM stockmetadata WHERE industry IS NOT NULL ORDER BY industry")
            return result['industry'].tolist() if not result.empty else []
        except Exception as e:
            logger.error(f"Error getting industries: {e}")
            return []
    
    def get_available_sectors(self) -> list:
        """Get list of available sectors"""
        try:
            result = self.execute_query("SELECT DISTINCT sector FROM stockmetadata WHERE sector IS NOT NULL ORDER BY sector")
            return result['sector'].tolist() if not result.empty else []
        except Exception as e:
            logger.error(f"Error getting sectors: {e}")
            return []
