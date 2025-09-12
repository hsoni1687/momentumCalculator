#!/usr/bin/env python3
"""
Data Service - Main Application
Handles stock data updates, financial attributes, and price data management
"""

import asyncio
import logging
import os
from typing import List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np

from config.settings import settings
from config.database_queries import DatabaseQueries
from utils.market_hours import MarketHours
from models import DatabaseService, StockService

# Initialize separate pollers
from price_poller import PricePoller
from attribute_poller import AttributePoller

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get service instance ID
SERVICE_INSTANCE = os.getenv("SERVICE_INSTANCE", "1")
logger.info(f"Starting Data Service Instance {SERVICE_INSTANCE}")

# Initialize services
database_service = DatabaseService()
stock_service = StockService(database_service)

# Initialize separate pollers
price_poller = PricePoller(database_service)
attribute_poller = AttributePoller(database_service)

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

@app.on_event("startup")
async def startup_event():
    """Start the poller services on startup"""
    try:
        logger.info("Starting poller services...")
        # Start price poller (runs on schedule)
        asyncio.create_task(price_poller.start_price_polling())
        logger.info("Price poller service started successfully")
        
        # Start attribute poller (runs continuously)
        asyncio.create_task(attribute_poller.start_attribute_polling())
        logger.info("Attribute poller service started successfully")
        
        logger.info("✅ Data service startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start poller services: {e}")
        raise  # Re-raise to prevent startup completion

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the poller services on shutdown"""
    try:
        logger.info("Stopping poller services...")
        await price_poller.stop_price_polling()
        await attribute_poller.stop_attribute_polling()
        logger.info("Poller services stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping poller services: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection with a simple query
        database_service.test_connection()
        return {
            "status": "healthy",
            "service": "data-service",
            "instance": SERVICE_INSTANCE,
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Data service is responding", "status": "ok"}

# Stock Data Endpoints moved to momentum service

# Data Status Endpoint
@app.get("/data-status")
async def get_data_status():
    """Get comprehensive data status"""
    try:
        attribute_status = attribute_poller.get_attribute_status()
        price_status = attribute_poller.get_price_status()
        
        return {
            "attribute_status": attribute_status,
            "price_status": price_status,
            "market_status": MarketHours.get_market_status_message()
        }
    except Exception as e:
        logger.error(f"Error getting data status: {e}")
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

# Price Poller Endpoints
@app.post("/price-update/manual")
async def trigger_manual_price_update():
    """Manually trigger price update for all stocks"""
    try:
        await price_poller.run_manual_price_update()
        return {"message": "Manual price update triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering manual price update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/price-update/status")
async def get_price_update_status():
    """Get current price update status"""
    try:
        pending_prices = price_poller.data_updater.get_pending_prices()
        return {
            "pending_prices": len(pending_prices),
            "pending_stocks": pending_prices[:10] if pending_prices else []  # Show first 10
        }
    except Exception as e:
        logger.error(f"Error getting price update status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Attribute Poller Endpoints
@app.post("/attributes-update/manual")
async def trigger_manual_attribute_update():
    """Manually trigger attribute update for all missing stocks"""
    try:
        await attribute_poller.run_manual_attribute_update()
        return {"message": "Manual attribute update triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering manual attribute update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/attributes-update/specific")
async def trigger_specific_attribute_update(stocks: List[str]):
    """Manually trigger attribute update for specific stocks"""
    try:
        await attribute_poller.run_manual_attribute_update(stocks)
        return {"message": f"Manual attribute update triggered for {len(stocks)} stocks"}
    except Exception as e:
        logger.error(f"Error triggering specific attribute update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attributes-update/status")
async def get_attribute_update_status():
    """Get current attribute update status"""
    try:
        return attribute_poller.get_attribute_status()
    except Exception as e:
        logger.error(f"Error getting attribute update status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/attributes-update/reset-retries")
async def reset_attribute_retries():
    """Reset retry counts for all stocks to allow fresh attribute fetching"""
    try:
        reset_count = await attribute_poller.reset_all_attribute_retries()
        return {
            "message": f"Reset retry counts for {reset_count} stocks",
            "reset_count": reset_count
        }
    except Exception as e:
        logger.error(f"Error resetting attribute retries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Different port for data service
        reload=True
    )
