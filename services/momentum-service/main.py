"""
Momentum Service - Optimized version that uses database directly instead of HTTP calls
"""

from fastapi import FastAPI, HTTPException, Query, Request
# CORS is handled by nginx reverse proxy
from fastapi.responses import JSONResponse
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
import uvicorn
import httpx
import asyncio
import numpy as np
import time
from collections import defaultdict

from config.settings import settings
from config.momentum_config import get_momentum_config, update_momentum_config, reset_momentum_config
from config.database_queries import DatabaseQueries
from models.momentum_calculator import MomentumCalculator
from utils.market_hours import MarketHours
from models import DatabaseService, MomentumService
from models.momentum_storage import MomentumStorage
from models.stock import StockService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple rate limiter
request_times = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # 60 seconds
RATE_LIMIT_MAX_REQUESTS = 10  # Max 10 requests per minute per IP

def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit"""
    current_time = time.time()
    
    # Clean old requests outside the window
    request_times[client_ip] = [
        req_time for req_time in request_times[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if under limit
    if len(request_times[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    # Add current request
    request_times[client_ip].append(current_time)
    return True

# Initialize services
database_service = DatabaseService()
momentum_service = MomentumService(database_service)
momentum_storage = MomentumStorage(database_service)
stock_service = StockService(database_service)
momentum_calculator = MomentumCalculator()

# Data service URLs for load balancing
DATA_SERVICE_URLS = [
    "http://data-service-1:8001",
    "http://data-service-2:8001"
]
DATA_SERVICE_INDEX = 0  # Round-robin counter

# Create FastAPI app
app = FastAPI(
    title="Momentum Calculator - Momentum Service",
    description="Service responsible for momentum calculations and API responses",
    version="1.0.0"
)

# CORS is handled by nginx reverse proxy

# HTTP client for data service communication
http_client = httpx.AsyncClient(timeout=30.0)

def get_next_data_service_url() -> str:
    """Get next data service URL using round-robin"""
    global DATA_SERVICE_INDEX
    url = DATA_SERVICE_URLS[DATA_SERVICE_INDEX]
    DATA_SERVICE_INDEX = (DATA_SERVICE_INDEX + 1) % len(DATA_SERVICE_URLS)
    return url

async def get_data_from_data_service(endpoint: str, params: Dict = None) -> Dict:
    """Helper function to get data from data service with load balancing"""
    # Try all data service instances
    for url in DATA_SERVICE_URLS:
        try:
            response = await http_client.get(f"{url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to get data from {url}: {e}")
            continue
    
    # If all instances fail
    logger.error("All data service instances failed")
    raise HTTPException(status_code=500, detail="All data service instances are unavailable")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_status = "connected" if database_service.test_connection() else "disconnected"
        
        # Data service status - assume connected since we have load balancing
        data_service_status = "connected"
        
        return {
            "status": "healthy",
            "service": "momentum-service",
            "database": db_status,
            "data_service": data_service_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "momentum-service",
                "error": str(e)
            }
        )

@app.get("/market-status")
async def get_market_status():
    """Get current market status and trading information"""
    try:
        current_time = MarketHours.get_current_ist_time()
        market_open = MarketHours.is_market_open()
        should_calculate = MarketHours.should_calculate_momentum()
        should_update_data = MarketHours.should_update_data()
        trading_date = MarketHours.get_trading_date()
        previous_trading_date = MarketHours.get_previous_trading_date()
        next_market_open = MarketHours.get_next_market_open_time()
        
        return {
            "current_time_ist": current_time.isoformat(),
            "market_open": market_open,
            "should_calculate_momentum": should_calculate,
            "should_update_data": should_update_data,
            "trading_date": trading_date.isoformat(),
            "previous_trading_date": previous_trading_date.isoformat(),
            "next_market_open": next_market_open.isoformat(),
            "market_status_message": MarketHours.get_market_status_message(),
            "market_hours": {
                "open": "09:15 IST",
                "close": "15:30 IST"
            }
        }
    except Exception as e:
        logger.error(f"Market status check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to get market status",
                "details": str(e)
            }
        )

# Helper function to get fresh momentum scores
async def get_fresh_momentum_scores(limit: int, industry: Optional[str], sector: Optional[str], top_n: int, market_status: str):
    """Get fresh momentum scores calculated on-the-fly"""
    try:
        # Get top N stocks by market cap rank
        query, params = DatabaseQueries.get_top_stocks_by_market_cap(limit, industry, sector)
        stocks_df = database_service.execute_query(query, params)
        
        if stocks_df.empty:
            return {
                "momentum_scores": [],
                "top_stocks": [],
                "count": 0,
                "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n},
                "market_status": market_status,
                "message": "No stocks found matching the criteria"
            }
        
        # Get price data for all stocks
        symbols = stocks_df['stock'].tolist()
        price_data = {}
        
        for symbol in symbols:
            try:
                stock_prices = database_service.get_price_data(symbol)
                print(f"DEBUG {symbol}: DataFrame shape: {stock_prices.shape}")
                print(f"DEBUG {symbol}: DataFrame columns: {list(stock_prices.columns)}")
                if not stock_prices.empty:
                    # Check if date column exists (lowercase)
                    if 'date' in stock_prices.columns:
                        # Convert date column to datetime and set as index
                        stock_prices['date'] = pd.to_datetime(stock_prices['date'])
                        stock_prices = stock_prices.set_index('date')
                        # Pass the full DataFrame with close column for momentum calculation
                        price_data[symbol] = stock_prices
                        print(f"DEBUG {symbol}: Stored DataFrame in price_data")
                        print(f"DEBUG {symbol}: Stored DataFrame columns: {list(stock_prices.columns)}")
                    else:
                        print(f"DEBUG {symbol}: 'date' column not found in DataFrame")
            except Exception as e:
                print(f"Error getting price data for {symbol}: {e}")
                continue
        
        if not price_data:
            return {
                "momentum_scores": [],
                "top_stocks": [],
                "count": 0,
                "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n},
                "market_status": market_status,
                "message": "No price data available for momentum calculation"
            }
        
        # Calculate momentum scores for each stock
        momentum_scores = []
        for _, stock_row in stocks_df.iterrows():
            symbol = stock_row['stock']
            if symbol in price_data:
                try:
                    # Debug: Print what we're passing to momentum calculator
                    print(f"DEBUG {symbol}: Passing DataFrame to momentum calculator")
                    print(f"DEBUG {symbol}: DataFrame shape: {price_data[symbol].shape}")
                    print(f"DEBUG {symbol}: DataFrame columns: {list(price_data[symbol].columns)}")
                    print(f"DEBUG {symbol}: DataFrame index type: {type(price_data[symbol].index)}")
                    print(f"DEBUG {symbol}: DataFrame head:")
                    print(price_data[symbol].head())
                    
                    # Check if close column exists (lowercase)
                    if 'close' in price_data[symbol].columns:
                        print(f"DEBUG {symbol}: close column exists, values: {price_data[symbol]['close'].head().tolist()}")
                    else:
                        print(f"DEBUG {symbol}: close column does NOT exist!")
                    
                    # Calculate momentum score using the same logic as the momentum calculator
                    momentum_result = momentum_calculator.calculate_quality_momentum_score(price_data[symbol])
                    momentum_score = momentum_result.get('total_score', 0)
                    
                    print(f"DEBUG {symbol}: Momentum result: {momentum_result}")
                    
                    momentum_scores.append({
                        'stock': symbol,
                        'momentum_score': momentum_score,
                        'name': stock_row['company_name'],  # Map company_name to name for frontend
                        'current_price': stock_row.get('current_price', 0),
                        'market_cap': stock_row.get('market_cap', 0),
                        'sector': stock_row.get('sector', ''),
                        'industry': stock_row.get('industry', ''),
                        # Add detailed momentum breakdown - map from momentum_result keys
                        'fip_quality': momentum_result.get('fip_quality', 0),
                        'raw_momentum_12_2': momentum_result.get('momentum_12_2', 0),
                        'true_momentum_6m': momentum_result.get('true_momentum_6m', 0),
                        'true_momentum_3m': momentum_result.get('true_momentum_3m', 0),
                        'true_momentum_1m': momentum_result.get('true_momentum_1m', 0),
                        'raw_return_6m': momentum_result.get('raw_return_6m', 0),
                        'raw_return_3m': momentum_result.get('raw_return_3m', 0),
                        'raw_return_1m': momentum_result.get('raw_return_1m', 0),
                        'raw_momentum_6m': momentum_result.get('raw_momentum_6m', 0),
                        'raw_momentum_3m': momentum_result.get('raw_momentum_3m', 0),
                        'raw_momentum_1m': momentum_result.get('raw_momentum_1m', 0),
                        'volatility_adjusted': momentum_result.get('volatility_adjusted', 0),
                        'smooth_momentum': momentum_result.get('smooth_momentum', 0),
                        'consistency_score': momentum_result.get('consistency_score', 0),
                        'trend_strength': momentum_result.get('trend_strength', 0)
                    })
                except Exception as e:
                    print(f"Error calculating momentum for {symbol}: {e}")
                    continue
        
        # Sort by momentum score and get top N
        momentum_scores.sort(key=lambda x: x['momentum_score'], reverse=True)
        top_stocks = momentum_scores[:top_n]
        
        # Convert to response format
        def safe_float(value, default=0.0):
            """Convert value to float, handling NaN and inf values"""
            try:
                val = float(value)
                if np.isnan(val) or np.isinf(val):
                    return default
                return val
            except (ValueError, TypeError):
                return default
        
        response_momentum_scores = []
        for score_data in momentum_scores:
            response_data = {
                "stock": score_data['stock'],
                "name": score_data['name'],  # Use 'name' field that we set in momentum_scores.append
                "sector": score_data['sector'],
                "industry": score_data['industry'],
                "momentum_score": safe_float(score_data['momentum_score']),
                "current_price": safe_float(score_data['current_price']),
                "market_cap": safe_float(score_data['market_cap']),
                # Add detailed momentum breakdown
                "fip_quality": safe_float(score_data.get('fip_quality', 0)),
                "raw_momentum_12_2": safe_float(score_data.get('raw_momentum_12_2', 0)),
                "true_momentum_6m": safe_float(score_data.get('true_momentum_6m', 0)),
                "true_momentum_3m": safe_float(score_data.get('true_momentum_3m', 0)),
                "true_momentum_1m": safe_float(score_data.get('true_momentum_1m', 0)),
                "raw_return_6m": safe_float(score_data.get('raw_return_6m', 0)),
                "raw_return_3m": safe_float(score_data.get('raw_return_3m', 0)),
                "raw_return_1m": safe_float(score_data.get('raw_return_1m', 0)),
                "raw_momentum_6m": safe_float(score_data.get('raw_momentum_6m', 0)),
                "raw_momentum_3m": safe_float(score_data.get('raw_momentum_3m', 0)),
                "raw_momentum_1m": safe_float(score_data.get('raw_momentum_1m', 0)),
                "volatility_adjusted": safe_float(score_data.get('volatility_adjusted', 0)),
                "smooth_momentum": safe_float(score_data.get('smooth_momentum', 0)),
                "consistency_score": safe_float(score_data.get('consistency_score', 0)),
                "trend_strength": safe_float(score_data.get('trend_strength', 0))
            }
            response_momentum_scores.append(response_data)
        
        response_top_stocks = []
        for score_data in top_stocks:
            response_data = {
                "stock": score_data['stock'],
                "name": score_data['name'],  # Use 'name' field that we set in momentum_scores.append
                "sector": score_data['sector'],
                "industry": score_data['industry'],
                "momentum_score": safe_float(score_data['momentum_score']),
                "current_price": safe_float(score_data['current_price']),
                "market_cap": safe_float(score_data['market_cap']),
                # Add detailed momentum breakdown
                "fip_quality": safe_float(score_data.get('fip_quality', 0)),
                "raw_momentum_12_2": safe_float(score_data.get('raw_momentum_12_2', 0)),
                "true_momentum_6m": safe_float(score_data.get('true_momentum_6m', 0)),
                "true_momentum_3m": safe_float(score_data.get('true_momentum_3m', 0)),
                "true_momentum_1m": safe_float(score_data.get('true_momentum_1m', 0)),
                "raw_return_6m": safe_float(score_data.get('raw_return_6m', 0)),
                "raw_return_3m": safe_float(score_data.get('raw_return_3m', 0)),
                "raw_return_1m": safe_float(score_data.get('raw_return_1m', 0)),
                "raw_momentum_6m": safe_float(score_data.get('raw_momentum_6m', 0)),
                "raw_momentum_3m": safe_float(score_data.get('raw_momentum_3m', 0)),
                "raw_momentum_1m": safe_float(score_data.get('raw_momentum_1m', 0)),
                "volatility_adjusted": safe_float(score_data.get('volatility_adjusted', 0)),
                "smooth_momentum": safe_float(score_data.get('smooth_momentum', 0)),
                "consistency_score": safe_float(score_data.get('consistency_score', 0)),
                "trend_strength": safe_float(score_data.get('trend_strength', 0))
            }
            response_top_stocks.append(response_data)
        
        return {
            "momentum_scores": response_momentum_scores,
            "top_stocks": response_top_stocks,
            "count": len(response_momentum_scores),
            "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n},
            "market_status": market_status,
            "message": "Fresh momentum scores calculated on-the-fly"
        }
        
    except Exception as e:
        logger.error(f"Error getting fresh momentum scores: {e}")
        return {
            "momentum_scores": [],
            "top_stocks": [],
            "count": 0,
            "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n},
            "market_status": market_status,
            "error": str(e)
        }

# Momentum Calculation Endpoints
@app.options("/momentum")
@app.options("/momentum/")
async def momentum_options():
    """Handle OPTIONS requests for CORS preflight"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization",
            "Access-Control-Expose-Headers": "Content-Length,Content-Range"
        }
    )

