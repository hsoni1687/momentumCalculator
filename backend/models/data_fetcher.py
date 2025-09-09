"""
Data Fetcher for retrieving stock price data from external sources
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import yfinance as yf
import time
import random
from .momentum_storage import MomentumStorage
from .momentum import MomentumService

logger = logging.getLogger(__name__)

class YahooFinanceFetcher:
    """Fetch stock data from Yahoo Finance"""
    
    def __init__(self):
        """Initialize Yahoo Finance fetcher"""
        self.session = None
        self.rate_limit_delay = 1  # seconds between requests
        self.max_retries = 3
        
    def _get_ticker_symbol(self, stock: str) -> str:
        """Convert stock symbol to Yahoo Finance format"""
        # Remove .NS suffix if present and add it back for Yahoo Finance
        if stock.endswith('.NS'):
            return stock
        else:
            return f"{stock}.NS"
    
    def fetch_stock_data(self, stock: str, start_date: date = None, end_date: date = None) -> Tuple[bool, pd.DataFrame, str]:
        """
        Fetch stock data from Yahoo Finance
        
        Returns:
            Tuple of (success, dataframe, error_message)
        """
        try:
            # Convert to Yahoo Finance symbol
            yf_symbol = self._get_ticker_symbol(stock)
            
            # Set default date range if not provided
            if not start_date:
                start_date = date.today() - timedelta(days=365)  # 1 year of data
            if not end_date:
                end_date = date.today()
            
            logger.info(f"Fetching data for {stock} ({yf_symbol}) from {start_date} to {end_date}")
            
            # Create ticker object
            ticker = yf.Ticker(yf_symbol)
            
            # Fetch historical data
            hist_data = ticker.history(
                start=start_date,
                end=end_date,
                interval='1d',
                auto_adjust=True,
                prepost=False,
                threads=True
            )
            
            if hist_data.empty:
                return False, pd.DataFrame(), f"No data available for {stock}"
            
            # Clean and format the data
            hist_data = hist_data.reset_index()
            hist_data.columns = hist_data.columns.str.lower()
            
            # Rename columns to match our database schema
            column_mapping = {
                'date': 'date',
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            
            # Keep only the columns we need
            hist_data = hist_data[list(column_mapping.keys())]
            hist_data = hist_data.rename(columns=column_mapping)
            
            # Ensure date column is datetime
            hist_data['date'] = pd.to_datetime(hist_data['date']).dt.date
            
            # Add stock symbol
            hist_data['stock'] = stock
            
            # Remove any rows with missing critical data
            hist_data = hist_data.dropna(subset=['open', 'high', 'low', 'close'])
            
            # Sort by date
            hist_data = hist_data.sort_values('date')
            
            logger.info(f"Successfully fetched {len(hist_data)} records for {stock} from {start_date} to {end_date}")
            return True, hist_data, ""
            
        except Exception as e:
            error_msg = f"Error fetching data for {stock}: {str(e)}"
            logger.error(error_msg)
            return False, pd.DataFrame(), error_msg
    
    def fetch_multiple_stocks(self, stocks: List[str], start_date: date = None, end_date: date = None) -> Dict[str, Tuple[bool, pd.DataFrame, str]]:
        """
        Fetch data for multiple stocks with rate limiting
        
        Returns:
            Dict mapping stock symbol to (success, dataframe, error_message)
        """
        results = {}
        
        for i, stock in enumerate(stocks):
            try:
                # Rate limiting
                if i > 0:
                    delay = self.rate_limit_delay + random.uniform(0, 0.5)  # Add some randomness
                    time.sleep(delay)
                
                success, data, error = self.fetch_stock_data(stock, start_date, end_date)
                results[stock] = (success, data, error)
                
                if success:
                    logger.info(f"Successfully fetched data for {stock} from {start_date} to {end_date}")
                else:
                    logger.warning(f"Failed to fetch data for {stock}: {error}")
                    
            except Exception as e:
                logger.error(f"Unexpected error fetching data for {stock}: {e}")
                results[stock] = (False, pd.DataFrame(), str(e))
        
        return results

class DataUpdater:
    """Update stock price data in database"""
    
    def __init__(self, database, update_tracker):
        """Initialize data updater"""
        self.db = database
        self.update_tracker = update_tracker
        self.data_fetcher = YahooFinanceFetcher()
        self.momentum_storage = MomentumStorage(database)
        self.momentum_service = MomentumService(database)
    
    def update_stock_price_data(self, stock: str) -> Tuple[bool, str]:
        """
        Update price data for a single stock
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Mark update as started
            self.update_tracker.mark_update_started(stock)
            
            # Check if stock exists in price table
            existing_data = self.db.get_price_data(stock)
            
            if not existing_data.empty:
                # Get the last date in existing data
                last_date = pd.to_datetime(existing_data['date']).max().date()
                start_date = last_date + timedelta(days=1)
                
                # Only fetch new data if we don't have today's data
                if start_date > date.today():
                    logger.info(f"Stock {stock} already has up-to-date data")
                    # Update last_price_date in stockMetadata table
                    self._update_stock_metadata_last_price_date(stock, last_date)
                    self.update_tracker.mark_update_completed(stock, len(existing_data), last_date)
                    return True, f"Stock {stock} already up-to-date"
            else:
                # No existing data, fetch from 1 year ago
                start_date = date.today() - timedelta(days=365)
            
            # Fetch new data
            success, new_data, error = self.data_fetcher.fetch_stock_data(stock, start_date, date.today())
            
            if not success:
                self.update_tracker.mark_update_failed(stock, error)
                return False, error
            
            if new_data.empty:
                # No new data available
                if not existing_data.empty:
                    last_date = pd.to_datetime(existing_data['date']).max().date()
                    # Update last_price_date in stockMetadata table
                    self._update_stock_metadata_last_price_date(stock, last_date)
                    self.update_tracker.mark_update_completed(stock, len(existing_data), last_date)
                return True, f"No new data available for {stock}"
            
            # Insert new data into database
            self._insert_price_data(new_data)
            
            # Get updated total count
            updated_data = self.db.get_price_data(stock)
            total_records = len(updated_data)
            last_price_date = pd.to_datetime(updated_data['date']).max().date()
            
            # Update last_price_date in stockMetadata table
            self._update_stock_metadata_last_price_date(stock, last_price_date)
            
            # Calculate and store momentum score for this stock
            self._calculate_and_store_momentum(stock)
            
            # Mark update as completed
            self.update_tracker.mark_update_completed(stock, total_records, last_price_date)
            
            return True, f"Successfully updated {stock} with {len(new_data)} new records"
            
        except Exception as e:
            error_msg = f"Error updating {stock}: {str(e)}"
            logger.error(error_msg)
            self.update_tracker.mark_update_failed(stock, error_msg)
            return False, error_msg
    
    def _insert_price_data(self, data: pd.DataFrame):
        """Insert price data into database"""
        try:
            # Prepare data for insertion
            data_to_insert = data.copy()
            
            # Ensure proper data types
            data_to_insert['date'] = pd.to_datetime(data_to_insert['date'])
            data_to_insert['open'] = pd.to_numeric(data_to_insert['open'], errors='coerce')
            data_to_insert['high'] = pd.to_numeric(data_to_insert['high'], errors='coerce')
            data_to_insert['low'] = pd.to_numeric(data_to_insert['low'], errors='coerce')
            data_to_insert['close'] = pd.to_numeric(data_to_insert['close'], errors='coerce')
            data_to_insert['volume'] = pd.to_numeric(data_to_insert['volume'], errors='coerce')
            
            # Remove any rows with NaN values
            data_to_insert = data_to_insert.dropna()
            
            if data_to_insert.empty:
                logger.warning("No valid data to insert after cleaning")
                return
            
            # Insert data using pandas to_sql
            with self.db.engine.connect() as conn:
                data_to_insert.to_sql(
                    'tickerprice',
                    conn,
                    if_exists='append',
                    index=False,
                    method='multi'
                )
                conn.commit()
            
            logger.info(f"Inserted {len(data_to_insert)} records into tickerprice table")
            
        except Exception as e:
            logger.error(f"Error inserting price data: {e}")
            raise
    
    def _update_stock_metadata_last_price_date(self, stock: str, last_price_date: date):
        """Update the last_price_date in stockMetadata table"""
        try:
            query = """
            UPDATE stockmetadata 
            SET last_price_date = %s 
            WHERE stock = %s
            """
            self.db.execute_query(query, (last_price_date, stock))
            logger.info(f"Updated last_price_date for {stock} to {last_price_date}")
        except Exception as e:
            logger.error(f"Error updating last_price_date for {stock}: {e}")
            # Don't raise the exception as this is not critical for the main update process
    
    def _calculate_and_store_momentum(self, stock: str):
        """Calculate and store momentum score for a single stock"""
        try:
            # Get stock metadata
            stocks_df = self.db.get_stock_metadata()
            stock_metadata = stocks_df[stocks_df['stock'] == stock]
            
            if stock_metadata.empty:
                logger.warning(f"No metadata found for {stock}")
                return
            
            # Get historical data for this stock
            historical_data = self.momentum_service.get_historical_data_from_db([stock])
            
            if not historical_data or stock not in historical_data:
                logger.warning(f"No historical data found for {stock}")
                return
            
            # Calculate momentum scores
            momentum_df = self.momentum_service.calculate_momentum_scores(stock_metadata, historical_data)
            
            if not momentum_df.empty:
                # Store momentum scores
                success = self.momentum_storage.store_momentum_scores(momentum_df)
                if success:
                    logger.info(f"Successfully calculated and stored momentum for {stock}")
                else:
                    logger.error(f"Failed to store momentum for {stock}")
            else:
                logger.warning(f"No momentum scores calculated for {stock}")
                
        except Exception as e:
            logger.error(f"Error calculating momentum for {stock}: {e}")
            # Don't raise the exception as this is not critical for the main update process
    
    def bulk_update_stocks(self, stocks: List[str]) -> Dict[str, Tuple[bool, str]]:
        """
        Update price data for multiple stocks
        
        Returns:
            Dict mapping stock symbol to (success, message)
        """
        results = {}
        
        for stock in stocks:
            try:
                success, message = self.update_stock_price_data(stock)
                results[stock] = (success, message)
                
                # Small delay between updates to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = f"Unexpected error updating {stock}: {str(e)}"
                logger.error(error_msg)
                results[stock] = (False, error_msg)
        
        return results
