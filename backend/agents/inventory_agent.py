from typing import Dict, Any
from openai import AzureOpenAI
from core.config import settings
from core.logger import logger
from database.postgres_db import get_db, InventoryData
from sqlalchemy import desc, func
from datetime import datetime, timedelta


class InventoryAgent:
    """Agent specialized in inventory optimization and demand forecasting"""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.OPENAI_ENDPOINT
        )
        self.system_prompt = """You are an inventory optimization expert.
        Analyze stock levels, sales trends, and forecast demand to prevent stockouts and overstock.
        Provide actionable recommendations for reorder points and quantities."""
    
    def analyze(self, query: str, product_id: str, location_id: str) -> Dict[str, Any]:
        """Analyze inventory and forecast demand"""
        try:
            with get_db() as db:
                # Get current inventory
                inventory = db.query(InventoryData).filter(
                    InventoryData.product_id == int(product_id),
                    InventoryData.store_id == location_id
                ).order_by(desc(InventoryData.end_date)).first()
                
                if not inventory:
                    return {
                        "status": "no_data",
                        "message": f"No inventory data for product {product_id} at location {location_id}"
                    }
                
                # Calculate average daily sales from inventory.sales_units
                sales_data = db.query(
                    func.avg(InventoryData.sales_units).label('avg_sales')
                ).filter(
                    InventoryData.product_id == int(product_id),
                    InventoryData.store_id == location_id
                ).first()
                
                avg_daily = float(sales_data.avg_sales or 0) / 7  # Weekly to daily
                
                # Generate forecast
                forecast = self._forecast_demand(avg_daily)
                
                # Build context
                context = f"""Inventory Analysis for Product {product_id} at {location_id}:
                Current Stock: {inventory.end_on_hand_units} units
                Base Stock Level: {inventory.base_stock_units} units
                Days of Supply: {inventory.days_of_supply_end:.1f} days
                Stock Status: {inventory.stock_status}
                Average Weekly Sales: {avg_daily * 7:.0f} units
                Forecasted Demand (7 days): {forecast['next_7_days']:.0f} units
                Forecasted Demand (14 days): {forecast['next_14_days']:.0f} units
                Forecasted Demand (30 days): {forecast['next_30_days']:.0f} units
                """
                
                # Get LLM recommendations
                response = self.client.chat.completions.create(
                    model=settings.OPENAI_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"{query}\n\n{context}"}
                    ],
                    max_tokens=500
                )
                
                return {
                    "status": "success",
                    "analysis": response.choices[0].message.content,
                    "current_stock": inventory.end_on_hand_units,
                    "days_of_supply": inventory.days_of_supply_end,
                    "stock_status": inventory.stock_status,
                    "forecast": forecast,
                    "recommendation": self._generate_recommendation(inventory, avg_daily)
                }
                
        except Exception as e:
            logger.error(f"Inventory analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _forecast_demand(self, avg_daily: float, days: int = 14) -> Dict[str, float]:
        """Simple demand forecast"""
        return {
            "next_7_days": avg_daily * 7,
            "next_14_days": avg_daily * 14,
            "next_30_days": avg_daily * 30
        }
    
    def _generate_recommendation(self, inventory, avg_daily: float) -> str:
        """Generate inventory recommendation"""
        if not inventory or avg_daily == 0:
            return "Insufficient data for recommendations"
        
        days_of_supply = inventory.days_of_supply_end or 0
        
        if days_of_supply < 7:
            return f"⚠️ URGENT: Only {days_of_supply:.1f} days of supply remaining. Recommend immediate reorder of {int(avg_daily * 14)} units."
        elif days_of_supply < 14:
            return f"⚡ LOW STOCK: {days_of_supply:.1f} days of supply. Consider reordering {int(avg_daily * 14)} units soon."
        elif days_of_supply > 60:
            return f"📦 OVERSTOCK: {days_of_supply:.1f} days of supply. Consider reducing inventory levels."
        else:
            return f"✅ HEALTHY: {days_of_supply:.1f} days of supply. Stock levels are optimal."
