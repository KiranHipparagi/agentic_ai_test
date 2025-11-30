from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from database.postgres_db import get_db, SalesData, InventoryData, WeatherData, EventsData
from sqlalchemy import func
from core.logger import logger

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class DataUploadRequest(BaseModel):
    data_type: str  # "sales", "inventory", "weather", "events"
    records: List[Dict[str, Any]]


@router.post("/ingest")
async def ingest_data(request: DataUploadRequest):
    """Ingest data directly into MySQL database"""
    try:
        count = 0
        
        with get_db() as db:
            if request.data_type == "sales":
                for record in request.records:
                    db.add(SalesData(**record))
                count = len(request.records)
                
            elif request.data_type == "inventory":
                for record in request.records:
                    db.add(InventoryData(**record))
                count = len(request.records)
                
            elif request.data_type == "weather":
                for record in request.records:
                    db.add(WeatherData(**record))
                count = len(request.records)
                
            elif request.data_type == "events":
                for record in request.records:
                    db.add(EventsData(**record))
                count = len(request.records)
            else:
                raise HTTPException(status_code=400, detail=f"Invalid data_type: {request.data_type}")
        
        return {"status": "success", "records_ingested": count, "data_type": request.data_type}
        
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database-stats")
async def get_database_stats():
    """Get MySQL database statistics"""
    try:
        with get_db() as db:
            stats = {
                "events_count": db.query(func.count(EventsData.id)).scalar(),
                "weather_count": db.query(func.count(WeatherData.id)).scalar(),
                "sales_count": db.query(func.count(SalesData.id)).scalar() if hasattr(db.query, 'SalesData') else 0,
                "inventory_count": db.query(func.count(InventoryData.id)).scalar() if hasattr(db.query, 'InventoryData') else 0
            }
        
        return {
            "database": "MySQL",
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
