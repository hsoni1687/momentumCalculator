git """
Data Service - Responsible for stock data updates and database operations
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
import uvicorn
import asyncio

from config.settings import settings
from models import DatabaseService, StockService
from poller_service import PollerService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
database_service = DatabaseService()
stock_service = StockService(database_service)
poller_service = PollerService(database_service)

# Create FastAPI app
app = FastAPI(
    title="Momentum Calculator - Data Service",
    description="Service responsible for stock data updates and database operations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_status = "connected" if database_service.test_connection() else "disconnected"
        
        return {
            "status": "healthy",
            "service": "data-service",
            "database": db_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "data-service",
                "error": str(e)
            }
        )

# Stock Data Endpoints
@app.get("/stocks")
async def get_stocks(
    limit: int = Query(50, ge=1, le=2525, description="Number of stocks to retrieve"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    sector: Optional[str] = Query(None, description="Filter by sector")
):
    """Get list of stocks with metadata"""
    try:
        stocks_df = stock_service.get_stocks(limit=limit, industry=industry, sector=sector)
        
        if stocks_df.empty:
            return {"stocks": [], "count": 0, "filters": {"limit": limit, "industry": industry, "sector": sector}}
        
        stocks = stocks_df.to_dict('records')
        return {
            "stocks": stocks,
            "count": len(stocks),
            "filters": {"limit": limit, "industry": industry, "sector": sector}
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

@app.get("/stocks/{symbol}/prices")
async def get_stock_prices(
    symbol: str,
    days: int = Query(250, ge=1, le=1000, description="Number of days of price data")
):
    """Get historical price data for a specific stock"""
    try:
        # Create a DataFrame with the single stock
        stocks_df = pd.DataFrame([{'stock': symbol}])
        
        # Get historical data using the correct method
        historical_data = stock_service.get_historical_data(stocks_df)
        
        if symbol not in historical_data or historical_data[symbol] is None or historical_data[symbol].empty:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")
        
        price_data = historical_data[symbol]
        
        # Convert to JSON-serializable format
        price_data_json = price_data.reset_index().to_dict('records')
        
        # Handle NaN and infinite values for JSON serialization
        import numpy as np
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

# Industry and Sector Endpoints
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

# Poller Service Endpoints
@app.post("/poller/start")
async def start_poller():
    """Start the automatic poller service"""
    try:
        if poller_service.is_running:
            return {"message": "Poller service is already running", "status": "running"}
        
        # Start poller in background
        asyncio.create_task(poller_service.start_polling())
        
        return {
            "message": "Poller service started successfully",
            "status": "started",
            "update_interval": poller_service.update_interval,
            "batch_size": poller_service.batch_size
        }
    except Exception as e:
        logger.error(f"Error starting poller service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/poller/stop")
async def stop_poller():
    """Stop the automatic poller service"""
    try:
        await poller_service.stop_polling()
        return {"message": "Poller service stopped successfully", "status": "stopped"}
    except Exception as e:
        logger.error(f"Error stopping poller service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/poller/status")
async def get_poller_status():
    """Get poller service status and statistics"""
    try:
        status = poller_service.get_poller_status()
        return status
    except Exception as e:
        logger.error(f"Error getting poller status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stocks/{symbol}/update")
async def update_stock_data(symbol: str):
    """Update data for a specific stock"""
    try:
        result = await poller_service.update_specific_stocks([symbol])
        return {
            "message": f"Update completed for {symbol}",
            "symbol": symbol,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error updating data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stocks/bulk-update")
async def bulk_update_stocks(
    symbols: List[str],
    force: bool = Query(False, description="Force update even if data is recent")
):
    """Bulk update data for multiple stocks"""
    try:
        if force:
            # Force update all stocks
            result = await poller_service.force_update_all()
        else:
            # Update specific stocks
            result = await poller_service.update_specific_stocks(symbols)
        
        return {
            "message": f"Bulk update completed",
            "requested_stocks": len(symbols),
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in bulk update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/poller/force-update-all")
async def force_update_all_stocks():
    """Force update all stocks (ignore last update date)"""
    try:
        result = await poller_service.force_update_all()
        return {
            "message": "Force update of all stocks completed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in force update all: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/poller/stocks-needing-update")
async def get_stocks_needing_update():
    """Get list of stocks that need updates"""
    try:
        stocks = poller_service.get_stocks_needing_update()
        return {
            "stocks_needing_update": stocks,
            "count": len(stocks)
        }
    except Exception as e:
        logger.error(f"Error getting stocks needing update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cache Management
@app.post("/cache/clear")
async def clear_cache():
    """Clear all caches"""
    try:
        stock_service.clear_cache()
        return {"message": "Data service cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Different port for data service
        reload=True
    )
