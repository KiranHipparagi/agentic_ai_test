from typing import Dict, Any, List
from openai import AzureOpenAI
from core.config import settings
from core.logger import logger
from database.gremlin_db import gremlin_conn


class LocationAgent:
    """Agent specialized in location-based analysis"""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.OPENAI_ENDPOINT
        )
        self.system_prompt = """You are a location intelligence expert for supply chains.
        Analyze geographical factors, regional patterns, and location-specific trends.
        Consider: demographics, infrastructure, proximity to suppliers, and regional preferences."""
    
    def analyze(self, query: str, location_id: str) -> Dict[str, Any]:
        """Analyze location-specific factors"""
        try:
            # Query Gremlin for location relationships
            location_data = []
            if gremlin_conn.ensure_connected():
                location_data = gremlin_conn.query_supply_chain_impact("", location_id)
            else:
                logger.warning("Gremlin unavailable - using limited location analysis")
            
            context = self._build_location_context(location_data)
            
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Query: {query}\n\nLocation Context:\n{context}"}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return {
                "agent": "location",
                "analysis": response.choices[0].message.content,
                "location_data": location_data,
                "regional_factors": self._extract_factors(location_data),
                "gremlin_available": gremlin_conn._connected
            }
        except Exception as e:
            logger.error(f"Location analysis failed: {e}")
            return {"agent": "location", "error": str(e)}
    
    def _build_location_context(self, data: List[Dict]) -> str:
        """Build readable location context"""
        if not data:
            return "No graph data available. Using basic location analysis."
        return f"Location analysis with {len(data)} connected factors"
    
    def _extract_factors(self, data: List[Dict]) -> Dict[str, Any]:
        """Extract key location factors"""
        return {
            "weather_impact": data[0].get("weather_impact", 0) if data else 0,
            "event_impact": data[0].get("event_impact", 0) if data else 0
        }
