"""
Strategy Service - Handles multiple trading strategies
"""
from fastapi import FastAPI, HTTPException, Query, Request
# CORS is handled by nginx reverse proxy
from fastapi.responses import JSONResponse
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
import uvicorn
import numpy as np
import time
from collections import defaultdict

from config.settings import settings
from config.database_queries import DatabaseQueries
from models import DatabaseService
from models.strategy_manager import StrategyManager
from models.stock import StockService
from models.momentum_calculator import MomentumCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sanitize numeric values to prevent JSON serialization errors
def sanitize_float(value):
    if pd.isna(value) or np.isinf(value) or np.isnan(value):
        return 0.0
    return float(value)

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
strategy_manager = StrategyManager()
momentum_calculator = MomentumCalculator()
stock_service = StockService(database_service)

# Placeholder strategy functions (to be implemented)
async def get_week52_breakout_data(market_cap_limit: int, industry: str = None, sector: str = None, input_df: Optional[pd.DataFrame] = None):
    """52-week breakout strategy - finds stocks near 52-week highs.

    If input_df is provided, compute using that set of symbols by deriving 52-week
    highs from price data; otherwise default to top N by market cap.
    """
    try:
        # Establish input universe
        if input_df is not None and not input_df.empty:
            symbols = input_df['stock'].tolist()
        else:
            query, params = DatabaseQueries.get_top_stocks_by_market_cap(market_cap_limit, industry, sector)
            stocks_df = database_service.execute_query(query, params)
            symbols = stocks_df['stock'].tolist() if not stocks_df.empty else []
        
        breakout_scores = []
        for symbol in symbols:
            try:
                # Get price data and derive metrics
                price_df = database_service.get_price_data(symbol)
                if price_df is None or price_df.empty or 'close' not in price_df.columns:
                    continue
                closes = price_df['close'].astype(float).tail(252)  # last ~52 weeks trading days
                if closes.empty:
                    continue
                current_price = float(closes.iloc[-1])
                fifty_two_week_high = float(closes.max())
                
                if fifty_two_week_high > 0:
                    # Score based on how close to 52-week high (0.8-1.0 range)
                    proximity_ratio = current_price / fifty_two_week_high
                    if proximity_ratio >= 0.95:  # Within 5% of 52-week high
                        breakout_score = 0.8 + (proximity_ratio - 0.95) * 4  # Scale to 0.8-1.0
                        
                        breakout_scores.append({
                            'stock': symbol,
                            'name': '',
                            'sector': '',
                            'industry': '',
                            'score': min(breakout_score, 1.0),  # Cap at 1.0
                            'current_price': current_price,
                            'market_cap': 0.0
                        })
            except (ValueError, TypeError):
                continue
                
        return {"strategy_scores": breakout_scores}
    except Exception as e:
        logger.error(f"Error in get_week52_breakout_data: {e}")
        return {"strategy_scores": []}

async def get_mean_reversion_data(market_cap_limit: int, industry: str = None, sector: str = None, input_df: Optional[pd.DataFrame] = None):
    """Mean reversion strategy - finds oversold stocks that may bounce back.

    If input_df is provided, compute using that symbol set via price data; else
    default to top N by market cap.
    """
    try:
        if input_df is not None and not input_df.empty:
            symbols = input_df['stock'].tolist()
        else:
            query, params = DatabaseQueries.get_top_stocks_by_market_cap(market_cap_limit, industry, sector)
            stocks_df = database_service.execute_query(query, params)
            symbols = stocks_df['stock'].tolist() if not stocks_df.empty else []
        
        reversion_scores = []
        for symbol in symbols:
            try:
                price_df = database_service.get_price_data(symbol)
                if price_df is None or price_df.empty or 'close' not in price_df.columns:
                    continue
                closes = price_df['close'].astype(float).tail(252)
                if closes.empty:
                    continue
                current_price = float(closes.iloc[-1])
                fifty_two_week_high = float(closes.max())
                fifty_two_week_low = float(closes.min())
                
                if fifty_two_week_high > 0 and fifty_two_week_low > 0:
                    # Calculate position in 52-week range
                    range_size = fifty_two_week_high - fifty_two_week_low
                    if range_size > 0:
                        position_in_range = (current_price - fifty_two_week_low) / range_size
                        
                        # Look for stocks in lower 30% of range (oversold)
                        if position_in_range <= 0.3:
                            # Score inversely related to position (lower = higher score)
                            reversion_score = 0.5 + (0.3 - position_in_range) * 1.67  # Scale to 0.5-1.0
                            
                            reversion_scores.append({
                                'stock': symbol,
                                'name': '',
                                'sector': '',
                                'industry': '',
                                'score': min(reversion_score, 1.0),  # Cap at 1.0
                                'current_price': current_price,
                                'market_cap': 0.0
                            })
            except (ValueError, TypeError):
                continue
                
        return {"strategy_scores": reversion_scores}
    except Exception as e:
        logger.error(f"Error in get_mean_reversion_data: {e}")
        return {"strategy_scores": []}

