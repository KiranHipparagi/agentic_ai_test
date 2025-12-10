from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from database.postgres_db import get_db, Metrics, WeatherData, EventsData
from sqlalchemy import func
from core.logger import logger

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class DataUploadRequest(BaseModel):
    data_type: str  # "sales", "inventory", "weather", "events"
    records: List[Dict[str, Any]]


@router.post("/ingest")
async def ingest_data(request: DataUploadRequest):
    """Ingest data into PostgreSQL database - NOTE: Data is already loaded, this endpoint is for reference only"""
    try:
        return {
            "status": "info",
            "message": "Data ingestion is not needed - all data is already loaded in planalytics_database",
            "note": "Use the PostgreSQL database directly. Tables: calendar, events, location, metrics, perishable, product_hierarchy, weekly_weather"
        }
        
    except Exception as e:
        logger.error(f"Data ingestion endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database-stats")
async def get_database_stats():
    """Get PostgreSQL database statistics for planalytics_database"""
    try:
        with get_db() as db:
            stats = {
                "events_count": db.query(func.count(EventsData.id)).scalar(),
                "weather_count": db.query(func.count(WeatherData.id)).scalar(),
                "metrics_count": db.query(func.count(Metrics.id)).scalar()
            }
        
        return {
            "database": "PostgreSQL (planalytics_database)",
            "connection": "active",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/{product_id}")
async def get_forecast(product_id: str, location_id: str, days: int = 14):
    """Get demand forecast for a product"""
    return {
        "product_id": product_id,
        "location_id": location_id,
        "forecast_days": days,
        "forecast": [{"day": i, "predicted_demand": 100 + i * 5} for i in range(days)]
    }
