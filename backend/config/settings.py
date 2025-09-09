"""
Backend configuration settings
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    api_title: str = "Momentum Calculator API"
    api_version: str = "1.0.0"
    api_description: str = "REST API for Indian Stock Momentum Calculator"
    debug: bool = False
    
    # Database Settings
    database_host: str = "postgres"
    database_port: int = 5432
    database_name: str = "momentum_calc"
    database_user: str = "momentum_user"
    database_password: str = "momentum_password"
    
    # CORS Settings
    cors_origins: list = ["http://localhost:8501", "http://localhost:3000"]
    
    # Cache Settings
    cache_ttl: int = 3600  # 1 hour
    
    # Application Limits
    max_stocks: int = 200
    default_stocks: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = ""

# Global settings instance
settings = Settings()
