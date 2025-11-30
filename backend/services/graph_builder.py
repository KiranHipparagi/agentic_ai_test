from typing import Dict, Any
from database.neo4j_db import neo4j_conn
from database.postgres_db import get_db, SalesData, WeatherData, EventsData  # ✅ Changed
from core.logger import logger
from sqlalchemy import func


class GraphBuilderService:
    """Service for building knowledge graphs in Neo4j"""
    
    def build_supply_chain_graph(self, product_id: str, location_id: str) -> bool:
        """Build complete supply chain graph for product-location pair"""
        try:
            if not neo4j_conn.ensure_connected():
                logger.warning("Neo4j unavailable - skipping graph building")
                return False
                
            with get_db() as db:
                # Get latest weather
                weather = db.query(WeatherData).filter(
                    WeatherData.location_id == location_id
                ).order_by(WeatherData.timestamp.desc()).first()
                
                # Get upcoming events
                event = db.query(EventsData).filter(
                    EventsData.location_id == location_id
                ).order_by(EventsData.start_date).first()
                
                # Calculate weather impact
                weather_impact = self._calculate_weather_impact(weather) if weather else 0.5
                event_impact = 0.6 if event else 0.1
            
            # Create graph relationships
            graph_data = {
                "product_id": product_id,
                "product_name": f"Product_{product_id}",
                "location_id": location_id,
                "location_name": f"Location_{location_id}",
                "weather_conditions": weather.conditions if weather else "unknown",
                "temperature": weather.temperature if weather else 20.0,
                "event_name": event.event_name if event else "none",
                "event_type": event.event_type if event else "none",
                "weather_impact": weather_impact,
                "event_impact": event_impact
            }
            
            neo4j_conn.create_supply_chain_graph(graph_data)
            logger.info(f"Built supply chain graph for {product_id} at {location_id}")
            return True
            
        except Exception as e:
            logger.error(f"Graph building failed: {e}")
            return False
    
    def _calculate_weather_impact(self, weather: WeatherData) -> float:
        """Calculate normalized weather impact coefficient"""
        impact = 0.5
        if weather.temperature < 0 or weather.temperature > 35:
            impact += 0.2
        if weather.precipitation > 50:
            impact += 0.2
        if "severe" in weather.conditions.lower():
            impact += 0.3
        return min(impact, 1.0)


# Global graph builder
graph_builder = GraphBuilderService()
