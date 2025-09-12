"""
Strategy Manager for handling multiple trading strategies
"""
import pandas as pd
from typing import Dict, List, Optional
import logging
from .strategy_base import BaseStrategy
from .strategies.week52_breakout import Week52BreakoutStrategy
from .strategies.ma_crossover import MACrossoverStrategy
from .strategies.low_volatility import LowVolatilityStrategy
from .strategies.mean_reversion import MeanReversionStrategy

logger = logging.getLogger(__name__)

class StrategyManager:
    """Manages all trading strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize all available strategies"""
        self.strategies = {
            'momentum': None,  # Will be handled separately by existing momentum service
            'week52_breakout': Week52BreakoutStrategy(),
            'ma_crossover': MACrossoverStrategy(),
            'low_volatility': LowVolatilityStrategy(),
            'mean_reversion': MeanReversionStrategy()
        }
        logger.info(f"Initialized {len(self.strategies)} strategies")
    
    def get_available_strategies(self) -> List[Dict[str, str]]:
        """Get list of all available strategies with their info"""
        strategy_info = []
        for name, strategy in self.strategies.items():
            if strategy is not None:
                info = strategy.get_strategy_info()
                info['key'] = name
                strategy_info.append(info)
        return strategy_info
    
    def calculate_strategy_scores(self, strategy_name: str, stock_metadata: pd.DataFrame, 
                                price_data: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        """
        Calculate scores for a specific strategy
        
        Args:
            strategy_name: Name of the strategy
            stock_metadata: DataFrame with stock metadata
            price_data: Dictionary mapping stock symbols to price DataFrames
            
        Returns:
            DataFrame with strategy scores or None if strategy not found
        """
        if strategy_name not in self.strategies:
            logger.error(f"Strategy '{strategy_name}' not found")
            return None
        
        strategy = self.strategies[strategy_name]
        if strategy is None:
            logger.error(f"Strategy '{strategy_name}' is not implemented")
            return None
        
        try:
            logger.info(f"Calculating scores for strategy: {strategy_name}")
            scores = strategy.calculate_scores(stock_metadata, price_data)
            logger.info(f"Calculated scores for {len(scores)} stocks using {strategy_name}")
            return scores
        except Exception as e:
            logger.error(f"Error calculating scores for strategy {strategy_name}: {e}")
            return None
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """Get a specific strategy instance"""
        return self.strategies.get(strategy_name)
    
    def add_strategy(self, name: str, strategy: BaseStrategy):
        """Add a new strategy"""
        self.strategies[name] = strategy
        logger.info(f"Added new strategy: {name}")
    
    def remove_strategy(self, name: str):
        """Remove a strategy"""
        if name in self.strategies:
            del self.strategies[name]
            logger.info(f"Removed strategy: {name}")
        else:
            logger.warning(f"Strategy {name} not found for removal")
