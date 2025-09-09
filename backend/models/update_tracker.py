"""
Update Tracker for monitoring stock data update status
"""

import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime, date
from sqlalchemy import text
from .database_local import LocalDatabase

logger = logging.getLogger(__name__)

class UpdateTracker:
    """Track and manage stock data update status"""
    
    def __init__(self, database: LocalDatabase):
        """Initialize update tracker with database connection"""
        self.db = database
        self._create_update_tracker_table()
    
    def _create_update_tracker_table(self):
        """Create update tracker table if it doesn't exist"""
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS stock_update_tracker (
                stock VARCHAR(50) PRIMARY KEY,
                last_updated DATE,
                update_status VARCHAR(20) DEFAULT 'pending',
                total_records INTEGER DEFAULT 0,
                last_price_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            with self.db.engine.connect() as conn:
                conn.execute(text(create_table_query))
                conn.commit()
            
            logger.info("Update tracker table created/verified")
            
        except Exception as e:
            logger.error(f"Error creating update tracker table: {e}")
            raise
    
    def get_stocks_needing_update(self) -> List[str]:
        """Get list of stocks that need price data updates"""
        try:
            today = date.today()
            
            # Get stocks that either:
            # 1. Don't exist in tracker table
            # 2. Haven't been updated today
            # 3. Have update_status = 'failed'
            query = """
            SELECT sm.stock, sm.market_cap
            FROM stockmetadata sm
            LEFT JOIN stock_update_tracker sut ON sm.stock = sut.stock
            WHERE sut.stock IS NULL 
               OR sut.last_updated < CURRENT_DATE::date 
               OR sut.update_status = 'failed'
            ORDER BY sm.market_cap DESC
            """
            
            result = self.db.execute_query(query)
            stocks = result['stock'].tolist() if not result.empty else []
            
            logger.info(f"Found {len(stocks)} stocks needing updates")
            return stocks
            
        except Exception as e:
            logger.error(f"Error getting stocks needing update: {e}")
            return []
    
    def get_update_status(self, stock: str) -> Optional[Dict]:
        """Get update status for a specific stock"""
        try:
            query = "SELECT * FROM stock_update_tracker WHERE stock = :stock"
            result = self.db.execute_query(query, {"stock": stock})
            
            if not result.empty:
                return result.iloc[0].to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error getting update status for {stock}: {e}")
            return None
    
    def mark_update_started(self, stock: str):
        """Mark that update has started for a stock"""
        try:
            query = """
            INSERT INTO stock_update_tracker (stock, update_status, updated_at)
            VALUES (:stock, 'in_progress', CURRENT_TIMESTAMP)
            ON CONFLICT (stock) 
            DO UPDATE SET 
                update_status = 'in_progress',
                updated_at = CURRENT_TIMESTAMP
            """
            
            with self.db.engine.connect() as conn:
                conn.execute(text(query), {"stock": stock})
                conn.commit()
            
            logger.debug(f"Marked update started for {stock}")
            
        except Exception as e:
            logger.error(f"Error marking update started for {stock}: {e}")
    
    def mark_update_completed(self, stock: str, total_records: int, last_price_date: date):
        """Mark that update has completed successfully for a stock"""
        try:
            today = date.today()
            query = """
            INSERT INTO stock_update_tracker 
            (stock, last_updated, update_status, total_records, last_price_date, updated_at)
            VALUES (:stock, :today, 'completed', :total_records, :last_price_date, CURRENT_TIMESTAMP)
            ON CONFLICT (stock) 
            DO UPDATE SET 
                last_updated = :today,
                update_status = 'completed',
                total_records = :total_records,
                last_price_date = :last_price_date,
                updated_at = CURRENT_TIMESTAMP
            """
            
            with self.db.engine.connect() as conn:
                conn.execute(text(query), {"stock": stock, "today": today, "total_records": total_records, 
                                         "last_price_date": last_price_date})
                conn.commit()
            
            logger.info(f"Marked update completed for {stock}: {total_records} records, last date: {last_price_date}")
            
        except Exception as e:
            logger.error(f"Error marking update completed for {stock}: {e}")
    
    def mark_update_failed(self, stock: str, error_message: str = None):
        """Mark that update has failed for a stock"""
        try:
            query = """
            INSERT INTO stock_update_tracker (stock, update_status, updated_at)
            VALUES (:stock, 'failed', CURRENT_TIMESTAMP)
            ON CONFLICT (stock) 
            DO UPDATE SET 
                update_status = 'failed',
                updated_at = CURRENT_TIMESTAMP
            """
            
            with self.db.engine.connect() as conn:
                conn.execute(text(query), {"stock": stock})
                conn.commit()
            
            logger.warning(f"Marked update failed for {stock}: {error_message}")
            
        except Exception as e:
            logger.error(f"Error marking update failed for {stock}: {e}")
    
    def get_update_statistics(self) -> Dict:
        """Get overall update statistics"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_stocks,
                COUNT(CASE WHEN sut.update_status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN sut.update_status = 'in_progress' THEN 1 END) as in_progress,
                COUNT(CASE WHEN sut.update_status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN sut.update_status = 'pending' OR sut.update_status IS NULL THEN 1 END) as pending,
                COUNT(CASE WHEN sut.last_updated = CURRENT_DATE::date THEN 1 END) as updated_today
            FROM stockmetadata sm
            LEFT JOIN stock_update_tracker sut ON sm.stock = sut.stock
            """
            
            result = self.db.execute_query(query)
            if not result.empty:
                return result.iloc[0].to_dict()
            return {}
            
        except Exception as e:
            logger.error(f"Error getting update statistics: {e}")
            return {}
    
    def clear_failed_updates(self):
        """Reset failed updates to pending status"""
        try:
            query = """
            UPDATE stock_update_tracker 
            SET update_status = 'pending', updated_at = CURRENT_TIMESTAMP
            WHERE update_status = 'failed'
            """
            
            with self.db.engine.connect() as conn:
                result = conn.execute(text(query))
                conn.commit()
            
            logger.info(f"Reset {result.rowcount} failed updates to pending")
            
        except Exception as e:
            logger.error(f"Error clearing failed updates: {e}")
