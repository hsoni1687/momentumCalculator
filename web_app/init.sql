-- PostgreSQL initialization script for Momentum Calculator
-- This script creates the necessary tables for the application

-- Create stockMetadata table
CREATE TABLE IF NOT EXISTS stockMetadata (
    stock VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255),
    market_cap BIGINT,
    sector VARCHAR(100),
    industry VARCHAR(100),
    exchange VARCHAR(10),
    dividend_yield DECIMAL(5,2),
    roce DECIMAL(5,2),
    roe DECIMAL(5,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tickerPrice table
CREATE TABLE IF NOT EXISTS tickerPrice (
    id SERIAL PRIMARY KEY,
    stock VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock, date)
);

-- Create momentumScores table
CREATE TABLE IF NOT EXISTS momentumScores (
    stock VARCHAR(50) PRIMARY KEY,
    total_score DECIMAL(10,4),
    raw_momentum_6m DECIMAL(10,4),
    raw_momentum_3m DECIMAL(10,4),
    raw_momentum_1m DECIMAL(10,4),
    volatility_adjusted_6m DECIMAL(10,4),
    volatility_adjusted_3m DECIMAL(10,4),
    volatility_adjusted_1m DECIMAL(10,4),
    relative_strength_6m DECIMAL(10,4),
    relative_strength_3m DECIMAL(10,4),
    relative_strength_1m DECIMAL(10,4),
    trend_score DECIMAL(10,4),
    volume_score DECIMAL(10,4),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock) REFERENCES stockMetadata(stock)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tickerprice_stock_date ON tickerPrice(stock, date);
CREATE INDEX IF NOT EXISTS idx_tickerprice_date ON tickerPrice(date);
CREATE INDEX IF NOT EXISTS idx_stockmetadata_industry ON stockMetadata(industry);
CREATE INDEX IF NOT EXISTS idx_stockmetadata_sector ON stockMetadata(sector);
CREATE INDEX IF NOT EXISTS idx_momentumscores_total_score ON momentumScores(total_score DESC);

-- Create a function to update last_updated timestamp
CREATE OR REPLACE FUNCTION update_last_updated_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update last_updated
CREATE TRIGGER update_stockmetadata_last_updated 
    BEFORE UPDATE ON stockMetadata 
    FOR EACH ROW 
    EXECUTE FUNCTION update_last_updated_column();

-- Load data from CSV files
\copy stockMetadata(stock, company_name, market_cap, sector, industry, exchange, dividend_yield, roce, roe, last_updated) FROM '/docker-entrypoint-initdb.d/stock_metadata.csv' WITH CSV HEADER;

\copy tickerPrice(stock, date, open, high, low, close, volume) FROM '/docker-entrypoint-initdb.d/ticker_price.csv' WITH CSV HEADER;

\copy momentumScores(stock, total_score, raw_momentum_6m, raw_momentum_3m, raw_momentum_1m, volatility_adjusted_6m, volatility_adjusted_3m, volatility_adjusted_1m, relative_strength_6m, relative_strength_3m, relative_strength_1m, trend_score, volume_score, calculated_at) FROM '/docker-entrypoint-initdb.d/momentum_scores.csv' WITH CSV HEADER;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO momentum_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO momentum_user;
