"""Context Resolver Service - Combines Azure Search entity resolution with Neo4j graph expansion"""
from typing import Dict, Any, List, Optional
from database.azure_search import azure_search
from database.neo4j_db import Neo4jConnection
from core.logger import logger


class ContextResolver:
    """
    Hybrid context resolution using Azure AI Search + Neo4j Knowledge Graph
    
    Workflow:
    1. Azure Search: Resolve vague terms to exact IDs (e.g., "Pepsi" → product_id)
    2. Neo4j Graph: Expand context via relationships (e.g., find all products in same category)
    3. Return enriched context for SQL generation
    """
    
    def __init__(self):
        self.search = azure_search
        self.graph = Neo4jConnection()
    
    def resolve_query_context(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point: Resolve full context from natural language query
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            {
                "products": {
                    "resolved": [...],  # From Azure Search
                    "expanded": [...]   # From Neo4j graph
                },
                "locations": {
                    "resolved": [...],
                    "expanded": [...]
                },
                "dates": {
                    "resolved": [...],
                    "date_range": (start, end)
                },
                "events": {
                    "resolved": [...],
                    "related_events": [...]
                },
                "metadata": {
                    "sales_coverage": [...],
                    "weather_coverage": [...],
                    "available_metrics": [...]
                }
            }
        """
        logger.info(f"🔍 Resolving context for query: {user_query}")
        
        # Step 1: Entity resolution via Azure Search
        entities = self.search.resolve_entities(user_query)
        
        # Step 2: Context expansion via Neo4j
        expanded_context = self._expand_context_via_graph(entities)
        
        # Step 3: Get metadata context
        metadata = self.search.get_schema_context(user_query)
        
        # Step 4: Combine everything
        full_context = {
            "products": {
                "resolved": entities.get("products", []),
                "expanded": expanded_context.get("expanded_products", [])
            },
            "locations": {
                "resolved": entities.get("locations", []),
                "expanded": expanded_context.get("expanded_locations", [])
            },
            "dates": {
                "resolved": entities.get("dates", []),
                "date_range": self._extract_date_range(entities.get("dates", []))
            },
            "events": {
                "resolved": entities.get("events", []),
                "related_events": expanded_context.get("related_events", [])
            },
            "metadata": metadata
        }
        
        logger.info(f"✅ Context resolved successfully")
        return full_context
    
    def _expand_context_via_graph(self, entities: Dict[str, List]) -> Dict[str, Any]:
        """Expand entity context using Neo4j knowledge graph relationships"""
        if not self.graph.ensure_connected():
            logger.warning("Neo4j unavailable, skipping graph expansion")
            return {
                "expanded_products": [],
                "expanded_locations": [],
                "related_events": []
            }
        
        expanded = {}
        
        # Expand products via category hierarchy
        product_ids = [p.get("id") for p in entities.get("products", []) if p.get("id")]
        if product_ids:
            expanded["expanded_products"] = self.graph.expand_product_context(product_ids)
        else:
            expanded["expanded_products"] = []
        
        # Expand locations via geographic hierarchy
        location_ids = [l.get("id") for l in entities.get("locations", []) if l.get("id")]
        if location_ids:
            expanded["expanded_locations"] = self.graph.expand_location_context(location_ids)
        else:
            expanded["expanded_locations"] = []
        
        # Find related events
        date_list = [d.get("date") for d in entities.get("dates", []) if d.get("date")]
        if date_list and location_ids:
            expanded["related_events"] = self.graph.find_related_events(location_ids, date_list)
        else:
            expanded["related_events"] = []
        
        return expanded
    
    def _extract_date_range(self, dates: List[Dict]) -> Optional[tuple]:
        """Extract min/max date range from calendar results"""
        if not dates:
            return None
        
        date_values = [d.get("date") for d in dates if d.get("date")]
        if not date_values:
            return None
        
        return (min(date_values), max(date_values))
    
    def get_sql_generation_prompt(self, user_query: str, context: Dict[str, Any]) -> str:
        """
        Generate a comprehensive prompt for SQL generation with full context
        
        This replaces the hardcoded schema prompt in database_agent.py
        """
        prompt_parts = []
        
        # User query
        prompt_parts.append(f"User Query: {user_query}\n")
        
        # Products context
        products = context.get("products", {})
        if products.get("resolved"):
            # Use 'product' field (fallback to 'product_name' or 'id')
            # Include category info to help LLM generalize
            product_info = []
            for p in products["resolved"][:5]:
                name = p.get("product", p.get("product_name", p.get("id", "Unknown")))
                cat = p.get("category", "Unknown")
                product_info.append(f"{name} (Category: {cat})")
            
            product_ids = [p.get("product_id", p.get("id")) for p in products["resolved"][:10]]
            
            prompt_parts.append(f"Relevant Products: {', '.join(product_info)}")
            prompt_parts.append(f"Product IDs (for specific item queries): {product_ids}")
            prompt_parts.append("NOTE: If user asks about a Category listed above, filter by 'category' column, NOT by Product IDs.\n")
        
        if products.get("expanded"):
            expanded_ids = [p.get("product_id") for p in products["expanded"][:20]]
            prompt_parts.append(f"Related Products (from same category): {len(expanded_ids)} products")
            prompt_parts.append(f"Expanded Product IDs: {expanded_ids}\n")
        
        # Locations context
        locations = context.get("locations", {})
        if locations.get("resolved"):
            # Use 'location' field (fallback to 'store_name' or 'id')
            location_names = [l.get("location", l.get("store_name", l.get("id", "Unknown"))) for l in locations["resolved"][:5]]
            location_ids = [l.get("id") for l in locations["resolved"][:20]]
            prompt_parts.append(f"Relevant Locations: {', '.join(str(x) for x in location_names)}")
            prompt_parts.append(f"Store IDs to filter: {location_ids}\n")
        
        if locations.get("expanded"):
            expanded_ids = [l.get("store_id") for l in locations["expanded"][:50]]
            prompt_parts.append(f"Related Locations (same region/market): {len(expanded_ids)} stores")
            prompt_parts.append(f"Expanded Store IDs: {expanded_ids}\n")
        
        # Date context
        dates = context.get("dates", {})
        if dates.get("date_range"):
            start_date, end_date = dates["date_range"]
            prompt_parts.append(f"Date Range: {start_date} to {end_date}\n")
        elif dates.get("resolved"):
            date_samples = [d.get("date") for d in dates["resolved"][:5]]
            prompt_parts.append(f"Relevant Dates: {date_samples}\n")
        
        # Events context
        events = context.get("events", {})
        if events.get("resolved"):
            # Use 'event' field (fallback to 'event_name')
            event_names = [e.get("event", e.get("event_name", "Unknown Event")) for e in events["resolved"][:5]]
            prompt_parts.append(f"Relevant Events: {', '.join(str(x) for x in event_names)}\n")
        
        # Database schema (dynamic based on query needs)
        prompt_parts.append("\nAvailable Database Tables:")
        prompt_parts.append("""
- metrics (product, location, end_date, metric, metric_nrm, metric_ly, product_id) -- SALES DATA
  * 'metric' = WDD Metric (Weather Driven Demand)
  * 'metric_nrm' = Normal Metric
  * 'metric_ly' = Last Year Metric (New addition)
  * DO NOT filter by metric='sales' - metric IS the value!
  
- inventory (store_id, product_id, end_date, begin_on_hand_units, received_units, 
             sales_units, end_on_hand_units, base_stock_units, days_of_supply_end, stock_status)
  
- weather (week_end_date, store_id, avg_temp_f, temp_anom_f, tmax_f, tmin_f, 
           precip_in, heatwave_flag, cold_spell_flag, heavy_rain_flag, snow_flag)
  
- events (event, event_type, event_date, store_id, region, market, state)

- locdim (location, region, market, state, latitude, longitude)

- phier (product_id, dept, category, product, unit_price, uom, storage)

- cal (year, quarter, month, week, end_date)

NEW FORMULAS (Apply these logic):
1. Short Term Planning (< 4 weeks): Use WDD vs Normal
   Formula: (SUM(metric) - SUM(metric_nrm)) / NULLIF(SUM(metric_nrm), 0)
2. Long Term Planning (> 4 weeks) & Historical: Use WDD vs LY
   Formula: (SUM(metric) - SUM(metric_ly)) / NULLIF(SUM(metric_ly), 0)

SEASONS DEFINITION:
- Spring: Feb, Mar, Apr
- Summer: May, Jun, Jul
- Fall: Aug, Sep, Oct
- Winter: Nov, Dec, Jan
""")
        
        # SQL generation instructions
        prompt_parts.append("""
IMPORTANT SQL GENERATION RULES:
1. Use PostgreSQL syntax (LIMIT not TOP, || for concat)
2. For sales data, query the 'metrics' table and use SUM(metric), SUM(metric_nrm), or SUM(metric_ly) based on the formulas above.
3. Join metrics with locdim on location field
4. Join metrics with phier on product_id
5. Filter using the Product IDs and Store IDs provided above
6. Include descriptive columns (product names, store names, states) in results
7. Use appropriate aggregations (SUM, AVG, COUNT) with GROUP BY
8. Add ORDER BY for meaningful sorting
9. Always include LIMIT clause (max 100 rows)
10. Return ONLY the SQL query, no explanation

Generate the PostgreSQL SELECT query:
""")
        
        return "\n".join(prompt_parts)
    
    def format_context_summary(self, context: Dict[str, Any]) -> str:
        """Format context as human-readable summary for debugging/logging"""
        summary = []
        
        products = context.get("products", {})
        if products.get("resolved"):
            summary.append(f"✓ {len(products['resolved'])} products identified")
        if products.get("expanded"):
            summary.append(f"✓ Expanded to {len(products['expanded'])} related products")
        
        locations = context.get("locations", {})
        if locations.get("resolved"):
            summary.append(f"✓ {len(locations['resolved'])} locations identified")
        if locations.get("expanded"):
            summary.append(f"✓ Expanded to {len(locations['expanded'])} stores")
        
        dates = context.get("dates", {})
        if dates.get("date_range"):
            summary.append(f"✓ Date range: {dates['date_range'][0]} to {dates['date_range'][1]}")
        
        events = context.get("events", {})
        if events.get("resolved"):
            summary.append(f"✓ {len(events['resolved'])} events found")
        
        return " | ".join(summary) if summary else "No specific context resolved"


# Global instance
context_resolver = ContextResolver()
