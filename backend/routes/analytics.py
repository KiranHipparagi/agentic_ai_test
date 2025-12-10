from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from database.postgres_db import get_db, Metrics, WeatherData, ProductHierarchy
from sqlalchemy import func, desc, or_, cast, Date
from core.logger import logger

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class KPIResponse(BaseModel):
    total_sales: float
    total_revenue: float
    avg_stock_level: float
    low_stock_items: int
    period: str


@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(
    days: int = Query(30, ge=1, le=365),
    location_id: Optional[str] = None
):
    """Get key performance indicators"""
    try:
        with get_db() as db:
            # Query metrics table for sales data (Metrics IS the sales table)
            sales_query = db.query(
                func.sum(Metrics.metric).label('total_sales')
            )
            
            if location_id:
                sales_query = sales_query.filter(Metrics.location == location_id)
            
            sales_result = sales_query.first()
            
            # Calculate revenue by joining with product prices
            # Join using product name (metrics.product = phier.product)
            revenue_query = db.query(
                func.sum(Metrics.metric * ProductHierarchy.unit_price).label('total_revenue')
            ).join(
                ProductHierarchy, Metrics.product == ProductHierarchy.product
            )
            
            if location_id:
                revenue_query = revenue_query.filter(Metrics.location == location_id)
            
            revenue_result = revenue_query.first()
            
            # Query inventory for stock levels
            # Note: end_on_hand_units is TIMESTAMP in schema, use begin_on_hand_units instead
            inventory_query = db.query(
                func.avg(InventoryData.begin_on_hand_units).label('avg_stock')
            )
            
            if location_id:
                inventory_query = inventory_query.filter(InventoryData.store_id == location_id)
            
            inventory_result = inventory_query.first()
            
            # Count low stock items based on stock_status field
            low_stock = db.query(func.count(InventoryData.store_id)).filter(
                InventoryData.stock_status.in_(['Critical', 'Low', 'Out of Stock'])
            )
            
            if location_id:
                low_stock = low_stock.filter(InventoryData.store_id == location_id)
            
            low_stock_count = low_stock.scalar() or 0
        
        return KPIResponse(
            total_sales=float(sales_result.total_sales or 0),
            total_revenue=float(revenue_result.total_revenue or 0),
            avg_stock_level=float(inventory_result.avg_stock or 0),
            low_stock_items=low_stock_count,
            period=f"Last {days} days"
        )
        
    except Exception as e:
        logger.error(f"KPI calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/sales")
async def get_sales_trends(
    product_id: Optional[str] = None,
    location_id: Optional[str] = None,
    days: int = Query(30, ge=1, le=365)
):
    """Get sales trends over time"""
    try:
        with get_db() as db:
            # Query metrics table (contains sales data)
            query = db.query(
                Metrics.end_date,
                func.sum(Metrics.metric).label('quantity'),
                func.sum(Metrics.metric * ProductHierarchy.unit_price).label('revenue')
            ).join(
                ProductHierarchy, Metrics.product_id == ProductHierarchy.product_id
            ).group_by(Metrics.end_date).order_by(desc(Metrics.end_date)).limit(days)
            
            if product_id:
                query = query.filter(Metrics.product_id == int(product_id))
            if location_id:
                query = query.filter(Metrics.location == location_id)
            
            results = query.all()
            
            return {
                "data": [
                    {
                        "date": str(r.end_date),
                        "quantity": float(r.quantity or 0),
                        "revenue": float(r.revenue or 0)
                    }
                    for r in reversed(results)  # Reverse to show chronological order
                ],
                "product_id": product_id,
                "location_id": location_id,
                "period": f"Last {days} records"
            }
        
    except Exception as e:
        logger.error(f"Sales trends query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather-impact")
async def get_weather_impact(location_id: str, days: int = Query(30, ge=1, le=90)):
    """Analyze weather impact on sales"""
    try:
        with get_db() as db:
            # Query weather data for the store
            weather_data = db.query(WeatherData).filter(
                WeatherData.store_id == location_id
            ).order_by(desc(WeatherData.week_end_date)).limit(days).all()
        
        impact_analysis = {
            "location_id": location_id,
            "period_days": days,
            "weather_records": len(weather_data),
            "conditions": [
                {
                    "date": str(w.week_end_date.date()) if w.week_end_date else None,
                    "avg_temp_f": float(w.avg_temp_f or 0),
                    "temp_anom_f": float(w.temp_anom_f or 0),
                    "precip_in": float(w.precip_in or 0),
                    "heatwave": bool(w.heatwave_flag),
                    "cold_spell": bool(w.cold_spell_flag),
                    "heavy_rain": bool(w.heavy_rain_flag),
                    "snow": bool(w.snow_flag)
                }
                for w in weather_data
            ]
        }
        
        return impact_analysis
        
    except Exception as e:
        logger.error(f"Weather impact analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
