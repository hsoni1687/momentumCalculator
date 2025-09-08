#!/usr/bin/env python3
"""
Startup Upserts Script
Runs upsert operations when the app starts to ensure data consistency
"""

import sys
import os
import logging
from typing import Dict, Any

# Add paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config'))

from upsert_stock_metadata import StockMetadataUpserter
from upsert_ticker_price import TickerPriceUpserter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StartupUpserter:
    def __init__(self, db_path: str = 'data/stock_data.db'):
        self.db_path = db_path
        self.metadata_upserter = StockMetadataUpserter(db_path)
        self.price_upserter = TickerPriceUpserter(db_path)
    
    def run_startup_upserts(self, force_metadata_update: bool = False) -> Dict[str, Any]:
        """
        Run all startup upsert operations
        """
        logger.info("🚀 Starting startup upsert operations...")
        
        results = {
            'metadata_upsert': None,
            'price_data_stats': None,
            'overall_success': False,
            'errors': []
        }
        
        try:
            # 1. Upsert stock metadata
            logger.info("📋 Step 1: Upserting stock metadata...")
            metadata_result = self.metadata_upserter.upsert_all_stocks_from_lists()
            results['metadata_upsert'] = metadata_result
            
            if metadata_result['success'] > 0:
                logger.info(f"✅ Metadata upsert completed: {metadata_result['success']} stocks processed")
            else:
                logger.warning("⚠️ No stocks were processed in metadata upsert")
            
            # 2. Get price data statistics
            logger.info("📊 Step 2: Checking price data statistics...")
            price_stats = self.price_upserter.get_price_data_stats()
            results['price_data_stats'] = price_stats
            
            if price_stats:
                logger.info(f"✅ Price data stats: {price_stats['total_records']} records for {price_stats['unique_stocks']} stocks")
            else:
                logger.warning("⚠️ No price data statistics available")
            
            # 3. Get overall metadata stats
            metadata_stats = self.metadata_upserter.get_metadata_stats()
            results['metadata_stats'] = metadata_stats
            
            results['overall_success'] = True
            logger.info("🎉 Startup upsert operations completed successfully")
            
        except Exception as e:
            error_msg = f"Error during startup upserts: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['overall_success'] = False
        
        return results
    
    def get_startup_summary(self) -> str:
        """
        Get a summary of the current database state
        """
        try:
            metadata_stats = self.metadata_upserter.get_metadata_stats()
            price_stats = self.price_upserter.get_price_data_stats()
            
            summary = "📊 Database Summary:\n"
            summary += "=" * 50 + "\n"
            
            if metadata_stats:
                summary += f"📋 Stock Metadata:\n"
                summary += f"   Total Stocks: {metadata_stats['total_stocks']:,}\n"
                summary += f"   Exchanges: {metadata_stats['exchange_counts']}\n"
                summary += f"   Top Sectors: {list(metadata_stats['top_sectors'].keys())[:5]}\n"
            
            if price_stats:
                summary += f"\n📈 Price Data:\n"
                summary += f"   Total Records: {price_stats['total_records']:,}\n"
                summary += f"   Stocks with Data: {price_stats['unique_stocks']}\n"
                summary += f"   Date Range: {price_stats['date_range'][0]} to {price_stats['date_range'][1]}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting startup summary: {e}")
            return f"❌ Error getting database summary: {e}"
    
    def check_data_consistency(self) -> Dict[str, Any]:
        """
        Check data consistency between metadata and price data
        """
        try:
            metadata_stats = self.metadata_upserter.get_metadata_stats()
            price_stats = self.price_upserter.get_price_data_stats()
            
            consistency_report = {
                'metadata_stocks': metadata_stats.get('total_stocks', 0),
                'price_data_stocks': price_stats.get('unique_stocks', 0),
                'price_records': price_stats.get('total_records', 0),
                'consistency_issues': [],
                'recommendations': []
            }
            
            # Check for consistency issues
            if consistency_report['metadata_stocks'] > consistency_report['price_data_stocks']:
                missing_price_data = consistency_report['metadata_stocks'] - consistency_report['price_data_stocks']
                consistency_report['consistency_issues'].append(
                    f"{missing_price_data} stocks have metadata but no price data"
                )
                consistency_report['recommendations'].append(
                    "Consider running price data fetch for missing stocks"
                )
            
            if consistency_report['price_data_stocks'] > consistency_report['metadata_stocks']:
                extra_price_data = consistency_report['price_data_stocks'] - consistency_report['metadata_stocks']
                consistency_report['consistency_issues'].append(
                    f"{extra_price_data} stocks have price data but no metadata"
                )
                consistency_report['recommendations'].append(
                    "Consider cleaning up orphaned price data"
                )
            
            if consistency_report['price_records'] == 0:
                consistency_report['consistency_issues'].append(
                    "No price data available in database"
                )
                consistency_report['recommendations'].append(
                    "Run price data fetch to populate the database"
                )
            
            return consistency_report
            
        except Exception as e:
            logger.error(f"Error checking data consistency: {e}")
            return {'error': str(e)}

def run_startup_upserts(db_path: str = 'data/stock_data.db') -> Dict[str, Any]:
    """
    Convenience function to run startup upserts
    """
    upserter = StartupUpserter(db_path)
    return upserter.run_startup_upserts()

def get_database_summary(db_path: str = 'data/stock_data.db') -> str:
    """
    Convenience function to get database summary
    """
    upserter = StartupUpserter(db_path)
    return upserter.get_startup_summary()

def main():
    """Main function for testing"""
    print("🚀 Startup Upserter Test")
    print("=" * 50)
    
    upserter = StartupUpserter()
    
    # Run startup upserts
    results = upserter.run_startup_upserts()
    
    print(f"\n📊 Results:")
    print(f"   Overall Success: {'✅' if results['overall_success'] else '❌'}")
    
    if results['metadata_upsert']:
        print(f"   Metadata Upsert: {results['metadata_upsert']['success']} success, {results['metadata_upsert']['failed']} failed")
    
    if results['price_data_stats']:
        print(f"   Price Data: {results['price_data_stats']['total_records']} records")
    
    if results['errors']:
        print(f"   Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"     - {error}")
    
    # Show summary
    print(f"\n{upserter.get_startup_summary()}")
    
    # Check consistency
    consistency = upserter.check_data_consistency()
    if consistency.get('consistency_issues'):
        print(f"\n⚠️ Consistency Issues:")
        for issue in consistency['consistency_issues']:
            print(f"   - {issue}")
    
    if consistency.get('recommendations'):
        print(f"\n💡 Recommendations:")
        for rec in consistency['recommendations']:
            print(f"   - {rec}")

if __name__ == "__main__":
    main()
