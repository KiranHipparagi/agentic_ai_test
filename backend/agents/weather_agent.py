from typing import Dict, Any
from openai import AzureOpenAI
from core.config import settings
from core.logger import logger
from database.postgres_db import get_db, WeatherData
from sqlalchemy import desc


class WeatherAgent:
    """Agent specialized in weather data analysis and impact assessment"""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.OPENAI_ENDPOINT
        )
        self.system_prompt = """You are a weather analysis expert for supply chain operations.
        Analyze weather data and provide insights on potential supply chain impacts.
        Focus on: temperature extremes, precipitation, severe conditions, and seasonal patterns."""
    
    def analyze(self, query: str, location_id: str) -> Dict[str, Any]:
        """Analyze weather impact on supply chain"""
        try:
            # Fetch recent weather data (location_id is the store_id in weather table)
            with get_db() as db:
                weather_records = db.query(WeatherData).filter(
                    WeatherData.store_id == location_id
                ).order_by(desc(WeatherData.week_end_date)).limit(10).all()
            
            if not weather_records:
                return {
                    "agent": "weather",
                    "analysis": f"No weather data available for location {location_id}",
                    "data": [],
                    "impact_score": 0.0
                }
            
            weather_context = "\n".join([
                f"Week Ending: {w.week_end_date}, Avg Temp: {w.avg_temp_f}°F, " +
                f"Temp Anomaly: {w.temp_anom_f}°F, Precip: {w.precip_in} in, " +
                f"Flags: Heatwave={w.heatwave_flag}, Cold={w.cold_spell_flag}, " +
                f"Heavy Rain={w.heavy_rain_flag}, Snow={w.snow_flag}"
                for w in weather_records
            ])
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Query: {query}\n\nWeather Data:\n{weather_context}"}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "agent": "weather",
                "analysis": analysis,
                "data": [
                    {
                        "week_end_date": str(w.week_end_date), 
                        "avg_temp_f": w.avg_temp_f,
                        "temp_anom_f": w.temp_anom_f,
                        "precip_in": w.precip_in,
                        "heatwave": w.heatwave_flag,
                        "cold_spell": w.cold_spell_flag,
                        "heavy_rain": w.heavy_rain_flag,
                        "snow": w.snow_flag
                    } 
                    for w in weather_records[:5]
                ],
                "impact_score": self._calculate_impact(weather_records)
            }
        except Exception as e:
            logger.error(f"Weather analysis failed: {e}")
            return {"agent": "weather", "error": str(e)}
    
    def _calculate_impact(self, weather_records: list) -> float:
        """Calculate weather impact score (0-1)"""
        if not weather_records:
            return 0.0
        
        impact = 0.0
        for w in weather_records:
            # Temperature extremes (above 90F or below 32F)
            if w.tmax_f and (w.tmax_f > 90 or w.tmax_f < 32):
                impact += 0.2
            # Heavy precipitation (> 1 inch)
            if w.precip_in and w.precip_in > 1.0:
                impact += 0.15
            # Extreme weather flags
            if w.heatwave_flag:
                impact += 0.3
            if w.cold_spell_flag:
                impact += 0.3
            if w.heavy_rain_flag:
                impact += 0.25
            if w.snow_flag:
                impact += 0.3
        
        return min(impact / len(weather_records), 1.0)
