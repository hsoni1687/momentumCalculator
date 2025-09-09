#!/usr/bin/env python3
"""
Indian Stock Momentum Calculator - Web Application
A Streamlit-based web application for analyzing momentum in Indian stocks
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Add src and config directories to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

# Load configuration system
from config.loader import setup_local_config, get_config
setup_local_config()
config_manager = get_config()

import streamlit as st
import pandas as pd
import logging
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Import our modules
from data_fetcher import IndianStockDataFetcher
from momentum_calculator import MomentumCalculator
from database import StockDatabase
from stock_lists import get_all_stocks
from database_smart import SmartDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Removed old database initialization function - now using database_preparation.py

# Page configuration
st.set_page_config(
    page_title="Indian Stock Momentum Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

class MomentumWebApp:
    def __init__(self):
        self.config_manager = config_manager
        self.app_config = self.config_manager.get_app_config()
        self.db = SmartDatabase()
        self.momentum_calculator = MomentumCalculator()
        self.cache = {}
    
    def load_stock_data(self, use_cache=True, n_stocks=None, industry=None, sector=None):
        """Load and cache stock data with optional industry/sector filtering"""
        if n_stocks is None:
            n_stocks = self.app_config.get('max_stocks', 100)
        
        # Create cache key that includes filters
        filter_suffix = ""
        if industry:
            filter_suffix += f"_industry_{industry.replace(' ', '_')}"
        if sector:
            filter_suffix += f"_sector_{sector.replace(' ', '_')}"
        
        cache_key = f"stock_data_{n_stocks}{filter_suffix}"
        
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Create loading message
        loading_msg = f"Fetching top {n_stocks} stocks"
        if industry:
            loading_msg += f" from {industry} industry"
        if sector:
            loading_msg += f" from {sector} sector"
        loading_msg += "..."
        
        with st.spinner(loading_msg):
            try:
<<<<<<< HEAD
                # Get stock metadata with filters
                metadata_query = "SELECT * FROM stockmetadata WHERE 1=1"
                params = []
=======
                # Get stock metadata with filters using Supabase methods
                top_stocks = self.db.get_stock_metadata(industry_filter=industry, sector_filter=sector)
>>>>>>> 2dacb80e81e1c89169900b09d21ec83393cae2f8
                
                # Sort by market cap and limit if needed
                if not top_stocks.empty and 'market_cap' in top_stocks.columns:
                    top_stocks = top_stocks.sort_values('market_cap', ascending=False)
                    if n_stocks:
                        top_stocks = top_stocks.head(n_stocks)
                
                if top_stocks.empty:
                    filter_info = []
                    if industry:
                        filter_info.append(f"industry: {industry}")
                    if sector:
                        filter_info.append(f"sector: {sector}")
                    
                    if filter_info:
                        st.warning(f"No stocks found matching filters: {', '.join(filter_info)}")
                    else:
                        st.error("Failed to fetch stock data. Please try again.")
                    return pd.DataFrame()
                
                # Cache the data
                self.cache[cache_key] = top_stocks
                return top_stocks
                
            except Exception as e:
                st.error(f"Error loading stock data: {e}")
                return pd.DataFrame()
    
    def get_available_industries(self):
        """Get available industries from database"""
        try:
<<<<<<< HEAD
            query = "SELECT DISTINCT industry FROM stockmetadata WHERE industry IS NOT NULL ORDER BY industry"
            result = self.db.execute_query(query)
            return result['industry'].tolist() if not result.empty else []
=======
            return self.db.get_available_industries()
>>>>>>> 2dacb80e81e1c89169900b09d21ec83393cae2f8
        except Exception as e:
            st.error(f"Error getting industries: {e}")
            return []
    
    def get_available_sectors(self):
        """Get available sectors from database"""
        try:
<<<<<<< HEAD
            query = "SELECT DISTINCT sector FROM stockmetadata WHERE sector IS NOT NULL ORDER BY sector"
            result = self.db.execute_query(query)
            return result['sector'].tolist() if not result.empty else []
=======
            return self.db.get_available_sectors()
>>>>>>> 2dacb80e81e1c89169900b09d21ec83393cae2f8
        except Exception as e:
            st.error(f"Error getting sectors: {e}")
            return []

    def load_historical_data(self, stocks_df, use_cache=True):
        """Load historical data for stocks"""
        cache_key = "historical_data"
        
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        with st.spinner("Loading historical price data..."):
            try:
                historical_data = {}
                for _, stock in stocks_df.iterrows():
                    symbol = stock['stock']  # Changed from 'symbol' to 'stock'
                    price_data = self.db.get_price_data(symbol)
                    if not price_data.empty:
                        # Convert to the expected format
                        price_data['Date'] = pd.to_datetime(price_data['date'])
                        price_data.set_index('Date', inplace=True)
                        price_data = price_data[['open', 'high', 'low', 'close', 'volume']]
                        price_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                        
                        # Calculate Returns column (required by momentum calculator)
                        price_data['Returns'] = price_data['Close'].pct_change()
                        
                        historical_data[symbol] = price_data
                
                # Cache the data
                self.cache[cache_key] = historical_data
                return historical_data
                
            except Exception as e:
                st.error(f"Error loading historical data: {e}")
                return {}
    
    def calculate_momentum_scores(self, stocks_df, historical_data):
        """Calculate momentum scores for stocks"""
        with st.spinner("Calculating momentum scores..."):
            try:
                # Check if we have cached momentum scores for today
                cached_scores = self.db.get_momentum_scores_today()
                
                if len(cached_scores) >= len(stocks_df) * 0.8:  # If we have 80%+ cached scores
                    st.info("Using cached momentum scores from today")
                    momentum_results = []
                    
                    for _, stock in stocks_df.iterrows():
                        symbol = stock['stock']
                        cached_score = cached_scores[cached_scores['stock'] == symbol]
                        
                        if not cached_score.empty:
                            score_data = cached_score.iloc[0]
                            momentum_results.append({
                                'stock': symbol,
                                'company_name': stock['company_name'],
                                'market_cap': stock['market_cap'],
                                'industry': stock.get('industry', 'N/A'),
                                'sector': stock.get('sector', 'N/A'),
                                'dividend_yield': stock.get('dividend_yield', 'N/A'),
                                'roce': stock.get('roce', 'N/A'),
                                'roe': stock.get('roe', 'N/A'),
                                'total_score': score_data['total_score'],
                                'raw_momentum_6m': score_data['raw_momentum_6m'],
                                'raw_momentum_3m': score_data['raw_momentum_3m'],
                                'raw_momentum_1m': score_data['raw_momentum_1m'],
                                'momentum_12_2': score_data.get('momentum_12_2', 0),
                                'fip_quality': score_data.get('fip_quality', 0),
                                'volatility_adjusted': score_data.get('volatility_adjusted', 0),
                                'smooth_momentum': score_data.get('smooth_momentum', 0),
                                'consistency_score': score_data.get('consistency_score', 0),
                                'trend_strength': score_data.get('trend_strength', 0)
                            })
                        else:
                            # Calculate fresh score for missing stocks
                            if symbol in historical_data:
                                momentum_score = self.momentum_calculator.calculate_quality_momentum_score(
                                    historical_data[symbol]
                                )
                                if momentum_score:
                                    # Store in database
                                    self.db.store_momentum_scores(symbol, momentum_score)
                                    
                                    momentum_results.append({
                                        'stock': symbol,
                                        'company_name': stock['company_name'],
                                        'market_cap': stock['market_cap'],
                                        'industry': stock.get('industry', 'N/A'),
                                        'sector': stock.get('sector', 'N/A'),
                                        'dividend_yield': stock.get('dividend_yield', 'N/A'),
                                        'roce': stock.get('roce', 'N/A'),
                                        'roe': stock.get('roe', 'N/A'),
                                        **momentum_score
                                    })
                else:
                    # Calculate fresh scores for all stocks
                    st.info("Calculating fresh momentum scores...")
                    momentum_results = self.momentum_calculator.calculate_momentum_for_stocks(
                        stocks_df, historical_data
                    )
                
                if momentum_results and len(momentum_results) > 0:
                    momentum_df = pd.DataFrame(momentum_results)
                    momentum_df = momentum_df.sort_values('total_score', ascending=False)
                    return momentum_df
                else:
                    st.error("Failed to calculate momentum scores")
                    return pd.DataFrame()
                    
            except Exception as e:
                st.error(f"Error calculating momentum scores: {e}")
                return pd.DataFrame()
    
    def display_results(self, momentum_df, top_n):
        """Display momentum analysis results"""
        if momentum_df.empty:
            st.warning("No momentum data to display")
            return
        
        st.subheader(f"🏆 Top {top_n} Momentum Stocks")
        
        # Get top N stocks
        top_stocks = momentum_df.head(top_n)
        
<<<<<<< HEAD
        # Prepare display columns - use 'symbol' if 'stock' is not available
        symbol_col = 'stock' if 'stock' in top_stocks.columns else 'symbol'
        display_columns = [
            symbol_col, 'company_name', 'market_cap', 'total_score',
            'momentum_12_2', 'fip_quality', 'raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m',
=======
        # Prepare display columns (matching what momentum calculator returns)
        base_columns = ['stock', 'company_name', 'market_cap', 'total_score']
        momentum_columns = [
            'momentum_12_2', 'fip_quality',
            'raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m',
>>>>>>> 2dacb80e81e1c89169900b09d21ec83393cae2f8
            'volatility_adjusted', 'smooth_momentum', 'consistency_score', 'trend_strength'
        ]
        optional_columns = ['industry', 'dividend_yield', 'roce', 'roe', 'sector']
        
<<<<<<< HEAD
        # Filter to only include columns that actually exist
        display_columns = [col for col in display_columns if col in top_stocks.columns]
        
        # Add optional columns if they exist
        available_columns = []
        for col in ['industry', 'dividend_yield', 'roce', 'roe', 'sector']:
=======
        # Only include columns that actually exist
        display_columns = []
        for col in base_columns + momentum_columns + optional_columns:
>>>>>>> 2dacb80e81e1c89169900b09d21ec83393cae2f8
            if col in top_stocks.columns:
                display_columns.append(col)
        
        # Create display dataframe
        display_df = top_stocks[display_columns].copy()
        
        # Format columns
        if 'market_cap' in display_df.columns:
            display_df['market_cap'] = display_df['market_cap'].apply(lambda x: f"₹{x:,.0f}Cr")
        
        # Format percentage columns (only if they exist)
        percentage_columns = [
<<<<<<< HEAD
            'total_score', 'momentum_12_2', 'fip_quality', 'raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m',
=======
            'total_score', 'momentum_12_2', 'fip_quality',
            'raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m',
>>>>>>> 2dacb80e81e1c89169900b09d21ec83393cae2f8
            'volatility_adjusted', 'smooth_momentum', 'consistency_score', 'trend_strength'
        ]
        
        for col in percentage_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
        
        # Format other numeric columns
        if 'dividend_yield' in display_df.columns:
            display_df['dividend_yield'] = display_df['dividend_yield'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
        if 'roce' in display_df.columns:
            display_df['roce'] = display_df['roce'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
        if 'roe' in display_df.columns:
            display_df['roe'] = display_df['roe'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
        
        # Rename columns for better display
        column_mapping = {
            'stock': 'Symbol',
<<<<<<< HEAD
            'symbol': 'Symbol',
=======
>>>>>>> 2dacb80e81e1c89169900b09d21ec83393cae2f8
            'company_name': 'Company Name',
            'market_cap': 'Market Cap',
            'total_score': 'Total Score',
            'momentum_12_2': '12-2 Momentum',
            'fip_quality': 'FIP Quality',
            'raw_momentum_6m': '6M Momentum',
            'raw_momentum_3m': '3M Momentum',
            'raw_momentum_1m': '1M Momentum',
            'volatility_adjusted': 'Vol-Adj Momentum',
            'smooth_momentum': 'Smooth Momentum',
            'consistency_score': 'Consistency',
            'trend_strength': 'Trend Strength',
            'industry': 'Industry',
            'sector': 'Sector',
            'dividend_yield': 'Dividend Yield',
            'roce': 'ROCE',
            'roe': 'ROE'
        }
        
        # Apply column renaming only to existing columns
        existing_columns = {k: v for k, v in column_mapping.items() if k in display_df.columns}
        display_df = display_df.rename(columns=existing_columns)
        
        # Display the dataframe
        st.dataframe(display_df, use_container_width=True)
        
        # Create visualizations
        self.create_visualizations(top_stocks)
    
    def create_visualizations(self, top_stocks):
        """Create interactive visualizations"""
        st.subheader("📊 Momentum Analysis Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Total Score vs Market Cap
            # Use the correct column name for the symbol
            symbol_col = 'stock' if 'stock' in top_stocks.columns else 'symbol'
            fig1 = px.scatter(
                top_stocks, 
                x='market_cap', 
                y='total_score',
<<<<<<< HEAD
                hover_data=[symbol_col, 'company_name'],
=======
                hover_data=['stock', 'company_name'],
>>>>>>> 2dacb80e81e1c89169900b09d21ec83393cae2f8
                title="Total Momentum Score vs Market Cap",
                labels={'market_cap': 'Market Cap (₹Cr)', 'total_score': 'Total Score (%)'}
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Momentum breakdown
            momentum_cols = ['raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m', 'raw_momentum_1m']
<<<<<<< HEAD
            momentum_data = top_stocks[[symbol_col] + momentum_cols].set_index(symbol_col)
=======
            momentum_data = top_stocks[['stock'] + momentum_cols].set_index('stock')
>>>>>>> 2dacb80e81e1c89169900b09d21ec83393cae2f8
            
            fig2 = px.bar(
                momentum_data.T,
                title="Momentum Breakdown by Time Period",
                labels={'value': 'Momentum (%)', 'index': 'Time Period'}
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    def run(self):
        """Main application runner"""
        # Header
        st.title("📈 Indian Stock Momentum Calculator")
        st.markdown("""
        This calculator identifies high-quality momentum stocks using the "Frog in the Pan" methodology 
        from Alpha Architect. It analyzes stocks from NSE and BSE, focusing on smooth, consistent 
        price movements rather than volatile spikes.
        """)
        
        # Sidebar controls
        st.sidebar.header("⚙️ Settings")
        
        # Stock selection settings
        from config.config import STOCK_SELECTION_SETTINGS
        max_stocks = STOCK_SELECTION_SETTINGS['max_stocks_to_analyze']
        default_stocks = STOCK_SELECTION_SETTINGS['default_stocks_to_analyze']
        
        stocks_to_analyze = st.sidebar.slider(
            "Number of stocks to analyze", 
            10, max_stocks, default_stocks,
            help=f"Maximum: {max_stocks} stocks"
        )
        
        # Industry and Sector filters
        st.sidebar.subheader("🔍 Filter by Industry/Sector")
        
        # Get available industries and sectors
        available_industries = self.get_available_industries()
        available_sectors = self.get_available_sectors()
        
        # Industry filter
        selected_industry = st.sidebar.selectbox(
            "Select Industry (Optional)",
            ["All Industries"] + available_industries,
            help="Filter stocks by specific industry"
        )
        
        # Sector filter
        selected_sector = st.sidebar.selectbox(
            "Select Sector (Optional)",
            ["All Sectors"] + available_sectors,
            help="Filter stocks by specific sector"
        )
        
        # Convert selections to None if "All" is selected
        industry_filter = None if selected_industry == "All Industries" else selected_industry
        sector_filter = None if selected_sector == "All Sectors" else selected_sector
        
        top_n = st.sidebar.slider("Number of top stocks to display", 10, 100, 20)
        use_cache = st.sidebar.checkbox("Use cached data", value=True)
        
        # Database stats (simplified)
        db_stats = self.db.get_database_stats()
        if db_stats:
            st.sidebar.header("📊 Database Stats")
            st.sidebar.metric("Total Stocks", db_stats.get('unique_stocks_with_price', 0))
            st.sidebar.metric("Stocks with Price Data", db_stats.get('unique_stocks_with_price', 0))
            st.sidebar.metric("Price Records", db_stats.get('record_counts', {}).get('tickerprice', 0))
        
        # Main application flow
        if st.button("🚀 Calculate Momentum Scores", type="primary"):
            # Load stock data with user-selected number of stocks
            stocks_df = self.load_stock_data(use_cache, stocks_to_analyze, industry_filter, sector_filter)
            
            if not stocks_df.empty:
                # Show filter status
                filter_info = []
                if industry_filter:
                    filter_info.append(f"Industry: {industry_filter}")
                if sector_filter:
                    filter_info.append(f"Sector: {sector_filter}")
                
                if filter_info:
                    st.success(f"Loaded {len(stocks_df)} stocks (Filtered by: {', '.join(filter_info)})")
                else:
                    st.success(f"Loaded {len(stocks_df)} stocks")
                
                # Load historical data
                historical_data = self.load_historical_data(stocks_df, use_cache)
                
                if historical_data:
                    st.success(f"Loaded historical data for {len(historical_data)} stocks")
                    
                    # Calculate momentum scores
                    momentum_df = self.calculate_momentum_scores(stocks_df, historical_data)
                    
                    if not momentum_df.empty:
                        st.success(f"Calculated momentum scores for {len(momentum_df)} stocks")
                        
                        # Display results
                        self.display_results(momentum_df, top_n)
                    else:
                        st.error("Failed to calculate momentum scores")
                else:
                    st.error("Failed to load historical data")
            else:
                st.error("Failed to load stock data")

def main():
    """Main function"""
    # Initialize database
    st.info("🔄 Connecting to database...")
    
    try:
        # Create database instance
<<<<<<< HEAD
        db = SmartDatabase()
=======
        db = SupabaseDatabase()
>>>>>>> 2dacb80e81e1c89169900b09d21ec83393cae2f8
        
        # Check if database is accessible
        stats = db.get_database_stats()
        
        if not stats or stats.get('unique_stocks_with_price', 0) == 0:
            st.error("❌ Database connection failed or no data found")
            return
        
        st.success("✅ Database connected successfully")
        
        # Show database summary
        with st.expander("📊 Database Summary", expanded=False):
            if stats:
                st.write(f"**Total Stocks:** {stats.get('unique_stocks_with_price', 0)}")
                st.write(f"**Price Records:** {stats.get('record_counts', {}).get('tickerprice', 0)}")
                st.write(f"**Momentum Scores:** {stats.get('momentum_scores_count', 0)}")
                st.write(f"**Date Range:** {stats.get('date_range', 'N/A')}")
            else:
                st.error("Could not retrieve database summary")
    
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.stop()
    
    app = MomentumWebApp()
    app.run()

if __name__ == "__main__":
    main()