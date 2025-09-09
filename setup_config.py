#!/usr/bin/env python3
"""
Configuration setup script for Momentum Calculator
This script helps users set up their local configuration
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    """Main setup function"""
    print("🚀 Momentum Calculator - Configuration Setup")
    print("=" * 50)
    
    # Get the current directory
    current_dir = Path(__file__).parent
    config_dir = current_dir / 'config'
    
    # Ensure config directory exists
    config_dir.mkdir(exist_ok=True)
    
    # Check if local.env already exists
    local_env_file = config_dir / 'local.env'
    template_file = config_dir / 'local.env.template'
    
    if local_env_file.exists():
        print(f"✅ Local configuration file already exists: {local_env_file}")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Configuration setup cancelled.")
            return
    
    # Copy template to local.env
    if template_file.exists():
        try:
            shutil.copy2(template_file, local_env_file)
            print(f"✅ Created local configuration file: {local_env_file}")
            print("\n📝 Please edit the configuration file with your settings:")
            print(f"   {local_env_file}")
            print("\n🔧 Key settings to configure:")
            print("   - DATABASE_URL: PostgreSQL connection string")
            print("   - POSTGRES_*: Individual PostgreSQL settings")
            print("   - MAX_STOCKS: Maximum number of stocks to analyze")
            print("   - DEBUG: Set to 'true' for development")
        except Exception as e:
            print(f"❌ Failed to create configuration file: {e}")
            return
    else:
        print(f"❌ Template file not found: {template_file}")
        return
    
    # Create logs directory
    logs_dir = current_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    print(f"✅ Created logs directory: {logs_dir}")
    
    # Create data directory
    data_dir = current_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    print(f"✅ Created data directory: {data_dir}")
    
    print("\n🎉 Configuration setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit the configuration file with your settings")
    print("2. Start the application with: streamlit run app.py")
    print("3. Or use Docker: docker-compose up --build")
    
    # Show current configuration
    print("\n🔍 Current configuration:")
    try:
        sys.path.append(str(config_dir))
        from config.loader import get_config
        config_manager = get_config()
        summary = config_manager.get_config_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"   ⚠️  Could not load configuration: {e}")

if __name__ == "__main__":
    main()
