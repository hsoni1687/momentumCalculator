"""
Low Volatility Strategy
Identifies stocks with the lowest daily return volatility over the past year
"""
import pandas as pd
import numpy as np
from typing import Dict
from ..strategy_base import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class LowVolatilityStrategy(BaseStrategy):
    """Strategy that identifies stocks with lowest volatility (most stable)"""
    
    def __init__(self):
        super().__init__(
            name="Low Volatility",
            description="Identifies stocks with the lowest daily return volatility over the past year, indicating stable price movement"
        )
    
    def get_minimum_data_required(self) -> int:
        """Need at least 252 trading days (1 year) for volatility calculation"""
        return 252
    
    def calculate_scores(self, stock_metadata: pd.DataFrame, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate low volatility scores
        
        Score = -1 * (Daily Return Standard Deviation)
        Lower volatility = Higher score (we want to rank by lowest volatility)
        """
        results = []
        
        for _, stock_info in stock_metadata.iterrows():
            stock = stock_info['stock']
            
            try:
                if stock not in price_data:
                    logger.warning(f"No price data available for {stock}")
                    results.append({
                        'stock': stock,
                        'score': None,
                        'daily_volatility': None,
                        'annual_volatility': None,
                        'insufficient_data': True
                    })
                    continue
                
                stock_prices = price_data[stock]
                
                # Validate data sufficiency
                if not self.validate_data_sufficiency(stock_prices, stock):
                    results.append({
                        'stock': stock,
                        'score': None,
                        'daily_volatility': None,
                        'annual_volatility': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Ensure we have the required columns
                if 'close' not in stock_prices.columns:
                    logger.warning(f"Missing close price data for {stock}")
                    results.append({
                        'stock': stock,
                        'score': None,
                        'daily_volatility': None,
                        'annual_volatility': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Sort by date to ensure proper chronological order
                stock_prices = stock_prices.sort_values('date')
                
                # Get last 252 trading days (approximately 1 year)
                recent_data = stock_prices.tail(252)
                
                if len(recent_data) < 50:  # Minimum threshold
                    logger.warning(f"Insufficient recent data for {stock}: {len(recent_data)} days")
                    results.append({
                        'stock': stock,
                        'score': None,
                        'daily_volatility': None,
                        'annual_volatility': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Calculate daily returns
                daily_returns = recent_data['close'].pct_change().dropna()
                
                if len(daily_returns) < 20:  # Need at least 20 returns for meaningful calculation
                    logger.warning(f"Insufficient return data for {stock}: {len(daily_returns)} returns")
                    results.append({
                        'stock': stock,
                        'score': None,
                        'daily_volatility': None,
                        'annual_volatility': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Calculate daily volatility (standard deviation of daily returns)
                daily_volatility = daily_returns.std()
                
                # Calculate annualized volatility (assuming 252 trading days per year)
                annual_volatility = daily_volatility * np.sqrt(252)
                
                # Score is negative volatility (lower volatility = higher score)
                # This way, when we sort by score descending, lowest volatility stocks come first
                score = -daily_volatility
                
                results.append({
                    'stock': stock,
                    'score': score,
                    'daily_volatility': daily_volatility,
                    'annual_volatility': annual_volatility,
                    'insufficient_data': False
                })
                
            except Exception as e:
                logger.error(f"Error calculating volatility for {stock}: {e}")
                results.append({
                    'stock': stock,
                    'score': None,
                    'daily_volatility': None,
                    'annual_volatility': None,
                    'insufficient_data': True
                })
        
        return pd.DataFrame(results)
