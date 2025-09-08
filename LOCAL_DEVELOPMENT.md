# Local Development Setup

This guide will help you set up the Momentum Calculator for local development using Docker containers.

## 🏗️ Architecture

The local development environment includes:
- **Streamlit Web App** (Port 8501)
- **PostgreSQL Database** (Port 5432)
- **Database Inspector** (Optional debugging tool)

## 🚀 Quick Start

### Option 1: Automated Setup
```bash
# Run the startup script
./start_local.sh
```

### Option 2: Manual Setup

1. **Create environment file:**
```bash
cp env.example .env
# Edit .env with your Supabase credentials if needed
```

2. **Generate clean data:**
```bash
python extract_clean_data.py
python clean_csv_data.py
```

3. **Start services:**
```bash
docker-compose up --build
```

## 📱 Access Points

- **Streamlit App**: http://localhost:8501
- **PostgreSQL**: localhost:5432
- **Database Inspector**: Check `docker logs momentum_db_inspector`

## 🔧 Database Configuration

### Local PostgreSQL (Default)
- **Host**: localhost
- **Port**: 5432
- **Database**: momentum_calc
- **Username**: momentum_user
- **Password**: momentum_password

### Environment Variables
The app automatically detects the environment:
- **Local Development**: Uses PostgreSQL when `DATABASE_URL` or `POSTGRES_HOST` is set
- **Production**: Uses Supabase when `SUPABASE_URL` is set

## 📊 Data Loading

The database is automatically initialized with:
- **Stock Metadata**: 2,525 stocks
- **Price Data**: 960,294 records (last 2 years)
- **Momentum Scores**: 646 records

## 🛠️ Development Commands

### Start Services
```bash
docker-compose up
```

### Rebuild and Start
```bash
docker-compose up --build
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs webapp
docker-compose logs postgres
```

### Database Access
```bash
# Connect to PostgreSQL
docker exec -it momentum_postgres psql -U momentum_user -d momentum_calc

# Run database inspector
docker-compose up db-inspector
```

## 🔄 Data Updates

### Regenerate Clean Data
```bash
python extract_clean_data.py
python clean_csv_data.py
```

### Reload Database
```bash
docker-compose down
docker volume rm web_app_postgres_data
docker-compose up --build
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8501
lsof -i :8501

# Check what's using port 5432
lsof -i :5432
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check PostgreSQL logs
docker-compose logs postgres
```

### App Not Loading
```bash
# Check app logs
docker-compose logs webapp

# Rebuild the app
docker-compose up --build webapp
```

## 📁 File Structure

```
web_app/
├── Dockerfile                 # Streamlit app container
├── docker-compose.yml         # Multi-service orchestration
├── init.sql                   # Database initialization
├── start_local.sh            # Startup script
├── env.example               # Environment template
├── data/                     # CSV data files
│   ├── clean_stock_metadata.csv
│   ├── clean_ticker_price.csv
│   └── clean_momentum_scores.csv
└── src/                      # Application code
    ├── database_smart.py     # Smart database adapter
    ├── database_local.py     # Local PostgreSQL adapter
    └── database_supabase.py  # Supabase adapter
```

## 🔄 Streamlit Cloud Compatibility

The app automatically detects the environment:
- **Local**: Uses PostgreSQL with Docker Compose
- **Streamlit Cloud**: Uses Supabase with secrets

No code changes needed for deployment!

## 🎯 Next Steps

1. **Start the local environment**: `./start_local.sh`
2. **Access the app**: http://localhost:8501
3. **Make your changes** in the code
4. **Test locally** with the containerized setup
5. **Deploy to Streamlit Cloud** - it will automatically use Supabase
