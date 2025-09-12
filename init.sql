-- Initialize the momentum calculator database
-- This script runs when the PostgreSQL container starts

-- Create stockMetadata table
CREATE TABLE IF NOT EXISTS stockmetadata (
    stock VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255),
    market_cap BIGINT,
    sector VARCHAR(100),
    industry VARCHAR(100),
    exchange VARCHAR(10),
    
    -- Basic Financial Attributes
    dividend_yield NUMERIC(5, 2),
    roce NUMERIC(5, 2),
    roe NUMERIC(5, 2),
    
    -- Financial Ratios
    pe_ratio NUMERIC(10, 2),
    forward_pe NUMERIC(10, 2),
    pb_ratio NUMERIC(10, 2),
    ps_ratio NUMERIC(10, 2),
    peg_ratio NUMERIC(10, 2),
    beta NUMERIC(10, 2),
    ev_to_revenue NUMERIC(10, 2),
    ev_to_ebitda NUMERIC(10, 2),
    
    -- Profitability Metrics
    gross_margin NUMERIC(5, 2),
    operating_margin NUMERIC(5, 2),
    profit_margin NUMERIC(5, 2),
    ebitda_margin NUMERIC(5, 2),
    roa NUMERIC(5, 2),
    
    -- Growth Metrics
    revenue_growth NUMERIC(5, 2),
    earnings_growth NUMERIC(5, 2),
    quarterly_earnings_growth NUMERIC(5, 2),
    
    -- Dividend Information
    dividend_rate NUMERIC(10, 2),
    payout_ratio NUMERIC(5, 2),
    ex_dividend_date DATE,
    dividend_date DATE,
    
    -- Balance Sheet Data
    total_cash BIGINT,
    total_debt BIGINT,
    debt_to_equity NUMERIC(10, 2),
    current_ratio NUMERIC(10, 2),
    quick_ratio NUMERIC(10, 2),
    total_revenue BIGINT,
    cash_per_share NUMERIC(10, 2),
    
    -- Valuation Metrics
    enterprise_value BIGINT,
    book_value NUMERIC(10, 2),
    price_to_book NUMERIC(10, 2),
    
    -- Market Data
    current_price NUMERIC(10, 2),
    previous_close NUMERIC(10, 2),
    day_low NUMERIC(10, 2),
    day_high NUMERIC(10, 2),
    fifty_two_week_low NUMERIC(10, 2),
    fifty_two_week_high NUMERIC(10, 2),
    volume BIGINT,
    average_volume BIGINT,
    shares_outstanding BIGINT,
    
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Create tickerPrice table
CREATE TABLE IF NOT EXISTS tickerprice (
    id SERIAL PRIMARY KEY,
    stock VARCHAR(50),
    date DATE,
    open NUMERIC(10, 2),
    high NUMERIC(10, 2),
    low NUMERIC(10, 2),
    close NUMERIC(10, 2),
    volume BIGINT,
    last_updated TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (stock) REFERENCES stockmetadata(stock)
);

-- Create momentumScores table
CREATE TABLE IF NOT EXISTS momentumscores (
    stock VARCHAR(50) PRIMARY KEY,
    total_score NUMERIC(10, 4),
    momentum_12_2 NUMERIC(10, 4),
    fip_quality NUMERIC(10, 4),
    raw_momentum_6m NUMERIC(10, 4),
    raw_momentum_3m NUMERIC(10, 4),
    raw_momentum_1m NUMERIC(10, 4),
    volatility_adjusted NUMERIC(10, 4),
    smooth_momentum NUMERIC(10, 4),
    consistency_score NUMERIC(10, 4),
    trend_strength NUMERIC(10, 4),
    calculated_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (stock) REFERENCES stockmetadata(stock)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_stockmetadata_industry ON stockmetadata(industry);
CREATE INDEX IF NOT EXISTS idx_stockmetadata_sector ON stockmetadata(sector);
CREATE INDEX IF NOT EXISTS idx_tickerprice_stock ON tickerprice(stock);
CREATE INDEX IF NOT EXISTS idx_tickerprice_date ON tickerprice(date);
CREATE INDEX IF NOT EXISTS idx_tickerprice_stock_date ON tickerprice(stock, date);
CREATE INDEX IF NOT EXISTS idx_momentumscores_calculated_date ON momentumscores(calculated_date);

-- Load data from CSV files if they exist
\copy stockmetadata(stock, company_name, market_cap, sector, industry, exchange, dividend_yield, roce, roe, last_updated) FROM '/docker-entrypoint-initdb.d/data/clean_stock_metadata.csv' WITH CSV HEADER;

\copy tickerprice(stock, date, open, high, low, close, volume) FROM '/docker-entrypoint-initdb.d/data/clean_ticker_price.csv' WITH CSV HEADER;

\copy momentumscores(stock, total_score, momentum_12_2, fip_quality, raw_momentum_6m, raw_momentum_3m, raw_momentum_1m, volatility_adjusted, smooth_momentum, consistency_score, trend_strength, calculated_date, created_at) FROM '/docker-entrypoint-initdb.d/data/clean_momentum_scores.csv' WITH CSV HEADER;

-- Update last_updated timestamps
UPDATE stockmetadata SET last_updated = NOW() WHERE last_updated IS NULL;
UPDATE tickerprice SET last_updated = NOW() WHERE last_updated IS NULL;
UPDATE momentumscores SET created_at = NOW() WHERE created_at IS NULL;
