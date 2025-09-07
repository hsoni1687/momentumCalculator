#!/usr/bin/env python3
"""
Database setup script for Indian Stock Momentum Calculator
This script populates the database with initial stock data from stock_lists.py
"""

import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

from src.database import StockDatabase
from src.stock_lists import get_all_stocks
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Setup database with initial stock data"""
    
    # Initialize database
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'stock_data.db')
    db = StockDatabase(db_path)
    
    logger.info("Setting up database with initial stock data...")
    
    # Get all stocks from stock_lists.py
    all_stocks = get_all_stocks()
    logger.info(f"Found {len(all_stocks)} stocks in stock_lists.py")
    
    # Prepare stock metadata as DataFrame for database
    import pandas as pd
    
    stock_data = []
    for stock in all_stocks:
        stock_data.append({
            'symbol': stock['symbol'],
            'company_name': stock['company_name'],
            'market_cap': stock['market_cap'],
            'sector': stock['sector'],
            'exchange': stock['exchange']
        })
    
    # Convert to DataFrame
    stock_df = pd.DataFrame(stock_data)
    
    # Store stock metadata in database
    logger.info("Storing stock metadata in database...")
    try:
        db.store_stock_metadata(stock_df)
        logger.info(f"Successfully stored metadata for {len(stock_df)} stocks")
    except Exception as e:
        logger.error(f"Failed to store stock metadata: {e}")
        return False
    
    # Verify database setup
    try:
        metadata_df = db.get_stock_metadata()
        total_stocks = len(metadata_df)
        logger.info(f"Database setup complete! Total stocks in database: {total_stocks}")
        
        # Show some sample data
        if total_stocks > 0:
            sample_stocks = metadata_df.head(5)
            logger.info("Sample stocks in database:")
            for _, stock in sample_stocks.iterrows():
                logger.info(f"  {stock['stock']}: {stock['company_name']} (Market Cap: {stock['market_cap']})")
        else:
            logger.warning("No stocks found in database after setup")
    except Exception as e:
        logger.error(f"Failed to verify database setup: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        setup_database()
        print("✅ Database setup completed successfully!")
        print("You can now run the Streamlit app and it will have stock data to work with.")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)
