"""
Configuration manager that automatically detects and loads the appropriate configuration
"""
import os
import logging
from typing import Optional
from base_config import BaseConfig
from local_config import LocalConfig
from cloud_config import CloudConfig

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration loading and environment detection"""
    
    def __init__(self):
        self._config: Optional[BaseConfig] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load the appropriate configuration based on environment detection"""
        environment = self._detect_environment()
        
        logger.info(f"Detected environment: {environment}")
        
        if environment == 'local':
            self._config = LocalConfig()
        elif environment == 'cloud':
            self._config = CloudConfig()
        else:
            # Default to local for safety
            logger.warning(f"Unknown environment '{environment}', defaulting to local")
            self._config = LocalConfig()
        
        # Validate configuration
        if not self._config.validate_config():
            logger.error("Configuration validation failed")
            raise ValueError("Invalid configuration")
        
        logger.info(f"Configuration loaded successfully: {self._config.get_config_summary()}")
    
    def _detect_environment(self) -> str:
        """Detect the current environment"""
        # Check explicit environment variable first
        explicit_env = os.getenv('MOMENTUM_ENV')
        if explicit_env:
            return explicit_env.lower()
        
        # Check for Streamlit Cloud environment
        if os.getenv('STREAMLIT_SHARING_MODE') == 'true':
            return 'cloud'
        
        # Check for Supabase credentials (indicates cloud deployment)
        supabase_url = os.getenv('SUPABASE_URL')
        if supabase_url and supabase_url != 'your_supabase_url_here' and 'supabase.co' in supabase_url:
            return 'cloud'
        
        # Check for local development indicators
        if os.getenv('DATABASE_URL') or os.getenv('POSTGRES_HOST'):
            return 'local'
        
        # Check if running in Docker (local development)
        if os.path.exists('/.dockerenv'):
            return 'local'
        
        # Default to local for development
        return 'local'
    
    @property
    def config(self) -> BaseConfig:
        """Get the current configuration"""
        if self._config is None:
            raise RuntimeError("Configuration not loaded")
        return self._config
    
    def get_database_config(self) -> dict:
        """Get database configuration"""
        return self.config.database_config
    
    def get_app_config(self) -> dict:
        """Get application configuration"""
        return self.config.app_config
    
    def get_logging_config(self) -> dict:
        """Get logging configuration"""
        return self.config.logging_config
    
    def is_local(self) -> bool:
        """Check if running in local environment"""
        return self.config.environment == 'local'
    
    def is_cloud(self) -> bool:
        """Check if running in cloud environment"""
        return self.config.environment == 'cloud'
    
    def get_config_summary(self) -> dict:
        """Get configuration summary"""
        return self.config.get_config_summary()
    
    def reload_config(self) -> None:
        """Reload configuration (useful for testing)"""
        logger.info("Reloading configuration...")
        self._config = None
        self._load_config()
