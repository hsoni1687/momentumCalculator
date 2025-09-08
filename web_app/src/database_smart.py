#!/usr/bin/env python3
"""
Smart Database Adapter
Automatically chooses between local PostgreSQL and Supabase based on environment
"""

import os
import logging
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class SmartDatabase:
    """Smart database adapter that chooses the right database based on configuration"""
    
    def __init__(self):
        """Initialize the appropriate database adapter"""
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_database_config()
        
        # Initialize the appropriate database adapter
        adapter_type = self.config.get('adapter', 'local')
        
        if adapter_type == 'local':
            logger.info("🔧 Using local database adapter")
            from database_local import LocalDatabase
            self.db = LocalDatabase()
            self.db_type = "local"
        elif adapter_type == 'supabase':
            logger.info("☁️ Using Supabase database adapter")
            from database_supabase import SupabaseDatabase
            self.db = SupabaseDatabase()
            self.db_type = "supabase"
        else:
            # Fallback to local
            logger.warning(f"Unknown adapter type '{adapter_type}', falling back to local")
            from database_local import LocalDatabase
            self.db = LocalDatabase()
            self.db_type = "local"
    
    def __getattr__(self, name):
        """Delegate all method calls to the underlying database adapter"""
        return getattr(self.db, name)
    
    def get_database_type(self):
        """Get the type of database being used"""
        return self.db_type
