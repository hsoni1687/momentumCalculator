#!/usr/bin/env python3
"""
Supabase Database Adapter
Provides database connectivity and operations for Supabase
"""

import os
import pandas as pd
from supabase import create_client, Client
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SupabaseDatabase:
    """Database adapter for Supabase"""
    
    def __init__(self):
        """Initialize Supabase connection"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
        
        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Connected to Supabase database")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
    
    def get_connection(self):
        """Get database connection (for compatibility)"""
        return self.client
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        try:
            # For Supabase, we'll use the table methods instead of raw SQL
            # This is a simplified version - you might need to implement specific query methods
            logger.warning("Raw SQL queries not directly supported in Supabase client. Use specific table methods.")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return pd.DataFrame()
    
    def get_stock_metadata(self, industry_filter: str = None, sector_filter: str = None) -> pd.DataFrame:
        """Get stock metadata with optional filters"""
        try:
            query = self.client.table('stockMetadata').select('*')
            
            if industry_filter:
                query = query.eq('industry', industry_filter)
            if sector_filter:
                query = query.eq('sector', sector_filter)
            
            result = query.execute()
            return pd.DataFrame(result.data)
        except Exception as e:
            logger.error(f"Error getting stock metadata: {e}")
            return pd.DataFrame()
    
    def get_price_data(self, stock_symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get price data for a specific stock"""
        try:
            query = self.client.table('tickerPrice').select('*').eq('stock', stock_symbol)
            
            if start_date:
                query = query.gte('date', start_date)
            if end_date:
                query = query.lte('date', end_date)
            
            query = query.order('date')
            result = query.execute()
            return pd.DataFrame(result.data)
        except Exception as e:
            logger.error(f"Error getting price data for {stock_symbol}: {e}")
            return pd.DataFrame()
    
    def get_all_price_data(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get all price data"""
        try:
            query = self.client.table('tickerPrice').select('*')
            
            if start_date:
                query = query.gte('date', start_date)
            if end_date:
                query = query.lte('date', end_date)
            
            query = query.order('stock', 'date')
            result = query.execute()
            return pd.DataFrame(result.data)
        except Exception as e:
            logger.error(f"Error getting all price data: {e}")
            return pd.DataFrame()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            
            # Get stock metadata count
            metadata_result = self.client.table('stockMetadata').select('stock', count='exact').execute()
            stats['unique_stocks_with_price'] = metadata_result.count
            
            # Get price data count
            price_result = self.client.table('tickerPrice').select('id', count='exact').execute()
            stats['record_counts'] = {'tickerprice': price_result.count}
            
            # Get momentum scores count
            momentum_result = self.client.table('momentumScores').select('stock', count='exact').execute()
            stats['momentum_scores_count'] = momentum_result.count
            
            # Get date range
            date_result = self.client.table('tickerPrice').select('date').order('date', desc=False).limit(1).execute()
            if date_result.data:
                min_date = date_result.data[0]['date']
            
            date_result = self.client.table('tickerPrice').select('date').order('date', desc=True).limit(1).execute()
            if date_result.data:
                max_date = date_result.data[0]['date']
                stats['date_range'] = f"{min_date} to {max_date}"
            
            stats['tables'] = ['stockMetadata', 'tickerPrice', 'momentumScores']
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def get_momentum_scores_today(self):
        """Get momentum scores calculated today or most recent"""
        try:
            # Get today's scores first
            today = datetime.now().date()
            result = self.client.table('momentumScores').select('*').gte('calculated_at', str(today)).execute()
            
            if not result.data:
                # If no scores for today, get the most recent scores
                result = self.client.table('momentumScores').select('*').order('calculated_at', desc=True).limit(1000).execute()
            
            return pd.DataFrame(result.data)
        except Exception as e:
            logger.error(f"Error getting momentum scores: {e}")
            return pd.DataFrame()
    
    def store_momentum_scores(self, stock: str, momentum_score: Dict[str, Any]):
        """Store momentum scores for a stock"""
        try:
            # Prepare the data
            score_data = {
                'stock': stock,
                'total_score': momentum_score.get('total_score', 0),
                'raw_momentum_6m': momentum_score.get('raw_momentum_6m', 0),
                'raw_momentum_3m': momentum_score.get('raw_momentum_3m', 0),
                'raw_momentum_1m': momentum_score.get('raw_momentum_1m', 0),
                'volatility_adjusted_6m': momentum_score.get('volatility_adjusted_6m', 0),
                'volatility_adjusted_3m': momentum_score.get('volatility_adjusted_3m', 0),
                'volatility_adjusted_1m': momentum_score.get('volatility_adjusted_1m', 0),
                'relative_strength_6m': momentum_score.get('relative_strength_6m', 0),
                'relative_strength_3m': momentum_score.get('relative_strength_3m', 0),
                'relative_strength_1m': momentum_score.get('relative_strength_1m', 0),
                'trend_score': momentum_score.get('trend_score', 0),
                'volume_score': momentum_score.get('volume_score', 0),
                'calculated_at': datetime.now().isoformat()
            }
            
            # Upsert the data
            result = self.client.table('momentumScores').upsert(score_data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Error storing momentum scores for {stock}: {e}")
            return False
    
    def get_available_industries(self) -> list:
        """Get list of available industries"""
        try:
            result = self.client.table('stockMetadata').select('industry').execute()
            industries = list(set([row['industry'] for row in result.data if row['industry']]))
            return sorted(industries)
        except Exception as e:
            logger.error(f"Error getting industries: {e}")
            return []
    
    def get_available_sectors(self) -> list:
        """Get list of available sectors"""
        try:
            result = self.client.table('stockMetadata').select('sector').execute()
            sectors = list(set([row['sector'] for row in result.data if row['sector']]))
            return sorted(sectors)
        except Exception as e:
            logger.error(f"Error getting sectors: {e}")
            return []
