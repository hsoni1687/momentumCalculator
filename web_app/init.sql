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
    dividend_yield NUMERIC(5, 2),
    roce NUMERIC(5, 2),
    roe NUMERIC(5, 2),
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
