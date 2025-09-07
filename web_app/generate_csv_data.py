#!/usr/bin/env python3
"""
Generate CSV files with comprehensive stock data for PostgreSQL import
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random

def generate_stock_metadata():
    """Generate comprehensive stock metadata with 2400+ stocks"""
    
    # Define sectors and industries for realistic distribution
    sectors_industries = {
        'Technology': ['IT Services', 'Software', 'Hardware', 'Telecom Equipment', 'Semiconductors'],
        'Financial Services': ['Banking', 'NBFC', 'Insurance', 'Asset Management', 'Broking'],
        'Consumer Goods': ['FMCG', 'Textiles', 'Apparel', 'Footwear', 'Personal Care'],
        'Healthcare': ['Pharmaceuticals', 'Biotechnology', 'Medical Devices', 'Hospitals', 'Diagnostics'],
        'Energy': ['Oil & Gas', 'Power', 'Coal', 'Renewable Energy', 'Petrochemicals'],
        'Materials': ['Cement', 'Steel', 'Chemicals', 'Paints', 'Mining'],
        'Industrials': ['Construction', 'Engineering', 'Machinery', 'Automotive', 'Aerospace'],
        'Consumer Discretionary': ['Automobiles', 'Retail', 'Entertainment', 'Jewelry', 'Real Estate'],
        'Utilities': ['Power Generation', 'Power Distribution', 'Water', 'Gas Distribution'],
        'Telecommunications': ['Telecom Services', 'Internet Services', 'Cable TV'],
        'Real Estate': ['Real Estate Development', 'Real Estate Investment', 'Construction Materials'],
        'Agriculture': ['Fertilizers', 'Seeds', 'Pesticides', 'Food Processing'],
        'Transportation': ['Logistics', 'Shipping', 'Aviation', 'Railways'],
        'Media': ['Broadcasting', 'Publishing', 'Digital Media', 'Advertising']
    }
    
    # Generate 2400+ stocks
    stocks_data = []
    stock_counter = 1
    
    # Major stocks (first 100) - removed duplicates
    major_stocks = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ITC', 'WIPRO', 'BHARTIARTL', 
        'SBIN', 'KOTAKBANK', 'LT', 'MARUTI', 'ASIANPAINT', 'NESTLEIND', 'BAJFINANCE',
        'TITAN', 'ULTRACEMCO', 'SUNPHARMA', 'TECHM', 'POWERGRID', 'HCLTECH', 'AXISBANK',
        'ONGC', 'NTPC', 'COALINDIA', 'M&M', 'TATAMOTORS', 'ADANIPORTS', 'JSWSTEEL',
        'TATASTEEL', 'DRREDDY', 'CIPLA', 'BRITANNIA', 'DIVISLAB', 'EICHERMOT', 'GRASIM',
        'HDFCLIFE', 'ICICIBANK', 'INDUSINDBK', 'LTTS', 'MCDOWELL-N', 'PIDILITIND',
        'SHREECEM', 'TATACONSUM', 'ZEEL', 'ADANIGREEN', 'ADANITRANS',
        'APOLLOHOSP', 'BAJAJFINSV', 'BAJAJHLDNG', 'BERGEPAINT', 'BIOCON', 'BOSCHLTD',
        'CADILAHC', 'COLPAL', 'DABUR', 'DMART', 'GAIL', 'GODREJCP',
        'HEROMOTOCO', 'HINDALCO', 'HINDPETRO', 'ICICIGI', 'ICICIPRULI', 'IGL', 'INDIGO',
        'JINDALSTEL', 'JUBLFOOD', 'LALPATHLAB', 'LICHSGFIN', 'LUPIN',
        'MFSL', 'MINDTREE', 'MOTHERSON', 'MPHASIS', 'MRF', 'MUTHOOTFIN', 'NAUKRI',
        'NMDC', 'PAGEIND', 'PETRONET', 'PNB',
        'PVR', 'RBLBANK', 'SAIL', 'SBILIFE', 'SIEMENS',
        'SRF', 'TATACHEM', 'TATAPOWER', 'TORNTPHARM', 'TVSMOTORS', 'UPL',
        'VEDL', 'YESBANK'
    ]
    
    # Generate major stocks first
    for i, stock in enumerate(major_stocks[:100]):
        sector = random.choice(list(sectors_industries.keys()))
        industry = random.choice(sectors_industries[sector])
        
        stocks_data.append({
            'stock': stock,
            'company_name': f'{stock} Ltd',
            'market_cap': random.randint(100000000000, 20000000000000),  # 100B to 20T
            'sector': sector,
            'industry': industry,
            'exchange': 'NSE',
            'dividend_yield': round(random.uniform(0.5, 4.0), 2),
            'roce': round(random.uniform(8.0, 45.0), 2),
            'roe': round(random.uniform(6.0, 40.0), 2)
        })
        stock_counter += 1
    
    # Generate remaining stocks (2300+ more)
    for i in range(2300):
        # Generate stock symbol
        stock_symbol = f'STOCK{stock_counter:04d}'
        
        # Select sector and industry
        sector = random.choice(list(sectors_industries.keys()))
        industry = random.choice(sectors_industries[sector])
        
        # Generate market cap (smaller for most stocks)
        market_cap = random.randint(1000000000, 500000000000)  # 1B to 500B
        
        stocks_data.append({
            'stock': stock_symbol,
            'company_name': f'{stock_symbol} Company Ltd',
            'market_cap': market_cap,
            'sector': sector,
            'industry': industry,
            'exchange': random.choice(['NSE', 'BSE']),
            'dividend_yield': round(random.uniform(0.0, 6.0), 2),
            'roce': round(random.uniform(5.0, 50.0), 2),
            'roe': round(random.uniform(3.0, 45.0), 2)
        })
        stock_counter += 1
    
    df = pd.DataFrame(stocks_data)
    df['last_updated'] = datetime.now()
    
    return df

def generate_price_data(stock_symbol, start_date, end_date, base_price=1000):
    """Generate realistic price data for a stock"""
    
    # Set random seed based on stock symbol for consistency
    random.seed(hash(stock_symbol) % 2**32)
    np.random.seed(hash(stock_symbol) % 2**32)
    
    # Generate date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    # Remove weekends
    date_range = date_range[date_range.weekday < 5]
    
    # Generate price data
    prices = []
    current_price = base_price + random.randint(-200, 200)
    
    for date in date_range:
        # Daily price movement (realistic volatility)
        daily_return = np.random.normal(0, 0.02)  # 2% daily volatility
        current_price *= (1 + daily_return)
        
        # Ensure price doesn't go too low
        current_price = max(current_price, base_price * 0.3)
        
        # Generate OHLC data
        open_price = current_price
        high_price = open_price * (1 + abs(np.random.normal(0, 0.01)))
        low_price = open_price * (1 - abs(np.random.normal(0, 0.01)))
        close_price = open_price * (1 + np.random.normal(0, 0.005))
        
        # Ensure high >= max(open, close) and low <= min(open, close)
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)
        
        # Generate volume
        volume = random.randint(100000, 5000000)
        
        prices.append({
            'stock': stock_symbol,
            'date': date.date(),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
        
        current_price = close_price
    
    return pd.DataFrame(prices)

def main():
    """Generate all CSV files"""
    
    print("🚀 Generating comprehensive stock data...")
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Generate stock metadata
    print("📊 Generating stock metadata...")
    metadata_df = generate_stock_metadata()
    metadata_df.to_csv('data/stock_metadata.csv', index=False)
    print(f"✅ Generated metadata for {len(metadata_df)} stocks")
    
    # Generate price data for all stocks
    print("📈 Generating price data...")
    start_date = datetime.now() - timedelta(days=730)  # 2 years
    end_date = datetime.now()
    
    all_price_data = []
    
    # Process stocks in batches to manage memory
    batch_size = 100
    total_stocks = len(metadata_df)
    
    for batch_start in range(0, total_stocks, batch_size):
        batch_end = min(batch_start + batch_size, total_stocks)
        batch_stocks = metadata_df.iloc[batch_start:batch_end]
        
        print(f"  Processing batch {batch_start//batch_size + 1}/{(total_stocks + batch_size - 1)//batch_size} ({batch_start+1}-{batch_end} of {total_stocks})")
        
        for _, stock in batch_stocks.iterrows():
            # Use market cap to determine base price (larger companies = higher prices)
            base_price = max(50, min(10000, stock['market_cap'] / 1000000000))  # Scale market cap to price
            
            price_data = generate_price_data(
                stock['stock'], 
                start_date, 
                end_date, 
                base_price
            )
            
            all_price_data.append(price_data)
    
    # Combine all price data
    print("📊 Combining all price data...")
    combined_price_data = pd.concat(all_price_data, ignore_index=True)
    combined_price_data.to_csv('data/ticker_price.csv', index=False)
    
    print(f"✅ Generated price data: {len(combined_price_data)} records for {len(metadata_df)} stocks")
    
    # Generate momentum scores for all stocks
    print("📊 Generating momentum scores...")
    momentum_data = []
    
    for _, stock in metadata_df.iterrows():
        # Generate realistic momentum scores
        total_score = random.uniform(0, 100)
        raw_momentum_6m = random.uniform(-20, 30)
        raw_momentum_3m = random.uniform(-15, 25)
        raw_momentum_1m = random.uniform(-10, 20)
        
        momentum_data.append({
            'stock': stock['stock'],
            'total_score': round(total_score, 4),
            'raw_momentum_6m': round(raw_momentum_6m, 4),
            'raw_momentum_3m': round(raw_momentum_3m, 4),
            'raw_momentum_1m': round(raw_momentum_1m, 4),
            'volatility_adjusted_6m': round(raw_momentum_6m * 0.8, 4),
            'volatility_adjusted_3m': round(raw_momentum_3m * 0.8, 4),
            'volatility_adjusted_1m': round(raw_momentum_1m * 0.8, 4),
            'relative_strength_6m': round(total_score * 0.3, 4),
            'relative_strength_3m': round(total_score * 0.4, 4),
            'relative_strength_1m': round(total_score * 0.3, 4),
            'trend_score': round(total_score * 0.2, 4),
            'volume_score': round(total_score * 0.1, 4),
            'calculated_at': datetime.now()
        })
    
    momentum_df = pd.DataFrame(momentum_data)
    momentum_df.to_csv('data/momentum_scores.csv', index=False)
    
    print(f"✅ Generated momentum scores for {len(momentum_df)} stocks")
    
    # Print summary
    print("\n📋 Data Generation Summary:")
    print(f"  Stock Metadata: {len(metadata_df)} records")
    print(f"  Price Data: {len(combined_price_data)} records")
    print(f"  Momentum Scores: {len(momentum_df)} records")
    print(f"  Date Range: {start_date.date()} to {end_date.date()}")
    print(f"  Files created in 'data/' directory")
    
    print("\n✅ All CSV files generated successfully!")

if __name__ == "__main__":
    main()
