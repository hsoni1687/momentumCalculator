"""
Momentum calculation configuration
Allows dynamic configuration of momentum calculation weights and parameters
"""

from typing import Dict, Any
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

class MomentumWeights(BaseModel):
    """Configuration for momentum calculation weights"""
    true_momentum_6m: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight for 6-month true momentum")
    true_momentum_3m: float = Field(default=0.2, ge=0.0, le=1.0, description="Weight for 3-month true momentum")
    smooth_momentum: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for smooth momentum (Frog in the Pan)")
    volatility_adjusted: float = Field(default=0.15, ge=0.0, le=1.0, description="Weight for volatility-adjusted momentum")
    consistency_score: float = Field(default=0.05, ge=0.0, le=1.0, description="Weight for consistency score")
    trend_strength: float = Field(default=0.05, ge=0.0, le=1.0, description="Weight for trend strength")
    
    @validator('*', pre=True)
    def validate_weights(cls, v):
        """Ensure weights are between 0 and 1"""
        if not isinstance(v, (int, float)):
            raise ValueError("Weight must be a number")
        return float(v)
    
    def validate_total_weights(self) -> bool:
        """Validate that weights sum to approximately 1.0"""
        total = sum([
            self.true_momentum_6m,
            self.true_momentum_3m,
            self.smooth_momentum,
            self.volatility_adjusted,
            self.consistency_score,
            self.trend_strength
        ])
        return abs(total - 1.0) < 0.01  # Allow small floating point errors
    
    def normalize_weights(self) -> 'MomentumWeights':
        """Normalize weights to sum to 1.0"""
        total = sum([
            self.true_momentum_6m,
            self.true_momentum_3m,
            self.smooth_momentum,
            self.volatility_adjusted,
            self.consistency_score,
            self.trend_strength
        ])
        
        if total == 0:
            # If all weights are 0, use default weights
            return MomentumWeights()
        
        return MomentumWeights(
            true_momentum_6m=self.true_momentum_6m / total,
            true_momentum_3m=self.true_momentum_3m / total,
            smooth_momentum=self.smooth_momentum / total,
            volatility_adjusted=self.volatility_adjusted / total,
            consistency_score=self.consistency_score / total,
            trend_strength=self.trend_strength / total
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary format expected by momentum calculator"""
        return {
            'true_momentum_6m': self.true_momentum_6m,
            'true_momentum_3m': self.true_momentum_3m,
            'smooth_momentum': self.smooth_momentum,
            'volatility_adjusted': self.volatility_adjusted,
            'consistency_score': self.consistency_score,
            'trend_strength': self.trend_strength
        }

class MomentumConfig(BaseModel):
    """Complete momentum calculation configuration"""
    weights: MomentumWeights = Field(default_factory=MomentumWeights)
    
    # Additional configuration parameters
    volatility_cap: float = Field(default=2.0, ge=0.1, le=10.0, description="Maximum volatility adjustment factor")
    momentum_cap: float = Field(default=1.0, ge=0.1, le=5.0, description="Maximum momentum value")
    smooth_factor_base: float = Field(default=0.1, ge=0.01, le=1.0, description="Base smooth factor for volatility penalty")
    
    def get_weights_dict(self) -> Dict[str, float]:
        """Get normalized weights as dictionary"""
        normalized_weights = self.weights.normalize_weights()
        return normalized_weights.to_dict()

# Global configuration instance
_momentum_config = MomentumConfig()

def get_momentum_config() -> MomentumConfig:
    """Get the current momentum configuration"""
    return _momentum_config

def update_momentum_config(config_data: Dict[str, Any]) -> MomentumConfig:
    """Update momentum configuration"""
    global _momentum_config
    
    try:
        # Update weights if provided
        if 'weights' in config_data:
            weights_data = config_data['weights']
            _momentum_config.weights = MomentumWeights(**weights_data)
        
        # Update other parameters if provided
        for key, value in config_data.items():
            if key != 'weights' and hasattr(_momentum_config, key):
                setattr(_momentum_config, key, value)
        
        # Validate the configuration
        if not _momentum_config.weights.validate_total_weights():
            logger.warning("Weights do not sum to 1.0, normalizing...")
            _momentum_config.weights = _momentum_config.weights.normalize_weights()
        
        logger.info(f"Updated momentum configuration: {_momentum_config.dict()}")
        return _momentum_config
        
    except Exception as e:
        logger.error(f"Error updating momentum configuration: {e}")
        raise ValueError(f"Invalid momentum configuration: {e}")

def reset_momentum_config() -> MomentumConfig:
    """Reset momentum configuration to defaults"""
    global _momentum_config
    _momentum_config = MomentumConfig()
    logger.info("Reset momentum configuration to defaults")
    return _momentum_config
