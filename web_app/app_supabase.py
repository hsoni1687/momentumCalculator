#!/usr/bin/env python3
"""
Indian Stock Momentum Calculator - Supabase Version
A Streamlit-based web application for analyzing momentum in Indian stocks using Supabase
"""

import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

import streamlit as st
import pandas as pd
import logging
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Import our modules
from momentum_calculator import MomentumCalculator
from database_supabase import SupabaseDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Indian Stock Momentum Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

class MomentumWebApp:
    def __init__(self):
        self.db = SupabaseDatabase()
        self.momentum_calculator = MomentumCalculator()
        self.cache = {}
    
    def load_stock_data(self, use_cache=True, stocks_to_analyze=100, industry_filter=None, sector_filter=None):
        """Load stock metadata with optional filters"""
        try:
            if use_cache and 'stocks_df' in self.cache:
                st.info("Using cached stock data")
                return self.cache['stocks_df']
            
            st.info("Loading stock data from database...")
            
            # Get stock metadata with filters
            stocks_df = self.db.get_stock_metadata(industry_filter, sector_filter)
            
            if stocks_df.empty:
                st.error("No stocks found with the specified filters")
                return pd.DataFrame()
            
            # Limit to specified number of stocks
            if len(stocks_df) > stocks_to_analyze:
                stocks_df = stocks_df.head(stocks_to_analyze)
            
            # Cache the result
            if use_cache:
                self.cache['stocks_df'] = stocks_df
            
            filter_info = []
            if industry_filter:
                filter_info.append(f"Industry: {industry_filter}")
            if sector_filter:
                filter_info.append(f"Sector: {sector_filter}")
            
            filter_text = f" (Filtered by: {', '.join(filter_info)})" if filter_info else ""
            st.success(f"Loaded {len(stocks_df)} stocks{filter_text}")
            
            return stocks_df
            
        except Exception as e:
            st.error(f"Error loading stock data: {e}")
            logger.error(f"Error loading stock data: {e}")
            return pd.DataFrame()
    
    def load_historical_data(self, stocks_df):
        """Load historical price data for stocks"""
        try:
            if 'historical_data' in self.cache:
                st.info("Using cached historical data")
                return self.cache['historical_data']
            
            st.info("Loading historical data from database...")
            
            historical_data = {}
            loaded_count = 0
            
            for _, stock in stocks_df.iterrows():
                symbol = stock['stock']
                price_data = self.db.get_price_data(symbol)
                
                if not price_data.empty:
                    # Convert date column to datetime
                    price_data['date'] = pd.to_datetime(price_data['date'])
                    price_data = price_data.set_index('date')
                    historical_data[symbol] = price_data
                    loaded_count += 1
            
            # Cache the result
            self.cache['historical_data'] = historical_data
            
            st.success(f"Loaded historical data for {loaded_count} stocks")
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
                                'symbol': symbol,
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
                                'volatility_adjusted_6m': score_data['volatility_adjusted_6m'],
                                'volatility_adjusted_3m': score_data['volatility_adjusted_3m'],
                                'volatility_adjusted_1m': score_data['volatility_adjusted_1m'],
                                'relative_strength_6m': score_data['relative_strength_6m'],
                                'relative_strength_3m': score_data['relative_strength_3m'],
                                'relative_strength_1m': score_data['relative_strength_1m'],
                                'trend_score': score_data['trend_score'],
                                'volume_score': score_data['volume_score']
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
                                        'symbol': symbol,
                                        'company_name': stock['company_name'],
                                        'market_cap': stock['market_cap'],
                                        'industry': stock.get('industry', 'N/A'),
                                        'sector': stock.get('sector', 'N/A'),
                                        'dividend_yield': stock.get('dividend_yield', 'N/A'),
                                        'roce': stock.get('roce', 'N/A'),
                                        'roe': stock.get('roe', 'N/A'),
                                        'total_score': momentum_score.get('total_score', 0),
                                        'raw_momentum_6m': momentum_score.get('raw_momentum_6m', 0),
                                        'raw_momentum_3m': momentum_score.get('raw_momentum_3m', 0),
                                        'raw_momentum_1m': momentum_score.get('raw_momentum_1m', 0),
                                        'volatility_adjusted_6m': momentum_score.get('volatility_adjusted_6m', 0),
                                        'volatility_adjusted_3m': momentum_score.get('volatility_adjusted_3m', 0),
                                        'volatility_adjusted_1m': momentum_score.get('volatility_adjusted_1m', 0),
                                        'relative_strength_6m': momentum_score.get('relative_strength_6m', 0),
                                        'relative_strength_3m': momentum_score.get('relative_strength_3m', 0),
                                        'relative_strength_1m': momentum_score.get('relative_strength_1m', 0),
                                        'trend_score': momentum_score.get('trend_score', 0),
                                        'volume_score': momentum_score.get('volume_score', 0)
                                    })
                
                if not momentum_results:
                    st.error("No momentum scores calculated")
                    return pd.DataFrame()
                
                # Convert to DataFrame and sort by total score
                momentum_df = pd.DataFrame(momentum_results)
                momentum_df = momentum_df.sort_values('total_score', ascending=False)
                
                st.success(f"Calculated momentum scores for {len(momentum_df)} stocks")
                return momentum_df
                
            except Exception as e:
                st.error(f"Error calculating momentum scores: {e}")
                logger.error(f"Error calculating momentum scores: {e}")
                return pd.DataFrame()
    
    def display_results(self, momentum_df, top_n):
        """Display momentum results"""
        if momentum_df.empty:
            st.warning("No momentum data to display")
            return
        
        st.subheader(f"🏆 Top {top_n} Momentum Stocks")
        
        # Get top N stocks
        top_stocks = momentum_df.head(top_n)
        
        # Prepare display columns
        display_columns = [
            'symbol', 'company_name', 'market_cap', 'total_score',
            'raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m',
            'volatility_adjusted_6m', 'volatility_adjusted_3m', 'volatility_adjusted_1m',
            'relative_strength_6m', 'relative_strength_3m', 'relative_strength_1m',
            'trend_score', 'volume_score'
        ]
        
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
            display_df['market_cap'] = display_df['market_cap'].apply(lambda x: f"₹{x:,.0f}Cr")
        
        # Format percentage columns
        percentage_columns = [
            'total_score', 'raw_momentum_6m', 'raw_momentum_3m', 'raw_momentum_1m',
            'volatility_adjusted_6m', 'volatility_adjusted_3m', 'volatility_adjusted_1m',
            'relative_strength_6m', 'relative_strength_3m', 'relative_strength_1m',
            'trend_score', 'volume_score'
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
        
        # Column name mapping
        column_mapping = {
            'symbol': 'Symbol',
            'company_name': 'Company',
            'market_cap': 'Market Cap',
            'total_score': 'Total Score',
            'raw_momentum_6m': '6M Momentum',
            'raw_momentum_3m': '3M Momentum',
            'raw_momentum_1m': '1M Momentum',
            'volatility_adjusted_6m': 'Vol-Adj 6M',
            'volatility_adjusted_3m': 'Vol-Adj 3M',
            'volatility_adjusted_1m': 'Vol-Adj 1M',
            'relative_strength_6m': 'Rel Strength 6M',
            'relative_strength_3m': 'Rel Strength 3M',
            'relative_strength_1m': 'Rel Strength 1M',
            'trend_score': 'Trend Score',
            'volume_score': 'Volume Score',
            'industry': 'Industry',
            'sector': 'Sector',
            'dividend_yield': 'Dividend Yield',
            'roce': 'ROCE',
            'roe': 'ROE'
        }
        
        # Rename columns
        display_df = display_df.rename(columns=column_mapping)
        
        # Display the table
        st.dataframe(display_df, use_container_width=True)
        
        # Create visualizations
        self.create_visualizations(top_stocks)
    
    def create_visualizations(self, top_stocks):
        """Create visualizations for the results"""
        if top_stocks.empty:
            return
        
        # Create tabs for different visualizations
        tab1, tab2, tab3 = st.tabs(["📊 Score Distribution", "📈 Top Performers", "🏢 Sector Analysis"])
        
        with tab1:
            # Score distribution
            fig = px.histogram(
                top_stocks, 
                x='total_score', 
                title="Distribution of Total Momentum Scores",
                nbins=20
            )
            fig.update_layout(xaxis_title="Total Score", yaxis_title="Number of Stocks")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Top 10 performers
            top_10 = top_stocks.head(10)
            fig = px.bar(
                top_10, 
                x='symbol', 
                y='total_score',
                title="Top 10 Momentum Stocks",
                hover_data=['company_name', 'sector']
            )
            fig.update_layout(xaxis_title="Stock Symbol", yaxis_title="Total Score")
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Sector analysis
            if 'sector' in top_stocks.columns:
                sector_analysis = top_stocks.groupby('sector').agg({
                    'total_score': ['mean', 'count']
                }).round(2)
                sector_analysis.columns = ['Average Score', 'Count']
                sector_analysis = sector_analysis.sort_values('Average Score', ascending=False)
                
                fig = px.bar(
                    sector_analysis.reset_index(),
                    x='sector',
                    y='Average Score',
                    title="Average Momentum Score by Sector",
                    hover_data=['Count']
                )
                fig.update_layout(xaxis_title="Sector", yaxis_title="Average Score")
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
    
    def run(self):
        """Main application runner"""
        # Header
        st.title("📈 Indian Stock Momentum Calculator")
        st.markdown("""
        This calculator identifies high-quality momentum stocks using the "Frog in the Pan" methodology from Alpha Architect. 
        It analyzes stocks from NSE and BSE, focusing on smooth, consistent price movements rather than volatile spikes.
        """)
        
        # Sidebar controls
        st.sidebar.header("🎛️ Controls")
        
        # Stock selection
        stocks_to_analyze = st.sidebar.slider("Number of stocks to analyze", 10, 500, 100)
        
        # Industry filter
        industries = self.db.get_available_industries()
        selected_industry = st.sidebar.selectbox("Select Industry (Optional)", ["All Industries"] + industries)
        industry_filter = None if selected_industry == "All Industries" else selected_industry
        
        # Sector filter
        sectors = self.db.get_available_sectors()
        selected_sector = st.sidebar.selectbox("Select Sector (Optional)", ["All Sectors"] + sectors)
        sector_filter = None if selected_sector == "All Sectors" else selected_sector
        
        top_n = st.sidebar.slider("Number of top stocks to display", 10, 100, 20)
        use_cache = st.sidebar.checkbox("Use cached data", value=True)
        
        # Database stats
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
            
            if stocks_df.empty:
                st.error("No stocks found. Please adjust your filters.")
                return
            
            # Load historical data
            historical_data = self.load_historical_data(stocks_df)
            
            if not historical_data:
                st.error("No historical data found.")
                return
            
            # Calculate momentum scores
            momentum_df = self.calculate_momentum_scores(stocks_df, historical_data)
            
            if momentum_df.empty:
                st.error("Failed to calculate momentum scores")
                return
            
            # Display results
            self.display_results(momentum_df, top_n)

def main():
    """Main function"""
    # Initialize database
    st.info("🔄 Connecting to Supabase database...")
    
    try:
        # Create database instance
        db = SupabaseDatabase()
        
        # Check if database is accessible
        stats = db.get_database_stats()
        
        if not stats or not stats.get('unique_stocks_with_price'):
            st.error("❌ Database connection failed or no data found")
            return
        
        st.success("✅ Connected to Supabase database successfully")
        
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
