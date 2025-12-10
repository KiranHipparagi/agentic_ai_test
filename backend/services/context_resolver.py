"""Context Resolver Service - Combines Azure Search entity resolution with Gremlin graph expansion"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from database.azure_search import azure_search
from database.gremlin_db import gremlin_conn
from core.logger import logger


class ContextResolver:
    """
    Hybrid context resolution using Azure AI Search + Gremlin Knowledge Graph
    
    Workflow:
    1. Azure Search: Resolve vague terms to exact IDs (e.g., "Pepsi" → product_id)
    2. Gremlin Graph: Expand context via relationships (e.g., find all products in same category)
    3. Return enriched context for SQL generation
    """
    
    def __init__(self):
        self.search = azure_search
        self.graph = gremlin_conn
    
    def resolve_query_context(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point: Resolve full context from natural language query
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            {
                "products": {
                    "resolved": [...],  # From Azure Search
                    "expanded": [...]   # From Gremlin graph
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
        print("\n" + "="*80)
        print("🔎 STEP 1: CONTEXT RESOLUTION - Starting RAG Pipeline")
        print("="*80)
        print(f"📝 User Query: {user_query}")
        logger.info(f"🔍 Resolving context for query: {user_query}")
        
        # Step 1: Entity resolution via Azure Search
        print("\n🔵 STEP 1.1: Azure AI Search - Entity Resolution")
        print("-" * 80)
        entities = self.search.resolve_entities(user_query)
        
        # Detailed printing of resolved entities
        print(f"✅ Entities found:")
        if entities.get('products'):
            print(f"   • Products ({len(entities['products'])}): {[p.get('product', p.get('product_name', 'Unknown')) for p in entities['products'][:5]]}" + (f" ... (+{len(entities['products'])-5} more)" if len(entities['products']) > 5 else ""))
        else:
            print("   • Products: None")
            
        if entities.get('locations'):
            print(f"   • Locations ({len(entities['locations'])}): {[l.get('location', l.get('store_name', 'Unknown')) for l in entities['locations'][:5]]}" + (f" ... (+{len(entities['locations'])-5} more)" if len(entities['locations']) > 5 else ""))
        else:
            print("   • Locations: None")
            
        if entities.get('events'):
            print(f"   • Events ({len(entities['events'])}): {[e.get('event', e.get('event_name', 'Unknown')) for e in entities['events'][:5]]}" + (f" ... (+{len(entities['events'])-5} more)" if len(entities['events']) > 5 else ""))
        else:
            print("   • Events: None")
            
        if entities.get('dates'):
            print(f"   • Dates ({len(entities['dates'])}): {[d.get('date') for d in entities['dates'][:5]]}" + (f" ... (+{len(entities['dates'])-5} more)" if len(entities['dates']) > 5 else ""))
        else:
            print("   • Dates: None")
        
        # Step 2: Context expansion via Gremlin
        print("\n🟢 STEP 1.2: Gremlin Knowledge Graph - Context Expansion")
        print("-" * 80)
        expanded_context = self._expand_context_via_graph(entities)
        
        # Detailed printing of expanded context
        print(f"✅ Graph expansion complete:")
        if expanded_context.get('expanded_products'):
            print(f"   • Expanded Products ({len(expanded_context['expanded_products'])}): {[p.get('product_name') for p in expanded_context['expanded_products'][:5]]}" + (f" ... (+{len(expanded_context['expanded_products'])-5} more)" if len(expanded_context['expanded_products']) > 5 else ""))
        else:
            print("   • Expanded Products: None")
            
        if expanded_context.get('expanded_locations'):
            print(f"   • Expanded Locations ({len(expanded_context['expanded_locations'])}): {[l.get('store_name') for l in expanded_context['expanded_locations'][:5]]}" + (f" ... (+{len(expanded_context['expanded_locations'])-5} more)" if len(expanded_context['expanded_locations']) > 5 else ""))
        else:
            print("   • Expanded Locations: None")
        
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
        """Expand entity context using Gremlin knowledge graph relationships"""
        print("  🌐 Querying Gremlin Graph Database...")
        if not self.graph.ensure_connected():
            logger.warning("Gremlin unavailable, skipping graph expansion")
            print("  ⚠️  Gremlin Graph unavailable - skipping expansion")
            return {
                "expanded_products": [],
                "expanded_locations": [],
                "related_events": []
            }
        
        expanded = {}
        
        # Expand products via category hierarchy
        product_ids = [p.get("id") for p in entities.get("products", []) if p.get("id")]
        if product_ids:
            print(f"  📦 Expanding product context for IDs: {product_ids[:3]}...")
            expanded["expanded_products"] = self.graph.expand_product_context(product_ids)
            print(f"  ✅ Found {len(expanded['expanded_products'])} related products via graph traversal")
        else:
            expanded["expanded_products"] = []
        
        # Expand locations via geographic hierarchy
        location_ids = [l.get("id") for l in entities.get("locations", []) if l.get("id")]
        if location_ids:
            print(f"  🏢 Expanding location context for IDs: {location_ids[:3]}...")
            expanded["expanded_locations"] = self.graph.expand_location_context(location_ids)
            print(f"  ✅ Found {len(expanded['expanded_locations'])} related locations via graph traversal")
        else:
            expanded["expanded_locations"] = []
        
        # Find related events
        date_list = [d.get("date") for d in entities.get("dates", []) if d.get("date")]
        if date_list and location_ids:
            expanded["related_events"] = self.graph.find_related_events(location_ids, date_list)
        else:
            expanded["related_events"] = []
        
        return expanded
    
    def _convert_excel_date(self, val: Any) -> Any:
        """Convert Excel serial date to YYYY-MM-DD string"""
        try:
            if isinstance(val, (int, float)):
                return (datetime(1899, 12, 30) + timedelta(days=val)).strftime('%Y-%m-%d')
            elif isinstance(val, str) and val.isdigit():
                return (datetime(1899, 12, 30) + timedelta(days=int(val))).strftime('%Y-%m-%d')
            return val
        except Exception:
            return val

    def _extract_date_range(self, dates: List[Dict]) -> Optional[tuple]:
        """Extract min/max date range from calendar results"""
        if not dates:
            return None
        
        date_values = [self._convert_excel_date(d.get("date")) for d in dates if d.get("date")]
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
- metrics (id, product, location, end_date, metric, metric_nrm, metric_ly)
  * 'product' = Product name (e.g., 'Hamburgers', 'Coffee & Tea', 'Milk', 'Bacon')
  * 'location' = Store ID (e.g., 'ST0050', 'ST2900')
  * 'metric' = WDD Metric (Weather Driven Demand)
  * 'metric_nrm' = Normal Metric
  * 'metric_ly' = Last Year Metric
  * DO NOT filter by metric='sales' - metric IS the sales value!
  
- weekly_weather (id, week_end_date, avg_temp_f, temp_anom_f, tmax_f, tmin_f, 
                  precip_in, precip_anom_in, heatwave_flag, cold_spell_flag, heavy_rain_flag, snow_flag, store_id)
  * week_end_date = DATE (not TIMESTAMP)
  * store_id links to location.location
  * All flags are BOOLEAN
  
- events (id, event, event_type, event_date, store_id, region, market, state)
  * event = Event name (e.g., 'Memorial Day', 'Black Friday')
  * event_type = Type of event (e.g., 'National Holiday', 'Sporting Event')
  * event_date = DATE (not TIMESTAMP)
  * store_id links to location.location

- location (id, location, region, market, state, latitude, longitude)
  * location = Store ID (primary key, e.g., 'ST6111')
  * region = Geographic region (e.g., 'eastern north central', 'southeast')
  * market = Market area (e.g., 'chicago, il', 'dallas, tx')
  * state = State name (lowercase, e.g., 'illinois', 'texas')

- product_hierarchy (product_id, dept, category, product)
  * product_id = Numeric product identifier (1-37)
  * product = Product name (e.g., 'Hamburgers', 'Pizza', 'Sandwiches')
  * category = Product category (e.g., 'QSR', 'Perishable')
  * dept = Department (e.g., 'Fast Food', 'Grocery')

- perishable (id, product, perishable_id, min_period, max_period, period_metric, storage)
  * product = Perishable product name (e.g., 'Bacon', 'Eggs', 'Milk', 'Lettuce')
  * perishable_id = Identifier for perishable item
  * min_period, max_period = Shelf life range
  * period_metric = Time unit (e.g., 'Days', 'Weeks', 'Months')
  * storage = Storage requirement (e.g., 'Refrigerate', 'Freeze', 'Pantry')

- calendar (id, end_date, year, quarter, month, week, season)
  * end_date = DATE (primary date field)
  * week = Week number (1-53)
  * season = Spring, Summer, Fall, Winter
  * All DATE fields are type DATE (not TIMESTAMP)

- sales (id, batch_id, store_code, product_code, sale_date, quantity_sold, revenue)
  * batch_id = Links to batches.batch_id (for batch tracking)
  * store_code = Store identifier (links to location.location)
  * product_code = Product identifier (links to product_hierarchy.product)
  * sale_date = Transaction date (DATE type)
  * quantity_sold = Number of units sold (DECIMAL)
  * revenue = Total revenue from sale (DECIMAL)
  * Use for: transaction-level sales analysis, batch-level sales tracking, revenue calculations

- batches (id, batch_id, product_code, store_code, received_date, expiry_date, initial_qty, current_qty)
  * batch_id = Unique batch identifier (PRIMARY KEY)
  * product_code = Product in this batch (links to product_hierarchy.product)
  * store_code = Store holding this batch (links to location.location)
  * received_date = Date batch was received (DATE type)
  * expiry_date = Expiration date of batch (DATE type)
  * initial_qty = Starting quantity (DECIMAL)
  * current_qty = Remaining quantity (DECIMAL)
  * Use for: batch expiry analysis, inventory levels, perishable tracking
  * To find expiring batches: WHERE expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL 'X days'

- batch_stock_tracking (id, batch_id, transaction_date, transaction_type, quantity, store_code, product_code)
  * batch_id = Links to batches.batch_id (tracking for specific batch)
  * transaction_date = Date of inventory movement (DATE type)
  * transaction_type = Movement type (TRANSFER_IN, SALE, ADJUSTMENT, SPOILAGE, RETURN)
  * quantity = Amount moved (DECIMAL)
  * store_code = Store identifier (links to location.location)
  * product_code = Product identifier (links to product_hierarchy.product)
  * Use for: inventory movement analysis, spoilage tracking, transfer tracking, stock adjustments
  * Common queries: 
    - Spoilage: WHERE transaction_type = 'SPOILAGE'
    - Transfers: WHERE transaction_type = 'TRANSFER_IN'
    - Sales: WHERE transaction_type = 'SALE'

- spoilage_report (id, batch_id, store_code, product_code, report_date, spoilage_qty, spoilage_pct, spoilage_case)
  * batch_id = Links to batches.batch_id (spoilage for specific batch)
  * store_code = Store with spoilage (links to location.location)
  * product_code = Product with spoilage (links to product_hierarchy.product)
  * report_date = Date of spoilage report (DATE type)
  * spoilage_qty = Quantity spoiled (DECIMAL)
  * spoilage_pct = Spoilage percentage (DECIMAL, 0-100)
  * spoilage_case = Severity category (No Spoilage, Low 0-5%, Medium 5-10%, High 10-20%, Critical 20%+)
  * Use for: spoilage analysis, waste tracking, product/store spoilage patterns
  * Severity filters:
    - Low: WHERE spoilage_pct BETWEEN 0 AND 5
    - Medium: WHERE spoilage_pct BETWEEN 5 AND 10
    - High: WHERE spoilage_pct BETWEEN 10 AND 20
    - Critical: WHERE spoilage_pct > 20

INVENTORY TABLE RELATIONSHIPS:
- sales.batch_id → batches.batch_id (sales linked to specific batches)
- batches.batch_id → batch_stock_tracking.batch_id (movements for each batch)
- batches.batch_id → spoilage_report.batch_id (spoilage for each batch)
- All tables link to location via store_code/location
- All tables link to product_hierarchy via product_code/product
- Join perishable with batches for shelf life analysis using product names

DEMAND FORMULAS (Critical - Use NRF Calendar):

1. SHORT-TERM PLANNING (Less than 4 weeks ahead):
   Use: WDD vs Normal Metric
   Formula: (SUM(metric) - SUM(metric_nrm)) / NULLIF(SUM(metric_nrm), 0)
   Meaning: Compare weather-driven demand to normal expected demand for upcoming weeks
   Example: "Show sales forecast for next 2 weeks" → Use metric vs metric_nrm

2. LONG-TERM PLANNING (More than 4 weeks ahead):
   Use: WDD vs Last Year (LY)
   Formula: (SUM(metric) - SUM(metric_ly)) / NULLIF(SUM(metric_ly), 0)
   Meaning: Compare to last year's demand for stable long-range forecasts
   Example: "Forecast for next quarter" OR "Next Month" → Use metric vs metric_ly

3. HISTORICAL REPORTING (Past analysis):
   Use: WDD vs Last Year (LY)
   Formula: (SUM(metric) - SUM(metric_ly)) / NULLIF(SUM(metric_ly), 0)
   Meaning: Year-over-year comparison to explain past performance
   Example: "How did we perform last month vs last year?" → Use metric vs metric_ly

IMPORTANT NOTES:
- ALWAYS use NULLIF to prevent division by zero errors
- metric = WDD (Weather Driven Demand) - the actual sales value
- metric_nrm = Normal expected demand
- metric_ly = Last year's demand for same period
- DO NOT filter by metric='sales' - metric column IS the sales value itself!

SEASONS DEFINITION:
- Spring: Feb, Mar, Apr
- Summer: May, Jun, Jul
- Fall: Aug, Sep, Oct
- Winter: Nov, Dec, Jan
""")
        
        # SQL generation instructions
        prompt_parts.append("""
IMPORTANT SQL GENERATION RULES:
1. Use PostgreSQL syntax (LIMIT not TOP, || for concat, CAST for type conversion)
2. For sales/metrics data: Query 'metrics' table, use SUM(metric), SUM(metric_nrm), or SUM(metric_ly)
3. CRITICAL: metric column IS the sales value - DO NOT use WHERE metric='sales'!
4. For demand calculations:
   - Short-term (< 4 weeks): SELECT (SUM(metric) - SUM(metric_nrm)) / NULLIF(SUM(metric_nrm), 0)
   - Long-term (> 4 weeks) OR "Next Month": SELECT (SUM(metric) - SUM(metric_ly)) / NULLIF(SUM(metric_ly), 0)
   - Historical: SELECT (SUM(metric) - SUM(metric_ly)) / NULLIF(SUM(metric_ly), 0)
5. Join 'metrics' with 'location' using: metrics.location = location.location
6. Join 'metrics' with 'product_hierarchy' using: metrics.product = product_hierarchy.product
7. Join 'weekly_weather' with 'location' using: weekly_weather.store_id = location.location
8. Join 'events' with 'location' using: events.store_id = location.location
9. Filter using the Product IDs and Store IDs provided above
10. Include descriptive columns (product names, store names, states) in results
11. Use appropriate aggregations (SUM, AVG, COUNT) with GROUP BY
12. Add ORDER BY for meaningful sorting (e.g., ORDER BY total_sales DESC)
13. Always include LIMIT clause (max 100 rows)
14. Handle date comparisons correctly - DATE columns don't need casting
15. ALWAYS use NULLIF(denominator, 0) to prevent division by zero
16. Return ONLY the SQL query, no explanation, no markdown formatting

CRITICAL TABLE NAMES (Use these exact names):
- metrics (NOT 'sales' or 'salesinventory')
- sales (transaction-level sales data with batch tracking)
- batches (inventory batches with expiry tracking)
- batch_stock_tracking (inventory movements: TRANSFER_IN, SALE, SPOILAGE, ADJUSTMENT, RETURN)
- spoilage_report (waste tracking with severity: No Spoilage, Low, Medium, High, Critical)
- weekly_weather (NOT 'weather' or 'weeklyweather')
- location (NOT 'locdim')
- product_hierarchy (NOT 'phier')
- calendar (NOT 'cal')
- perishable (for perishable products info)
- All DATE columns are type DATE (not TIMESTAMP) - compare directly with '2024-01-01'

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
