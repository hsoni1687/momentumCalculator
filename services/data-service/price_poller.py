#!/usr/bin/env python3
"""
Price Data Poller Service
Automatically runs at 3:35 PM daily to update stock price data
"""

import asyncio
import logging
from datetime import datetime, time, date, timedelta
import pytz
from typing import List, Tuple
from models.data_fetcher import DataUpdater
from models.database_local import LocalDatabase
from utils.market_hours import MarketHours

logger = logging.getLogger(__name__)

class PricePoller:
    """Dedicated poller for stock price data updates"""
    
    def __init__(self, database_service):
        self.db = database_service.db  # Get the LocalDatabase instance
        from models.update_tracker import UpdateTracker
        update_tracker = UpdateTracker(self.db)
        self.data_updater = DataUpdater(self.db, update_tracker)
        self.is_running = False
        self.max_retries = 5  # Total attempts: initial + 4 retries
        self.retry_delay = 300  # 5 minutes between retries
        
        # Schedule: 3:35 PM IST daily
        self.schedule_time = time(15, 35)  # 3:35 PM
        self.ist = pytz.timezone('Asia/Kolkata')
        
    async def start_price_polling(self):
        """Start the price polling service with scheduled execution"""
        if self.is_running:
            logger.warning("Price poller service is already running")
            return
        
        self.is_running = True
        logger.info("Starting price poller service for automatic price updates")
        
        try:
            while self.is_running:
                # Check if it's time to run (3:35 PM IST)
                if self._should_run_price_update():
                    logger.info("Starting scheduled price update cycle...")
                    await self._run_price_update_cycle()
                else:
                    # Wait 1 minute before checking again
                    await asyncio.sleep(60)
                    
        except Exception as e:
            logger.error(f"Error in price poller service: {e}")
        finally:
            self.is_running = False
            logger.info("Price poller service stopped")
    
    def _should_run_price_update(self) -> bool:
        """Check if it's time to run price updates (market closed or 3:35 PM IST)"""
        try:
            now_ist = datetime.now(self.ist)
            current_time = now_ist.time()
            current_date = now_ist.date()
            
            # Check if market is closed (after 3:30 PM) and we haven't run today
            if (current_time >= time(15, 30) and  # After market close
                not self._has_run_today(current_date)):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking schedule: {e}")
            return False
    
    def _has_run_today(self, check_date: date) -> bool:
        """Check if price update has already run today"""
        try:
            # Check if we have price data updated today
            query = """
            SELECT COUNT(*) as count FROM stockmetadata s
            WHERE EXISTS (
                SELECT 1 FROM tickerprice t 
                WHERE t.stock = s.stock 
                AND DATE(t.date) = %s
            )
            """
            result = self.db.execute_query(query, (check_date,))
            return result.iloc[0]['count'] > 0 if not result.empty else False
            
        except Exception as e:
            logger.error(f"Error checking if price update ran today: {e}")
            return False
    
    async def _run_price_update_cycle(self):
        """Run the complete price update cycle with retries"""
        try:
            logger.info("Starting price update cycle...")
            
            # Get all stocks that need price updates
            stocks_to_update = self._get_stocks_needing_price_update()
            
            # Get stocks that have exceeded retry limit for prices
            exhausted_price_stocks = self.data_updater.get_exhausted_retry_stocks('prices')
            if exhausted_price_stocks:
                logger.warning(f"⚠️ Skipping {len(exhausted_price_stocks)} stocks that have exceeded 5 price update retry attempts: {exhausted_price_stocks[:5]}{'...' if len(exhausted_price_stocks) > 5 else ''}")
            
            if not stocks_to_update:
                logger.info("No stocks need price updates")
                return
            
            logger.info(f"Found {len(stocks_to_update)} stocks needing price updates")
            
            # Run initial update
            success_count = await self._update_stock_prices(stocks_to_update, attempt=1)
            
            # Run retries for failed stocks
            for attempt in range(2, self.max_retries + 1):
                if not self.is_running:
                    break
                    
                # Wait before retry
                logger.info(f"Waiting {self.retry_delay} seconds before retry attempt {attempt}")
                await asyncio.sleep(self.retry_delay)
                
                # Get stocks that still need updates
                pending_stocks = self._get_pending_price_stocks()
                
                if not pending_stocks:
                    logger.info("All stocks updated successfully")
                    break
                
                logger.info(f"Retry attempt {attempt}: {len(pending_stocks)} stocks still pending")
                retry_success = await self._update_stock_prices(pending_stocks, attempt=attempt)
                success_count += retry_success
            
            # Final status
            final_pending = self._get_pending_price_stocks()
            logger.info(f"Price update cycle completed. Final pending: {len(final_pending)} stocks")
            
        except Exception as e:
            logger.error(f"Error in price update cycle: {e}")
    
    def _get_stocks_needing_price_update(self) -> List[str]:
        """Get list of stocks that need price updates (only stocks without recent price data)"""
        try:
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            # Get stocks that don't have price data for today OR yesterday
            # This ensures we only update stocks that actually need new data
            query = """
            SELECT sm.stock FROM stockmetadata sm
            WHERE NOT EXISTS (
                SELECT 1 FROM tickerprice tp 
                WHERE tp.stock = sm.stock 
                AND DATE(tp.date) IN (%s, %s)
            )
            ORDER BY sm.market_cap DESC
            """
            result = self.db.execute_query(query, (today, yesterday))
            stocks_needing_update = result['stock'].tolist() if not result.empty else []
            
            if stocks_needing_update:
                logger.info(f"📊 Found {len(stocks_needing_update)} stocks without recent price data (today or yesterday)")
            else:
                logger.info("✅ All stocks have recent price data")
                
            return stocks_needing_update
            
        except Exception as e:
            logger.error(f"Error getting stocks needing price update: {e}")
            return []
    
    def _get_pending_price_stocks(self) -> List[str]:
        """Get stocks that are in pending operations for price updates"""
        try:
            query = """
            SELECT stock FROM pending_operations 
            WHERE operation_type = 'prices' 
            AND retry_count < %s
            ORDER BY created_at ASC
            """
            result = self.db.execute_query(query, (5,))  # Use 5 as max retries
            return result['stock'].tolist() if not result.empty else []
            
        except Exception as e:
            logger.error(f"Error getting pending price stocks: {e}")
            return []
    
    async def _update_stock_prices(self, stocks: List[str], attempt: int) -> int:
        """Update prices for a list of stocks using batch processing"""
        try:
            logger.info(f"🚀 Starting batch price update for {len(stocks)} stocks (attempt {attempt}/{self.max_retries})")
            
            # Use batch processing instead of individual updates
            results = self.data_updater.bulk_update_stocks(stocks)
            
            success_count = 0
            failed_stocks = []
            
            for stock, (success, message) in results.items():
                if success:
                    success_count += 1
                    logger.info(f"✅ {stock}: Price updated successfully + momentum calculated")
                    # Remove from pending if it was there
                    self.data_updater.remove_from_pending(stock, 'prices')
                else:
                    failed_stocks.append(stock)
                    logger.warning(f"❌ {stock}: Price update failed: {message}")
                    # Add to pending for retry
                    self.data_updater.add_to_pending_prices(stock, message)
            
            logger.info(f"📊 Batch price update attempt {attempt} completed: ✅ {success_count}/{len(stocks)} successful, ❌ {len(failed_stocks)} failed")
            
            if failed_stocks:
                logger.info(f"Failed stocks: {failed_stocks[:10]}{'...' if len(failed_stocks) > 10 else ''}")
            
            return success_count
            
        except Exception as e:
            error_msg = f"Batch price update error: {str(e)}"
            logger.error(error_msg)
            
            # Fall back to individual processing
            logger.info("Falling back to individual stock processing...")
            success_count = 0
            
            for stock in stocks:
                if not self.is_running:
                    break
                    
                try:
                    logger.info(f"📈 {stock}: Updating price data (fallback attempt {attempt}/{self.max_retries})")
                    
                    # Update price data
                    success, message = self.data_updater.update_stock_price_data(stock)
                    
                    if success:
                        success_count += 1
                        logger.info(f"✅ {stock}: Price updated successfully + momentum calculated")
                        # Remove from pending if it was there
                        self.data_updater.remove_from_pending(stock, 'prices')
                    else:
                        logger.warning(f"❌ {stock}: Price update failed: {message}")
                        # Add to pending for retry
                        self.data_updater.add_to_pending_prices(stock, message)
                    
                    # Small delay between updates
                    await asyncio.sleep(0.5)
                    
                except Exception as stock_error:
                    stock_error_msg = f"Error updating price for {stock}: {str(stock_error)}"
                    logger.error(stock_error_msg)
                    self.data_updater.add_to_pending_prices(stock, stock_error_msg)
            
            logger.info(f"📊 Fallback price update attempt {attempt} completed: ✅ {success_count}/{len(stocks)} successful, ❌ {len(stocks) - success_count} failed")
            return success_count
    
    async def stop_price_polling(self):
        """Stop the price polling service"""
        logger.info("Stopping price poller service...")
        self.is_running = False
    
    async def run_manual_price_update(self):
        """Manually trigger price update (for testing/admin use)"""
        logger.info("🚀 Manual price update triggered")
        await self._run_price_update_cycle()
