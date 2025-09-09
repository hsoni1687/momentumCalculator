"""
Momentum service for backend
"""

import pandas as pd
import logging
from typing import Dict, List, Optional
import sys
import os

from .momentum_calculator import MomentumCalculator

logger = logging.getLogger(__name__)

class MomentumService:
    """Momentum service for backend operations"""
    
    def __init__(self, database_service=None):
        """Initialize momentum calculator"""
        self.momentum_calculator = MomentumCalculator()
        self.cache = {}
        self.database_service = database_service
        logger.info("Momentum service initialized")
    
    def calculate_momentum_scores(self, stocks_df: pd.DataFrame, 
                                 historical_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calculate momentum scores for all stocks"""
        cache_key = f"momentum_{len(stocks_df)}_{hash(str(historical_data.keys()))}"
        
        if cache_key in self.cache:
            logger.info(f"Returning cached momentum scores: {cache_key}")
            return self.cache[cache_key]
        
        momentum_scores = []
        
        for _, stock in stocks_df.iterrows():
            symbol = stock['stock']
            if symbol in historical_data:
                try:
                    hist_data = historical_data[symbol]
                    momentum_score = self.momentum_calculator.calculate_quality_momentum_score(hist_data)
                    
                    if momentum_score is not None:
                        # Get last price date from historical data
                        last_price_date = None
                        if symbol in historical_data and not historical_data[symbol].empty:
                            last_price_date = historical_data[symbol].index.max().strftime('%Y-%m-%d')
                        
                        momentum_scores.append({
                            'stock': symbol,
                            'name': stock.get('company_name', 'N/A'),
                            'sector': stock.get('sector', 'N/A'),
                            'industry': stock.get('industry', 'N/A'),
                            'momentum_score': momentum_score.get('total_score', 0),
                            'fip_quality': momentum_score.get('fip_quality', 0),
                            'last_price_date': last_price_date,
                            
                            # 12-2 Month momentum (Alpha Architect primary measure)
                            'raw_momentum_12_2': momentum_score.get('momentum_12_2', 0),
                            
                            # True momentum (considering trend consistency and quality)
                            'true_momentum_6m': momentum_score.get('true_momentum_6m', 0),
                            'true_momentum_3m': momentum_score.get('true_momentum_3m', 0),
                            'true_momentum_1m': momentum_score.get('true_momentum_1m', 0),
                            
                            # Simple returns for reference
                            'raw_return_6m': momentum_score.get('raw_return_6m', 0),
                            'raw_return_3m': momentum_score.get('raw_return_3m', 0),
                            'raw_return_1m': momentum_score.get('raw_return_1m', 0),
                            
                            # Legacy fields for backward compatibility
                            'raw_momentum_6m': momentum_score.get('raw_momentum_6m', 0),
                            'raw_momentum_3m': momentum_score.get('raw_momentum_3m', 0),
                            'raw_momentum_1m': momentum_score.get('raw_momentum_1m', 0)
                        })
                        logger.debug(f"Calculated momentum for {symbol}: {momentum_score.get('total_score', 0):.2f}")
                    else:
                        logger.warning(f"No momentum score calculated for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Error calculating momentum for {symbol}: {e}")
        
        momentum_df = pd.DataFrame(momentum_scores)
        
        if not momentum_df.empty:
            # Sort by momentum score
            momentum_df = momentum_df.sort_values('momentum_score', ascending=False)
            # Cache the result
            self.cache[cache_key] = momentum_df
            logger.info(f"Calculated momentum scores for {len(momentum_df)} stocks")
        else:
            logger.warning("No momentum scores calculated")
        
        return momentum_df
    
    def get_top_momentum_stocks(self, momentum_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """Get top N momentum stocks"""
        return momentum_df.head(top_n)
    
    def get_momentum_by_sector(self, momentum_df: pd.DataFrame) -> pd.DataFrame:
        """Get momentum scores grouped by sector"""
        if momentum_df.empty:
            return pd.DataFrame()
        
        sector_momentum = momentum_df.groupby('sector').agg({
            'momentum_score': ['mean', 'count'],
            'raw_momentum_12_2': 'mean',
            'raw_momentum_6m': 'mean',
            'raw_momentum_3m': 'mean',
            'raw_momentum_1m': 'mean'
        }).round(4)
        
        # Flatten column names
        sector_momentum.columns = ['_'.join(col).strip() for col in sector_momentum.columns]
        sector_momentum = sector_momentum.sort_values('momentum_score_mean', ascending=False)
        
        logger.info(f"Calculated sector momentum for {len(sector_momentum)} sectors")
        return sector_momentum
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        logger.info("Momentum service cache cleared")
    
    def get_historical_data_from_db(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Get historical data directly from database for multiple symbols - OPTIMIZED"""
        if not self.database_service:
            logger.error("Database service not initialized")
            return {}
        
        try:
            historical_data = {}
            
            # Use parameterized query for security and performance
            placeholders = ','.join(['%s'] * len(symbols))
            query = f"""
            SELECT stock, date, open, high, low, close, volume
            FROM tickerPrice 
            WHERE stock IN ({placeholders})
            ORDER BY stock, date
            """
            
            result = self.database_service.execute_query(query, tuple(symbols))
            
            if result.empty:
                logger.warning("No price data found in database")
                return {}
            
            # Optimize data processing - process all stocks at once
            if not result.empty:
                # Convert date column once for all data
                result['date'] = pd.to_datetime(result['date'])
                
                # Rename columns once for all data
                result.columns = ['stock', 'date', 'Open', 'High', 'Low', 'Close', 'Volume']
                
                # Group by stock and process each group
                grouped = result.groupby('stock')
                for symbol, group in grouped:
                    if not group.empty:
                        # Set date as index
                        group = group.set_index('date')
                        group = group.drop('stock', axis=1)
                        
                        # Calculate Returns column (required by momentum calculator)
                        group['Returns'] = group['Close'].pct_change()
                        
                        historical_data[symbol] = group
            
            logger.info(f"Retrieved historical data for {len(historical_data)} stocks from database")
            return historical_data
            
        except Exception as e:
            logger.error(f"Error getting historical data from database: {e}")
            return {}
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_keys": list(self.cache.keys())
        }
