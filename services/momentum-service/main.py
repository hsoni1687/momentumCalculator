"""
Momentum Service - Optimized version that uses database directly instead of HTTP calls
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
import uvicorn
import httpx
import asyncio
import numpy as np

from config.settings import settings
from config.momentum_config import get_momentum_config, update_momentum_config, reset_momentum_config
from models import DatabaseService, MomentumService
from models.momentum_storage import MomentumStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
database_service = DatabaseService()
momentum_service = MomentumService(database_service)
momentum_storage = MomentumStorage(database_service)

# Data service URL (will be configurable)
DATA_SERVICE_URL = "http://data-service:8001"

# Create FastAPI app
app = FastAPI(
    title="Momentum Calculator - Momentum Service",
    description="Service responsible for momentum calculations and API responses",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP client for data service communication
http_client = httpx.AsyncClient(timeout=30.0)

async def get_data_from_data_service(endpoint: str, params: Dict = None) -> Dict:
    """Helper function to get data from data service"""
    try:
        response = await http_client.get(f"{DATA_SERVICE_URL}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Unexpected error communicating with data service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_status = "connected" if database_service.test_connection() else "disconnected"
        
        # Test data service connection
        try:
            data_service_response = await http_client.get(f"{DATA_SERVICE_URL}/health", timeout=5.0)
            data_service_status = "connected" if data_service_response.status_code == 200 else "disconnected"
        except:
            data_service_status = "disconnected"
        
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

# Momentum Calculation Endpoints
@app.get("/momentum")
async def calculate_momentum(
    limit: int = Query(50, ge=1, le=2525, description="Number of stocks to analyze"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    top_n: int = Query(10, ge=1, le=100, description="Number of top stocks to return")
):
    """Calculate momentum scores for stocks - ULTRA OPTIMIZED VERSION"""
    try:
        # Step 1: Get stocks that need momentum calculation (ordered by market cap)
        stocks_needing_calculation = momentum_storage.get_stocks_needing_momentum_calculation(limit)
        
        # Step 2: Calculate momentum for stocks that don't have today's scores
        if stocks_needing_calculation:
            logger.info(f"Calculating momentum for {len(stocks_needing_calculation)} stocks that need it")
            
            # Get stock metadata for these stocks
            stocks_df = database_service.get_stock_metadata()
            stocks_to_calculate = stocks_df[stocks_df['stock'].isin(stocks_needing_calculation)]
            
            if not stocks_to_calculate.empty:
                # Get historical data for these stocks
                historical_data = momentum_service.get_historical_data_from_db(stocks_needing_calculation)
                
                if historical_data:
                    # Calculate momentum scores
                    momentum_df = momentum_service.calculate_momentum_scores(stocks_to_calculate, historical_data)
                    
                    if not momentum_df.empty:
                        # Store the calculated scores
                        momentum_storage.store_momentum_scores(momentum_df)
                        logger.info(f"Stored momentum scores for {len(momentum_df)} stocks")
        
        # Step 3: Get all momentum scores for today (including pre-calculated ones)
        momentum_scores_df = momentum_storage.get_momentum_scores_for_date(limit=limit)
        
        if momentum_scores_df.empty:
            return {
                "momentum_scores": [],
                "top_stocks": [],
                "count": 0,
                "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n}
            }
        
        # Step 4: Apply filters if specified
        if industry:
            momentum_scores_df = momentum_scores_df[momentum_scores_df['industry'] == industry]
        if sector:
            momentum_scores_df = momentum_scores_df[momentum_scores_df['sector'] == sector]
        
        # Step 5: Get top stocks
        top_stocks_df = momentum_scores_df.head(top_n)
        
        # Convert to JSON format and handle NaN/inf values
        momentum_scores = momentum_scores_df.to_dict('records')
        top_stocks = top_stocks_df.to_dict('records')
        
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
        
        momentum_scores = clean_float_values(momentum_scores)
        top_stocks = clean_float_values(top_stocks)
        
        return {
            "momentum_scores": momentum_scores,
            "top_stocks": top_stocks,
            "count": len(momentum_scores),
            "filters": {"limit": limit, "industry": industry, "sector": sector, "top_n": top_n}
        }
        
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
