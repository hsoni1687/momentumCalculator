"""
Mean Reversion Strategy
Identifies stocks where price is far below 200-day moving average (potential buy)
and stocks where price is far above 200-day moving average (potential sell)
"""
import pandas as pd
import numpy as np
from typing import Dict
from ..strategy_base import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class MeanReversionStrategy(BaseStrategy):
    """Strategy that identifies mean reversion opportunities based on z-score"""
    
    def __init__(self):
        super().__init__(
            name="Mean Reversion",
            description="Identifies stocks where price deviates significantly from 200-day moving average, indicating potential mean reversion opportunities"
        )
    
    def get_minimum_data_required(self) -> int:
        """Need at least 200 days for 200-day MA calculation"""
        return 200
    
    def calculate_scores(self, stock_metadata: pd.DataFrame, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate mean reversion scores using z-score
        
        Z-Score = (Current Price - 200-day MA) / Standard Deviation of prices over 200 days
        Negative z-scores indicate price below mean (potential buy)
        Positive z-scores indicate price above mean (potential sell)
        
        Score = -abs(z-score) for buy opportunities (price below mean)
        Score = abs(z-score) for sell opportunities (price above mean)
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
                        'ma_200': None,
                        'z_score': None,
                        'price_deviation_pct': None,
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
                        'ma_200': None,
                        'z_score': None,
                        'price_deviation_pct': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Ensure we have the required columns
                if 'close' not in stock_prices.columns:
                    logger.warning(f"Missing close price data for {stock}")
                    results.append({
                        'stock': stock,
                        'score': None,
                        'current_price': None,
                        'ma_200': None,
                        'z_score': None,
                        'price_deviation_pct': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Sort by date to ensure proper chronological order
                stock_prices = stock_prices.sort_values('date')
                
                # Get last 200 days for MA calculation
                recent_data = stock_prices.tail(200)
                
                if len(recent_data) < 200:
                    logger.warning(f"Insufficient data for 200-day MA for {stock}: {len(recent_data)} days")
                    results.append({
                        'stock': stock,
                        'score': None,
                        'current_price': None,
                        'ma_200': None,
                        'z_score': None,
                        'price_deviation_pct': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Calculate 200-day moving average
                ma_200 = recent_data['close'].rolling(window=200, min_periods=200).mean()
                latest_ma_200 = ma_200.iloc[-1]
                
                # Calculate standard deviation of prices over 200 days
                price_std = recent_data['close'].std()
                
                # Use current_price from stock metadata (latest price pulled) instead of historical data
                current_price = stock_info.get('current_price')
                if current_price is None or pd.isna(current_price):
                    # Fallback to latest close price from historical data if current_price is not available
                    current_price = recent_data['close'].iloc[-1]
                
                # Check if we have valid data
                if pd.isna(latest_ma_200) or pd.isna(price_std) or price_std == 0:
                    logger.warning(f"Invalid data for mean reversion calculation for {stock}")
                    results.append({
                        'stock': stock,
                        'score': None,
                        'current_price': None,
                        'ma_200': None,
                        'z_score': None,
                        'price_deviation_pct': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Calculate z-score
                z_score = (current_price - latest_ma_200) / price_std
                
                # Calculate price deviation percentage
                price_deviation_pct = ((current_price - latest_ma_200) / latest_ma_200) * 100
                
                # Score calculation:
                # For mean reversion, we want to identify stocks that are significantly deviating from mean
                # Negative z-scores (price below mean) are potential buy opportunities
                # Positive z-scores (price above mean) are potential sell opportunities
                # We use absolute z-score as the score, with sign indicating direction
                score = z_score
                
                results.append({
                    'stock': stock,
                    'score': score,
                    'current_price': current_price,
                    'ma_200': latest_ma_200,
                    'z_score': z_score,
                    'price_deviation_pct': price_deviation_pct,
                    'insufficient_data': False
                })
                
            except Exception as e:
                logger.error(f"Error calculating mean reversion for {stock}: {e}")
                results.append({
                    'stock': stock,
                    'score': None,
                    'current_price': None,
                    'ma_200': None,
                    'z_score': None,
                    'price_deviation_pct': None,
                    'insufficient_data': True
                })
        
        return pd.DataFrame(results)
