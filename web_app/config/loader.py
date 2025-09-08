"""
Configuration loader utility
"""
import os
import logging
from typing import Optional
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

def load_env_file(env_file: str) -> None:
    """Load environment variables from a file"""
    if not os.path.exists(env_file):
        logger.warning(f"Environment file not found: {env_file}")
        return
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Only set if not already set
                    if key not in os.environ:
                        os.environ[key] = value
                        logger.debug(f"Loaded environment variable: {key}")
        
        logger.info(f"Loaded environment variables from: {env_file}")
    except Exception as e:
        logger.error(f"Failed to load environment file {env_file}: {e}")

def setup_local_config() -> None:
    """Setup local configuration by loading local.env file"""
    local_env_file = os.path.join(os.path.dirname(__file__), 'local.env')
    load_env_file(local_env_file)

def get_config() -> ConfigManager:
    """Get the configuration manager instance"""
    return ConfigManager()

def create_local_config_template() -> None:
    """Create a local.env file from template if it doesn't exist"""
    config_dir = os.path.dirname(__file__)
    local_env_file = os.path.join(config_dir, 'local.env')
    template_file = os.path.join(config_dir, 'local.env.template')
    
    if not os.path.exists(local_env_file) and os.path.exists(template_file):
        try:
            with open(template_file, 'r') as src, open(local_env_file, 'w') as dst:
                dst.write(src.read())
            logger.info(f"Created local configuration file: {local_env_file}")
            logger.info("Please edit the file with your local settings")
        except Exception as e:
            logger.error(f"Failed to create local configuration file: {e}")
    elif os.path.exists(local_env_file):
        logger.info(f"Local configuration file already exists: {local_env_file}")
    else:
        logger.warning(f"Template file not found: {template_file}")
