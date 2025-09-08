"""
Configuration settings for the Momentum Calculator
"""

# Data fetching settings
DATA_FETCH_SETTINGS = {
    'lookback_period': '1y',  # 1 year of historical data
    'cache_duration': 3600,   # Cache data for 1 hour
    'rate_limit_delay': 0.1,  # Delay between API calls
}

# Momentum calculation settings
MOMENTUM_SETTINGS = {
    'lookback_periods': {
        'short_term': 20,   # 1 month
        'medium_term': 60,  # 3 months
        'long_term': 120    # 6 months
    },
    'weights': {
        'raw_momentum_6m': 0.3,      # Long-term momentum
        'raw_momentum_3m': 0.2,      # Medium-term momentum
        'smooth_momentum': 0.25,     # Smooth momentum (Frog in the Pan)
        'volatility_adjusted': 0.15,    # Risk-adjusted momentum
        'consistency_score': 0.05,   # Consistency
        'trend_strength': 0.05       # Trend alignment
    },
    'normalization_ranges': {
        'raw_momentum_6m': (-0.5, 1.0),   # -50% to +100%
        'raw_momentum_3m': (-0.3, 0.6),   # -30% to +60%
        'smooth_momentum': (-0.3, 0.6),   # -30% to +60%
        'volatility_adjusted': (-1, 1),      # -1 to +1
    }
}

# Display settings
DISPLAY_SETTINGS = {
    'default_top_n': 50,
    'max_top_n': 10,
    'currency_symbol': '₹',
    'market_cap_unit': 'Cr',  # Crores
}

# Stock selection settings
STOCK_SELECTION_SETTINGS = {
    'max_stocks_to_analyze': 1000,  # Maximum number of stocks to fetch and analyze
    'default_stocks_to_analyze': 100,  # Default number of stocks to analyze
}

# API settings (for future use with real APIs)
API_SETTINGS = {
    'nse_base_url': 'https://www.nseindia.com',
    'bse_base_url': 'https://www.bseindia.com',
    'yfinance_enabled': True,
    'timeout': 30,
}

