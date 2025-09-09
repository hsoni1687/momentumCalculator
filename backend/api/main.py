"""
FastAPI main application
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
import uvicorn

from config.settings import settings
from config.momentum_config import get_momentum_config, update_momentum_config, reset_momentum_config
from models import DatabaseService, StockService, MomentumService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db_service = DatabaseService()
stock_service = StockService(db_service)
momentum_service = MomentumService()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Momentum Calculator API",
        "version": settings.api_version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        is_connected = db_service.test_connection()
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "database": "connected" if is_connected else "disconnected",
            "version": settings.api_version
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/stocks")
async def get_stocks(
    limit: int = Query(default=50, ge=1, le=200, description="Number of stocks to return"),
    industry: Optional[str] = Query(default=None, description="Filter by industry"),
    sector: Optional[str] = Query(default=None, description="Filter by sector")
):
    """Get stocks with optional filtering"""
    try:
        stocks_df = stock_service.get_stocks(limit=limit, industry=industry, sector=sector)
        
        if stocks_df.empty:
            return {"stocks": [], "count": 0}
        
        # Convert to list of dictionaries
        stocks = stocks_df.to_dict('records')
        
        return {
            "stocks": stocks,
            "count": len(stocks),
            "filters": {
                "limit": limit,
                "industry": industry,
                "sector": sector
            }
        }
    except Exception as e:
        logger.error(f"Error getting stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/{symbol}")
async def get_stock_info(symbol: str):
    """Get detailed information for a specific stock"""
    try:
        stock_info = stock_service.get_stock_info(symbol)
        
        if stock_info is None:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        return {"stock": stock_info}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/momentum")
async def calculate_momentum(
    limit: int = Query(default=50, ge=1, le=200, description="Number of stocks to analyze"),
    industry: Optional[str] = Query(default=None, description="Filter by industry"),
    sector: Optional[str] = Query(default=None, description="Filter by sector"),
    top_n: int = Query(default=10, ge=1, le=50, description="Number of top stocks to return")
):
    """Calculate momentum scores for stocks"""
    try:
        # Get stocks
        stocks_df = stock_service.get_stocks(limit=limit, industry=industry, sector=sector)
        
        if stocks_df.empty:
            return {"momentum_scores": [], "count": 0, "message": "No stocks found"}
        
        # Get historical data
        historical_data = stock_service.get_historical_data(stocks_df)
        
        if not historical_data:
            return {"momentum_scores": [], "count": 0, "message": "No historical data available"}
        
        # Calculate momentum scores
        momentum_df = momentum_service.calculate_momentum_scores(stocks_df, historical_data)
        
        if momentum_df.empty:
            return {"momentum_scores": [], "count": 0, "message": "No momentum scores calculated"}
        
        # Get top stocks
        top_stocks = momentum_service.get_top_momentum_stocks(momentum_df, top_n)
        
        # Convert to list of dictionaries
        momentum_scores = momentum_df.to_dict('records')
        top_stocks_list = top_stocks.to_dict('records')
        
        return {
            "momentum_scores": momentum_scores,
            "top_stocks": top_stocks_list,
            "count": len(momentum_scores),
            "filters": {
                "limit": limit,
                "industry": industry,
                "sector": sector,
                "top_n": top_n
            }
        }
    except Exception as e:
        logger.error(f"Error calculating momentum: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/momentum/sectors")
async def get_momentum_by_sector(
    limit: int = Query(default=50, ge=1, le=200, description="Number of stocks to analyze"),
    industry: Optional[str] = Query(default=None, description="Filter by industry"),
    sector: Optional[str] = Query(default=None, description="Filter by sector")
):
    """Get momentum scores grouped by sector"""
    try:
        # Get stocks
        stocks_df = stock_service.get_stocks(limit=limit, industry=industry, sector=sector)
        
        if stocks_df.empty:
            return {"sector_momentum": [], "count": 0}
        
        # Get historical data
        historical_data = stock_service.get_historical_data(stocks_df)
        
        if not historical_data:
            return {"sector_momentum": [], "count": 0, "message": "No historical data available"}
        
        # Calculate momentum scores
        momentum_df = momentum_service.calculate_momentum_scores(stocks_df, historical_data)
        
        if momentum_df.empty:
            return {"sector_momentum": [], "count": 0, "message": "No momentum scores calculated"}
        
        # Get sector momentum
        sector_momentum = momentum_service.get_momentum_by_sector(momentum_df)
        
        # Convert to list of dictionaries
        sector_data = sector_momentum.to_dict('index')
        
        return {
            "sector_momentum": sector_data,
            "count": len(sector_data),
            "filters": {
                "limit": limit,
                "industry": industry,
                "sector": sector
            }
        }
    except Exception as e:
        logger.error(f"Error getting sector momentum: {e}")
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

@app.post("/cache/clear")
async def clear_cache():
    """Clear all caches"""
    try:
        stock_service.clear_cache()
        momentum_service.clear_cache()
        
        return {"message": "All caches cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Momentum Configuration Endpoints
@app.get("/config/momentum")
async def get_momentum_configuration():
    """Get current momentum calculation configuration"""
    try:
        config = get_momentum_config()
        return {
            "weights": config.weights.dict(),
            "volatility_cap": config.volatility_cap,
            "momentum_cap": config.momentum_cap,
            "smooth_factor_base": config.smooth_factor_base,
            "weights_sum": sum(config.weights.dict().values())
        }
    except Exception as e:
        logger.error(f"Error getting momentum configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/config/momentum")
async def update_momentum_configuration(config_data: Dict[str, Any]):
    """Update momentum calculation configuration"""
    try:
        updated_config = update_momentum_config(config_data)
        # Clear cache to ensure new configuration is used
        momentum_service.clear_cache()
        return {
            "message": "Momentum configuration updated successfully",
            "config": {
                "weights": updated_config.weights.dict(),
                "volatility_cap": updated_config.volatility_cap,
                "momentum_cap": updated_config.momentum_cap,
                "smooth_factor_base": updated_config.smooth_factor_base,
                "weights_sum": sum(updated_config.weights.dict().values())
            }
        }
    except Exception as e:
        logger.error(f"Error updating momentum configuration: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/config/momentum/reset")
async def reset_momentum_configuration():
    """Reset momentum configuration to defaults"""
    try:
        reset_config = reset_momentum_config()
        # Clear cache to ensure new configuration is used
        momentum_service.clear_cache()
        return {
            "message": "Momentum configuration reset to defaults",
            "config": {
                "weights": reset_config.weights.dict(),
                "volatility_cap": reset_config.volatility_cap,
                "momentum_cap": reset_config.momentum_cap,
                "smooth_factor_base": reset_config.smooth_factor_base,
                "weights_sum": sum(reset_config.weights.dict().values())
            }
        }
    except Exception as e:
        logger.error(f"Error resetting momentum configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
