"""
Market Hours Utility
Handles market hours logic for Indian stock market (NSE/BSE)
"""

from datetime import datetime, time, date, timedelta
from typing import Tuple
import pytz

class MarketHours:
    """Handles Indian stock market hours and trading day logic"""
    
    # Indian market hours (IST)
    MARKET_OPEN_TIME = time(9, 15)  # 9:15 AM
    MARKET_CLOSE_TIME = time(15, 30)  # 3:30 PM
    
    # Market timezone
    IST = pytz.timezone('Asia/Kolkata')
    
    @classmethod
    def get_current_ist_time(cls) -> datetime:
        """Get current time in IST"""
        return datetime.now(cls.IST)
    
    @classmethod
    def is_market_open(cls) -> bool:
        """
        Check if market is currently open
        
        Returns:
            bool: True if market is open, False otherwise
        """
        now = cls.get_current_ist_time()
        current_time = now.time()
        current_date = now.date()
        
        # Check if it's a weekday (Monday = 0, Sunday = 6)
        if current_date.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Check if it's within market hours
        return cls.MARKET_OPEN_TIME <= current_time <= cls.MARKET_CLOSE_TIME
    
    @classmethod
    def is_market_closed_for_day(cls) -> bool:
        """
        Check if market is closed for the current day
        
        Returns:
            bool: True if market is closed for the day, False otherwise
        """
        now = cls.get_current_ist_time()
        current_time = now.time()
        current_date = now.date()
        
        # Check if it's a weekend
        if current_date.weekday() >= 5:  # Saturday or Sunday
            return True
        
        # Check if it's after market close
        return current_time > cls.MARKET_CLOSE_TIME
    
    @classmethod
    def get_trading_date(cls) -> date:
        """
        Get the current trading date
        - If market is open: return today
        - If market is closed: return today (for same-day calculations)
        - If weekend: return next Monday
        
        Returns:
            date: The current trading date
        """
        now = cls.get_current_ist_time()
        current_date = now.date()
        
        # If it's weekend, return next Monday
        if current_date.weekday() >= 5:  # Saturday or Sunday
            days_until_monday = (7 - current_date.weekday()) % 7
            if days_until_monday == 0:  # Sunday
                days_until_monday = 1
            return current_date + timedelta(days=days_until_monday)
        
        return current_date
    
    @classmethod
    def get_previous_trading_date(cls) -> date:
        """
        Get the previous trading date
        
        Returns:
            date: The previous trading date
        """
        current_trading_date = cls.get_trading_date()
        
        # Go back one day
        prev_date = current_trading_date - timedelta(days=1)
        
        # If it's weekend, go back to Friday
        while prev_date.weekday() >= 5:  # Saturday or Sunday
            prev_date -= timedelta(days=1)
        
        return prev_date
    
    @classmethod
    def should_calculate_momentum(cls) -> bool:
        """
        Determine if momentum calculations should be performed
        
        Logic:
        - If market is open: Don't calculate (data might be incomplete)
        - If market is closed for the day: Calculate (complete daily data available)
        - If weekend: Don't calculate (wait for next trading day)
        
        Returns:
            bool: True if momentum should be calculated, False otherwise
        """
        now = cls.get_current_ist_time()
        current_time = now.time()
        current_date = now.date()
        
        # Don't calculate on weekends
        if current_date.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Don't calculate while market is open (data incomplete)
        if cls.is_market_open():
            return False
        
        # Calculate after market close (complete daily data available)
        return True
    
    @classmethod
    def should_update_data(cls) -> bool:
        """
        Determine if stock data should be updated
        
        Logic:
        - If market is open: Don't update (prices changing continuously)
        - If market is closed for the day: Update (prices are stable)
        - If weekend: Don't update (wait for next trading day)
        
        Returns:
            bool: True if data should be updated, False otherwise
        """
        now = cls.get_current_ist_time()
        current_date = now.date()
        
        # Don't update on weekends
        if current_date.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Only update when market is closed (prices are stable)
        return not cls.is_market_open()
    
    @classmethod
    def get_market_status_message(cls) -> str:
        """
        Get a human-readable market status message
        
        Returns:
            str: Market status message
        """
        now = cls.get_current_ist_time()
        current_time = now.time()
        current_date = now.date()
        
        if current_date.weekday() >= 5:  # Weekend
            return f"Weekend - Market closed. Next trading day: {cls.get_trading_date()}"
        elif cls.is_market_open():
            return f"Market is open (9:15 AM - 3:30 PM IST). Current time: {current_time.strftime('%H:%M:%S')} IST"
        else:
            return f"Market is closed. Current time: {current_time.strftime('%H:%M:%S')} IST"
    
    @classmethod
    def get_next_market_open_time(cls) -> datetime:
        """
        Get the next market open time
        
        Returns:
            datetime: Next market open time in IST
        """
        now = cls.get_current_ist_time()
        current_date = now.date()
        
        # If it's weekend, get next Monday
        if current_date.weekday() >= 5:  # Saturday or Sunday
            days_until_monday = (7 - current_date.weekday()) % 7
            if days_until_monday == 0:  # Sunday
                days_until_monday = 1
            next_trading_date = current_date + timedelta(days=days_until_monday)
        else:
            # If market is closed for today, next open is tomorrow
            if cls.is_market_closed_for_day():
                next_trading_date = current_date + timedelta(days=1)
            else:
                # Market is open, next open is today
                next_trading_date = current_date
        
        # Combine date with market open time
        return datetime.combine(next_trading_date, cls.MARKET_OPEN_TIME).replace(tzinfo=cls.IST)

