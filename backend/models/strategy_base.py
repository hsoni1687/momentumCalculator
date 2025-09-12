"""
Base strategy interface for all trading strategies
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def calculate_scores(self, stock_metadata: pd.DataFrame, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate strategy scores for all stocks
        
        Args:
            stock_metadata: DataFrame with stock metadata
            price_data: Dictionary mapping stock symbols to price DataFrames
            
        Returns:
            DataFrame with stock symbols and their strategy scores
        """
        pass
    
    @abstractmethod
    def get_minimum_data_required(self) -> int:
        """
        Get minimum number of data points required for this strategy
        
        Returns:
            Minimum number of days of data required
        """
        pass
    
    def validate_data_sufficiency(self, price_data: pd.DataFrame, stock: str) -> bool:
        """
        Check if there's sufficient data for the strategy
        
        Args:
            price_data: Price data for the stock
            stock: Stock symbol
            
        Returns:
            True if sufficient data, False otherwise
        """
        if price_data is None or price_data.empty:
            logger.warning(f"Insufficient data for {stock}: No price data available")
            return False
            
        min_required = self.get_minimum_data_required()
        if len(price_data) < min_required:
            logger.warning(f"Insufficient data for {stock}: Need {min_required} days, have {len(price_data)}")
            return False
            
        return True
    
    def get_strategy_info(self) -> Dict[str, str]:
        """Get strategy information"""
        return {
            "name": self.name,
            "description": self.description,
            "minimum_data_required": str(self.get_minimum_data_required())
        }
