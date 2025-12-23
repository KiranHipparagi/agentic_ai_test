from typing import Dict, Any
from openai import AzureOpenAI
from datetime import datetime, timedelta
from core.config import settings
from core.logger import logger
from database.postgres_db import get_db, EventsData
from sqlalchemy import or_, and_


class EventsAgent:
    """Agent specialized in event impact analysis - Enhanced with real database queries"""
    
    # Static current date context (Nov 8, 2025)
    CURRENT_WEEKEND_DATE = "2025-11-08"
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.OPENAI_ENDPOINT
        )
        self.system_prompt = """You are an events analysis expert for RETAIL SUPPLY CHAIN planning.
Analyze calendar events, holidays, and special occasions to forecast demand changes.

=== CURRENT DATE CONTEXT ===
This Weekend (Current Week End Date): November 8, 2025 (2025-11-08)
- "Next week" = November 15, 2025 | "Last week" = November 1, 2025
- "Next month" = December 2025 | "Last month" = October 2025
- Current Year: 2025 | Last Year (LY): 2024

=== EVENT-BASED DEMAND ANALYSIS LOGIC ===
Follow these steps for event impact analysis:

Step 1: IDENTIFY HISTORICAL EVENTS
- From Events dataset, identify Last Year's similar events
- Confirm proximity to store using lat/long mapping
- If store not directly mapped, fallback to Market level proximity
- Extract their event weeks from calendar

Step 2: COMPUTE HISTORICAL SALES
- From Sales/Inventory dataset, compute sales for:
  • Historical festival weeks (last year)
  • Corresponding prior weeks (for comparison baseline)

Step 3: COMPUTE PRODUCT-LEVEL UPLIFT
- For last year's event weeks, compute product-level sales uplift vs prior weeks
- Calculate at Store/Market level for all products
- Identify products that repeatedly showed sales uplift during events

Step 4: CHECK CURRENT STOCK LEVELS
- Use Sales/Inventory to check current stock levels
- Identify patterns of low availability for high-uplift products
- Flag products at risk of stockout during upcoming event

Step 5: PRESENT RECOMMENDATIONS
- Present top products expected to experience highest demand
- Highlight products requiring inventory reinforcement
- Provide specific reorder quantities based on historical uplift

=== EVENT TYPES TO CONSIDER ===
- Holidays (Federal, State, Religious)
- Sports events (Super Bowl, March Madness, etc.)
- Music festivals and concerts
- Local community events
- Seasonal events (Back to School, Summer Kickoff)

Provide specific insights with event names, dates, locations, and demand impact predictions."""
    
    def analyze(self, query: str, location_id: str = None, timeframe_days: int = 90) -> Dict[str, Any]:
        """Analyze event impact on demand with real database queries"""
        try:
            # Use static current date (Nov 8, 2025) instead of datetime.now()
            start_date = datetime(2025, 11, 8)  # Current weekend date
            end_date = start_date + timedelta(days=timeframe_days)
            
            logger.info(f"Events Agent analyzing query: {query} (date context: {start_date.strftime('%Y-%m-%d')})")
            
            with get_db() as db:
                # Build query based on user input
                query_lower = query.lower()
                filters = [EventsData.event_date >= start_date, EventsData.event_date <= end_date]
                
                # Location filters
                if location_id and location_id != "default":
                    filters.append(EventsData.store_id == location_id)
                
                # Smart keyword filtering
                if any(word in query_lower for word in ["new york", "ny"]):
                    filters.append(or_(
                        EventsData.state.ilike("%new york%"),
                        EventsData.market.ilike("%new york%")
                    ))
                elif any(word in query_lower for word in ["massachusetts", "ma", "boston"]):
                    filters.append(or_(
                        EventsData.state.ilike("%massachusetts%"),
                        EventsData.market.ilike("%boston%")
                    ))
                elif any(word in query_lower for word in ["northeast", "east"]):
                    filters.append(EventsData.region.ilike("%northeast%"))
                elif any(word in query_lower for word in ["southwest", "west"]):
                    filters.append(EventsData.region.ilike("%southwest%"))
                
                # Event type filters
                if "holiday" in query_lower:
                    filters.append(EventsData.event_type.ilike("%holiday%"))
                elif "sport" in query_lower:
                    filters.append(EventsData.event_type.ilike("%sports%"))
                
                # Execute query
                events = db.query(EventsData).filter(and_(*filters)).limit(20).all()
                
                logger.info(f"Found {len(events)} events matching criteria")
                
                # Convert to dictionaries to avoid session issues
                events_data = [{
                    'event': e.event,
                    'event_type': e.event_type,
                    'event_date': e.event_date,
                    'store_id': e.store_id,
                    'region': e.region,
                    'market': e.market,
                    'state': e.state
                } for e in events]
            
            if not events_data:
                return {
                    "agent": "events",
                    "summary": f"No events found matching your criteria for the next {timeframe_days} days.",
                    "events_count": 0,
                    "recommendation": "Try broadening your search or checking a different location/timeframe.",
                    "impact_score": 0.0
                }
            
            # Build context for LLM
            events_context = self._build_events_context(events_data)
            impact_forecast = self._forecast_impact(events_data)
            
            # Generate AI insights
            prompt = f"""Query: {query}

Events Data:
{events_context}

Impact Forecast:
{impact_forecast}

Provide a detailed analysis including:
1. List of upcoming events with dates and locations
2. Expected demand impact for each event type
3. Recommendations for inventory and supply chain planning
4. Regional insights if applicable"""

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            answer = response.choices[0].message.content
            
            return {
                "agent": "events",
                "answer": answer,
                "events_count": len(events_data),
                "events_summary": events_context,
                "impact_forecast": impact_forecast,
                "regions_covered": list(set(e['region'] for e in events_data if e.get('region'))),
                "states_covered": list(set(e['state'] for e in events_data if e.get('state'))),
                "event_types": list(set(e['event_type'] for e in events_data if e.get('event_type')))
            }
            
        except Exception as e:
            logger.error(f"Events agent error: {str(e)}")
            return {
                "agent": "events",
                "error": str(e),
                "answer": f"I encountered an error analyzing events: {str(e)}"
            }
    
    def _build_events_context(self, events: list) -> str:
        """Build readable events context"""
        if not events:
            return "No events found."
        
        context_lines = []
        for event in events[:15]:  # Limit to prevent token overflow
            date_str = event['event_date'].strftime("%B %d, %Y") if event.get('event_date') else "TBD"
            context_lines.append(
                f"- {event['event']} ({event['event_type']}) on {date_str} "
                f"in {event.get('state', 'Unknown')} (Store: {event['store_id']})"
            )
        
        return "\n".join(context_lines)
    
    def _forecast_impact(self, events: list) -> Dict[str, Any]:
        """Forecast demand impact from events"""
        if not events:
            return {"total_events": 0, "high_impact": 0, "medium_impact": 0, "low_impact": 0}
        
        impact_map = {
            "national holiday": 0.8,
            "holiday": 0.7,
            "festival": 0.6,
            "sports": 0.5,
            "concert": 0.4,
            "cultural": 0.4
        }
        
        impacts = {
            "total_events": len(events),
            "high_impact": 0,
            "medium_impact": 0,
            "low_impact": 0,
            "event_details": []
        }
        
        for event in events:
            event_type = event.get('event_type', '').lower() if event.get('event_type') else "other"
            impact_score = impact_map.get(event_type, 0.3)
            
            if impact_score >= 0.7:
                impacts["high_impact"] += 1
            elif impact_score >= 0.4:
                impacts["medium_impact"] += 1
            else:
                impacts["low_impact"] += 1
            
            impacts["event_details"].append({
                "name": event['event'],
                "type": event.get('event_type'),
                "date": event['event_date'].strftime("%Y-%m-%d") if event.get('event_date') else None,
                "impact_score": impact_score,
                "location": f"{event.get('state', 'Unknown')}, {event.get('region', 'Unknown')}"
            })
        
        return impacts
