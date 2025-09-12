"""
Database Queries Configuration
Centralized location for all SQL queries used across the application.
This makes it easy to view, tune, and maintain all database queries.
"""

from typing import Dict, Any

class DatabaseQueries:
    """Centralized database queries configuration"""
    
    # =============================================================================
    # STOCK METADATA QUERIES
    # =============================================================================
    
    @staticmethod
    def get_stock_metadata() -> str:
        """Get all stock metadata"""
        return """
        SELECT stock, company_name, sector, industry, market_cap, market_cap_rank, last_price_date
        FROM stockmetadata 
        ORDER BY market_cap_rank
        """
    
    @staticmethod
    def get_top_stocks_by_market_cap(limit: int, industry: str = None, sector: str = None) -> tuple:
        """Get top N stocks by market cap rank with optional filters"""
        query = """
        SELECT * FROM stockmetadata 
        WHERE market_cap_rank <= %s
        """
        params = [limit]
        
        if industry:
            query += " AND industry = %s"
            params.append(industry)
        if sector:
            query += " AND sector = %s"
            params.append(sector)
        
        query += " ORDER BY market_cap_rank"
        return query, tuple(params)
    
    @staticmethod
    def get_stocks_by_industry() -> str:
        """Get unique industries"""
        return """
        SELECT DISTINCT industry 
        FROM stockmetadata 
        WHERE industry IS NOT NULL AND industry != 'Unknown'
        ORDER BY industry
        """
    
    @staticmethod
    def get_stocks_by_sector() -> str:
        """Get unique sectors"""
        return """
        SELECT DISTINCT sector 
        FROM stockmetadata 
        WHERE sector IS NOT NULL AND sector != 'Unknown'
        ORDER BY sector
        """
    
    @staticmethod
    def update_stock_last_price_date() -> str:
        """Update last_price_date for a stock"""
        return """
        UPDATE stockmetadata 
        SET last_price_date = %s 
        WHERE stock = %s
        """
    
    # =============================================================================
    # STOCK PRICE QUERIES
    # =============================================================================
    
    @staticmethod
    def get_stock_prices_by_symbol() -> str:
        """Get price data for specific stocks"""
        return """
        SELECT stock, date, open, high, low, close, volume
        FROM tickerPrice 
        WHERE stock = ANY(%s)
        ORDER BY stock, date
        """
    
    @staticmethod
    def get_stock_prices_by_symbol_and_date_range() -> str:
        """Get price data for specific stocks within date range"""
        return """
        SELECT stock, date, open, high, low, close, volume
        FROM tickerPrice 
        WHERE stock = ANY(%s) 
        AND date >= %s 
        AND date <= %s
        ORDER BY stock, date
        """
    
    @staticmethod
    def insert_stock_price() -> str:
        """Insert new stock price record"""
        return """
        INSERT INTO tickerPrice (stock, date, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (stock, date) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
        """
    
    @staticmethod
    def get_latest_stock_price() -> str:
        """Get latest price for a stock"""
        return """
        SELECT stock, date, open, high, low, close, volume
        FROM tickerPrice 
        WHERE stock = %s
        ORDER BY date DESC
        LIMIT 1
        """
    
    # =============================================================================
    # MOMENTUM SCORES QUERIES
    # =============================================================================
    
    @staticmethod
    def create_momentum_scores_table() -> str:
        """Create momentum_scores table if it doesn't exist"""
        return """
        CREATE TABLE IF NOT EXISTS momentum_scores (
            id SERIAL PRIMARY KEY,
            stock VARCHAR(50) NOT NULL REFERENCES stockmetadata(stock),
            calculation_date DATE NOT NULL,
            momentum_score NUMERIC(10, 6),
            fip_quality NUMERIC(10, 6),
            raw_momentum_12_2 NUMERIC(10, 6),
            true_momentum_6m NUMERIC(10, 6),
            true_momentum_3m NUMERIC(10, 6),
            true_momentum_1m NUMERIC(10, 6),
            raw_return_6m NUMERIC(10, 6),
            raw_return_3m NUMERIC(10, 6),
            raw_return_1m NUMERIC(10, 6),
            UNIQUE (stock, calculation_date)
        );
        CREATE INDEX IF NOT EXISTS idx_momentumscores_stock_date ON momentum_scores (stock, calculation_date);
        CREATE INDEX IF NOT EXISTS idx_momentumscores_date ON momentum_scores (calculation_date);
        """
    
    @staticmethod
    def get_momentum_scores_for_date() -> str:
        """Get momentum scores for a specific date with stock metadata"""
        return """
        SELECT ms.*, sm.company_name, sm.sector, sm.industry, sm.last_price_date
        FROM momentum_scores ms
        JOIN stockmetadata sm ON ms.stock = sm.stock
        WHERE ms.calculation_date = %s
        ORDER BY ms.momentum_score DESC
        """
    
    @staticmethod
    def get_momentum_scores_for_date_with_limit() -> str:
        """Get momentum scores for a specific date with limit"""
        return """
        SELECT ms.*, sm.company_name, sm.sector, sm.industry, sm.last_price_date
        FROM momentum_scores ms
        JOIN stockmetadata sm ON ms.stock = sm.stock
        WHERE ms.calculation_date = %s
        ORDER BY ms.momentum_score DESC
        LIMIT %s
        """
    
    @staticmethod
    def get_stocks_needing_momentum_calculation() -> str:
        """Get stocks that don't have momentum scores for today, ordered by market cap"""
        return """
        SELECT sm.stock
        FROM stockmetadata sm
        LEFT JOIN momentum_scores ms ON sm.stock = ms.stock AND ms.calculation_date = CURRENT_DATE::date
        WHERE ms.stock IS NULL
        ORDER BY sm.market_cap_rank
        """
    
    @staticmethod
    def get_stocks_needing_momentum_calculation_with_limit() -> str:
        """Get stocks that don't have momentum scores for today, with limit"""
        return """
        SELECT sm.stock
        FROM stockmetadata sm
        LEFT JOIN momentum_scores ms ON sm.stock = ms.stock AND ms.calculation_date = CURRENT_DATE::date
        WHERE ms.stock IS NULL
        ORDER BY sm.market_cap_rank
        LIMIT %s
        """
    
    @staticmethod
    def insert_momentum_scores() -> str:
        """Insert momentum scores with conflict resolution"""
        return """
        INSERT INTO momentum_scores (
            stock, calculation_date, momentum_score, fip_quality,
            raw_momentum_12_2, true_momentum_6m, true_momentum_3m,
            true_momentum_1m, raw_return_6m, raw_return_3m, raw_return_1m
        ) VALUES (
            %(stock)s, %(calculation_date)s, %(momentum_score)s, %(fip_quality)s,
            %(raw_momentum_12_2)s, %(true_momentum_6m)s, %(true_momentum_3m)s,
            %(true_momentum_1m)s, %(raw_return_6m)s, %(raw_return_3m)s, %(raw_return_1m)s
        )
        ON CONFLICT (stock, calculation_date) DO UPDATE SET
            momentum_score = EXCLUDED.momentum_score,
            fip_quality = EXCLUDED.fip_quality,
            raw_momentum_12_2 = EXCLUDED.raw_momentum_12_2,
            true_momentum_6m = EXCLUDED.true_momentum_6m,
            true_momentum_3m = EXCLUDED.true_momentum_3m,
            true_momentum_1m = EXCLUDED.true_momentum_1m,
            raw_return_6m = EXCLUDED.raw_return_6m,
            raw_return_3m = EXCLUDED.raw_return_3m,
            raw_return_1m = EXCLUDED.raw_return_1m
        """
    
    @staticmethod
    def get_momentum_scores_count() -> str:
        """Get count of momentum scores for a date"""
        return """
        SELECT COUNT(*) FROM momentum_scores WHERE calculation_date = %s
        """
    
    @staticmethod
    def get_momentum_scores_for_stocks(symbols: list) -> tuple:
        """Get momentum scores for specific stocks (latest calculation)"""
        placeholders = ','.join(['%s'] * len(symbols))
        query = f"""
        SELECT 
            ms.stock,
            ms.momentum_score,
            ms.fip_quality,
            ms.raw_momentum_12_2,
            ms.true_momentum_6m,
            ms.true_momentum_3m,
            ms.true_momentum_1m,
            ms.raw_return_6m,
            ms.raw_return_3m,
            ms.raw_return_1m,
            ms.raw_momentum_6m,
            ms.raw_momentum_3m,
            ms.raw_momentum_1m,
            sm.company_name,
            sm.current_price,
            sm.last_price_date
        FROM momentum_scores ms
        JOIN stockmetadata sm ON ms.stock = sm.stock
        WHERE ms.stock IN ({placeholders})
        AND ms.calculation_date = (
            SELECT MAX(calculation_date) 
            FROM momentum_scores ms2 
            WHERE ms2.stock = ms.stock
        )
        ORDER BY ms.momentum_score DESC
        """
        return query, tuple(symbols)
    
    # =============================================================================
    # STOCK UPDATE TRACKER QUERIES
    # =============================================================================
    
    @staticmethod
    def create_stock_update_tracker_table() -> str:
        """Create stock_update_status table if it doesn't exist"""
        return """
        CREATE TABLE IF NOT EXISTS stock_update_status (
            id SERIAL PRIMARY KEY,
            stock VARCHAR(50) NOT NULL REFERENCES stockmetadata(stock),
            last_updated DATE NOT NULL,
            update_status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (stock)
        );
        CREATE INDEX IF NOT EXISTS idx_stockupdatestatus_stock ON stock_update_status (stock);
        CREATE INDEX IF NOT EXISTS idx_stockupdatestatus_date ON stock_update_status (last_updated);
        """
    
    @staticmethod
    def get_stocks_needing_update() -> str:
        """Get stocks that need price data update"""
        return """
        SELECT DISTINCT sm.stock, sm.market_cap
        FROM stockmetadata sm
        LEFT JOIN stock_update_status sut ON sm.stock = sut.stock
        WHERE sut.stock IS NULL 
        OR sut.last_updated < CURRENT_DATE::date
        OR sut.update_status = 'failed'
        ORDER BY sm.market_cap DESC
        """
    
    @staticmethod
    def get_stocks_needing_update_with_limit() -> str:
        """Get stocks that need price data update with limit"""
        return """
        SELECT DISTINCT sm.stock, sm.market_cap
        FROM stockmetadata sm
        LEFT JOIN stock_update_status sut ON sm.stock = sut.stock
        WHERE sut.stock IS NULL 
        OR sut.last_updated < CURRENT_DATE::date
        OR sut.update_status = 'failed'
        ORDER BY sm.market_cap DESC
        LIMIT %s
        """
    
    @staticmethod
    def get_update_status() -> str:
        """Get update status for a stock"""
        return """
        SELECT stock, last_updated, update_status
        FROM stock_update_status
        WHERE stock = :stock
        """
    
    @staticmethod
    def mark_update_started() -> str:
        """Mark update as started for a stock"""
        return """
        INSERT INTO stock_update_status (stock, last_updated, update_status)
        VALUES (:stock, CURRENT_DATE::date, 'in_progress')
        ON CONFLICT (stock) DO UPDATE SET
            last_updated = CURRENT_DATE::date,
            update_status = 'in_progress',
            updated_at = CURRENT_TIMESTAMP
        """
    
    @staticmethod
    def mark_update_completed() -> str:
        """Mark update as completed for a stock"""
        return """
        UPDATE stock_update_status 
        SET update_status = 'completed', updated_at = CURRENT_TIMESTAMP
        WHERE stock = :stock
        """
    
    @staticmethod
    def mark_update_failed() -> str:
        """Mark update as failed for a stock"""
        return """
        UPDATE stock_update_status 
        SET update_status = 'failed', updated_at = CURRENT_TIMESTAMP
        WHERE stock = :stock
        """
    
    @staticmethod
    def get_overall_update_statistics() -> str:
        """Get overall update statistics"""
        return """
        SELECT 
            COUNT(*) as total_stocks,
            COUNT(sut.stock) as tracked_stocks,
            COUNT(CASE WHEN sut.last_updated = CURRENT_DATE::date THEN 1 END) as updated_today,
            COUNT(CASE WHEN sut.update_status = 'completed' THEN 1 END) as completed_updates,
            COUNT(CASE WHEN sut.update_status = 'failed' THEN 1 END) as failed_updates
        FROM stockmetadata sm
        LEFT JOIN stock_update_status sut ON sm.stock = sut.stock
        """
    
    # =============================================================================
    # DATABASE INDEXES QUERIES
    # =============================================================================
    
    @staticmethod
    def create_all_indexes() -> list:
        """Create all database indexes for optimal performance"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_stockmetadata_market_cap_rank ON stockmetadata (market_cap_rank);",
            "CREATE INDEX IF NOT EXISTS idx_stockmetadata_sector ON stockmetadata (sector);",
            "CREATE INDEX IF NOT EXISTS idx_stockmetadata_industry ON stockmetadata (industry);",
            "CREATE INDEX IF NOT EXISTS idx_tickerprice_stock_date ON tickerPrice (stock, date);",
            "CREATE INDEX IF NOT EXISTS idx_tickerprice_stock ON tickerPrice (stock);",
            "CREATE INDEX IF NOT EXISTS idx_tickerprice_date ON tickerPrice (date);",
            "CREATE INDEX IF NOT EXISTS idx_momentumscores_stock_date ON momentum_scores (stock, calculation_date);",
            "CREATE INDEX IF NOT EXISTS idx_momentumscores_date ON momentum_scores (calculation_date);",
            "CREATE INDEX IF NOT EXISTS idx_momentumscores_momentum_score ON momentum_scores (momentum_score DESC);",
            "CREATE INDEX IF NOT EXISTS idx_stockupdatestatus_stock ON stock_update_status (stock);",
            "CREATE INDEX IF NOT EXISTS idx_stockupdatestatus_date ON stock_update_status (last_updated);",
            "CREATE INDEX IF NOT EXISTS idx_stockupdatestatus_status ON stock_update_status (update_status);"
        ]
    
    # =============================================================================
    # UTILITY QUERIES
    # =============================================================================
    
    @staticmethod
    def get_database_info() -> str:
        """Get database information and statistics"""
        return """
        SELECT 
            'stockmetadata' as table_name, COUNT(*) as row_count
        FROM stockmetadata
        UNION ALL
        SELECT 
            'tickerPrice' as table_name, COUNT(*) as row_count
        FROM tickerPrice
        UNION ALL
        SELECT 
            'momentum_scores' as table_name, COUNT(*) as row_count
        FROM momentum_scores
        UNION ALL
        SELECT 
            'stock_update_status' as table_name, COUNT(*) as row_count
        FROM stock_update_status
        """
    
    @staticmethod
    def get_table_sizes() -> str:
        """Get table sizes in MB"""
        return """
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """

