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
                prepost=False
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
        self.min_price_date = date(2024, 1, 2)  # Jan 2, 2024 (Jan 1 is holiday)
    
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
                    logger.info(f"Stock {stock} already has up-to-date data (last date: {last_date})")
                    # Update last_price_date in stockMetadata table
                    self._update_stock_metadata_last_price_date(stock, last_date)
                    self.update_tracker.mark_update_completed(stock, len(existing_data), last_date)
                    return True, f"Stock {stock} already up-to-date (last date: {last_date})"
                
                # If start_date is today, fetch from yesterday to today to get latest data
                if start_date == date.today():
                    start_date = date.today() - timedelta(days=1)
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
            SET last_price_date = :last_price_date 
            WHERE stock = :stock
            """
            self.db.execute_update(query, {"last_price_date": last_price_date, "stock": stock})
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
        Update price data for multiple stocks using batch processing
        
        Returns:
            Dict mapping stock symbol to (success, message)
        """
        results = {}
        
        # Process stocks in batches of 50 to avoid overwhelming Yahoo Finance
        batch_size = 50
        
        for i in range(0, len(stocks), batch_size):
            batch = stocks[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(stocks) + batch_size - 1)//batch_size}: {len(batch)} stocks")
            
            try:
                # Use batch processing for this batch
                batch_results = self._batch_update_stocks(batch)
                results.update(batch_results)
                
                # Small delay between batches to avoid rate limiting
                if i + batch_size < len(stocks):
                    time.sleep(2)
                    
            except Exception as e:
                error_msg = f"Batch processing error: {str(e)}"
                logger.error(error_msg)
                # Fall back to individual processing for this batch
                for stock in batch:
                    results[stock] = (False, error_msg)
        
        return results
    
    def _batch_update_stocks(self, stocks: List[str]) -> Dict[str, Tuple[bool, str]]:
        """
        Update price data for a batch of stocks using Yahoo Finance batch download
        
        Returns:
            Dict mapping stock symbol to (success, message)
        """
        results = {}
        
        try:
            # Get the date range for fetching
            today = date.today()
            start_date = today - timedelta(days=5)  # Fetch last 5 days to ensure we get latest data
            
            logger.info(f"Batch fetching data for {len(stocks)} stocks from {start_date} to {today}")
            
            # Use yf.download for batch processing
            batch_data = yf.download(stocks, start=start_date, end=today, group_by='ticker', progress=False, auto_adjust=True)
            
            if batch_data.empty:
                logger.warning("No data returned from batch download")
                for stock in stocks:
                    results[stock] = (False, "No data returned from Yahoo Finance")
                return results
            
            # Process each stock's data
            for stock in stocks:
                try:
                    # Extract data for this stock
                    if len(stocks) == 1:
                        # Single stock - data is not grouped
                        stock_data = batch_data
                    else:
                        # Multiple stocks - data is grouped by ticker
                        # Use a more efficient approach to avoid lexsort warnings
                        try:
                            # Try to access the stock data directly
                            stock_data = batch_data[stock]
                        except KeyError:
                            # If direct access fails, try with tuple notation
                            try:
                                stock_data = batch_data[(stock,)]
                            except KeyError:
                                logger.warning(f"No data found for {stock} in batch")
                                results[stock] = (False, "No data found in batch download")
                                continue
                    
                    # Process the stock data
                    success, message = self._process_stock_batch_data(stock, stock_data)
                    results[stock] = (success, message)
                    
                except Exception as e:
                    error_msg = f"Error processing batch data for {stock}: {str(e)}"
                    logger.error(error_msg)
                    results[stock] = (False, error_msg)
            
            logger.info(f"Batch processing completed: {len([r for r in results.values() if r[0]])} successful, {len([r for r in results.values() if not r[0]])} failed")
            
        except Exception as e:
            error_msg = f"Batch download error: {str(e)}"
            logger.error(error_msg)
            for stock in stocks:
                results[stock] = (False, error_msg)
        
        return results
    
    def _process_stock_batch_data(self, stock: str, stock_data: pd.DataFrame) -> Tuple[bool, str]:
        """
        Process batch data for a single stock
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if stock_data.empty:
                return False, "No data in batch"
            
            # Reset index to make date a column
            stock_data = stock_data.reset_index()
            
            # Rename columns to match our database schema
            stock_data = stock_data.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Add stock column
            stock_data['stock'] = stock
            
            # Get existing data to avoid duplicates
            existing_data = self.db.get_price_data(stock)
            if not existing_data.empty:
                existing_dates = set(pd.to_datetime(existing_data['date']).dt.date)
                # Filter out data we already have
                stock_data['date_only'] = pd.to_datetime(stock_data['date']).dt.date
                new_data = stock_data[~stock_data['date_only'].isin(existing_dates)]
                new_data = new_data.drop('date_only', axis=1)
            else:
                new_data = stock_data
            
            if new_data.empty:
                return True, f"No new data for {stock}"
            
            # Insert new data
            self._insert_price_data(new_data)
            
            # Update last_price_date
            latest_date = pd.to_datetime(new_data['date']).max().date()
            self._update_stock_metadata_last_price_date(stock, latest_date)
            
            # Calculate and store momentum
            self._calculate_and_store_momentum(stock)
            
            # Mark update as completed
            total_records = len(self.db.get_price_data(stock))
            self.update_tracker.mark_update_completed(stock, total_records, latest_date)
            
            return True, f"Successfully updated {stock} with {len(new_data)} new records"
            
        except Exception as e:
            error_msg = f"Error processing batch data for {stock}: {str(e)}"
            logger.error(error_msg)
            self.update_tracker.mark_update_failed(stock, error_msg)
            return False, error_msg
    
    def fetch_financial_attributes(self, stock: str) -> Tuple[bool, Dict[str, any], str]:
        """
        Fetch comprehensive financial attributes from Yahoo Finance
        
        Returns:
            Tuple of (success, attributes_dict, error_message)
        """
        try:
            yf_symbol = self.data_fetcher._get_ticker_symbol(stock)
            ticker = yf.Ticker(yf_symbol)
            
            # Apply more conservative rate limiting to avoid hitting Yahoo Finance limits
            time.sleep(3 + random.uniform(0, 2))  # 3-5 seconds between requests
            
            # Get company info
            info = ticker.info
            
            attributes = {}
            
            # Helper function to safely extract and convert values
            def safe_extract(key, convert_func=None, default=None):
                if key in info and info[key] is not None:
                    try:
                        value = info[key]
                        if convert_func:
                            return convert_func(value)
                        return value
                    except (ValueError, TypeError):
                        return default
                return default
            
            # Basic Company Information
            attributes['sector'] = safe_extract('sector', str)
            attributes['industry'] = safe_extract('industry', str)
            attributes['company_name'] = safe_extract('longName', str)
            attributes['exchange'] = safe_extract('exchange', str)
            
            # Financial Ratios
            attributes['pe_ratio'] = safe_extract('trailingPE', float)
            attributes['forward_pe'] = safe_extract('forwardPE', float)
            attributes['pb_ratio'] = safe_extract('priceToBook', float)
            attributes['ps_ratio'] = safe_extract('priceToSalesTrailing12Months', float)
            attributes['peg_ratio'] = safe_extract('pegRatio', float)
            attributes['beta'] = safe_extract('beta', float)
            attributes['ev_to_revenue'] = safe_extract('enterpriseToRevenue', float)
            attributes['ev_to_ebitda'] = safe_extract('enterpriseToEbitda', float)
            
            # Profitability Metrics
            attributes['gross_margin'] = safe_extract('grossMargins', lambda x: float(x) * 100)
            attributes['operating_margin'] = safe_extract('operatingMargins', lambda x: float(x) * 100)
            attributes['profit_margin'] = safe_extract('profitMargins', lambda x: float(x) * 100)
            attributes['ebitda_margin'] = safe_extract('ebitdaMargins', lambda x: float(x) * 100)
            attributes['roe'] = safe_extract('returnOnEquity', lambda x: float(x) * 100)
            attributes['roa'] = safe_extract('returnOnAssets', lambda x: float(x) * 100)
            attributes['roce'] = safe_extract('returnOnAssets', lambda x: float(x) * 100)  # Using ROA as proxy
            
            # Growth Metrics
            attributes['revenue_growth'] = safe_extract('revenueGrowth', lambda x: float(x) * 100)
            attributes['earnings_growth'] = safe_extract('earningsGrowth', lambda x: float(x) * 100)
            attributes['quarterly_earnings_growth'] = safe_extract('earningsQuarterlyGrowth', lambda x: float(x) * 100)
            
            # Dividend Information
            attributes['dividend_yield'] = safe_extract('dividendYield', lambda x: float(x) * 100)
            attributes['dividend_rate'] = safe_extract('dividendRate', float)
            attributes['payout_ratio'] = safe_extract('payoutRatio', lambda x: float(x) * 100)
            
            # Handle date fields
            ex_dividend_date = safe_extract('exDividendDate')
            if ex_dividend_date:
                try:
                    from datetime import datetime
                    if isinstance(ex_dividend_date, (int, float)):
                        attributes['ex_dividend_date'] = datetime.fromtimestamp(ex_dividend_date).date()
                    else:
                        attributes['ex_dividend_date'] = ex_dividend_date
                except:
                    pass
            
            dividend_date = safe_extract('dividendDate')
            if dividend_date:
                try:
                    from datetime import datetime
                    if isinstance(dividend_date, (int, float)):
                        attributes['dividend_date'] = datetime.fromtimestamp(dividend_date).date()
                    else:
                        attributes['dividend_date'] = dividend_date
                except:
                    pass
            
            # Balance Sheet Data
            attributes['total_cash'] = safe_extract('totalCash', int)
            attributes['total_debt'] = safe_extract('totalDebt', int)
            attributes['debt_to_equity'] = safe_extract('debtToEquity', float)
            attributes['current_ratio'] = safe_extract('currentRatio', float)
            attributes['quick_ratio'] = safe_extract('quickRatio', float)
            attributes['total_revenue'] = safe_extract('totalRevenue', int)
            attributes['cash_per_share'] = safe_extract('totalCashPerShare', float)
            
            # Valuation Metrics
            attributes['enterprise_value'] = safe_extract('enterpriseValue', int)
            attributes['book_value'] = safe_extract('bookValue', float)
            attributes['price_to_book'] = safe_extract('priceToBook', float)
            
            # Market Data
            attributes['current_price'] = safe_extract('currentPrice', float)
            attributes['previous_close'] = safe_extract('previousClose', float)
            attributes['day_low'] = safe_extract('dayLow', float)
            attributes['day_high'] = safe_extract('dayHigh', float)
            attributes['fifty_two_week_low'] = safe_extract('fiftyTwoWeekLow', float)
            attributes['fifty_two_week_high'] = safe_extract('fiftyTwoWeekHigh', float)
            attributes['volume'] = safe_extract('volume', int)
            attributes['average_volume'] = safe_extract('averageVolume', int)
            attributes['shares_outstanding'] = safe_extract('sharesOutstanding', int)
            attributes['market_cap'] = safe_extract('marketCap', int)
            
            # Remove None values
            attributes = {k: v for k, v in attributes.items() if v is not None}
            
            # Check if we got any useful attributes
            if not attributes:
                return False, {}, "No financial attributes found"
            
            logger.info(f"✅ {stock}: Fetched {len(attributes)} attributes: {list(attributes.keys())}")
            return True, attributes, ""
            
        except Exception as e:
            error_msg = f"Error fetching financial attributes for {stock}: {str(e)}"
            logger.error(error_msg)
            
            # Check if this is a rate limit error
            if "Too Many Requests" in str(e) or "Rate limited" in str(e):
                logger.warning(f"🚫 Rate limit detected for {stock}. Implementing cooldown...")
                # Add a longer cooldown period for rate limit errors
                time.sleep(30 + random.uniform(0, 10))  # 30-40 seconds cooldown
            
            return False, {}, error_msg
    
    def update_stock_attributes(self, stock: str, attributes: Dict[str, any]) -> bool:
        """Update comprehensive stock attributes in database"""
        try:
            # Build dynamic update query for all comprehensive attributes
            set_clauses = []
            params = []
            
            # Map attribute names to database column names
            attribute_mapping = {
                'sector': 'sector',
                'industry': 'industry',
                'company_name': 'company_name',
                'exchange': 'exchange',
                'pe_ratio': 'pe_ratio',
                'forward_pe': 'forward_pe',
                'pb_ratio': 'pb_ratio',
                'ps_ratio': 'ps_ratio',
                'peg_ratio': 'peg_ratio',
                'beta': 'beta',
                'ev_to_revenue': 'ev_to_revenue',
                'ev_to_ebitda': 'ev_to_ebitda',
                'gross_margin': 'gross_margin',
                'operating_margin': 'operating_margin',
                'profit_margin': 'profit_margin',
                'ebitda_margin': 'ebitda_margin',
                'roe': 'roe',
                'roa': 'roa',
                'roce': 'roce',
                'revenue_growth': 'revenue_growth',
                'earnings_growth': 'earnings_growth',
                'quarterly_earnings_growth': 'quarterly_earnings_growth',
                'dividend_yield': 'dividend_yield',
                'dividend_rate': 'dividend_rate',
                'payout_ratio': 'payout_ratio',
                'ex_dividend_date': 'ex_dividend_date',
                'dividend_date': 'dividend_date',
                'total_cash': 'total_cash',
                'total_debt': 'total_debt',
                'debt_to_equity': 'debt_to_equity',
                'current_ratio': 'current_ratio',
                'quick_ratio': 'quick_ratio',
                'total_revenue': 'total_revenue',
                'cash_per_share': 'cash_per_share',
                'enterprise_value': 'enterprise_value',
                'book_value': 'book_value',
                'price_to_book': 'price_to_book',
                'current_price': 'current_price',
                'previous_close': 'previous_close',
                'day_low': 'day_low',
                'day_high': 'day_high',
                'fifty_two_week_low': 'fifty_two_week_low',
                'fifty_two_week_high': 'fifty_two_week_high',
                'volume': 'volume',
                'average_volume': 'average_volume',
                'shares_outstanding': 'shares_outstanding',
                'market_cap': 'market_cap'
            }
            
            for key, value in attributes.items():
                if key in attribute_mapping:
                    db_column = attribute_mapping[key]
                    set_clauses.append(f"{db_column} = %s")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            query = f"""
            UPDATE stockmetadata 
            SET {', '.join(set_clauses)}, last_updated = CURRENT_TIMESTAMP
            WHERE stock = %s
            """
            params.append(stock)
            
            # Debug: Log the actual query and parameters
            logger.info(f"🔍 DEBUG {stock}: SQL Query: {query}")
            logger.info(f"🔍 DEBUG {stock}: Parameters: {tuple(params)}")
            
            result = self.db.execute_update(query, tuple(params))
            
            if result > 0:
                logger.info(f"💾 {stock}: Updated {len(set_clauses)} attributes in database: {list(attributes.keys())}")
                return True
            else:
                logger.warning(f"No rows updated for {stock}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating attributes for {stock}: {e}")
            return False
    
    def get_stocks_missing_attributes(self) -> List[str]:
        """Get list of stocks missing comprehensive financial attributes"""
        try:
            query = """
            SELECT stock FROM stockmetadata 
            WHERE sector IS NULL 
               OR industry IS NULL 
               OR pe_ratio IS NULL 
               OR forward_pe IS NULL 
               OR pb_ratio IS NULL 
               OR ps_ratio IS NULL 
               OR peg_ratio IS NULL 
               OR beta IS NULL 
               OR ev_to_revenue IS NULL 
               OR ev_to_ebitda IS NULL 
               OR gross_margin IS NULL 
               OR operating_margin IS NULL 
               OR profit_margin IS NULL 
               OR ebitda_margin IS NULL 
               OR roe IS NULL 
               OR roa IS NULL 
               OR revenue_growth IS NULL 
               OR earnings_growth IS NULL 
               OR quarterly_earnings_growth IS NULL 
               OR dividend_yield IS NULL 
               OR dividend_rate IS NULL 
               OR payout_ratio IS NULL 
               OR total_cash IS NULL 
               OR total_debt IS NULL 
               OR debt_to_equity IS NULL 
               OR current_ratio IS NULL 
               OR quick_ratio IS NULL 
               OR total_revenue IS NULL 
               OR cash_per_share IS NULL 
               OR enterprise_value IS NULL 
               OR book_value IS NULL 
               OR price_to_book IS NULL 
               OR current_price IS NULL 
               OR previous_close IS NULL 
               OR day_low IS NULL 
               OR day_high IS NULL 
               OR fifty_two_week_low IS NULL 
               OR fifty_two_week_high IS NULL 
               OR volume IS NULL 
               OR average_volume IS NULL 
               OR shares_outstanding IS NULL
            ORDER BY market_cap DESC
            """
            result = self.db.execute_query(query)
            return result['stock'].tolist() if not result.empty else []
        except Exception as e:
            logger.error(f"Error getting stocks missing attributes: {e}")
            return []
    
    def ensure_missing_stocks_in_pending(self) -> int:
        """Ensure stocks with missing CRITICAL attributes are in the pending operations table"""
        try:
            # Only check for critical attributes that are actually needed for the application
            # Focus on sector, industry, and basic financial metrics that are commonly used
            query = """
            SELECT s.stock 
            FROM stockmetadata s 
            LEFT JOIN pending_operations p ON s.stock = p.stock AND p.operation_type = 'attributes'
            WHERE (s.sector IS NULL 
               OR s.industry IS NULL 
               OR s.current_price IS NULL 
               OR s.market_cap IS NULL)
              AND p.stock IS NULL
            ORDER BY s.market_cap DESC
            """
            result = self.db.execute_query(query)
            missing_stocks = result['stock'].tolist() if not result.empty else []
            
            # Add missing stocks to pending operations
            added_count = 0
            for stock in missing_stocks:
                self.add_to_pending_attributes(stock, "Missing financial attributes")
                added_count += 1
            
            if added_count > 0:
                logger.info(f"Added {added_count} stocks with missing attributes to pending operations")
            
            return added_count
            
        except Exception as e:
            logger.error(f"Error ensuring missing stocks in pending: {e}")
            return 0
    
    def get_stocks_missing_price_data(self) -> List[Tuple[str, date]]:
        """
        Get list of stocks missing price data since min_price_date
        
        Returns:
            List of tuples (stock, earliest_missing_date)
        """
        try:
            query = """
            SELECT sm.stock, 
                   COALESCE(MIN(tp.date), %s) as earliest_date
            FROM stockmetadata sm
            LEFT JOIN tickerprice tp ON sm.stock = tp.stock
            GROUP BY sm.stock
            HAVING COALESCE(MIN(tp.date), %s) > %s
            ORDER BY sm.market_cap DESC
            """
            
            result = self.db.execute_query(query, (self.min_price_date, self.min_price_date, self.min_price_date))
            
            missing_stocks = []
            for _, row in result.iterrows():
                stock = row['stock']
                earliest_date = row['earliest_date']
                missing_stocks.append((stock, earliest_date))
            
            return missing_stocks
            
        except Exception as e:
            logger.error(f"Error getting stocks missing price data: {e}")
            return []
    
    def create_pending_operations_table(self):
        """Create pending operations table if it doesn't exist"""
        try:
            query = """
            CREATE TABLE IF NOT EXISTS pending_operations (
                stock VARCHAR(50) NOT NULL,
                operation_type VARCHAR(20) NOT NULL,
                error_message TEXT,
                target_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_attempt TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                PRIMARY KEY (stock, operation_type),
                FOREIGN KEY (stock) REFERENCES stockmetadata(stock)
            )
            """
            self.db.execute_update(query)
            logger.info("Created pending_operations table")
        except Exception as e:
            logger.error(f"Error creating pending_operations table: {e}")
    
    def add_to_pending_attributes(self, stock: str, error_message: str):
        """Add stock to pending attributes list"""
        try:
            query = """
            INSERT INTO pending_operations (stock, operation_type, error_message, created_at, retry_count)
            VALUES (%s, 'attributes', %s, CURRENT_TIMESTAMP, 0)
            ON CONFLICT (stock, operation_type) 
            DO UPDATE SET 
                error_message = %s,
                last_attempt = CURRENT_TIMESTAMP,
                retry_count = pending_operations.retry_count + 1
            """
            self.db.execute_update(query, (stock, error_message, error_message))
            logger.info(f"⏳ {stock}: Added to pending attributes list")
        except Exception as e:
            logger.error(f"Error adding {stock} to pending attributes: {e}")
    
    def add_to_pending_prices(self, stock: str, error_message: str, target_date: date = None):
        """Add stock to pending prices list"""
        try:
            query = """
            INSERT INTO pending_operations (stock, operation_type, error_message, target_date, created_at, retry_count)
            VALUES (%s, 'prices', %s, %s, CURRENT_TIMESTAMP, 0)
            ON CONFLICT (stock, operation_type) 
            DO UPDATE SET 
                error_message = %s,
                target_date = %s,
                last_attempt = CURRENT_TIMESTAMP,
                retry_count = pending_operations.retry_count + 1
            """
            self.db.execute_update(query, (stock, error_message, target_date, error_message, target_date))
            logger.info(f"Added {stock} to pending prices list")
        except Exception as e:
            logger.error(f"Error adding {stock} to pending prices: {e}")
    
    def get_pending_attributes(self, max_retries: int = 5) -> List[str]:
        """Get stocks pending attribute updates (skip stocks with 5+ retries)"""
        try:
            query = """
            SELECT stock FROM pending_operations 
            WHERE operation_type = 'attributes' 
              AND retry_count < %s
            ORDER BY created_at ASC
            """
            result = self.db.execute_query(query, (max_retries,))
            return result['stock'].tolist() if not result.empty else []
        except Exception as e:
            logger.error(f"Error getting pending attributes: {e}")
            return []
    
    def get_exhausted_retry_stocks(self, operation_type: str = 'attributes') -> List[str]:
        """Get stocks that have exceeded max retry attempts"""
        try:
            query = """
            SELECT stock FROM pending_operations 
            WHERE operation_type = %s 
              AND retry_count >= 5
            ORDER BY created_at ASC
            """
            result = self.db.execute_query(query, (operation_type,))
            return result['stock'].tolist() if not result.empty else []
        except Exception as e:
            logger.error(f"Error getting exhausted retry stocks: {e}")
            return []
    
    def get_pending_attribute_stocks(self) -> List[str]:
        """Get stocks that are in pending operations for attribute updates"""
        try:
            query = """
            SELECT stock FROM pending_operations 
            WHERE operation_type = 'attributes' 
            AND retry_count < 5
            ORDER BY created_at ASC
            """
            result = self.db.execute_query(query)
            return result['stock'].tolist() if not result.empty else []
        except Exception as e:
            logger.error(f"Error getting pending attribute stocks: {e}")
            return []
    
    def cleanup_completed_attribute_stocks(self) -> int:
        """Remove stocks from pending that have sector/industry but are missing other attributes"""
        try:
            # Find stocks in pending that have sector/industry but are missing key attributes
            query = """
            SELECT p.stock FROM pending_operations p
            JOIN stockmetadata s ON p.stock = s.stock
            WHERE p.operation_type = 'attributes'
            AND s.sector IS NOT NULL 
            AND s.industry IS NOT NULL
            AND (
                s.pe_ratio IS NULL OR 
                s.pb_ratio IS NULL OR 
                s.beta IS NULL OR 
                s.roe IS NULL OR 
                s.roa IS NULL OR 
                s.gross_margin IS NULL OR 
                s.operating_margin IS NULL OR 
                s.profit_margin IS NULL OR 
                s.dividend_yield IS NULL OR 
                s.total_cash IS NULL OR 
                s.total_debt IS NULL OR 
                s.current_ratio IS NULL OR 
                s.enterprise_value IS NULL OR 
                s.book_value IS NULL OR 
                s.current_price IS NULL OR 
                s.volume IS NULL
            )
            """
            result = self.db.execute_query(query)
            if result.empty:
                return 0
            
            # Remove these stocks from pending
            stocks_to_remove = result['stock'].tolist()
            for stock in stocks_to_remove:
                self.remove_from_pending(stock, 'attributes')
                logger.info(f"🧹 {stock}: Removed from pending (has sector/industry but missing other attributes)")
            
            return len(stocks_to_remove)
        except Exception as e:
            logger.error(f"Error cleaning up completed attribute stocks: {e}")
            return 0
    
    def get_pending_prices(self, max_retries: int = 5) -> List[Tuple[str, date]]:
        """Get stocks pending price updates"""
        try:
            query = """
            SELECT stock, target_date FROM pending_operations 
            WHERE operation_type = 'prices' 
              AND retry_count < %s
            ORDER BY created_at ASC
            """
            result = self.db.execute_query(query, (max_retries,))
            
            pending_stocks = []
            for _, row in result.iterrows():
                stock = row['stock']
                target_date = row['target_date'] if pd.notna(row['target_date']) else self.min_price_date
                pending_stocks.append((stock, target_date))
            
            return pending_stocks
        except Exception as e:
            logger.error(f"Error getting pending prices: {e}")
            return []
    
    def remove_from_pending(self, stock: str, operation_type: str):
        """Remove stock from pending list after successful operation"""
        try:
            query = """
            DELETE FROM pending_operations 
            WHERE stock = %s AND operation_type = %s
            """
            self.db.execute_update(query, (stock, operation_type))
            logger.info(f"✅ {stock}: Removed from pending {operation_type} list (completed successfully)")
        except Exception as e:
            logger.error(f"Error removing {stock} from pending {operation_type}: {e}")
    
    def update_attributes_for_stocks(self, stocks: List[str]) -> Dict[str, Tuple[bool, str]]:
        """
        Update financial attributes for multiple stocks using parallel processing
        
        Returns:
            Dict mapping stock symbol to (success, message)
        """
        import concurrent.futures
        import threading
        
        results = {}
        
        def process_single_stock(stock: str) -> Tuple[str, bool, str]:
            """Process a single stock and return (stock, success, message)"""
            try:
                # Fetch attributes
                success, attributes, error_msg = self.fetch_financial_attributes(stock)
                
                if success and attributes:
                    # Update database
                    update_success = self.update_stock_attributes(stock, attributes)
                    if update_success:
                        # Check if ALL required attributes are now present
                        if self._all_attributes_present(stock):
                            logger.info(f"✅ {stock}: All attributes complete - removing from pending")
                            self.remove_from_pending(stock, 'attributes')
                            return (stock, True, f"Updated {len(attributes)} attributes")
                        else:
                            # Still missing some attributes, keep in pending
                            missing_attrs = self._get_missing_attributes(stock)
                            logger.info(f"⏳ {stock}: Still missing attributes: {missing_attrs} - keeping in pending")
                            self.add_to_pending_attributes(stock, f"Still missing: {missing_attrs}")
                            return (stock, True, f"Updated {len(attributes)} attributes, still missing: {missing_attrs}")
                    else:
                        # Add to pending for retry
                        self.add_to_pending_attributes(stock, "Failed to update attributes in database")
                        return (stock, False, "Failed to update attributes in database")
                else:
                    # Add to pending for retry
                    self.add_to_pending_attributes(stock, error_msg or "Failed to fetch attributes")
                    return (stock, False, error_msg or "Failed to fetch attributes")
                    
            except Exception as e:
                logger.error(f"Error processing {stock}: {e}")
                # Add to pending for retry
                self.add_to_pending_attributes(stock, str(e))
                return (stock, False, str(e))
        
        # Process stocks in parallel with thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all tasks
            future_to_stock = {executor.submit(process_single_stock, stock): stock for stock in stocks}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_stock):
                stock, success, message = future.result()
                results[stock] = (success, message)
        
        return results
    
    def _all_attributes_present(self, stock: str) -> bool:
        """Check if comprehensive financial attributes are present for a stock"""
        try:
            # A stock is considered "complete" if it has:
            # 1. Core attributes: sector AND industry (required)
            # 2. At least some key financial metrics from different categories
            query = """
            SELECT stock FROM stockmetadata 
            WHERE stock = %s
              AND sector IS NOT NULL 
              AND industry IS NOT NULL 
              AND (
                pe_ratio IS NOT NULL OR 
                pb_ratio IS NOT NULL OR 
                beta IS NOT NULL OR 
                roe IS NOT NULL OR 
                roa IS NOT NULL OR 
                gross_margin IS NOT NULL OR 
                operating_margin IS NOT NULL OR 
                profit_margin IS NOT NULL OR 
                dividend_yield IS NOT NULL OR 
                total_cash IS NOT NULL OR 
                total_debt IS NOT NULL OR 
                current_ratio IS NOT NULL OR 
                enterprise_value IS NOT NULL OR 
                book_value IS NOT NULL OR 
                current_price IS NOT NULL OR 
                volume IS NOT NULL
              )
            """
            result = self.db.execute_query(query, (stock,))
            return not result.empty
        except Exception as e:
            logger.error(f"Error checking attributes for {stock}: {e}")
            return False
    
    def _get_missing_attributes(self, stock: str) -> List[str]:
        """Get list of missing comprehensive attributes for a stock"""
        try:
            query = """
            SELECT sector, industry, pe_ratio, pb_ratio, beta, roe, roa, 
                   gross_margin, operating_margin, profit_margin, dividend_yield,
                   total_cash, total_debt, current_ratio, enterprise_value, 
                   book_value, current_price, volume FROM stockmetadata 
            WHERE stock = %s
            """
            result = self.db.execute_query(query, (stock,))
            
            if result.empty:
                return ["stock not found"]
            
            row = result.iloc[0]
            missing = []
            
            # Core attributes
            if pd.isna(row['sector']) or row['sector'] is None:
                missing.append('sector')
            if pd.isna(row['industry']) or row['industry'] is None:
                missing.append('industry')
            
            # Financial ratios
            if pd.isna(row['pe_ratio']) or row['pe_ratio'] is None:
                missing.append('pe_ratio')
            if pd.isna(row['pb_ratio']) or row['pb_ratio'] is None:
                missing.append('pb_ratio')
            if pd.isna(row['beta']) or row['beta'] is None:
                missing.append('beta')
            
            # Profitability metrics
            if pd.isna(row['roe']) or row['roe'] is None:
                missing.append('roe')
            if pd.isna(row['roa']) or row['roa'] is None:
                missing.append('roa')
            if pd.isna(row['gross_margin']) or row['gross_margin'] is None:
                missing.append('gross_margin')
            if pd.isna(row['operating_margin']) or row['operating_margin'] is None:
                missing.append('operating_margin')
            if pd.isna(row['profit_margin']) or row['profit_margin'] is None:
                missing.append('profit_margin')
            
            # Dividend information
            if pd.isna(row['dividend_yield']) or row['dividend_yield'] is None:
                missing.append('dividend_yield')
            
            # Balance sheet data
            if pd.isna(row['total_cash']) or row['total_cash'] is None:
                missing.append('total_cash')
            if pd.isna(row['total_debt']) or row['total_debt'] is None:
                missing.append('total_debt')
            if pd.isna(row['current_ratio']) or row['current_ratio'] is None:
                missing.append('current_ratio')
            
            # Valuation metrics
            if pd.isna(row['enterprise_value']) or row['enterprise_value'] is None:
                missing.append('enterprise_value')
            if pd.isna(row['book_value']) or row['book_value'] is None:
                missing.append('book_value')
            
            # Market data
            if pd.isna(row['current_price']) or row['current_price'] is None:
                missing.append('current_price')
            if pd.isna(row['volume']) or row['volume'] is None:
                missing.append('volume')
            
            return missing
        except Exception as e:
            logger.error(f"Error getting missing attributes for {stock}: {e}")
            return ["error checking attributes"]
    
    def update_prices_for_stocks(self, stocks_with_dates: List[Tuple[str, date]]) -> Dict[str, Tuple[bool, str]]:
        """
        Update price data for multiple stocks from specific dates
        
        Returns:
            Dict mapping stock symbol to (success, message)
        """
        results = {}
        
        for stock, start_date in stocks_with_dates:
            try:
                # Fetch price data from start_date to today
                success, price_data, error_msg = self.data_fetcher.fetch_stock_data(stock, start_date, date.today())
                
                if success and not price_data.empty:
                    # Insert price data
                    insert_success = self.insert_price_data(stock, price_data)
                    if insert_success:
                        # Update last_price_date
                        latest_date = price_data['date'].max()
                        if hasattr(latest_date, 'date'):
                            latest_date = latest_date.date()
                        self._update_stock_metadata_last_price_date(stock, latest_date)
                        
                        results[stock] = (True, f"Updated {len(price_data)} price records from {start_date}")
                        self.remove_from_pending(stock, 'prices')
                    else:
                        results[stock] = (False, "Failed to insert price data")
                        self.add_to_pending_prices(stock, "Failed to insert price data", start_date)
                else:
                    results[stock] = (False, error_msg)
                    self.add_to_pending_prices(stock, error_msg, start_date)
                
                # Small delay between updates to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = f"Unexpected error updating prices for {stock}: {str(e)}"
                logger.error(error_msg)
                results[stock] = (False, error_msg)
                self.add_to_pending_prices(stock, error_msg, start_date)
        
        return results
    
    def reset_all_retry_counts(self, operation_type: str = 'attributes') -> int:
        """Reset retry count for all stocks of a specific operation type"""
        try:
            query = """
            UPDATE pending_operations 
            SET retry_count = 0, last_attempt = NULL, error_message = NULL
            WHERE operation_type = %s
            """
            result = self.db.execute_query(query, (operation_type,))
            logger.info(f"Reset retry counts for {operation_type} operations")
            return result.rowcount if hasattr(result, 'rowcount') else 0
        except Exception as e:
            logger.error(f"Error resetting retry counts: {e}")
            return 0
