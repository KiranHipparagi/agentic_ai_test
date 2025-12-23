"""Context Resolver Service - Combines Azure Search entity resolution with Gremlin graph expansion"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from database.azure_search import azure_search
from database.gremlin_db import gremlin_conn
from core.logger import logger

# Static current date context for demo data (November 8, 2025)
CURRENT_WEEKEND_DATE = datetime(2025, 11, 8)
CURRENT_WEEK_END = "2025-11-08"


class ContextResolver:
    """
    Hybrid context resolution using Azure AI Search + Gremlin Knowledge Graph
    
    Workflow:
    1. Azure Search: Resolve vague terms to exact IDs (e.g., "Pepsi" → product_id)
    2. Gremlin Graph: Expand context via relationships (e.g., find all products in same category)
    3. Return enriched context for SQL generation
    
    Date Context:
    - Current Weekend: November 8, 2025 (static for demo data)
    - Next Week: November 15, 2025
    - Last Week: November 1, 2025
    - Next Month: December 2025
    - Last Month: October 2025
    """
    
    def __init__(self):
        self.search = azure_search
        self.graph = gremlin_conn
        # Static date context
        self.current_date = CURRENT_WEEKEND_DATE
        self.current_week_end = CURRENT_WEEK_END
    
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
        
        # Add static date context at the top (CRITICAL for relative date queries)
        prompt_parts.append("=== CURRENT DATE CONTEXT ===")
        prompt_parts.append(f"Current Weekend (Week End Date): {self.current_week_end} (November 8, 2025)")
        prompt_parts.append("- 'This week' or 'current week' = end_date '2025-11-08'")
        prompt_parts.append("- 'Next week' or 'NW' = end_date '2025-11-15'")
        prompt_parts.append("- 'Last week' or 'LW' = end_date '2025-11-01'")
        prompt_parts.append("- 'Next month' or 'NM' = December 2025 → Use: c.month = 'December' AND c.year = 2025")
        prompt_parts.append("- 'Last month' or 'LM' = October 2025 → Use: c.month = 'October' AND c.year = 2025")
        prompt_parts.append("- 'Last year' or 'LY' = 2024")
        prompt_parts.append("- 'Next 2 weeks' = end_dates '2025-11-15' and '2025-11-22'")
        prompt_parts.append("- 'Last 6 weeks' = 6 weeks ending before '2025-11-08'")
        prompt_parts.append("- CRITICAL: calendar.month column is STRING ('January', 'December'), NOT integer!\n")
        
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
=== QUERY TYPE DETECTION ===
FIRST, determine which type of data the user needs:

1. WEATHER-DRIVEN DEMAND (WDD) → Use 'metrics' table
   Keywords: "weather impact", "WDD", "demand forecast", "weather-driven", "seasonal demand"
   
2. ACTUAL SALES TRANSACTIONS → Use 'sales' table  
   Keywords: "sales", "revenue", "sold", "transactions", "units sold", "sales amount", "discount"
   
3. INVENTORY/BATCH TRACKING → Use 'batches' + 'batch_stock_tracking' tables
   Keywords: "inventory", "stock", "batch", "expiry", "expiring", "stock level"
   
4. SPOILAGE/WASTE → Use 'spoilage_report' table
   Keywords: "spoilage", "waste", "spoiled", "expired products", "loss"

5. EVENT-BASED ANALYSIS → Use 'events' table joined with sales/metrics
   Keywords: "event", "festival", "holiday", "concert", "game", "football", "music festival"

=== TABLE SCHEMAS ===

METRICS TABLE (Weekly WDD data - for weather-driven demand TRENDS, not actual sales):
- metrics (id, product, location, end_date, metric, metric_nrm, metric_ly)
  * product = Product name (e.g., 'Hamburgers', 'Coffee & Tea', 'Milk')
  * location = Store ID (e.g., 'ST0050', 'ST2900')
  * end_date = Week ending date (joins with calendar.end_date)
  * metric = WDD (Weather Driven Demand) trend value
  * metric_nrm = Normal demand trend (baseline)
  * metric_ly = Last Year demand trend
  * NOTE: This is for TREND analysis only, not actual sales numbers!

SALES TABLE (Actual transaction-level sales data):
- sales (id, batch_id, store_code, product_code, transaction_date, sales_units, sales_amount, discount_amount, total_amount)
  * batch_id = Links to batches.batch_id
  * store_code = Store ID (links to location.location) e.g., 'ST0050'
  * product_code = Product ID INTEGER (links to product_hierarchy.product_id)
  * transaction_date = Date of sale (DATE type)
  * sales_units = Number of units sold (INTEGER)
  * sales_amount = Gross sales amount before discount (NUMERIC)
  * discount_amount = Discount applied (NUMERIC)
  * total_amount = Net sales after discount (NUMERIC)
  * USE THIS for: actual revenue, units sold, transaction analysis

BATCHES TABLE (Inventory batches with expiry tracking):
- batches (id, batch_id, store_code, product_code, transaction_date, expiry_date, unit_price, total_value, received_qty, mfg_date, week_end_date, stock_received, stock_at_week_start, stock_at_week_end)
  * batch_id = Unique batch identifier (PRIMARY KEY for batch queries)
  * store_code = Store ID (links to location.location)
  * product_code = Product ID INTEGER (links to product_hierarchy.product_id)
  * transaction_date = Date batch was received
  * expiry_date = Expiration date (DATE) - use for expiry analysis!
  * mfg_date = Manufacturing date
  * received_qty = Quantity received in batch
  * stock_at_week_start = Opening stock for the week
  * stock_at_week_end = Closing stock for the week
  * week_end_date = Week ending date (joins with calendar.end_date)
  * USE THIS for: inventory levels, expiry tracking, batch lifecycle

BATCH_STOCK_TRACKING TABLE (Inventory movements):
- batch_stock_tracking (record_id, batch_id, store_code, product_code, transaction_type, transaction_date, qty_change, stock_after_transaction, unit_price)
  * record_id = Unique record ID
  * batch_id = Links to batches.batch_id
  * store_code = Store ID (links to location.location)
  * product_code = Product ID INTEGER (links to product_hierarchy.product_id)
  * transaction_type = Movement type:
    - 'SALE' = Units sold from this batch
    - 'TRANSFER_IN' = Stock transferred in
    - 'ADJUSTMENT' = Inventory adjustment
    - 'SPOILAGE' = Stock spoiled/wasted
    - 'RETURN' = Customer returns
  * transaction_date = Date of movement (DATE type)
  * qty_change = Quantity changed (positive=in, negative=out)
  * stock_after_transaction = Running balance after this transaction
  * USE THIS for: stock movement analysis, transfer tracking

SPOILAGE_REPORT TABLE (Waste tracking):
- spoilage_report (id, batch_id, store_code, product_code, qty, spoilage_qty, spoilage_pct, spoilage_case)
  * batch_id = Links to batches.batch_id
  * store_code = Store ID (links to location.location)
  * product_code = Product ID INTEGER (links to product_hierarchy.product_id)
  * qty = Original quantity in batch
  * spoilage_qty = Quantity spoiled (INTEGER)
  * spoilage_pct = Spoilage percentage (0-100, NUMERIC)
  * spoilage_case = Severity level (INTEGER: 1=Low 0-5%, 2=Medium 5-10%, 3=High 10-20%, 4=Critical 20%+)
  * USE THIS for: spoilage analysis, waste patterns, loss tracking

EVENTS TABLE (for event-based analysis - IMPORTANT for festival/holiday queries):
- events (id, event, event_type, event_date, store_id, region, market, state)
  * event = Event name (e.g., 'Memorial Day', 'Black Friday', 'Music Festival')
  * event_type = Category (e.g., 'National Holiday', 'Sporting Event', 'Concert', 'Festival')
  * event_date = Date of event (DATE type)
  * store_id = Affected store (links to location.location)
  * region, market, state = Location info
  * USE THIS for: finding events near stores, event impact on sales

WEEKLY_WEATHER TABLE:
- weekly_weather (id, week_end_date, avg_temp_f, temp_anom_f, tmax_f, tmin_f, 
                  precip_in, precip_anom_in, heatwave_flag, cold_spell_flag, heavy_rain_flag, snow_flag, store_id)
  * week_end_date = Week ending date (joins with calendar.end_date)
  * store_id = Store ID (links to location.location)
  * heatwave_flag, cold_spell_flag, heavy_rain_flag, snow_flag = BOOLEAN weather alerts

LOCATION TABLE:
- location (id, location, region, market, state, latitude, longitude)
  * location = Store ID (PRIMARY KEY, e.g., 'ST6111')
  * region = LOWERCASE: 'northeast', 'southeast', 'midwest', 'west', 'southwest'
  * market = Market area (e.g., 'chicago, il', 'dallas, tx')
  * state = State name lowercase (e.g., 'illinois', 'texas')

PRODUCT_HIERARCHY TABLE:
- product_hierarchy (product_id, dept, category, product)
  * product_id = INTEGER (for joining with sales, batches, etc.)
  * product = Product name string (for joining with metrics.product)
  * category = Product category (e.g., 'QSR', 'Perishable', 'Beverages')
  * dept = Department (e.g., 'Fast Food', 'Grocery')

PERISHABLE TABLE:
- perishable (id, product, perishable_id, min_period, max_period, period_metric, storage)
  * product = Perishable product name
  * min_period, max_period = Shelf life range
  * period_metric = 'Days', 'Weeks', 'Months'
  * storage = 'Refrigerate', 'Freeze', 'Pantry'

CALENDAR TABLE (NRF Retail Calendar):
- calendar (id, end_date, year, quarter, month, week, season)
  * end_date = Week ending date (DATE)
  * year = INTEGER (fiscal year)
  * quarter = INTEGER (1-4)
  * month = STRING (FULL NAME: 'January', 'February', etc.) NOT integer!
  * week = NRF retail week number (1-53)
  * season = 'Spring', 'Summer', 'Fall', 'Winter'

=== JOIN PATTERNS ===
- metrics → location: metrics.location = location.location
- metrics → product_hierarchy: metrics.product = product_hierarchy.product
- metrics → calendar: metrics.end_date = calendar.end_date
- sales → location: sales.store_code = location.location
- sales → product_hierarchy: sales.product_code = product_hierarchy.product_id
- batches → location: batches.store_code = location.location
- batches → product_hierarchy: batches.product_code = product_hierarchy.product_id
- batches → calendar: batches.week_end_date = calendar.end_date
- batch_stock_tracking → batches: batch_stock_tracking.batch_id = batches.batch_id
- spoilage_report → batches: spoilage_report.batch_id = batches.batch_id
- spoilage_report → product_hierarchy: spoilage_report.product_code = product_hierarchy.product_id
- events → location: events.store_id = location.location
- weekly_weather → location: weekly_weather.store_id = location.location

=== EVENT-BASED ANALYSIS APPROACH ===
When user asks about events (festivals, holidays, concerts, games):
1. Find relevant events from events table by name/type/date
2. Get the stores affected (events.store_id)
3. For sales impact: Join with sales table on store_code and nearby transaction_date
4. For demand forecast: Join with metrics on location and end_date
5. Look at historical data from same event last year for comparison

Example: "What products should I stock for a music festival in Nashville?"
1. SELECT * FROM events WHERE event ILIKE '%music%' AND market ILIKE '%nashville%'
2. Find affected stores
3. Join with historical sales data around similar events
4. Identify top-selling products during past events""")
        
        # WDD Formulas section
        prompt_parts.append("""
=== WDD FORMULAS (For metrics table ONLY) ===

1. SHORT-TERM PLANNING (Less than 4 weeks ahead):
   Use: WDD vs Normal
   Formula: (SUM(metric) - SUM(metric_nrm)) / NULLIF(SUM(metric_nrm), 0)

2. LONG-TERM PLANNING (More than 4 weeks ahead):
   Use: WDD vs Last Year
   Formula: (SUM(metric) - SUM(metric_ly)) / NULLIF(SUM(metric_ly), 0)

3. HISTORICAL REPORTING:
   Use: WDD vs Last Year
   Formula: (SUM(metric) - SUM(metric_ly)) / NULLIF(SUM(metric_ly), 0)

SEASONS: Spring=Feb/Mar/Apr, Summer=May/Jun/Jul, Fall=Aug/Sep/Oct, Winter=Nov/Dec/Jan
""")
        
        # SQL generation instructions
        prompt_parts.append("""
IMPORTANT SQL GENERATION RULES:
1. Use PostgreSQL syntax (LIMIT not TOP, || for concat)
2. FIRST determine query type (see QUERY TYPE DETECTION above)
3. For WEATHER DEMAND analysis → Use 'metrics' table
4. For ACTUAL SALES data → Use 'sales' table (NOT metrics!)
5. For INVENTORY/STOCK → Use 'batches' and 'batch_stock_tracking' tables
6. For SPOILAGE/WASTE → Use 'spoilage_report' table
7. For EVENT analysis → Use 'events' table, join with sales or metrics

CRITICAL JOIN RULES:
- sales/batches/spoilage use product_code (INTEGER) → joins with product_hierarchy.product_id
- metrics uses product (STRING) → joins with product_hierarchy.product
- All inventory tables use store_code → joins with location.location

8. For REGION queries: l.region = 'northeast' (LOWERCASE!)
9. calendar.month is STRING ('January', 'December') NOT integer!
10. ALWAYS use NULLIF(denominator, 0) to prevent division by zero
11. Use SELECT DISTINCT unless aggregating with GROUP BY
12. Maximum 30 rows (use LIMIT 30)
13. Return ONLY the SQL query, no explanation

CRITICAL TABLE NAMES:
- metrics (WDD trends)
- sales (actual transactions)
- batches (inventory batches)
- batch_stock_tracking (stock movements)
- spoilage_report (waste tracking)
- events (festivals, holidays, games)
- weekly_weather
- location
- product_hierarchy
- calendar
- perishable

=== EXAMPLE QUERY PATTERNS ===

-- WDD Analysis: "weather impact on demand"
SELECT ph.product, l.region, ROUND((SUM(m.metric) - SUM(m.metric_nrm)) / NULLIF(SUM(m.metric_nrm), 0) * 100, 2) AS wdd_vs_normal_pct
FROM metrics m
JOIN product_hierarchy ph ON m.product = ph.product
JOIN location l ON m.location = l.location
JOIN calendar c ON m.end_date = c.end_date
WHERE c.end_date BETWEEN '2025-11-08' AND '2025-11-22'
GROUP BY ph.product, l.region ORDER BY wdd_vs_normal_pct DESC LIMIT 30

-- SALES Query: "top selling products"  
SELECT ph.product, SUM(s.sales_units) AS total_units, SUM(s.total_amount) AS total_revenue
FROM sales s
JOIN product_hierarchy ph ON s.product_code = ph.product_id
WHERE s.transaction_date >= '2025-10-01'
GROUP BY ph.product ORDER BY total_revenue DESC LIMIT 30

-- INVENTORY Query: "products low on stock"
SELECT ph.product, l.location, SUM(b.stock_at_week_end) AS current_stock
FROM batches b
JOIN product_hierarchy ph ON b.product_code = ph.product_id
JOIN location l ON b.store_code = l.location
WHERE b.week_end_date = '2025-11-08'
GROUP BY ph.product, l.location HAVING SUM(b.stock_at_week_end) < 100 LIMIT 30

-- EVENTS Query: "football games this week"
SELECT DISTINCT e.event, e.event_type, e.event_date, e.market, e.state
FROM events e
WHERE (e.event ILIKE '%football%' OR e.event_type ILIKE '%sporting%')
  AND e.event_date BETWEEN '2025-11-02' AND '2025-11-08'
ORDER BY e.event_date LIMIT 30

-- SPOILAGE Query: "products with highest waste"
SELECT ph.product, SUM(sr.spoilage_qty) AS total_spoilage, AVG(sr.spoilage_pct) AS avg_spoilage_pct
FROM spoilage_report sr
JOIN product_hierarchy ph ON sr.product_code = ph.product_id
GROUP BY ph.product ORDER BY total_spoilage DESC LIMIT 30

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