async def get_low_volatility_data(market_cap_limit: int, industry: str = None, sector: str = None, input_df: Optional[pd.DataFrame] = None):
    """Low volatility strategy - finds stocks with stable price movements.

    If input_df is provided, compute vol from price data for that set; else
    default to top N by market cap.
    """
    try:
        if input_df is not None and not input_df.empty:
            symbols = input_df['stock'].tolist()
        else:
            query, params = DatabaseQueries.get_top_stocks_by_market_cap(market_cap_limit, industry, sector)
            stocks_df = database_service.execute_query(query, params)
            symbols = stocks_df['stock'].tolist() if not stocks_df.empty else []
        
        volatility_scores = []
        for symbol in symbols:
            try:
                price_df = database_service.get_price_data(symbol)
                if price_df is None or price_df.empty or 'close' not in price_df.columns:
                    continue
                closes = price_df['close'].astype(float).tail(252)
                if len(closes) < 20:
                    continue
                returns = closes.pct_change().dropna()
                daily_vol = float(returns.std())
                # Lower volatility => higher score; map roughly to 0.5-1.0
                # Assume daily_vol between 0 and 0.05 typical
                vol_clamped = max(0.0, min(daily_vol, 0.05))
                volatility_score = 1.0 - (vol_clamped / 0.05) * 0.5
                current_price = float(closes.iloc[-1])

                volatility_scores.append({
                    'stock': symbol,
                    'name': '',
                    'sector': '',
                    'industry': '',
                    'score': min(max(volatility_score, 0.5), 1.0),
                    'current_price': current_price,
                    'market_cap': 0.0
                })
            except (ValueError, TypeError):
                continue
                
        return {"strategy_scores": volatility_scores}
    except Exception as e:
        logger.error(f"Error in get_low_volatility_data: {e}")
        return {"strategy_scores": []}

# Create FastAPI app
app = FastAPI(
    title="Momentum Calculator - Strategy Service",
    description="Service responsible for multiple trading strategy calculations",
    version="1.0.0"
)

# CORS is handled by nginx reverse proxy

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_status = "connected" if database_service.test_connection() else "disconnected"
        
        return {
            "status": "healthy",
            "service": "strategy-service",
            "database": db_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "strategy-service",
                "error": str(e)
            }
        )

@app.get("/strategies")
async def get_available_strategies():
    """Get list of all available strategies"""
    try:
        strategies = strategy_manager.get_available_strategies()
        return {
            "strategies": strategies,
            "count": len(strategies)
        }
    except Exception as e:
        logger.error(f"Error getting available strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategy/v2/{strategy_name}")
