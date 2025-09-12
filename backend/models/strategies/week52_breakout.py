"""
52-Week High Breakout Strategy
Identifies stocks that are trading near or at their 52-week high
"""
import pandas as pd
import numpy as np
from typing import Dict
from ..strategy_base import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class Week52BreakoutStrategy(BaseStrategy):
    """Strategy that identifies stocks breaking out to 52-week highs"""
    
    def __init__(self):
        super().__init__(
            name="52-Week High Breakout",
            description="Identifies stocks trading near or at their 52-week high, indicating potential breakout momentum"
        )
    
    def get_minimum_data_required(self) -> int:
        """Need at least 252 trading days (1 year) for 52-week calculation"""
        return 252
    
    def calculate_scores(self, stock_metadata: pd.DataFrame, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate 52-week high breakout scores
        
        Score = (Current Price - 52-Week Low) / (52-Week High - 52-Week Low)
        Higher scores indicate stocks closer to 52-week high
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
                        'current_price': None,
                        'week52_high': None,
                        'week52_low': None,
                        'breakout_ratio': None,
                        'insufficient_data': True
                    })
                    continue
                
                stock_prices = price_data[stock]
                
                # Validate data sufficiency
                if not self.validate_data_sufficiency(stock_prices, stock):
                    results.append({
                        'stock': stock,
                        'score': None,
                        'current_price': None,
                        'week52_high': None,
                        'week52_low': None,
                        'breakout_ratio': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Ensure we have the required columns
                required_columns = ['close', 'high', 'low']
                if not all(col in stock_prices.columns for col in required_columns):
                    logger.warning(f"Missing required columns for {stock}")
                    results.append({
                        'stock': stock,
                        'score': None,
                        'current_price': None,
                        'week52_high': None,
                        'week52_low': None,
                        'breakout_ratio': None,
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
                        'current_price': None,
                        'week52_high': None,
                        'week52_low': None,
                        'breakout_ratio': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Calculate 52-week high and low
                week52_high = recent_data['high'].max()
                week52_low = recent_data['low'].min()
                
                # Use current_price from stock metadata (latest price pulled) instead of historical data
                current_price = stock_info.get('current_price')
                if current_price is None or pd.isna(current_price):
                    # Fallback to latest close price from historical data if current_price is not available
                    current_price = recent_data['close'].iloc[-1]
                
                # Calculate breakout ratio
                if week52_high == week52_low:
                    # Edge case: all prices are the same
                    breakout_ratio = 0.5
                else:
                    breakout_ratio = (current_price - week52_low) / (week52_high - week52_low)
                
                # Score is the breakout ratio (0 to 1, where 1 is at 52-week high)
                score = breakout_ratio
                
                results.append({
                    'stock': stock,
                    'score': score,
                    'current_price': current_price,
                    'week52_high': week52_high,
                    'week52_low': week52_low,
                    'breakout_ratio': breakout_ratio,
                    'insufficient_data': False
                })
                
            except Exception as e:
                logger.error(f"Error calculating 52-week breakout for {stock}: {e}")
                results.append({
                    'stock': stock,
                    'score': None,
                    'current_price': None,
                    'week52_high': None,
                    'week52_low': None,
                    'breakout_ratio': None,
                    'insufficient_data': True
                })
        
        return pd.DataFrame(results)
