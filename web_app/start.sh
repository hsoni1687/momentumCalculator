#!/bin/bash

# Indian Stock Momentum Calculator - Startup Script

echo "🚀 Starting Indian Stock Momentum Calculator..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs static templates

# Check if database exists
if [ ! -f "data/stock_data.db" ]; then
    echo "⚠️  Database not found. Please ensure stock_data.db is in the data/ directory."
    echo "   You can copy it from the main project directory."
fi

# Start the application
echo "🌟 Starting Streamlit application..."
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
