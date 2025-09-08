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
        
        # Check for Streamlit Cloud environment (highest priority)
        if os.getenv('STREAMLIT_SHARING_MODE') == 'true':
            logger.info("Detected Streamlit Cloud environment")
            return 'cloud'
        
        # Check for Supabase credentials (indicates cloud deployment)
        supabase_url = os.getenv('SUPABASE_URL')
        if supabase_url and supabase_url != 'your_supabase_url_here' and 'supabase.co' in supabase_url:
            logger.info("Detected Supabase cloud environment")
            return 'cloud'
        
        # Check for Streamlit secrets (cloud deployment)
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and st.secrets.get('SUPABASE_URL'):
                logger.info("Detected Streamlit secrets cloud environment")
                return 'cloud'
        except:
            pass
        
        # Check for local development indicators (only if not in cloud)
        if os.getenv('DATABASE_URL') and 'localhost' in os.getenv('DATABASE_URL', ''):
            logger.info("Detected local PostgreSQL environment")
            return 'local'
        
        if os.getenv('POSTGRES_HOST') and os.getenv('POSTGRES_HOST') in ['localhost', '127.0.0.1']:
            logger.info("Detected local PostgreSQL environment")
            return 'local'
        
        # Check if running in Docker (local development)
        if os.path.exists('/.dockerenv'):
            logger.info("Detected Docker local environment")
            return 'local'
        
        # Default to cloud if we have any Supabase-like indicators
        if supabase_url and 'supabase' in supabase_url.lower():
            logger.info("Defaulting to cloud environment based on Supabase URL")
            return 'cloud'
        
        # Default to local for development
        logger.info("Defaulting to local environment")
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
