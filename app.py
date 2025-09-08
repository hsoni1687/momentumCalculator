#!/usr/bin/env python3
"""
Indian Stock Momentum Calculator - Web Application
A Streamlit-based web application for analyzing momentum in Indian stocks
"""

import sys
import os

# Add src and config directories to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

# CRITICAL: Force cloud environment if running on Streamlit Cloud
if os.getenv('STREAMLIT_SHARING_MODE') == 'true':
    os.environ['MOMENTUM_ENV'] = 'cloud'
    print("🌐 STREAMLIT CLOUD DETECTED - FORCING CLOUD ENVIRONMENT")
    print("🌐 This should use Supabase, not localhost PostgreSQL")

# Load configuration system
from config.loader import setup_local_config, get_config
setup_local_config()
config_manager = get_config()

# Debug: Print configuration details
print(f"🔍 Environment: {config_manager.config.environment}")
print(f"🔍 Database config: {config_manager.get_database_config()}")
print(f"🔍 STREAMLIT_SHARING_MODE: {os.getenv('STREAMLIT_SHARING_MODE', 'Not set')}")

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

# Configure logging based on config
logging_config = config_manager.get_logging_config()
logging.basicConfig(
    level=getattr(logging, logging_config['level']),
    format=logging_config['format']
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Momentum Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

class MomentumWebApp:
    def __init__(self):
        self.config_manager = config_manager
        self.app_config = self.config_manager.get_app_config()
        
        # CRITICAL: Force Supabase on Streamlit Cloud
        if os.getenv('STREAMLIT_SHARING_MODE') == 'true':
            print("🌐 FORCING SUPABASE DATABASE ON STREAMLIT CLOUD")
            from database_supabase import SupabaseDatabase
            self.db = SupabaseDatabase()
            print(f"🌐 Database type: {type(self.db).__name__}")
        else:
            self.db = SmartDatabase()
            print(f"🔧 Local database type: {type(self.db).__name__}")
        
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
        
        cache_key = f"stocks_{n_stocks}{filter_suffix}"
        
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        loading_msg = f"Loading top {n_stocks} stocks"
        if industry:
            loading_msg += f" in {industry}"
        if sector:
            loading_msg += f" from {sector}"
        loading_msg += "..."
        
        with st.spinner(loading_msg):
            try:
                # Get stock metadata with filters
                metadata_query = "SELECT * FROM stockmetadata WHERE 1=1"
                params = []
                
                if industry:
                    metadata_query += " AND industry = %s"
                    params.append(industry)
                
                if sector:
                    metadata_query += " AND sector = %s"
                    params.append(sector)
                
                metadata_query += " ORDER BY market_cap DESC"
                if n_stocks:
                    metadata_query += f" LIMIT {n_stocks}"
                
                top_stocks = self.db.execute_query(metadata_query, params)
                
                if top_stocks.empty:
                    st.warning("No stocks found with the specified criteria")
                    return pd.DataFrame()
                
                # Cache the result
                self.cache[cache_key] = top_stocks
                return top_stocks
                
            except Exception as e:
                st.error(f"Error loading stock data: {e}")
                logger.error(f"Error loading stock data: {e}")
                return pd.DataFrame()
    
    def load_historical_data(self, stocks_df, use_cache=True):
        """Load historical price data for stocks"""
        cache_key = f"historical_data_{len(stocks_df)}"
        
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
                        price_data = price_data.sort_values('date')
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
                logger.error(f"Error loading historical data: {e}")
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
                                'volatility_adjusted': score_data['volatility_adjusted'],
                                'smooth_momentum': score_data['smooth_momentum'],
                                'consistency_score': score_data['consistency_score'],
                                'trend_strength': score_data['trend_strength'],
                                'momentum_12_2': score_data['momentum_12_2'],
                                'fip_quality': score_data['fip_quality']
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
                                        'total_score': momentum_score['total_score'],
                                        'raw_momentum_6m': momentum_score['raw_momentum_6m'],
                                        'raw_momentum_3m': momentum_score['raw_momentum_3m'],
                                        'raw_momentum_1m': momentum_score['raw_momentum_1m'],
                                        'volatility_adjusted': momentum_score['volatility_adjusted'],
                                        'smooth_momentum': momentum_score['smooth_momentum'],
                                        'consistency_score': momentum_score['consistency_score'],
                                        'trend_strength': momentum_score['trend_strength'],
                                        'momentum_12_2': momentum_score['momentum_12_2'],
                                        'fip_quality': momentum_score['fip_quality']
                                    })
                
                else:
                    # Calculate fresh scores for all stocks
                    momentum_results = []
                    for _, stock in stocks_df.iterrows():
                        symbol = stock['stock']
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
                                    'total_score': momentum_score['total_score'],
                                    'raw_momentum_6m': momentum_score['raw_momentum_6m'],
                                    'raw_momentum_3m': momentum_score['raw_momentum_3m'],
                                    'raw_momentum_1m': momentum_score['raw_momentum_1m'],
                                    'volatility_adjusted': momentum_score['volatility_adjusted'],
                                    'smooth_momentum': momentum_score['smooth_momentum'],
                                    'consistency_score': momentum_score['consistency_score'],
                                    'trend_strength': momentum_score['trend_strength'],
                                    'momentum_12_2': momentum_score['momentum_12_2'],
                                    'fip_quality': momentum_score['fip_quality']
                                })
                
                if momentum_results:
                    momentum_df = pd.DataFrame(momentum_results)
                    momentum_df = momentum_df.sort_values('total_score', ascending=False)
                    return momentum_df
                else:
                    st.error("No momentum scores calculated")
                    return pd.DataFrame()
                    
            except Exception as e:
                st.error(f"Error calculating momentum scores: {e}")
                logger.error(f"Error calculating momentum scores: {e}")
                return pd.DataFrame()
    
    def get_available_industries(self):
        """Get list of available industries"""
        try:
            query = "SELECT DISTINCT industry FROM stockmetadata WHERE industry IS NOT NULL ORDER BY industry"
            result = self.db.execute_query(query)
            return result['industry'].tolist() if not result.empty else []
        except Exception as e:
            logger.error(f"Error getting industries: {e}")
            return []
    
    def get_available_sectors(self):
        """Get list of available sectors"""
        try:
            query = "SELECT DISTINCT sector FROM stockmetadata WHERE sector IS NOT NULL ORDER BY sector"
            result = self.db.execute_query(query)
            return result['sector'].tolist() if not result.empty else []
        except Exception as e:
            logger.error(f"Error getting sectors: {e}")
            return []
    
    def display_results(self, momentum_df, top_n=20):
        """Display momentum analysis results"""
        if momentum_df.empty:
            st.warning("No results to display")
            return
        
        st.subheader(f"🏆 Top {top_n} Momentum Stocks")
        
        # Get top N stocks
        top_stocks = momentum_df.head(top_n)
        
        # Prepare display columns - use 'symbol' if 'stock' is not available
        symbol_col = 'stock' if 'stock' in top_stocks.columns else 'symbol'
        display_columns = [
            symbol_col, 'company_name', 'market_cap', 'total_score',
            'momentum_12_2', 'fip_quality', 'raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m',
            'volatility_adjusted', 'smooth_momentum', 'consistency_score', 'trend_strength'
        ]
        
        # Filter to only include columns that actually exist
        display_columns = [col for col in display_columns if col in top_stocks.columns]
        
        # Add optional columns if they exist
        available_columns = []
        for col in ['industry', 'dividend_yield', 'roce', 'roe', 'sector']:
            if col in top_stocks.columns:
                available_columns.append(col)
        
        display_columns.extend(available_columns)
        
        # Create display dataframe
        display_df = top_stocks[display_columns].copy()
        
        # Format columns
        if 'market_cap' in display_df.columns:
            display_df['market_cap'] = display_df['market_cap'].apply(lambda x: f"₹{x/10000000:.1f}Cr" if pd.notna(x) else "N/A")
        
        # Format percentage columns
        percentage_columns = ['total_score', 'momentum_12_2', 'fip_quality', 'raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m', 'volatility_adjusted', 'smooth_momentum', 'consistency_score', 'trend_strength']
        for col in percentage_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
        
        # Format other percentage columns
        if 'dividend_yield' in display_df.columns:
            display_df['dividend_yield'] = display_df['dividend_yield'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
        if 'roce' in display_df.columns:
            display_df['roce'] = display_df['roce'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
        if 'roe' in display_df.columns:
            display_df['roe'] = display_df['roe'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
        
        # Rename columns for better display
        column_mapping = {
            'stock': 'Symbol',
            'symbol': 'Symbol',
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
            'dividend_yield': 'Div Yield',
            'roce': 'ROCE',
            'roe': 'ROE'
        }
        
        display_df = display_df.rename(columns=column_mapping)
        
        # Display the table
        st.dataframe(display_df, use_container_width=True)
        
        # Create visualizations
        self.create_visualizations(top_stocks)
    
    def create_visualizations(self, top_stocks):
        """Create momentum analysis visualizations"""
        if top_stocks.empty:
            return
        
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
                hover_data=[symbol_col, 'company_name'],
                title="Total Momentum Score vs Market Cap",
                labels={'market_cap': 'Market Cap (₹Cr)', 'total_score': 'Total Score (%)'}
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Momentum breakdown
            momentum_cols = ['raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m', 'raw_momentum_1m']
            momentum_data = top_stocks[[symbol_col] + momentum_cols].set_index(symbol_col)
            
            fig2 = px.bar(
                momentum_data.T,
                title="Momentum Breakdown by Time Period",
                labels={'value': 'Momentum (%)', 'index': 'Time Period'}
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    def run(self):
        """Main application runner"""
        st.title("📈 Indian Stock Momentum Calculator")
        st.markdown("Analyze momentum patterns in Indian stocks using advanced quantitative metrics")
        
        # Sidebar controls
        st.sidebar.header("🎛️ Analysis Controls")
        
        # Stock selection
        n_stocks = st.sidebar.slider("Number of stocks to analyze", 10, 200, 50)
        
        # Industry and sector filters
        industries = self.get_available_industries()
        sectors = self.get_available_sectors()
        
        industry = st.sidebar.selectbox("Filter by Industry", ["All"] + industries)
        sector = st.sidebar.selectbox("Filter by Sector", ["All"] + sectors)
        
        if industry == "All":
            industry = None
        if sector == "All":
            sector = None
        
        # Display options
        top_n = st.sidebar.slider("Top N results to display", 5, 50, 20)
        
        # Database stats
        if st.sidebar.button("📊 Database Stats"):
            try:
                stats = self.db.get_database_stats()
                st.sidebar.json(stats)
            except Exception as e:
                st.sidebar.error(f"Error getting database stats: {e}")
        
        # Main analysis
        if st.button("🚀 Run Momentum Analysis"):
            # Load stock data
            stocks_df = self.load_stock_data(n_stocks=n_stocks, industry=industry, sector=sector)
            
            if not stocks_df.empty:
                st.success(f"Loaded {len(stocks_df)} stocks")
                
                # Load historical data
                historical_data = self.load_historical_data(stocks_df)
                
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
    try:
        app = MomentumWebApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()
