#!/bin/bash

# Local Development Startup Script
echo "🚀 Starting Momentum Calculator Local Development Environment"
echo "=============================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file. Please edit it with your Supabase credentials if needed."
fi

# Check if clean data files exist
if [ ! -f "data/clean_stock_metadata.csv" ]; then
    echo "📊 Generating clean data files..."
    python extract_clean_data.py
    python clean_csv_data.py
    echo "✅ Clean data files generated."
fi

# Start the services
echo "🐳 Starting Docker Compose services..."
docker-compose up --build

echo "🎉 Local development environment started!"
echo "📱 Streamlit app: http://localhost:8501"
echo "🗄️  PostgreSQL: localhost:5432"
echo "📊 Database Inspector: Check docker logs momentum_db_inspector"
