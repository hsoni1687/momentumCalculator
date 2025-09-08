# Database Directory

This directory contains the SQLite database file for the Indian Stock Momentum Calculator.

## Database File

- **stock_data.db**: SQLite database containing:
  - Stock metadata (2,500+ Indian stocks)
  - Historical price data (OHLCV)
  - Momentum scores and calculations
  - Industry and sector classifications

## Setup Instructions

1. **For Local Development**: 
   - Copy `stock_data.db` from the main project directory to this folder
   - The database file is approximately 182MB

2. **For Production Deployment**:
   - Ensure the database file is in this directory
   - The application will automatically use this database

## Database Schema

### Tables:
- `stockMetadata`: Company information, market cap, industry, sector
- `tickerPrice`: Historical OHLCV price data
- `momentumScores`: Calculated momentum metrics

## Note

The database file is excluded from Git due to size limitations. 
Please ensure you have the database file in this directory before running the application.
