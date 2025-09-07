"""
Momentum Calculator implementing the "Frog in the Pan" methodology
Based on Alpha Architect's approach to identifying high-quality momentum stocks
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MomentumCalculator:
    def __init__(self):
        # Updated to match Alpha Architect methodology
        # Adjusted for available data (249 days)
        self.lookback_periods = {
            'momentum_12_2': 180,  # ~9 months (180 trading days)
            'momentum_6m': 100,    # ~5 months (100 trading days)
            'momentum_3m': 50,     # ~2.5 months (50 trading days)
            'momentum_1m': 15,     # ~3 weeks (15 trading days)
            'skip_recent': 15      # Skip most recent 3 weeks (15 trading days)
        }
    
    def calculate_raw_momentum(self, price_data, period):
        """Calculate raw momentum (total return) over specified period"""
        if len(price_data) < period + 1:
            return np.nan
        
        current_price = price_data.iloc[-1]
        past_price = price_data.iloc[-(period+1)]
        
        return (current_price - past_price) / past_price
    
    def calculate_12_2_momentum(self, price_data):
        """
        Calculate 12-2 momentum: 12 months return excluding the most recent month
        This is the primary momentum measure used by Alpha Architect
        """
        if len(price_data) < self.lookback_periods['momentum_12_2'] + self.lookback_periods['skip_recent']:
            return np.nan
        
        # Current price (end of period)
        current_price = price_data.iloc[-1]
        
        # Price 12 months ago (start of period)
        start_price = price_data.iloc[-(self.lookback_periods['momentum_12_2'] + self.lookback_periods['skip_recent'])]
        
        return (current_price - start_price) / start_price
    
    def calculate_volatility_adjusted_momentum(self, returns, period):
        """Calculate volatility-adjusted momentum (Sharpe-like ratio)"""
        if len(returns) < period:
            return np.nan
        
        recent_returns = returns.tail(period)
        mean_return = recent_returns.mean()
        volatility = recent_returns.std()
        
        if volatility == 0:
            return 0
        
        return mean_return / volatility
    
    def calculate_smooth_momentum(self, price_data, period):
        """
        Calculate smooth momentum - stocks with consistent upward movement
        This is the core of the "Frog in the Pan" methodology
        """
        if len(price_data) < period:
            return np.nan
        
        # Calculate rolling returns over the period
        rolling_returns = price_data.pct_change().tail(period)
        
        # Count positive return days
        positive_days = (rolling_returns > 0).sum()
        total_days = len(rolling_returns)
        
        # Calculate consistency ratio
        consistency_ratio = positive_days / total_days
        
        # Calculate total return
        total_return = self.calculate_raw_momentum(price_data, period)
        
        # Smooth momentum = total return * consistency ratio
        smooth_momentum = total_return * consistency_ratio
        
        return smooth_momentum
    
    def calculate_fip_momentum_quality(self, price_data):
        """
        Calculate Frog-in-the-Pan (FIP) momentum quality measure
        Based on Alpha Architect's methodology for measuring momentum quality
        
        FIP measures the consistency of returns by analyzing the pattern of 
        positive vs negative return periods (typically months)
        """
        if len(price_data) < self.lookback_periods['momentum_12_2']:
            return np.nan
        
        # Calculate monthly returns for the past 10 months (adjusted for available data)
        monthly_returns = self._calculate_monthly_returns(price_data, 10)
        
        if len(monthly_returns) < 8:  # Need at least 8 months of data
            return np.nan
        
        # Count positive and negative months
        positive_months = (monthly_returns > 0).sum()
        negative_months = (monthly_returns < 0).sum()
        total_months = len(monthly_returns)
        
        # Calculate percentages
        pct_positive = positive_months / total_months
        pct_negative = negative_months / total_months
        
        # Calculate cumulative 12-month return
        cumulative_return = (1 + monthly_returns).prod() - 1
        
        # Information discreteness: (pct_positive - pct_negative) * sign(cumulative_return)
        information_discreteness = (pct_positive - pct_negative) * np.sign(cumulative_return)
        
        return information_discreteness
    
    def _calculate_monthly_returns(self, price_data, months):
        """
        Calculate monthly returns from daily price data
        """
        # Resample to monthly and calculate returns
        monthly_prices = price_data.resample('ME').last()
        monthly_returns = monthly_prices.pct_change().dropna()
        
        # Return the last N months
        return monthly_returns.tail(months)
    
    def calculate_quality_momentum_score(self, hist_data):
        """
        Calculate comprehensive quality momentum score
        Combines multiple momentum factors with quality adjustments
        """
        # Check if hist_data is valid and has enough data
        if hist_data is None or len(hist_data) < 120:
            return {
                'total_score': 0,
                'raw_momentum_6m': 0,
                'raw_momentum_3m': 0,
                'raw_momentum_1m': 0,
                'volatility_adjusted': 0,
                'smooth_momentum': 0,
                'consistency_score': 0,
                'trend_strength': 0
            }
        
        # Additional check for empty DataFrame/Series
        try:
            if hasattr(hist_data, 'empty') and hist_data.empty:
                return {
                    'total_score': 0,
                    'raw_momentum_6m': 0,
                    'raw_momentum_3m': 0,
                    'raw_momentum_1m': 0,
                    'volatility_adjusted': 0,
                    'smooth_momentum': 0,
                    'consistency_score': 0,
                    'trend_strength': 0
                }
        except Exception:
            # If there's any issue with the empty check, continue
            pass
        
        # Get close prices - use uppercase 'Close' column
        try:
            close_prices = hist_data['Close']
            returns = hist_data['Returns'].dropna()
        except KeyError as e:
            logger.error(f"Missing required column in historical data: {e}")
            return {
                'total_score': 0,
                'raw_momentum_6m': 0,
                'raw_momentum_3m': 0,
                'raw_momentum_1m': 0,
                'volatility_adjusted': 0,
                'smooth_momentum': 0,
                'consistency_score': 0,
                'trend_strength': 0
            }
        
        # Calculate momentum metrics using Alpha Architect methodology
        # Primary momentum measure: 12-2 momentum (12 months excluding last month)
        momentum_12_2 = self.calculate_12_2_momentum(close_prices)
        
        # Additional momentum periods for analysis
        raw_momentum_6m = self.calculate_raw_momentum(close_prices, self.lookback_periods['momentum_6m'])
        raw_momentum_3m = self.calculate_raw_momentum(close_prices, self.lookback_periods['momentum_3m'])
        raw_momentum_1m = self.calculate_raw_momentum(close_prices, self.lookback_periods['momentum_1m'])
        
        # Volatility-adjusted momentum
        vol_adj_momentum = self.calculate_volatility_adjusted_momentum(returns, 60)
        
        # FIP (Frog in the Pan) momentum quality measure
        fip_quality = self.calculate_fip_momentum_quality(close_prices)
        
        # Smooth momentum (backward compatibility)
        smooth_momentum = self.calculate_smooth_momentum(close_prices, 120)
        
        # Consistency score (percentage of positive return days)
        if len(returns) >= 60:
            recent_returns = returns.tail(60)
            consistency_score = (recent_returns > 0).sum() / len(recent_returns)
        else:
            consistency_score = 0
        
        # Trend strength (how well price follows moving averages)
        if 'SMA_20' in hist_data.columns and 'SMA_50' in hist_data.columns:
            sma_20 = hist_data['SMA_20'].iloc[-1]
            sma_50 = hist_data['SMA_50'].iloc[-1]
            current_price = close_prices.iloc[-1]
            
            # Trend strength: 1 if price > SMA20 > SMA50, 0.5 if mixed, 0 if declining
            if current_price > sma_20 > sma_50:
                trend_strength = 1.0
            elif current_price > sma_20 or current_price > sma_50:
                trend_strength = 0.5
            else:
                trend_strength = 0.0
        else:
            trend_strength = 0.0
        
        # Calculate weighted total score
        # Weights based on Alpha Architect methodology
        weights = {
            'raw_momentum_6m': 0.3,      # Long-term momentum
            'raw_momentum_3m': 0.2,      # Medium-term momentum
            'smooth_momentum': 0.25,     # Smooth momentum (Frog in the Pan)
            'vol_adj_momentum': 0.15,    # Risk-adjusted momentum
            'consistency_score': 0.05,   # Consistency
            'trend_strength': 0.05       # Trend alignment
        }
        
        # Normalize scores to 0-1 range
        normalized_scores = {
            'raw_momentum_6m': max(0, min(1, (raw_momentum_6m + 0.5) / 1.0)),  # Assume -50% to +50% range
            'raw_momentum_3m': max(0, min(1, (raw_momentum_3m + 0.3) / 0.6)),  # Assume -30% to +30% range
            'smooth_momentum': max(0, min(1, (smooth_momentum + 0.3) / 0.6)),  # Assume -30% to +30% range
            'vol_adj_momentum': max(0, min(1, (vol_adj_momentum + 1) / 2)),    # Assume -1 to +1 range
            'consistency_score': consistency_score,
            'trend_strength': trend_strength
        }
        
        # Calculate weighted total score
        total_score = sum(weights[key] * normalized_scores[key] for key in weights)
        
        return {
            'total_score': total_score,
            'momentum_12_2': momentum_12_2,  # Primary Alpha Architect momentum measure
            'fip_quality': fip_quality,      # Frog in the Pan quality measure
            'raw_momentum_6m': raw_momentum_6m,
            'raw_momentum_3m': raw_momentum_3m,
            'raw_momentum_1m': raw_momentum_1m,
            'volatility_adjusted': vol_adj_momentum,
            'smooth_momentum': smooth_momentum,
            'consistency_score': consistency_score,
            'trend_strength': trend_strength,
            'normalized_scores': normalized_scores
        }
    
    def calculate_momentum_for_stocks(self, stocks_data, historical_data_dict):
        """
        Calculate momentum scores for a list of stocks
        """
        results = []
        
        for _, stock in stocks_data.iterrows():
            symbol = stock['symbol']
            company_name = stock['company_name']
            market_cap = stock['market_cap']
            sector = stock['sector']
            exchange = stock['exchange']
            
            logger.info(f"Calculating momentum for {symbol} - {company_name}")
            
            # Get historical data for this stock
            if symbol in historical_data_dict:
                hist_data = historical_data_dict[symbol]
                try:
                    momentum_scores = self.calculate_quality_momentum_score(hist_data)
                    
                    result = {
                        'symbol': symbol,
                        'company_name': company_name,
                        'market_cap': market_cap,
                        'sector': sector,
                        'exchange': exchange,
                        'industry': stock.get('industry', 'Unknown'),
                        'dividend_yield': stock.get('dividend_yield', None),
                        'roce': stock.get('roce', None),
                        'roe': stock.get('roe', None),
                        **momentum_scores
                    }
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error calculating momentum for {symbol}: {e}")
                    # Add a result with zero scores for this stock
                    result = {
                        'symbol': symbol,
                        'company_name': company_name,
                        'market_cap': market_cap,
                        'sector': sector,
                        'exchange': exchange,
                        'industry': stock.get('industry', 'Unknown'),
                        'dividend_yield': stock.get('dividend_yield', None),
                        'roce': stock.get('roce', None),
                        'roe': stock.get('roe', None),
                        'total_score': 0,
                        'raw_momentum_6m': 0,
                        'raw_momentum_3m': 0,
                        'raw_momentum_1m': 0,
                        'volatility_adjusted': 0,
                        'smooth_momentum': 0,
                        'consistency_score': 0,
                        'trend_strength': 0
                    }
                    results.append(result)
            else:
                logger.warning(f"No historical data found for {symbol}")
        
        return pd.DataFrame(results)
    
    def rank_stocks(self, momentum_df, top_n=20):
        """
        Rank stocks by momentum score and return top N
        """
        if momentum_df is None or len(momentum_df) == 0:
            return pd.DataFrame()
        
        # Additional check for empty DataFrame
        try:
            if hasattr(momentum_df, 'empty') and momentum_df.empty:
                return pd.DataFrame()
        except Exception:
            # If there's any issue with the empty check, continue
            pass
        
        # Sort by total score in descending order
        ranked_stocks = momentum_df.sort_values('total_score', ascending=False)
        
        # Add rank
        ranked_stocks['rank'] = range(1, len(ranked_stocks) + 1)
        
        return ranked_stocks.head(top_n)

if __name__ == "__main__":
    # Test the momentum calculator
    calculator = MomentumCalculator()
    print("Momentum Calculator initialized successfully")