async def calculate_strategy_scores_v2(
    request: Request,
    strategy_name: str,
    limit: int = Query(50, ge=1, le=2525, description="Number of stocks to analyze"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    top_n: int = Query(10, ge=1, le=100, description="Number of top stocks to return")
):
    """Calculate scores for a specific strategy"""
    try:
        # Strict behavior preserved for legacy UI - invalid names should 404
        # Rate limiting
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
        
        # Check if strategy exists
        if strategy_name not in strategy_manager.strategies:
            raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found")
        
        # Get stock metadata with filters
        query, params = DatabaseQueries.get_top_stocks_by_market_cap(limit, industry, sector)
        stock_metadata = database_service.execute_query(query, params)
        
        if stock_metadata.empty:
            return {
                "strategy_scores": [],
                "top_stocks": [],
                "count": 0,
                "strategy_name": strategy_name,
                "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n},
                "message": "No stocks found matching the criteria"
            }
        
        # Get price data for all stocks
        symbols = stock_metadata['stock'].tolist()
        price_data = {}
        
        for symbol in symbols:
            try:
                logger.info(f"DEBUG: Getting price data for {symbol}")
                price_df = database_service.get_price_data(symbol)
                logger.info(f"DEBUG: Got price data for {symbol}, shape: {price_df.shape}")
                if not price_df.empty:
                    price_data[symbol] = price_df
                    logger.info(f"DEBUG: Added {symbol} to price_data")
                else:
                    logger.warning(f"DEBUG: Empty price data for {symbol}")
            except Exception as e:
                logger.warning(f"Could not get price data for {symbol}: {e}")
                continue
        
        if not price_data:
            return {
                "strategy_scores": [],
                "top_stocks": [],
                "count": 0,
                "strategy_name": strategy_name,
                "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n},
                "message": "No price data available for any stocks"
            }
        
        # Calculate strategy scores
        strategy_scores_df = strategy_manager.calculate_strategy_scores(
            strategy_name, stock_metadata, price_data
        )
        
        if strategy_scores_df is None or strategy_scores_df.empty:
            return {
                "strategy_scores": [],
                "top_stocks": [],
                "count": 0,
                "strategy_name": strategy_name,
                "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n},
                "message": f"Could not calculate scores for strategy '{strategy_name}'"
            }
        
        # Merge with stock metadata
        merged_df = strategy_scores_df.merge(stock_metadata, on='stock', how='inner')
        
        # Filter out stocks with insufficient data
        valid_scores_df = merged_df[merged_df['insufficient_data'] == False].copy()
        
        if valid_scores_df.empty:
            return {
                "strategy_scores": [],
                "top_stocks": [],
                "count": 0,
                "strategy_name": strategy_name,
                "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n},
                "message": "No stocks have sufficient data for this strategy"
            }
        
        # Sort by score (descending for most strategies, ascending for low volatility)
        if strategy_name == 'low_volatility':
            # For low volatility, lower scores (more negative) are better
            valid_scores_df = valid_scores_df.sort_values('score', ascending=True)
        else:
            # For other strategies, higher scores are better
            valid_scores_df = valid_scores_df.sort_values('score', ascending=False)
        
        # Get top N stocks
        top_stocks_df = valid_scores_df.head(top_n)
        
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
        
        strategy_scores = []
        for _, row in valid_scores_df.iterrows():
            score_data = {
                "stock": row['stock'],
                "name": row.get('company_name', ''),
                "sector": row.get('sector', ''),
                "industry": row.get('industry', ''),
                "score": safe_float(row['score']),
                "insufficient_data": row.get('insufficient_data', False)
            }
            
            # Add strategy-specific fields
            if strategy_name == 'week52_breakout':
                # Use current_price_y (from metadata) as it's the latest price pulled
                current_price_val = row.get('current_price_y') or row.get('current_price_x')
                score_data.update({
                    "current_price": safe_float(current_price_val),
                    "week52_high": safe_float(row.get('week52_high')),
                    "week52_low": safe_float(row.get('week52_low')),
                    "breakout_ratio": safe_float(row.get('breakout_ratio'))
                })
            elif strategy_name == 'ma_crossover':
                score_data.update({
                    "ma_50": safe_float(row.get('ma_50')),
                    "ma_200": safe_float(row.get('ma_200')),
                    "crossover_ratio": safe_float(row.get('crossover_ratio'))
                })
            elif strategy_name == 'low_volatility':
                score_data.update({
                    "daily_volatility": safe_float(row.get('daily_volatility')),
                    "annual_volatility": safe_float(row.get('annual_volatility'))
                })
            elif strategy_name == 'mean_reversion':
                # Use current_price_y (from metadata) as it's the latest price pulled
                current_price_val = row.get('current_price_y') or row.get('current_price_x')
                score_data.update({
                    "current_price": safe_float(current_price_val),
                    "ma_200": safe_float(row.get('ma_200')),
                    "z_score": safe_float(row.get('z_score')),
                    "price_deviation_pct": safe_float(row.get('price_deviation_pct'))
                })
            
            strategy_scores.append(score_data)
        
        top_stocks = []
        for _, row in top_stocks_df.iterrows():
            score_data = {
                "stock": row['stock'],
                "name": row.get('company_name', ''),
                "sector": row.get('sector', ''),
                "industry": row.get('industry', ''),
                "score": safe_float(row['score']),
                "insufficient_data": row.get('insufficient_data', False)
            }
            
            # Add strategy-specific fields
            if strategy_name == 'week52_breakout':
                # Use current_price_y (from metadata) as it's the latest price pulled
                current_price_val = row.get('current_price_y') or row.get('current_price_x')
                score_data.update({
                    "current_price": safe_float(current_price_val),
                    "week52_high": safe_float(row.get('week52_high')),
                    "week52_low": safe_float(row.get('week52_low')),
                    "breakout_ratio": safe_float(row.get('breakout_ratio'))
                })
            elif strategy_name == 'ma_crossover':
                score_data.update({
                    "ma_50": safe_float(row.get('ma_50')),
                    "ma_200": safe_float(row.get('ma_200')),
                    "crossover_ratio": safe_float(row.get('crossover_ratio'))
                })
            elif strategy_name == 'low_volatility':
                score_data.update({
                    "daily_volatility": safe_float(row.get('daily_volatility')),
                    "annual_volatility": safe_float(row.get('annual_volatility'))
                })
            elif strategy_name == 'mean_reversion':
                # Use current_price_y (from metadata) as it's the latest price pulled
                current_price_val = row.get('current_price_y') or row.get('current_price_x')
                score_data.update({
                    "current_price": safe_float(current_price_val),
                    "ma_200": safe_float(row.get('ma_200')),
                    "z_score": safe_float(row.get('z_score')),
                    "price_deviation_pct": safe_float(row.get('price_deviation_pct'))
                })
            
            top_stocks.append(score_data)
        
        return {
            "strategy_scores": strategy_scores,
            "top_stocks": top_stocks,
            "count": len(strategy_scores),
            "strategy_name": strategy_name,
            "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating strategy scores for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategy/{strategy_name}")
async def calculate_strategy_scores_legacy(
    request: Request,
    strategy_name: str,
    limit: int = Query(50, ge=1, le=2525, description="Number of stocks to analyze"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    top_n: int = Query(10, ge=1, le=100, description="Number of top stocks to return")
):
    """Legacy endpoint for strategy calculations - defaults to momentum for undefined strategies"""
    try:
        # Handle undefined/invalid strategy names by defaulting to momentum
        if not strategy_name or strategy_name in ['undefined', 'null', 'none', '']:
            strategy_name = 'momentum'
        
        # If strategy doesn't exist in our manager, default to momentum
        if strategy_name not in strategy_manager.strategies:
            logger.warning(f"Strategy '{strategy_name}' not found, defaulting to momentum")
            strategy_name = 'momentum'
        
        # Call the v2 endpoint internally
        return await calculate_strategy_scores_v2(request, strategy_name, limit, industry, sector, top_n)
        
    except Exception as e:
        logger.error(f"Error in legacy strategy endpoint for {strategy_name}: {e}")
        # Fallback to momentum on any error
        return await calculate_strategy_scores_v2(request, 'momentum', limit, industry, sector, top_n)

# Stock Data Endpoints (same as momentum service for consistency)
@app.get("/stocks")
async def get_stocks(
    limit: int = Query(100, description="Maximum number of stocks to return"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    sector: Optional[str] = Query(None, description="Filter by sector")
):
    """Get list of stocks with optional filters"""
    try:
        logger.info(f"Getting stocks with limit={limit}, industry={industry}, sector={sector}")
        stocks_df = stock_service.get_stocks(limit, industry, sector)
        
        if stocks_df.empty:
            logger.warning("No stocks found")
            return {
                "stocks": [],
                "count": 0,
                "filters": {"limit": limit, "industry": industry, "sector": sector}
            }
        
        logger.info(f"Retrieved {len(stocks_df)} stocks from database")
        
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
        
        # Convert to dict first, then clean
        stocks_json = stocks_df.to_dict('records')
        logger.info(f"Converted to dict, cleaning {len(stocks_json)} records")
        
        stocks_json = clean_float_values(stocks_json)
        logger.info("Successfully cleaned float values")
        
        return {
            "stocks": stocks_json,
            "count": len(stocks_json),
            "filters": {"limit": limit, "industry": industry, "sector": sector}
        }
    except Exception as e:
        logger.error(f"Error getting stocks: {e}")
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

# Pipeline endpoints
@app.get("/pipeline/strategies")
async def get_available_strategies():
    """Get list of available strategies for pipeline building"""
    try:
        strategies = [
            {
                "id": "momentum",
                "name": "Momentum Strategy",
                "description": "Identifies stocks with strong price momentum using the Frog in the Pan methodology",
                "category": "momentum",
                "icon": "trending-up",
                "color": "blue"
            },
            {
                "id": "week52_breakout",
                "name": "52-Week Breakout",
                "description": "Finds stocks breaking out to new 52-week highs with strong volume",
                "category": "breakout",
                "icon": "target",
                "color": "green"
            },
            {
                "id": "mean_reversion",
                "name": "Mean Reversion",
                "description": "Identifies oversold stocks that may bounce back to their mean",
                "category": "mean-reversion",
                "icon": "bar-chart",
                "color": "purple"
            },
            {
                "id": "low_volatility",
                "name": "Low Volatility",
                "description": "Finds stocks with low price volatility for stable returns",
                "category": "volatility",
                "icon": "shield",
                "color": "orange"
            }
        ]
        return {"strategies": strategies, "count": len(strategies)}
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pipeline/execute")
async def execute_pipeline(pipeline_request: dict):
    """Execute a strategy pipeline"""
    try:
        import time
        import uuid
        from datetime import datetime
        
        start_time = time.time()
        pipeline_id = str(uuid.uuid4())
        
        strategies = pipeline_request.get("strategies", [])
        pipeline_name = pipeline_request.get("name", f"Pipeline {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        if not strategies:
            raise HTTPException(status_code=400, detail="No strategies provided")
        
        # Initialize with all stocks
        current_stocks = None
        results = []
        total_stocks_processed = 0
        
        for i, strategy_config in enumerate(strategies):
            # Handle both camelCase (frontend) and snake_case (API) formats
            strategy_id = strategy_config.get("strategyId") or strategy_config.get("strategy_id")
            market_cap_limit = strategy_config.get("marketCapLimit") or strategy_config.get("market_cap_limit", 1000)
            output_count = strategy_config.get("outputCount") or strategy_config.get("output_count", 50)
            industry = strategy_config.get("industry")
            sector = strategy_config.get("sector")
            
            strategy_start_time = time.time()
            
            # Get stocks for this strategy
            if i == 0:
                # First strategy - get top stocks by market cap
                query, params = DatabaseQueries.get_top_stocks_by_market_cap(
                    market_cap_limit, industry, sector
                )
                stocks_df = database_service.execute_query(query, params)
                input_count = len(stocks_df)
                input_symbols = stocks_df['stock'].tolist() if not stocks_df.empty else []
            else:
                # Subsequent strategies - use explicit input from previous output
                if current_stocks is None or current_stocks.empty:
                    break
                # current_stocks contains at least 'stock'; build metadata frame for next step
                symbols = current_stocks['stock'].tolist()
                # Create a minimal DataFrame with just stock symbols
                stocks_df = pd.DataFrame({'stock': symbols})
                input_count = len(stocks_df)
                input_symbols = symbols
            
            total_stocks_processed += input_count
            
            # Execute strategy
            if strategy_id == "momentum":
                # Get momentum scores
                momentum_scores = []
                for _, stock_row in stocks_df.iterrows():
                    symbol = stock_row['stock']
                    try:
                        stock_prices = database_service.get_price_data(symbol)
                        if not stock_prices.empty and 'close' in stock_prices.columns:
                            stock_prices['date'] = pd.to_datetime(stock_prices['date'])
                            stock_prices = stock_prices.set_index('date')
                            
                            momentum_result = momentum_calculator.calculate_quality_momentum_score(stock_prices)
                            momentum_score = momentum_result.get('total_score', 0)

                            momentum_scores.append({
                                'stock': symbol,
                                'name': stock_row.get('company_name', ''),
                                'sector': stock_row.get('sector', ''),
                                'industry': stock_row.get('industry', ''),
                                'score': sanitize_float(momentum_score),
                                'current_price': sanitize_float(stock_row.get('current_price', 0)),
                                'market_cap': sanitize_float(stock_row.get('market_cap', 0))
                            })
                    except Exception as e:
                        logger.warning(f"Error calculating momentum for {symbol}: {e}")
                        continue
                
                # Sort by score and take top N
                momentum_scores.sort(key=lambda x: x['score'], reverse=True)
                current_stocks = pd.DataFrame(momentum_scores[:output_count])
                strategy_name = "Momentum Strategy"
                
            elif strategy_id == "week52_breakout":
                # Get 52-week breakout results
                breakout_data = await get_week52_breakout_data(market_cap_limit, industry, sector, input_df=stocks_df if i > 0 else None)
                breakout_stocks = breakout_data.get("strategy_scores", [])
                
                # Convert to DataFrame and sort by score
                breakout_df = pd.DataFrame(breakout_stocks)
                if not breakout_df.empty:
                    breakout_df = breakout_df.sort_values('score', ascending=False)
                    current_stocks = breakout_df.head(output_count)
                else:
                    current_stocks = pd.DataFrame()
                strategy_name = "52-Week Breakout"
                
            elif strategy_id == "mean_reversion":
                # Get mean reversion results
                reversion_data = await get_mean_reversion_data(market_cap_limit, industry, sector, input_df=stocks_df if i > 0 else None)
                reversion_stocks = reversion_data.get("strategy_scores", [])
                
                # Convert to DataFrame and sort by score
                reversion_df = pd.DataFrame(reversion_stocks)
                if not reversion_df.empty:
                    reversion_df = reversion_df.sort_values('score', ascending=False)
                    current_stocks = reversion_df.head(output_count)
                else:
                    current_stocks = pd.DataFrame()
                strategy_name = "Mean Reversion"
                
            elif strategy_id == "low_volatility":
                # Get low volatility results
                volatility_data = await get_low_volatility_data(market_cap_limit, industry, sector, input_df=stocks_df if i > 0 else None)
                volatility_stocks = volatility_data.get("strategy_scores", [])
                
                # Convert to DataFrame and sort by score
                volatility_df = pd.DataFrame(volatility_stocks)
                if not volatility_df.empty:
                    volatility_df = volatility_df.sort_values('score', ascending=False)
                    current_stocks = volatility_df.head(output_count)
                else:
                    current_stocks = pd.DataFrame()
                strategy_name = "Low Volatility"
                
            else:
                # Default - just take top N stocks
                current_stocks = stocks_df.head(output_count)
                strategy_name = f"Strategy {i+1}"
            
            strategy_execution_time = sanitize_float((time.time() - strategy_start_time) * 1000)  # Convert to ms
            output_count_actual = len(current_stocks)
            
            # Calculate metrics
            if not current_stocks.empty and 'score' in current_stocks.columns:
                scores = current_stocks['score'].values
                avg_score = sanitize_float(scores.mean()) if len(scores) > 0 else 0
                top_score = sanitize_float(scores.max()) if len(scores) > 0 else 0
                bottom_score = sanitize_float(scores.min()) if len(scores) > 0 else 0
            else:
                avg_score = top_score = bottom_score = 0
            
            # Convert stocks to list of dicts and sanitize numeric values
            stocks_list = current_stocks.to_dict('records') if not current_stocks.empty else []
            for stock in stocks_list:
                for key, value in stock.items():
                    if isinstance(value, (int, float)):
                        stock[key] = sanitize_float(value)
            
            results.append({
                "strategyId": strategy_id,
                "strategyName": strategy_name,
                "inputCount": input_count,
                "outputCount": output_count_actual,
                "executionTime": strategy_execution_time,
                "stocks": stocks_list,
                "debug": {
                    "universe": "market_cap" if i == 0 else "previous_output",
                    "inputSymbols": input_symbols[:100]
                },
                "metrics": {
                    "averageScore": avg_score,
                    "topScore": top_score,
                    "bottomScore": bottom_score
                }
            })
        
        execution_time = sanitize_float((time.time() - start_time) * 1000)  # Convert to ms
        final_stocks = current_stocks.to_dict('records') if current_stocks is not None and not current_stocks.empty else []
        # Sanitize final stocks
        for stock in final_stocks:
            for key, value in stock.items():
                if isinstance(value, (int, float)):
                    stock[key] = sanitize_float(value)
        
        pipeline_result = {
            "pipelineId": pipeline_id,
            "name": pipeline_name,
            "strategies": strategies,
            "results": results,
            "finalStocks": final_stocks,
            "executionTime": execution_time,
            "totalStocksProcessed": total_stocks_processed,
            "createdAt": datetime.now().isoformat()
        }
        
        return pipeline_result
        
    except Exception as e:
        logger.error(f"Error executing pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipeline/{pipeline_id}")
async def get_pipeline_result(pipeline_id: str):
    """Get pipeline execution result by ID"""
    # In a real implementation, this would fetch from a database
    # For now, return a placeholder
    raise HTTPException(status_code=404, detail="Pipeline result not found")

@app.post("/pipeline/save")
async def save_pipeline(pipeline_data: dict):
    """Save a pipeline configuration"""
    try:
        import uuid
        from datetime import datetime
        
        pipeline_id = str(uuid.uuid4())
        # In a real implementation, this would save to a database
        # For now, just return the ID
        
        return {"pipelineId": pipeline_id}
        
    except Exception as e:
        logger.error(f"Error saving pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipeline/saved")
async def get_saved_pipelines():
    """Get list of saved pipelines"""
    # In a real implementation, this would fetch from a database
    # For now, return empty list
    return {"pipelines": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
