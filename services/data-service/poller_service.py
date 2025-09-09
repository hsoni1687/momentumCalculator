"""
Poller Service - Integrated into Data Service for automatic stock data updates
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
import time
from models import DatabaseService, UpdateTracker, DataUpdater

logger = logging.getLogger(__name__)

class PollerService:
    """Automatic poller service for stock data updates"""
    
    def __init__(self, database_service: DatabaseService):
        """Initialize poller service"""
        self.db_service = database_service
        self.update_tracker = UpdateTracker(database_service.db)
        self.data_updater = DataUpdater(database_service.db, self.update_tracker)
        self.is_running = False
        self.update_interval = 300  # 5 minutes between update cycles
        self.batch_size = 10  # Number of stocks to update in each batch
        
    async def start_polling(self):
        """Start the automatic polling service"""
        if self.is_running:
            logger.warning("Poller service is already running")
            return
        
        self.is_running = True
        logger.info("Starting poller service for automatic stock data updates")
        
        try:
            while self.is_running:
                await self._update_cycle()
                
                if self.is_running:
                    logger.info(f"Update cycle completed. Waiting {self.update_interval} seconds for next cycle...")
                    await asyncio.sleep(self.update_interval)
                    
        except Exception as e:
            logger.error(f"Error in poller service: {e}")
        finally:
            self.is_running = False
            logger.info("Poller service stopped")
    
    async def stop_polling(self):
        """Stop the automatic polling service"""
        logger.info("Stopping poller service...")
        self.is_running = False
    
    async def _update_cycle(self):
        """Execute one update cycle"""
        try:
            # Get stocks that need updates
            stocks_to_update = self.update_tracker.get_stocks_needing_update()
            
            if not stocks_to_update:
                logger.info("No stocks need updates. All data is current.")
                return
            
            logger.info(f"Starting update cycle for {len(stocks_to_update)} stocks")
            
            # Process stocks in batches
            total_updated = 0
            total_failed = 0
            
            for i in range(0, len(stocks_to_update), self.batch_size):
                if not self.is_running:
                    break
                
                batch = stocks_to_update[i:i + self.batch_size]
                logger.info(f"Processing batch {i//self.batch_size + 1}: {len(batch)} stocks")
                
                # Update batch of stocks
                batch_results = self.data_updater.bulk_update_stocks(batch)
                
                # Count results
                for stock, (success, message) in batch_results.items():
                    if success:
                        total_updated += 1
                        logger.info(f"✅ {stock}: {message}")
                    else:
                        total_failed += 1
                        logger.warning(f"❌ {stock}: {message}")
                
                # Small delay between batches
                if i + self.batch_size < len(stocks_to_update):
                    await asyncio.sleep(2)
            
            # Log cycle summary
            logger.info(f"Update cycle completed: {total_updated} successful, {total_failed} failed")
            
            # Get and log statistics
            stats = self.update_tracker.get_update_statistics()
            if stats:
                logger.info(f"Update statistics: {stats}")
            
        except Exception as e:
            logger.error(f"Error in update cycle: {e}")
    
    async def force_update_all(self):
        """Force update all stocks (ignore last update date)"""
        logger.info("Starting forced update of all stocks")
        
        try:
            # Get all stocks from metadata
            all_stocks_df = self.db_service.get_stock_metadata()
            all_stocks = all_stocks_df['stock'].tolist()
            
            logger.info(f"Force updating {len(all_stocks)} stocks")
            
            # Clear failed updates first
            self.update_tracker.clear_failed_updates()
            
            # Update all stocks
            results = self.data_updater.bulk_update_stocks(all_stocks)
            
            # Log results
            successful = sum(1 for success, _ in results.values() if success)
            failed = len(results) - successful
            
            logger.info(f"Force update completed: {successful} successful, {failed} failed")
            
            return {
                "total_stocks": len(all_stocks),
                "successful": successful,
                "failed": failed,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in force update: {e}")
            return {"error": str(e)}
    
    async def update_specific_stocks(self, stocks: List[str]):
        """Update specific stocks"""
        logger.info(f"Updating specific stocks: {stocks}")
        
        try:
            results = self.data_updater.bulk_update_stocks(stocks)
            
            successful = sum(1 for success, _ in results.values() if success)
            failed = len(results) - successful
            
            logger.info(f"Specific update completed: {successful} successful, {failed} failed")
            
            return {
                "requested_stocks": len(stocks),
                "successful": successful,
                "failed": failed,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error updating specific stocks: {e}")
            return {"error": str(e)}
    
    def get_poller_status(self) -> Dict:
        """Get current poller service status"""
        stats = self.update_tracker.get_update_statistics()
        
        return {
            "is_running": self.is_running,
            "update_interval": self.update_interval,
            "batch_size": self.batch_size,
            "statistics": stats,
            "last_check": datetime.now().isoformat()
        }
    
    def get_stocks_needing_update(self) -> List[str]:
        """Get list of stocks that need updates"""
        return self.update_tracker.get_stocks_needing_update()
    
    def get_update_statistics(self) -> Dict:
        """Get update statistics"""
        return self.update_tracker.get_update_statistics()
