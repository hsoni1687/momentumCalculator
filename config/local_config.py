"""
Local development configuration
"""
import os
from typing import Dict, Any
import logging
from base_config import BaseConfig

logger = logging.getLogger(__name__)

class LocalConfig(BaseConfig):
    """Configuration for local development environment"""
    
    def get_environment(self) -> str:
        """Get the current environment name"""
        return 'local'
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for local development"""
        # Check for Docker Compose environment first
        if os.getenv('DATABASE_URL'):
            return {
                'type': 'postgresql',
                'url': os.getenv('DATABASE_URL'),
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': int(os.getenv('POSTGRES_PORT', '5432')),
                'database': os.getenv('POSTGRES_DB', 'momentum_calc'),
                'username': os.getenv('POSTGRES_USER', 'momentum_user'),
                'password': os.getenv('POSTGRES_PASSWORD', 'momentum_password'),
                'adapter': 'local'
            }
        
        # Fallback to SQLite for local development
        return {
            'type': 'sqlite',
            'url': 'sqlite:///data/momentum_calc.db',
            'adapter': 'local'
        }
    
    def _validate_environment_config(self) -> bool:
        """Validate local environment configuration"""
        db_config = self.database_config
        
        if db_config['type'] == 'postgresql':
            # Validate PostgreSQL connection parameters
            required_params = ['host', 'port', 'database', 'username', 'password']
            for param in required_params:
                if not db_config.get(param):
                    logger.error(f"Missing required PostgreSQL parameter: {param}")
                    return False
        
        elif db_config['type'] == 'sqlite':
            # Ensure data directory exists
            data_dir = 'data'
            if not os.path.exists(data_dir):
                try:
                    os.makedirs(data_dir)
                    logger.info(f"Created data directory: {data_dir}")
                except Exception as e:
                    logger.error(f"Failed to create data directory: {e}")
                    return False
        
        return True
