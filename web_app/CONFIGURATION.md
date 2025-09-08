# Configuration System

The Momentum Calculator uses a flexible configuration system that automatically detects the environment and loads the appropriate settings.

## Overview

The configuration system consists of:

- **Base Configuration**: Abstract base class with common functionality
- **Local Configuration**: For local development with PostgreSQL/SQLite
- **Cloud Configuration**: For Streamlit Cloud deployment with Supabase
- **Configuration Manager**: Automatically detects and loads the right config
- **Configuration Loader**: Handles environment file loading

## Quick Setup

### 1. Run the Setup Script

```bash
python setup_config.py
```

This will:
- Create a `local.env` file from the template
- Create necessary directories (`logs/`, `data/`)
- Show you the current configuration

### 2. Edit Your Configuration

Edit `config/local.env` with your settings:

```bash
# Local Development Environment Configuration
MOMENTUM_ENV=local
DEBUG=true

# Local PostgreSQL Database (for docker-compose)
DATABASE_URL=postgresql://momentum_user:momentum_password@localhost:5432/momentum_calc

# Application Settings
MAX_STOCKS=100
CACHE_TTL=3600
```

### 3. Start the Application

```bash
# Using Streamlit directly
streamlit run app.py

# Using Docker Compose
docker-compose up --build
```

## Configuration Files

### Local Development (`config/local.env`)

```ini
# Environment
MOMENTUM_ENV=local
DEBUG=true

# Database
DATABASE_URL=postgresql://momentum_user:momentum_password@localhost:5432/momentum_calc
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=momentum_calc
POSTGRES_USER=momentum_user
POSTGRES_PASSWORD=momentum_password

# Application
MAX_STOCKS=100
CACHE_TTL=3600
```

### Cloud Deployment

For Streamlit Cloud, set these as secrets in your Streamlit Cloud dashboard:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key

## Environment Detection

The system automatically detects the environment based on:

1. **Explicit Environment Variable**: `MOMENTUM_ENV=local|cloud`
2. **Streamlit Cloud**: `STREAMLIT_SHARING_MODE=true`
3. **Supabase URL**: Valid Supabase URL in environment
4. **Local Indicators**: `DATABASE_URL` or `POSTGRES_HOST` set
5. **Docker**: Running in Docker container
6. **Default**: Falls back to local development

## Configuration Classes

### BaseConfig

Abstract base class with common functionality:
- Environment detection
- Database configuration
- Application settings
- Logging configuration
- Configuration validation

### LocalConfig

For local development:
- PostgreSQL or SQLite support
- Docker Compose integration
- Local file system access
- Debug mode support

### CloudConfig

For cloud deployment:
- Supabase integration
- Streamlit secrets support
- Production optimizations
- Fallback to local PostgreSQL

## Usage in Code

```python
from config.loader import get_config

# Get configuration manager
config_manager = get_config()

# Get specific configurations
db_config = config_manager.get_database_config()
app_config = config_manager.get_app_config()
logging_config = config_manager.get_logging_config()

# Check environment
if config_manager.is_local():
    print("Running in local development mode")
elif config_manager.is_cloud():
    print("Running in cloud deployment mode")
```

## Database Adapters

The system automatically selects the right database adapter:

- **Local**: Uses `LocalDatabase` for PostgreSQL/SQLite
- **Cloud**: Uses `SupabaseDatabase` for Supabase
- **Fallback**: Falls back to local if cloud config is invalid

## Security

- Local configuration files are excluded from Git
- Sensitive information is not committed to version control
- Cloud secrets are handled by Streamlit Cloud
- Environment variables are loaded securely

## Troubleshooting

### Configuration Not Loading

1. Check if `config/local.env` exists
2. Verify environment variables are set correctly
3. Check logs for configuration errors

### Database Connection Issues

1. Verify database credentials in `config/local.env`
2. Ensure database is running (for local PostgreSQL)
3. Check network connectivity (for cloud databases)

### Environment Detection Issues

1. Set `MOMENTUM_ENV` explicitly
2. Check environment variable values
3. Verify file paths and permissions

## File Structure

```
web_app/
├── config/
│   ├── __init__.py
│   ├── base_config.py
│   ├── local_config.py
│   ├── cloud_config.py
│   ├── config_manager.py
│   ├── loader.py
│   ├── local.env.template
│   └── cloud.env.template
├── config/
│   └── local.env          # Created by setup script (not in Git)
├── setup_config.py
└── CONFIGURATION.md
```

## Best Practices

1. **Never commit sensitive data**: Use templates and local files
2. **Use environment variables**: For deployment-specific settings
3. **Validate configurations**: The system validates all configs
4. **Use appropriate adapters**: Let the system choose the right database
5. **Test both environments**: Ensure local and cloud configs work
