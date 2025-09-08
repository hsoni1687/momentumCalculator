"""
Cloud deployment configuration (Streamlit Cloud + Supabase)
"""
import os
from typing import Dict, Any
import logging
from base_config import BaseConfig

logger = logging.getLogger(__name__)

class CloudConfig(BaseConfig):
    """Configuration for cloud deployment environment"""
    
    def get_environment(self) -> str:
        """Get the current environment name"""
        return 'cloud'
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for cloud deployment"""
        # Check for Supabase credentials in Streamlit secrets
        try:
            import streamlit as st
            
            # Try to get from Streamlit secrets first
            supabase_url = st.secrets.get('SUPABASE_URL')
            supabase_key = st.secrets.get('SUPABASE_ANON_KEY')
            
            if supabase_url and supabase_key:
                return {
                    'type': 'supabase',
                    'url': supabase_url,
                    'anon_key': supabase_key,
                    'adapter': 'supabase'
                }
        except Exception as e:
            logger.debug(f"Could not access Streamlit secrets: {e}")
        
        # Fallback to environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if supabase_url and supabase_key and supabase_url != 'your_supabase_url_here':
            return {
                'type': 'supabase',
                'url': supabase_url,
                'anon_key': supabase_key,
                'adapter': 'supabase'
            }
        
        # If no valid Supabase config, fallback to local PostgreSQL
        logger.warning("No valid Supabase configuration found, falling back to local PostgreSQL")
        return {
            'type': 'postgresql',
            'url': os.getenv('DATABASE_URL', 'postgresql://momentum_user:momentum_password@localhost:5432/momentum_calc'),
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'momentum_calc'),
            'username': os.getenv('POSTGRES_USER', 'momentum_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'momentum_password'),
            'adapter': 'local'
        }
    
    def _validate_environment_config(self) -> bool:
        """Validate cloud environment configuration"""
        db_config = self.database_config
        
        if db_config['type'] == 'supabase':
            # Validate Supabase configuration
            if not db_config.get('url') or not db_config.get('anon_key'):
                logger.error("Missing Supabase URL or anonymous key")
                return False
            
            if 'supabase.co' not in db_config['url']:
                logger.error("Invalid Supabase URL format")
                return False
        
        elif db_config['type'] == 'postgresql':
            # Validate PostgreSQL connection parameters
            required_params = ['host', 'port', 'database', 'username', 'password']
            for param in required_params:
                if not db_config.get(param):
                    logger.error(f"Missing required PostgreSQL parameter: {param}")
                    return False
        
        return True
