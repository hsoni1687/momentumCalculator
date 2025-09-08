"""
Base configuration class
"""
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseConfig(ABC):
    """Base configuration class that all environment configs inherit from"""
    
    def __init__(self):
        self.environment = self.get_environment()
        self.database_config = self.get_database_config()
        self.app_config = self.get_app_config()
        self.logging_config = self.get_logging_config()
    
    @abstractmethod
    def get_environment(self) -> str:
        """Get the current environment name"""
        pass
    
    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        pass
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        return {
            'app_name': 'Momentum Calculator',
            'version': '1.0.0',
            'debug': self.is_debug_mode(),
            'max_stocks': int(os.getenv('MAX_STOCKS', '100')),
            'cache_ttl': int(os.getenv('CACHE_TTL', '3600')),  # 1 hour
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'level': 'DEBUG' if self.is_debug_mode() else 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': f'logs/{self.environment}.log' if self.is_debug_mode() else None,
        }
    
    def is_debug_mode(self) -> bool:
        """Check if running in debug mode"""
        return os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration"""
        return {
            'environment': self.environment,
            'debug_mode': self.is_debug_mode(),
            'database_type': self.database_config.get('type', 'unknown'),
            'app_name': self.app_config.get('app_name'),
            'version': self.app_config.get('version'),
        }
    
    def validate_config(self) -> bool:
        """Validate the configuration"""
        try:
            # Validate database config
            db_config = self.database_config
            if not db_config.get('type'):
                logger.error("Database type not specified")
                return False
            
            # Environment-specific validation
            return self._validate_environment_config()
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    @abstractmethod
    def _validate_environment_config(self) -> bool:
        """Environment-specific configuration validation"""
        pass
