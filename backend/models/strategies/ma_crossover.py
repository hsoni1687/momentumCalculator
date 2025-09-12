"""
Moving Average Crossover Strategy
Identifies stocks where 50-day MA > 200-day MA (bullish crossover)
"""
import pandas as pd
import numpy as np
from typing import Dict
from ..strategy_base import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class MACrossoverStrategy(BaseStrategy):
    """Strategy that identifies bullish moving average crossovers"""
    
    def __init__(self):
        super().__init__(
            name="Moving Average Crossover",
            description="Identifies stocks where 50-day moving average is above 200-day moving average, indicating bullish momentum"
        )
    
    def get_minimum_data_required(self) -> int:
        """Need at least 200 days for 200-day MA calculation"""
        return 200
    
    def calculate_scores(self, stock_metadata: pd.DataFrame, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate moving average crossover scores
        
        Score = (50-day MA - 200-day MA) / 200-day MA
        Positive scores indicate bullish crossover (50-day MA > 200-day MA)
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
                        'ma_50': None,
                        'ma_200': None,
                        'crossover_ratio': None,
                        'insufficient_data': True
                    })
                    continue
                
                stock_prices = price_data[stock]
                
                # Debug: Log the DataFrame info
                logger.info(f"DEBUG {stock}: DataFrame is empty: {stock_prices.empty}")
                logger.info(f"DEBUG {stock}: DataFrame shape: {stock_prices.shape}")
                if not stock_prices.empty:
                    logger.info(f"DEBUG {stock}: DataFrame columns: {list(stock_prices.columns)}")
                
                # Validate data sufficiency
                if not self.validate_data_sufficiency(stock_prices, stock):
                    results.append({
                        'stock': stock,
                        'score': None,
                        'ma_50': None,
                        'ma_200': None,
                        'crossover_ratio': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Debug: Log the actual columns
                logger.info(f"DEBUG {stock}: DataFrame columns: {list(stock_prices.columns)}")
                logger.info(f"DEBUG {stock}: DataFrame shape: {stock_prices.shape}")
                
                # Ensure we have the required columns
                if 'close' not in stock_prices.columns:
                    logger.warning(f"Missing close price data for {stock}. Available columns: {list(stock_prices.columns)}")
                    results.append({
                        'stock': stock,
                        'score': None,
                        'ma_50': None,
                        'ma_200': None,
                        'crossover_ratio': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Sort by date to ensure proper chronological order
                stock_prices = stock_prices.sort_values('date')
                
                # Calculate moving averages
                ma_50 = stock_prices['close'].rolling(window=50, min_periods=50).mean()
                ma_200 = stock_prices['close'].rolling(window=200, min_periods=200).mean()
                
                # Get the latest values
                latest_ma_50 = ma_50.iloc[-1]
                latest_ma_200 = ma_200.iloc[-1]
                
                # Check if we have valid moving averages
                if pd.isna(latest_ma_50) or pd.isna(latest_ma_200):
                    logger.warning(f"Insufficient data for moving averages for {stock}")
                    results.append({
                        'stock': stock,
                        'score': None,
                        'ma_50': None,
                        'ma_200': None,
                        'crossover_ratio': None,
                        'insufficient_data': True
                    })
                    continue
                
                # Calculate crossover ratio
                if latest_ma_200 == 0:
                    crossover_ratio = 0
                else:
                    crossover_ratio = (latest_ma_50 - latest_ma_200) / latest_ma_200
                
                # Score is the crossover ratio (positive = bullish, negative = bearish)
                score = crossover_ratio
                
                results.append({
                    'stock': stock,
                    'score': score,
                    'ma_50': latest_ma_50,
                    'ma_200': latest_ma_200,
                    'crossover_ratio': crossover_ratio,
                    'insufficient_data': False
                })
                
            except Exception as e:
                logger.error(f"Error calculating MA crossover for {stock}: {e}")
                results.append({
                    'stock': stock,
                    'score': None,
                    'ma_50': None,
                    'ma_200': None,
                    'crossover_ratio': None,
                    'insufficient_data': True
                })
        
        return pd.DataFrame(results)
