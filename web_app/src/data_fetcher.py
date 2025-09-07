"""
Data fetching module for Indian stock market data from NSE and BSE
"""

import pandas as pd
import numpy as np
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import logging
from database import StockDatabase
from stock_lists import get_all_stocks, get_nse_stocks, get_bse_stocks, get_top_stocks_by_market_cap

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndianStockDataFetcher:
    def __init__(self, db_path=None):
        if db_path is None:
            # Use database in the data directory
            import os
            current_dir = os.path.dirname(os.path.dirname(__file__))
            db_path = os.path.join(current_dir, 'data', 'stock_data.db')
        
        self.nse_url = "https://www.nseindia.com"
        self.bse_url = "https://www.bseindia.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.db = StockDatabase(db_path)
    
    def get_nse_stock_list(self):
        """Get NSE stocks from database"""
        try:
            all_stocks = self.get_all_stocks_data()
            nse_stocks = all_stocks[all_stocks['exchange'] == 'NSE']
            logger.info(f"Retrieved {len(nse_stocks)} NSE stocks from database")
            return nse_stocks
                
        except Exception as e:
            logger.error(f"Error fetching NSE stock list: {e}")
            return pd.DataFrame()
    
    def get_bse_stock_list(self):
        """Get BSE stocks from database"""
        try:
            all_stocks = self.get_all_stocks_data()
            bse_stocks = all_stocks[all_stocks['exchange'] == 'BSE']
            logger.info(f"Retrieved {len(bse_stocks)} BSE stocks from database")
            return bse_stocks
            
        except Exception as e:
            logger.error(f"Error fetching BSE stock list: {e}")
            return pd.DataFrame()
    
    def get_historical_data(self, symbol, period="1y", force_refresh=False):
        """Fetch historical OHLC data for a stock from database or API with smart updates"""
        try:
            # Check if we have recent data in database
            if not force_refresh:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=365)  # 1 year
                
                # Try with .NS suffix first, then without
                db_data = self.db.get_price_data(f"{symbol}.NS", start_date, end_date)
                if db_data.empty:
                    db_data = self.db.get_price_data(symbol, start_date, end_date)
                
                if not db_data.empty:
                    # Check if data is recent enough (within last 2 days)
                    latest_date = db_data.index.max().date()
                    days_old = (datetime.now().date() - latest_date).days
                    
                    if days_old <= 2:
                        logger.info(f"Using cached data for {symbol} (last updated: {latest_date})")
                        # Calculate additional metrics
                        db_data['Returns'] = db_data['close'].pct_change()
                        db_data['Volatility'] = db_data['Returns'].rolling(window=20).std()
                        db_data['SMA_20'] = db_data['close'].rolling(window=20).mean()
                        db_data['SMA_50'] = db_data['close'].rolling(window=50).mean()
                        
                        # Rename columns to match expected format
                        db_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Returns', 'Volatility', 'SMA_20', 'SMA_50']
                        return db_data
                    else:
                        # Smart update: only fetch missing dates
                        logger.info(f"Smart update for {symbol}: data is {days_old} days old")
                        latest_db_date = self.db.get_latest_date_for_stock(f"{symbol}.NS")
                        if not latest_db_date:
                            latest_db_date = self.db.get_latest_date_for_stock(symbol)
                        
                        if latest_db_date:
                            # Only fetch data from the day after our latest date
                            # Convert to datetime to avoid timezone issues
                            smart_start_date = datetime.combine(latest_db_date + timedelta(days=1), datetime.min.time())
                            logger.info(f"Fetching incremental data for {symbol} from {smart_start_date}")
                            new_data = self._fetch_from_api(symbol, period, smart_start_date)
                            
                            # Combine with existing data
                            if not new_data.empty:
                                # Ensure both datasets have timezone-naive index
                                if new_data.index.tz is not None:
                                    new_data.index = new_data.index.tz_localize(None)
                                if db_data.index.tz is not None:
                                    db_data.index = db_data.index.tz_localize(None)
                                
                                # Ensure both datasets have the same column structure
                                # Keep only the basic OHLCV columns from new_data and rename to lowercase
                                new_data_clean = new_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                                new_data_clean.columns = ['open', 'high', 'low', 'close', 'volume']
                                
                                combined_data = pd.concat([db_data, new_data_clean]).sort_index()
                                # Remove duplicates
                                combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                                
                                # Calculate additional metrics using lowercase columns
                                combined_data['Returns'] = combined_data['close'].pct_change()
                                combined_data['Volatility'] = combined_data['Returns'].rolling(window=20).std()
                                combined_data['SMA_20'] = combined_data['close'].rolling(window=20).mean()
                                combined_data['SMA_50'] = combined_data['close'].rolling(window=50).mean()
                                
                                # Rename columns to uppercase for consistency with momentum calculator
                                combined_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Returns', 'Volatility', 'SMA_20', 'SMA_50']
                                return combined_data
            
            # Fetch fresh data from API
            logger.info(f"Fetching fresh data for {symbol}")
            return self._fetch_from_api(symbol, period)
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_from_api(self, symbol, period="1y", start_date=None, end_date=None):
        """Fetch data from yfinance API and store in database"""
        try:
            # Add .NS suffix for NSE stocks if not present
            if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
                symbol = f"{symbol}.NS"
            
            ticker = yf.Ticker(symbol)
            
            # Use start_date and end_date if provided, otherwise use period
            if start_date and end_date:
                hist = ticker.history(start=start_date, end=end_date)
            elif start_date:
                hist = ticker.history(start=start_date)
            else:
                hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"No historical data found for {symbol}")
                return pd.DataFrame()
            
            # Store in database
            self.db.store_price_data(symbol, hist)
            
            # Calculate additional metrics
            hist['Returns'] = hist['Close'].pct_change()
            hist['Volatility'] = hist['Returns'].rolling(window=20).std()
            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
            
            return hist
            
        except Exception as e:
            logger.error(f"Error fetching from API for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_all_stocks_data(self):
        """Get combined data from database (primary source)"""
        logger.info("Fetching stock data from database...")
        
        # Get from database (this is now our primary source)
        db_stocks = self.db.get_stock_metadata()
        
        if not db_stocks.empty:
            logger.info(f"Retrieved {len(db_stocks)} stocks from database")
            return db_stocks
        else:
            logger.warning("No stocks found in database. Please run import_excel_data.py import first.")
            return pd.DataFrame()
    
    def get_top_stocks_by_market_cap(self, n=None, industry=None, sector=None):
        """Get top N stocks by market capitalization with optional industry/sector filtering"""
        from config import STOCK_SELECTION_SETTINGS
        
        if n is None:
            n = STOCK_SELECTION_SETTINGS['default_stocks_to_analyze']
        
        all_stocks = self.get_all_stocks_data()
        
        # Apply filters
        filtered_stocks = all_stocks.copy()
        
        if industry:
            filtered_stocks = filtered_stocks[filtered_stocks['industry'] == industry]
            logger.info(f"Filtered by industry '{industry}': {len(filtered_stocks)} stocks")
        
        if sector:
            filtered_stocks = filtered_stocks[filtered_stocks['sector'] == sector]
            logger.info(f"Filtered by sector '{sector}': {len(filtered_stocks)} stocks")
        
        if filtered_stocks.empty:
            logger.warning(f"No stocks found matching filters: industry={industry}, sector={sector}")
            return pd.DataFrame()
        
        # Sort by market cap and get top N
        top_stocks = filtered_stocks.nlargest(n, 'market_cap')
        
        logger.info(f"Selected top {len(top_stocks)} stocks by market cap (filtered)")
        return top_stocks
    
    def get_top_100_by_market_cap(self):
        """Get top 100 stocks by market capitalization (backward compatibility)"""
        return self.get_top_stocks_by_market_cap(100)
    
    def get_available_industries(self):
        """Get list of available industries"""
        try:
            metadata = self.db.get_stock_metadata()
            industries = metadata[
                (metadata['industry'].notna()) & 
                (metadata['industry'] != '') & 
                (metadata['industry'] != 'Unknown')
            ]['industry'].unique()
            return sorted(industries.tolist())
        except Exception as e:
            logger.error(f"Error getting available industries: {e}")
            return []
    
    def get_available_sectors(self):
        """Get list of available sectors"""
        try:
            metadata = self.db.get_stock_metadata()
            sectors = metadata[
                (metadata['sector'].notna()) & 
                (metadata['sector'] != 'Unknown')
            ]['sector'].unique()
            return sorted(sectors.tolist())
        except Exception as e:
            logger.error(f"Error getting available sectors: {e}")
            return []
    
    def update_stock_data(self, symbols=None, force_refresh=False):
        """Update stock data for specified symbols or all stocks"""
        if symbols is None:
            # Get all stocks that need updates
            symbols = self.db.get_stocks_needing_update()
        
        if not symbols:
            logger.info("No stocks need updates")
            return
        
        logger.info(f"Updating data for {len(symbols)} stocks")
        
        for symbol in symbols:
            try:
                logger.info(f"Updating data for {symbol}")
                self.get_historical_data(symbol, force_refresh=force_refresh)
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.error(f"Error updating {symbol}: {e}")
    
    def refresh_all_stock_data(self):
        """Refresh all stock price data to current date for all stocks in database"""
        try:
            # Get all stocks from database
            all_stocks = self.db.get_stock_metadata()
            
            if all_stocks.empty:
                logger.warning("No stocks found in database")
                return False
            
            logger.info(f"Starting smart refresh for {len(all_stocks)} stocks")
            
            # Get all unique symbols
            symbols = all_stocks['symbol'].unique()
            
            success_count = 0
            error_count = 0
            skipped_count = 0
            
            for i, symbol in enumerate(symbols):
                try:
                    logger.info(f"Checking data for {symbol} ({i+1}/{len(symbols)})")
                    
                    # Check if we need to update this stock
                    latest_db_date = self.db.get_latest_date_for_stock(f"{symbol}.NS")
                    if not latest_db_date:
                        latest_db_date = self.db.get_latest_date_for_stock(symbol)
                    
                    if latest_db_date:
                        days_old = (datetime.now().date() - latest_db_date).days
                        
                        if days_old <= 2:
                            logger.info(f"Skipping {symbol} - data is fresh ({days_old} days old)")
                            skipped_count += 1
                            continue
                        else:
                            logger.info(f"Updating {symbol} - data is {days_old} days old")
                            # Use smart update (don't force refresh)
                            self.get_historical_data(symbol, force_refresh=False)
                            success_count += 1
                    else:
                        logger.info(f"No existing data for {symbol}, fetching full history")
                        # No existing data, fetch full history
                        self.get_historical_data(symbol, force_refresh=True)
                        success_count += 1
                    
                    # Rate limiting to avoid API blocks
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error refreshing {symbol}: {e}")
                    error_count += 1
            
            logger.info(f"Smart refresh completed: {success_count} updated, {skipped_count} skipped, {error_count} errors")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error in refresh_all_stock_data: {e}")
            return False

    def get_update_summary(self):
        """Get summary of stocks that need updates"""
        try:
            all_stocks = self.db.get_stock_metadata()
            if all_stocks.empty:
                return {"total_stocks": 0, "needs_update": 0, "fresh": 0, "no_data": 0}
            
            symbols = all_stocks['symbol'].unique()
            needs_update = 0
            fresh = 0
            no_data = 0
            
            for symbol in symbols:
                latest_db_date = self.db.get_latest_date_for_stock(f"{symbol}.NS")
                if not latest_db_date:
                    latest_db_date = self.db.get_latest_date_for_stock(symbol)
                
                if latest_db_date:
                    days_old = (datetime.now().date() - latest_db_date).days
                    if days_old <= 2:
                        fresh += 1
                    else:
                        needs_update += 1
                else:
                    no_data += 1
            
            return {
                "total_stocks": len(symbols),
                "needs_update": needs_update,
                "fresh": fresh,
                "no_data": no_data
            }
            
        except Exception as e:
            logger.error(f"Error getting update summary: {e}")
            return {"total_stocks": 0, "needs_update": 0, "fresh": 0, "no_data": 0}

    def get_database_stats(self):
        """Get database statistics"""
        return self.db.get_database_stats()

if __name__ == "__main__":
    fetcher = IndianStockDataFetcher()
    top_100_stocks = fetcher.get_top_100_by_market_cap()
    print(top_100_stocks.head())
