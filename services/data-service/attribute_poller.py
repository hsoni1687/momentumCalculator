#!/usr/bin/env python3
"""
Financial Attributes Poller Service
On-demand poller for updating financial attributes (sector, industry, roce, roe, dividend_yield)
"""

import asyncio
import logging
import os
from typing import List, Dict, Tuple
from models.data_fetcher import DataUpdater
from models.database_local import LocalDatabase

logger = logging.getLogger(__name__)

class AttributePoller:
    """Dedicated poller for financial attributes updates"""
    
    def __init__(self, database_service):
        self.db = database_service.db  # Get the LocalDatabase instance
        from models.update_tracker import UpdateTracker
        update_tracker = UpdateTracker(self.db)
        self.data_updater = DataUpdater(self.db, update_tracker)
        self.is_running = False
        self.batch_size = 50  # Process 50 stocks at a time
        self.max_retries = 5
        self.rate_limit_cooldown = False
        self.cooldown_until = None
        
        # Get service instance ID for coordination
        self.instance_id = os.getenv("SERVICE_INSTANCE", "1")
        logger.info(f"AttributePoller initialized for instance {self.instance_id}")
        
    def _should_pause_due_to_rate_limit(self) -> bool:
        """Check if we should pause due to rate limiting"""
        if self.rate_limit_cooldown and self.cooldown_until:
            from datetime import datetime
            if datetime.now() < self.cooldown_until:
                return True
            else:
                # Cooldown period has ended
                self.rate_limit_cooldown = False
                self.cooldown_until = None
                logger.info("🔄 Rate limit cooldown period ended. Resuming attribute updates...")
        return False
        
    async def start_attribute_polling(self):
        """Start the attribute polling service (on-demand)"""
        if self.is_running:
            logger.warning("Attribute poller service is already running")
            return
        
        self.is_running = True
        logger.info("Starting attribute poller service for financial attributes updates")
        
        try:
            while self.is_running:
                # Check for stocks needing attribute updates
                await self._run_attribute_update_cycle()
                
                # Wait 5 minutes before next check (less aggressive)
                await asyncio.sleep(300)
                
        except Exception as e:
            logger.error(f"Error in attribute poller service: {e}")
        finally:
            self.is_running = False
            logger.info("Attribute poller service stopped")
    
    async def _run_attribute_update_cycle(self):
        """Run the attribute update cycle"""
        try:
            # Check if we should pause due to rate limiting
            if self._should_pause_due_to_rate_limit():
                logger.info("⏸️ Pausing attribute updates due to rate limit cooldown...")
                return
                
            logger.info("Starting attribute update cycle...")
            
            # Check if there are any pending operations first
            pending_count = self.data_updater.get_pending_attribute_stocks()
            if not pending_count:
                logger.info("No stocks pending attribute updates. Skipping cycle.")
                return
            
            # Ensure all missing stocks are in pending operations (only critical ones now)
            added_count = self.data_updater.ensure_missing_stocks_in_pending()
            if added_count > 0:
                logger.info(f"Added {added_count} stocks to pending operations")
            
            # Clean up stocks that have sector/industry but are missing other attributes
            cleaned_count = self.data_updater.cleanup_completed_attribute_stocks()
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} stocks with partial attributes")
            
            # Get stocks pending attribute updates (excluding those with 5+ retries)
            missing_attributes = self.data_updater.get_pending_attribute_stocks()
            
            # Instance coordination: Each instance processes different stocks
            # Instance 1 processes even indices, Instance 2 processes odd indices
            if self.instance_id == "2":
                missing_attributes = missing_attributes[1::2]  # Odd indices
            else:
                missing_attributes = missing_attributes[0::2]  # Even indices
            
            # Get stocks that have exceeded retry limit
            exhausted_stocks = self.data_updater.get_exhausted_retry_stocks('attributes')
            if exhausted_stocks:
                logger.warning(f"⚠️ Skipping {len(exhausted_stocks)} stocks that have exceeded 5 retry attempts: {exhausted_stocks[:5]}{'...' if len(exhausted_stocks) > 5 else ''}")
                # Remove exhausted stocks from missing_attributes list
                missing_attributes = [stock for stock in missing_attributes if stock not in exhausted_stocks]
            
            if not missing_attributes:
                if exhausted_stocks:
                    logger.info(f"All remaining stocks have financial attributes. {len(exhausted_stocks)} stocks skipped due to retry limit.")
                else:
                    logger.info("All stocks have financial attributes")
                return
            
            logger.info(f"Instance {self.instance_id}: Found {len(missing_attributes)} stocks missing financial attributes")
            
            # Process in batches
            for i in range(0, len(missing_attributes), self.batch_size):
                if not self.is_running:
                    break
                    
                batch = missing_attributes[i:i + self.batch_size]
                logger.info(f"🔄 Instance {self.instance_id}: Processing batch {i//self.batch_size + 1}/{len(missing_attributes)//self.batch_size + 1}: {len(batch)} stocks")
                
                # Update attributes
                results = self.data_updater.update_attributes_for_stocks(batch)
                
                # Log results
                successful = sum(1 for success, _ in results.values() if success)
                failed = len(results) - successful
                logger.info(f"📊 Instance {self.instance_id}: Batch {i//self.batch_size + 1} completed: ✅ {successful} successful, ❌ {failed} failed")
                
                # Check if we're hitting rate limits
                rate_limit_errors = sum(1 for success, msg in results.values() 
                                      if not success and ("Too Many Requests" in msg or "Rate limited" in msg))
                
                if rate_limit_errors > 0:
                    logger.warning(f"🚫 Detected {rate_limit_errors} rate limit errors in this batch. Implementing extended cooldown...")
                    # Set cooldown period
                    from datetime import datetime, timedelta
                    self.rate_limit_cooldown = True
                    self.cooldown_until = datetime.now() + timedelta(minutes=5)  # 5 minute cooldown
                    logger.warning(f"⏸️ Attribute updates paused until {self.cooldown_until.strftime('%H:%M:%S')}")
                    break  # Stop processing more batches
                else:
                    # Normal delay between batches
                    await asyncio.sleep(10)
            
            logger.info("Attribute update cycle completed")
            
        except Exception as e:
            logger.error(f"Error in attribute update cycle: {e}")
    
    async def run_manual_attribute_update(self, stocks: List[str] = None):
        """Manually trigger attribute update for specific stocks or all missing stocks"""
        try:
            if stocks:
                logger.info(f"Manual attribute update triggered for {len(stocks)} specific stocks")
                results = self.data_updater.update_attributes_for_stocks(stocks)
            else:
                logger.info("Manual attribute update triggered for all missing stocks")
                await self._run_attribute_update_cycle()
                
        except Exception as e:
            logger.error(f"Error in manual attribute update: {e}")
    
    async def stop_attribute_polling(self):
        """Stop the attribute polling service"""
        logger.info("Stopping attribute poller service...")
        self.is_running = False
    
    def get_attribute_status(self) -> Dict:
        """Get current status of attribute updates"""
        try:
            missing_attributes = self.data_updater.get_stocks_missing_attributes()
            pending_attributes = self.data_updater.get_pending_attributes()
            total_stocks = len(self.db.get_stock_metadata())
            
            return {
                "total_stocks": total_stocks,
                "missing_attributes": len(missing_attributes),
                "pending_attributes": len(pending_attributes),
                "completion_percentage": round(((total_stocks - len(missing_attributes)) / total_stocks) * 100, 2) if total_stocks > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting attribute status: {e}")
            return {}
    
    def get_price_status(self) -> Dict:
        """Get current status of price updates"""
        try:
            pending_prices = self.data_updater.get_pending_prices()
            total_stocks = len(self.db.get_stock_metadata())
            
            return {
                "total_stocks": total_stocks,
                "pending_prices": len(pending_prices),
                "completion_percentage": round(((total_stocks - len(pending_prices)) / total_stocks) * 100, 2) if total_stocks > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting price status: {e}")
            return {}
    
    async def reset_all_attribute_retries(self):
        """Reset retry count for all stocks to allow fresh attribute fetching"""
        try:
            logger.info("🔄 Resetting retry counts for all stocks...")
            reset_count = self.data_updater.reset_all_retry_counts('attributes')
            logger.info(f"✅ Reset retry counts for {reset_count} stocks")
            return reset_count
        except Exception as e:
            logger.error(f"Error resetting retry counts: {e}")
            return 0