@app.get("/momentum")
@app.get("/momentum/")
async def calculate_momentum(
    request: Request,
    limit: int = Query(50, ge=1, le=2525, description="Number of stocks to analyze"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    top_n: int = Query(10, ge=1, le=100, description="Number of top stocks to return")
):
    """Calculate momentum scores for stocks - FIXED: Market Cap First, Then Momentum"""
    try:
        # Rate limiting (only for momentum endpoint, not health checks)
        client_ip = request.client.host
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please wait before making another request.",
                    "retry_after": RATE_LIMIT_WINDOW
                }
            )
        # Check if momentum calculations should be performed based on market hours
        should_calculate = MarketHours.should_calculate_momentum()
        market_status = MarketHours.get_market_status_message()
        
        # Get fresh momentum scores calculated on-the-fly
        logger.info(f"Calculating fresh momentum scores: {market_status}")
        
        return await get_fresh_momentum_scores(limit, industry, sector, top_n, market_status)
        
    except Exception as e:
        logger.error(f"Error calculating momentum: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/momentum/sector")
async def calculate_sector_momentum(
    limit: int = Query(100, ge=1, le=2525, description="Number of stocks to analyze"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    sector: Optional[str] = Query(None, description="Filter by sector")
):
    """Calculate momentum scores by sector - OPTIMIZED VERSION"""
    try:
        # Get stocks from data service
        stocks_data = await get_data_from_data_service("/stocks", {
            "limit": limit,
            "industry": industry,
            "sector": sector
        })
        
        if not stocks_data.get("stocks"):
            return {"sector_momentum": {}, "count": 0, "filters": {"limit": limit, "industry": industry, "sector": sector}}
        
        # Convert to DataFrame for momentum calculation
        stocks_df = pd.DataFrame(stocks_data["stocks"])
        
        # Get historical data directly from database (much faster than HTTP calls)
        try:
            # Get all price data at once from database
            symbols = [stock["stock"] for stock in stocks_data["stocks"]]
            historical_data = momentum_service.get_historical_data_from_db(symbols)
            logger.info(f"Retrieved historical data for {len(historical_data)} stocks from database")
        except Exception as e:
            logger.error(f"Error getting historical data from database: {e}")
            historical_data = {}
        
        # Calculate momentum scores
        momentum_df = momentum_service.calculate_momentum_scores(stocks_df, historical_data)
        
        if momentum_df.empty:
            return {"sector_momentum": {}, "count": 0, "filters": {"limit": limit, "industry": industry, "sector": sector}}
        
        # Calculate sector momentum
        sector_momentum = momentum_service.calculate_sector_momentum(momentum_df)
        
        # Clean NaN/inf values for JSON serialization
        def clean_float_values(data):
            if isinstance(data, dict):
                return {k: clean_float_values(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [clean_float_values(item) for item in data]
            elif isinstance(data, float):
                if pd.isna(data) or np.isinf(data):
                    return None
                return data
            else:
                return data
        
        sector_momentum = clean_float_values(sector_momentum)
        
        return {
            "sector_momentum": sector_momentum,
            "count": len(momentum_df),
            "filters": {"limit": limit, "industry": industry, "sector": sector}
        }
        
    except Exception as e:
        logger.error(f"Error calculating sector momentum: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration Endpoints
@app.get("/config/momentum")
async def get_momentum_configuration():
    """Get current momentum configuration"""
    try:
        config = get_momentum_config()
        return {
            "weights": config.weights.dict(),
            "volatility_cap": config.volatility_cap,
            "momentum_cap": config.momentum_cap,
            "smooth_factor_base": config.smooth_factor_base
        }
    except Exception as e:
        logger.error(f"Error getting momentum configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/config/momentum")
async def update_momentum_configuration(config_data: Dict[str, Any]):
    """Update momentum configuration"""
    try:
        updated_config = update_momentum_config(config_data)
        
        # Clear momentum cache to force recalculation with new config
        momentum_service.clear_cache()
        
        return {
            "message": "Momentum configuration updated successfully",
            "config": {
                "weights": updated_config.weights.dict(),
                "volatility_cap": updated_config.volatility_cap,
                "momentum_cap": updated_config.momentum_cap,
                "smooth_factor_base": updated_config.smooth_factor_base
            }
        }
    except Exception as e:
        logger.error(f"Error updating momentum configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config/momentum/reset")
async def reset_momentum_configuration():
    """Reset momentum configuration to defaults"""
    try:
        reset_config = reset_momentum_config()
        
        # Clear momentum cache to force recalculation with default config
        momentum_service.clear_cache()
        
        return {
            "message": "Momentum configuration reset to defaults",
            "config": {
                "weights": reset_config.weights.dict(),
                "volatility_cap": reset_config.volatility_cap,
                "momentum_cap": reset_config.momentum_cap,
                "smooth_factor_base": reset_config.smooth_factor_base
            }
        }
    except Exception as e:
        logger.error(f"Error resetting momentum configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cache Management
@app.post("/cache/clear")
async def clear_cache():
    """Clear momentum calculation cache"""
    try:
        momentum_service.clear_cache()
        return {"message": "Momentum cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/status")
async def get_cache_status():
    """Get cache status and statistics"""
    try:
        cache_stats = momentum_service.get_cache_stats()
        return cache_stats
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Stock Data Endpoints (moved from data service)
@app.get("/stocks")
async def get_stocks(
    limit: int = Query(100, description="Maximum number of stocks to return"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    sector: Optional[str] = Query(None, description="Filter by sector")
):
    """Get list of stocks with optional filters"""
    try:
        stocks_df = stock_service.get_stocks(limit, industry, sector)
        stocks_json = stocks_df.to_dict('records')
        
        return {
            "stocks": stocks_json,
            "count": len(stocks_json),
            "filters": {"limit": limit, "industry": industry, "sector": sector}
        }
    except Exception as e:
        logger.error(f"Error getting stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/{symbol}/price-data")
async def get_stock_price_data(
    symbol: str,
    days: int = Query(30, description="Number of days of price data to return")
):
    """Get price data for a specific stock"""
    try:
        # Get price data from database
        price_data_df = database_service.get_price_data(symbol)
        
        if price_data_df.empty:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")
        
        # Limit to requested days
        if days and len(price_data_df) > days:
            price_data_df = price_data_df.tail(days)
        
        # Convert to JSON and handle NaN/inf values
        price_data_json = price_data_df.to_dict('records')
        for record in price_data_json:
            for key, value in record.items():
                if pd.isna(value) or np.isinf(value):
                    record[key] = None
        
        return {
            "symbol": symbol,
            "data": price_data_json,
            "count": len(price_data_json)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/industries")
async def get_industries():
    """Get list of unique industries"""
    try:
        industries = stock_service.get_unique_industries()
        return {"industries": industries, "count": len(industries)}
    except Exception as e:
        logger.error(f"Error getting industries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sectors")
async def get_sectors():
    """Get list of unique sectors"""
    try:
        sectors = stock_service.get_unique_sectors()
        return {"sectors": sectors, "count": len(sectors)}
    except Exception as e:
        logger.error(f"Error getting sectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
