from typing import Dict, Any, List
from decimal import Decimal
from openai import AzureOpenAI
from sqlalchemy import text
from core.config import settings
from core.logger import logger
from database.postgres_db import get_db
from services.context_resolver import context_resolver


class DatabaseAgent:
    """
    Intelligent agent that uses Azure AI Search + Gremlin for context resolution,
    then generates and executes SQL queries to fetch real data from PostgreSQL
    
    Workflow:
    1. Resolve entities from user query (Azure AI Search)
    2. Expand context via knowledge graph (Gremlin)
    3. Generate SQL with enriched context (LLM)
    4. Execute query on PostgreSQL
    5. Return results
    """
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.OPENAI_ENDPOINT
        )
        self.resolver = context_resolver
        
        # Current date context (STATIC for demo data - Nov 8, 2025)
        self.CURRENT_WEEKEND_DATE = "2025-11-08"  # This weekend's end_date
        
        # Simplified system prompt (schema is now dynamic via context)
        self.system_prompt = f"""You are a PostgreSQL SQL expert for RETAIL SUPPLY CHAIN analytics.

CONTEXT: You work with retail industry data using NRF (National Retail Federation) Calendar standards.        
Your task is to generate accurate PostgreSQL SELECT queries based on:
1. User's natural language query
2. Resolved entity context (products, locations, dates, events)
3. Database schema information

=== QUERY TYPE DETECTION (CRITICAL) ===
You MUST determine which type of query the user is asking:

TYPE 1: WEATHER-DRIVEN DEMAND (WDD) ANALYSIS
- Keywords: "weather impact", "WDD", "demand forecast", "weather-driven", "seasonal demand", "metric"
- Use: metrics table with WDD formulas
- Purpose: Analyze how weather affects product demand trends

TYPE 2: ACTUAL SALES TRANSACTIONS
- Keywords: "sales", "revenue", "sold", "transactions", "units sold", "sales amount", "discounts"
- Use: sales table (transaction-level data)
- Purpose: Analyze actual transaction data, revenue, units sold

TYPE 3: INVENTORY & BATCH TRACKING
- Keywords: "inventory", "stock", "batch", "expiry", "expiring", "stock level", "received"
- Use: batches table + batch_stock_tracking table
- Purpose: Track inventory levels, batch expiry, stock movements

TYPE 4: SPOILAGE & WASTE
- Keywords: "spoilage", "waste", "spoiled", "expired", "loss"
- Use: spoilage_report table
- Purpose: Analyze product waste and spoilage patterns

TYPE 5: EVENT-BASED ANALYSIS
- Keywords: "event", "festival", "holiday", "concert", "game", "football", "music festival"
- Use: events table joined with sales/metrics
- Purpose: Analyze impact of events on sales/demand

=== CURRENT DATE CONTEXT (CRITICAL) ===
This Weekend (Current Week End Date): November 8, 2025 (2025-11-08)
- When user says "this week" or "current week", use end_date = '2025-11-08'
- When user says "next week" or "NW", use end_date = '2025-11-15'
- When user says "last week" or "LW", use end_date = '2025-11-01'
- Current Month: November 2025
- Next Month (NM): December 2025
- Last Month (LM): October 2025
- Current Year: 2025
- Last Year (LY): 2024
- Current Quarter: Q4 2025
- Next Quarter (NQ): Q1 2026
- Last Quarter (LQ): Q3 2025

=== NRF CALENDAR DEFINITIONS ===
- LY (Last Year): Previous year per NRF calendar. If 2025, use 2024.
- LQ (Last Quarter): Previous quarter per NRF. If Q4 2025, use Q3 2025.
- LM (Last Month): Previous month per NRF. If Nov 2025, use Oct 2025.
- LW (Last Week): Previous week ending date. If current is 2025-11-08, use 2025-11-01.
- NY (Next Year): Upcoming year. If 2025, use 2026.
- NQ (Next Quarter): Next quarter per NRF. If Q4 2025, use Q1 2026.
- NM (Next Month): Next month per NRF. If Nov 2025, use Dec 2025.
- NW (Next Week): Next week ending date. If current is 2025-11-08, use 2025-11-15.

=== SEASONS (NRF Calendar) ===
- Spring: February, March, April
- Summer: May, June, July
- Fall: August, September, October
- Winter: November, December, January

=== WDD (Weather Driven Demand) FORMULAS - FOR METRICS TABLE ONLY ===
1. Short-Term Planning (≤4 weeks): Use WDD vs Normal
   Formula: (SUM(metrics.metric) - SUM(metrics.metric_nrm)) / NULLIF(SUM(metrics.metric_nrm), 0)
   
2. Long-Term Planning (>4 weeks): Use WDD vs LY (Last Year)
   Formula: (SUM(metrics.metric) - SUM(metrics.metric_ly)) / NULLIF(SUM(metrics.metric_ly), 0)
   
3. Historical Reporting: Use WDD vs LY for year-over-year comparisons
   Formula: (SUM(metrics.metric) - SUM(metrics.metric_ly)) / NULLIF(SUM(metrics.metric_ly), 0)

=== TABLE SCHEMAS ===

METRICS TABLE (for WDD/demand trend analysis):
- metrics (id, product, location, end_date, metric, metric_nrm, metric_ly)
  * product = Product name (e.g., 'Hamburgers', 'Coffee & Tea')
  * location = Store ID (e.g., 'ST0050')
  * metric = WDD value (Weather Driven Demand)
  * metric_nrm = Normal demand baseline
  * metric_ly = Last year's demand

SALES TABLE (for actual transaction data):
- sales (id, batch_id, store_code, product_code, transaction_date, sales_units, sales_amount, discount_amount, total_amount)
  * batch_id = Links to batches table
  * store_code = Store ID (links to location.location)
  * product_code = Product ID (INTEGER, links to product_hierarchy.product_id)
  * transaction_date = Date of sale (DATE type)
  * sales_units = Number of units sold (INTEGER)
  * sales_amount = Gross sales amount (NUMERIC)
  * discount_amount = Discount applied (NUMERIC)
  * total_amount = Net sales after discount (NUMERIC)

BATCHES TABLE (for inventory/expiry tracking):
- batches (id, batch_id, store_code, product_code, transaction_date, expiry_date, unit_price, total_value, received_qty, mfg_date, week_end_date, stock_received, stock_at_week_start, stock_at_week_end)
  * batch_id = Unique batch identifier
  * expiry_date = When batch expires (DATE)
  * stock_at_week_end = Current stock level
  * received_qty = Quantity received

BATCH_STOCK_TRACKING TABLE (for inventory movements):
- batch_stock_tracking (record_id, batch_id, store_code, product_code, transaction_type, transaction_date, qty_change, stock_after_transaction, unit_price)
  * transaction_type = 'SALE', 'TRANSFER_IN', 'ADJUSTMENT', 'SPOILAGE', 'RETURN'
  * qty_change = Quantity changed (positive or negative)

SPOILAGE_REPORT TABLE (for waste analysis):
- spoilage_report (id, batch_id, store_code, product_code, qty, spoilage_qty, spoilage_pct, spoilage_case)
  * spoilage_qty = Quantity spoiled
  * spoilage_pct = Spoilage percentage (0-100)
  * spoilage_case = Severity (1=Low, 2=Medium, 3=High, 4=Critical)

EVENTS TABLE (for event-based analysis):
- events (id, event, event_type, event_date, store_id, region, market, state)
  * event = Event name (e.g., 'Memorial Day', 'Music Festival')
  * event_type = Type (e.g., 'National Holiday', 'Sporting Event', 'Concert')
  * store_id = Affected store (links to location.location)

LOCATION TABLE:
- location (id, location, region, market, state, latitude, longitude)
  * region = 'northeast', 'southeast', 'midwest', 'west', 'southwest' (LOWERCASE!)

PRODUCT_HIERARCHY TABLE:
- product_hierarchy (product_id, dept, category, product)
  * product_id = INTEGER (for joining with sales.product_code, batches.product_code)
  * product = Product name (for joining with metrics.product)

CALENDAR TABLE:
- calendar (id, end_date, year, quarter, month, week, season)
  * month = STRING ('January', 'February', etc.) NOT INTEGER!
  * week = NRF retail week number

CRITICAL RULES:
- This is PostgreSQL: use LIMIT (not TOP), || for concatenation
- ALWAYS use NULLIF(denominator, 0) to prevent division by zero
- Use SELECT DISTINCT unless aggregating with GROUP BY
- Maximum 30 rows in results (use LIMIT)
- Return ONLY the SQL query without explanation

JOIN PATTERNS:
- metrics → location: metrics.location = location.location
- metrics → product_hierarchy: metrics.product = product_hierarchy.product
- sales → location: sales.store_code = location.location
- sales → product_hierarchy: sales.product_code = product_hierarchy.product_id
- batches → location: batches.store_code = location.location
- batches → product_hierarchy: batches.product_code = product_hierarchy.product_id
- events → location: events.store_id = location.location

DATE FORMATTING:
- Cast dates: end_date::DATE
- Format dates: TO_CHAR(date_column, 'YYYY-MM-DD')

NRF CALENDAR RULES:
- ALWAYS JOIN with calendar table for week/period queries
- NEVER use DATE_PART(week, date) or EXTRACT(week FROM date)
- calendar.month is STRING ('October', 'November') NOT integer!

=== EXAMPLE QUERIES BY TYPE ===

-- Example 1: WDD Analysis (Weather Impact on Demand Trends)
-- "What's the weather impact on demand next 2 weeks?"
SELECT ph.product, l.region,
       ROUND((SUM(m.metric) - SUM(m.metric_nrm)) / NULLIF(SUM(m.metric_nrm), 0) * 100, 2) AS wdd_vs_normal_pct
FROM metrics m
JOIN calendar c ON m.end_date = c.end_date
JOIN product_hierarchy ph ON m.product = ph.product
JOIN location l ON m.location = l.location
WHERE c.end_date IN ('2025-11-15', '2025-11-22')
GROUP BY ph.product, l.region
ORDER BY wdd_vs_normal_pct DESC
LIMIT 30

-- Example 2: ACTUAL SALES Revenue Query (NOT metrics!)
-- "What are the top selling products by revenue?"
SELECT ph.product, SUM(s.sales_units) AS total_units, SUM(s.total_amount) AS total_revenue
FROM sales s
JOIN product_hierarchy ph ON s.product_code = ph.product_id
JOIN location l ON s.store_code = l.location
WHERE s.transaction_date >= '2025-10-01'
GROUP BY ph.product
ORDER BY total_revenue DESC
LIMIT 30

-- Example 3: INVENTORY/STOCK LEVEL Query
-- "Which products are running low on stock?"
SELECT ph.product, l.location, SUM(b.stock_at_week_end) AS current_stock
FROM batches b
JOIN product_hierarchy ph ON b.product_code = ph.product_id
JOIN location l ON b.store_code = l.location
WHERE b.week_end_date = '2025-11-08'
GROUP BY ph.product, l.location
HAVING SUM(b.stock_at_week_end) < 100
ORDER BY current_stock ASC
LIMIT 30

-- Example 4: EXPIRING BATCH Query
-- "Which batches are expiring in the next 7 days?"
SELECT b.batch_id, ph.product, l.location, b.expiry_date, b.stock_at_week_end AS remaining_stock
FROM batches b
JOIN product_hierarchy ph ON b.product_code = ph.product_id
JOIN location l ON b.store_code = l.location
WHERE b.expiry_date BETWEEN '2025-11-08' AND '2025-11-15'
  AND b.stock_at_week_end > 0
ORDER BY b.expiry_date ASC
LIMIT 30

-- Example 5: SPOILAGE Analysis
-- "Which products have highest spoilage?"
SELECT ph.product, l.region, SUM(sr.spoilage_qty) AS total_spoilage, AVG(sr.spoilage_pct) AS avg_spoilage_pct
FROM spoilage_report sr
JOIN product_hierarchy ph ON sr.product_code = ph.product_id
JOIN location l ON sr.store_code = l.location
GROUP BY ph.product, l.region
ORDER BY total_spoilage DESC
LIMIT 30

-- Example 6: EVENT-BASED Analysis (Music Festival)
-- "What products should I stock for music festival in Nashville?"
-- Step 1: Find events
SELECT e.event, e.event_type, e.event_date, e.store_id, e.market
FROM events e
WHERE (e.event ILIKE '%music%' OR e.event ILIKE '%festival%' OR e.event_type ILIKE '%concert%' OR e.event_type ILIKE '%festival%')
  AND e.market ILIKE '%nashville%'
ORDER BY e.event_date
LIMIT 30

-- Example 7: Sales during Events (Historical data for planning)
-- Find past sales during similar events
SELECT ph.product, SUM(s.sales_units) AS units_sold, SUM(s.total_amount) AS revenue
FROM sales s
JOIN product_hierarchy ph ON s.product_code = ph.product_id
JOIN location l ON s.store_code = l.location
JOIN events e ON e.store_id = l.location
WHERE (e.event ILIKE '%music%' OR e.event_type ILIKE '%festival%')
  AND s.transaction_date BETWEEN e.event_date - INTERVAL '3 days' AND e.event_date + INTERVAL '3 days'
GROUP BY ph.product
ORDER BY revenue DESC
LIMIT 30

-- Example 8: Combined WDD + Inventory for Replenishment
-- "Which items need replenishment due to weather impact?"
SELECT ph.product, l.location,
       ROUND((SUM(m.metric) - SUM(m.metric_nrm)) / NULLIF(SUM(m.metric_nrm), 0) * 100, 2) AS wdd_uplift_pct,
       COALESCE(SUM(b.stock_at_week_end), 0) AS current_stock
FROM metrics m
JOIN calendar c ON m.end_date = c.end_date
JOIN product_hierarchy ph ON m.product = ph.product
JOIN location l ON m.location = l.location
LEFT JOIN batches b ON b.product_code = ph.product_id AND b.store_code = l.location AND b.week_end_date = c.end_date
WHERE c.end_date IN ('2025-11-15', '2025-11-22')
GROUP BY ph.product, l.location
HAVING ROUND((SUM(m.metric) - SUM(m.metric_nrm)) / NULLIF(SUM(m.metric_nrm), 0) * 100, 2) > 5
ORDER BY wdd_uplift_pct DESC
LIMIT 30

-- Example 9: Football/Sporting Event Query
-- "Which cities have football games this week?"
SELECT DISTINCT e.event, e.event_type, e.event_date, e.market, e.state
FROM events e
WHERE (e.event ILIKE '%football%' OR e.event ILIKE '%NFL%' OR e.event_type ILIKE '%sporting%' OR e.event_type ILIKE '%sports%')
  AND e.event_date BETWEEN '2025-11-02' AND '2025-11-08'
ORDER BY e.event_date
LIMIT 30"""

    def query_database(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate SQL query from natural language and execute it
        
        Uses Azure Search + Gremlin for context before SQL generation
        """
        print("\n" + "="*80)
        print("\ud83d\uddc4\ufe0f  STEP 2: DATABASE AGENT - SQL Generation & Execution")
        print("="*80)
        try:
            # Step 1: Resolve entities and expand context via Azure Search + Gremlin
            print("\n\ud83d\udd04 Step 2.1: Resolving context (Azure Search + Gremlin)...")
            logger.info(f"\ud83d\udd0d Resolving context for query: {user_query}")
            resolved_context = self.resolver.resolve_query_context(user_query)
            
            # Log context summary
            context_summary = self.resolver.format_context_summary(resolved_context)
            logger.info(f"\ud83d\udcca Context: {context_summary}")
            print("\u2705 Context resolution complete")
            
            # Step 2: Generate SQL query with enriched context
            print("\n\ud83e\udd16 Step 2.2: Generating SQL query with LLM...")
            sql_query = self._generate_sql_with_context(user_query, resolved_context)
            
            # Fix common SQL syntax errors (semicolon before LIMIT)
            sql_query = sql_query.replace("; LIMIT", " LIMIT").replace(";LIMIT", " LIMIT")
            
            print("\n\ud83d\udcdd Generated SQL Query:")
            print("-" * 80)
            print(sql_query)
            print("-" * 80)
            logger.info(f"Generated SQL: {sql_query}")
            
            # 3. Execute query on PostgreSQL
            print("\n⚡ Step 2.3: Executing query on PostgreSQL...")
            with get_db() as db:
                result = db.execute(text(sql_query))
                rows = result.fetchall()
                columns = result.keys()
                print(f"✅ Query executed successfully! Retrieved {len(rows)} rows")
                
                # Convert to list of dicts with proper type handling
                data = []
                for row in rows:
                    row_dict = {}
                    for col, value in zip(columns, row):
                        row_dict[col] = self._normalize_value(value)
                    data.append(row_dict)
            
            print(f"\n\u2705 Database Agent Complete: {len(data)} rows returned")
            print("="*80)
            logger.info(f"\u2705 Query returned {len(data)} rows")
            
            return {
                "agent": "database",
                "sql_query": sql_query,
                "data": data,
                "row_count": len(data),
                "columns": list(columns),
                "context_summary": context_summary,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Database query failed: {e}")
            return {
                "agent": "database",
                "error": str(e),
                "sql_query": sql_query if 'sql_query' in locals() else "Query generation failed",
                "status": "failed",
                "data": []
            }
    
    def _generate_sql_with_context(self, user_query: str, resolved_context: Dict[str, Any]) -> str:
        """
        Generate SQL query using LLM with full context from Azure Search + Gremlin
        
        This replaces the old _generate_sql_query method that used hardcoded schema
        """
        # Get comprehensive prompt with all context
        prompt = self.resolver.get_sql_generation_prompt(user_query, resolved_context)
        
        print("\n🧠 STEP 2.2a: LLM Decision Making - Input Prompt")
        print("-" * 80)
        print(prompt)
        print("-" * 80)
        
        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up the query
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        # Add LIMIT if not present
        if "LIMIT" not in sql_query.upper():
            sql_query += " LIMIT 50"
        
        return sql_query
    
    def _generate_sql_query(self, user_query: str, context: Dict[str, Any] = None) -> str:

        logger.warning("Using deprecated _generate_sql_query method - consider using _generate_sql_with_context")
        
        # Minimal context for backward compatibility
        resolved_context = self.resolver.resolve_query_context(user_query)
        return self._generate_sql_with_context(user_query, resolved_context)
        
        return sql_query
    
    def query_database_for_chart(
        self, 
        user_query: str, 
        chart_type: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate and execute SQL optimized for specific chart type"""
        try:
            # Resolve context first
            resolved_context = self.resolver.resolve_query_context(user_query)
            
            # Generate chart-specific SQL with context
            sql_query = self._generate_chart_specific_sql(user_query, chart_type, resolved_context)
            logger.info(f"📊 Chart-specific SQL ({chart_type}): {sql_query}")
            
            # Execute query
            with get_db() as db:
                result = db.execute(text(sql_query))
                rows = result.fetchall()
                columns = result.keys()
                
                # Convert to clean data
                data = []
                for row in rows:
                    row_dict = {}
                    for col, value in zip(columns, row):
                        row_dict[col] = self._normalize_value(value)
                    data.append(row_dict)
            
            logger.info(f"✅ Retrieved {len(data)} rows optimized for {chart_type}")
            
            return {
                "agent": "database",
                "sql_query": sql_query,
                "data": data,
                "row_count": len(data),
                "columns": list(columns),
                "chart_type": chart_type,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Chart-specific query failed: {e}")
            return {
                "agent": "database",
                "error": str(e),
                "status": "failed",
                "data": []
            }
    
    def _generate_chart_specific_sql(
        self, 
        user_query: str, 
        chart_type: str,
        resolved_context: Dict[str, Any]
    ) -> str:
        """Generate SQL query optimized for specific chart type with full context"""
        
        # Chart type requirements
        chart_requirements = {
            "PieChart": "Need 1 category field and 1 numeric field. Use GROUP BY for aggregation.",
            "BarChart": "Need 1-2 category fields and 1-3 numeric fields. Limit to top 20 rows.",
            "LineChart": "Need 1 time/sequence field and 1-3 numeric trend fields. Order by time.",
            "AreaChart": "Need 1 time field and 1-3 numeric fields for cumulative trends.",
            "ScatterChart": "Need 2 numeric fields (X and Y axis). Include labels if available.",
            "GeoChart": "Need location field (state/region) and 1 numeric field. Aggregate by location.",
            "Table": "Return all relevant fields with proper formatting.",
            "Histogram": "Need 1 numeric field for distribution analysis.",
            "ColumnChart": "Similar to BarChart but for vertical orientation."
        }
        
        requirement = chart_requirements.get(chart_type, "Return relevant data")
        
        # Get base context prompt from resolver
        base_prompt = self.resolver.get_sql_generation_prompt(user_query, resolved_context)
        
        # Enhance with chart-specific requirements
        chart_prompt = f"""
{base_prompt}

CHART-SPECIFIC REQUIREMENTS FOR {chart_type}:
{requirement}

CHART-SPECIFIC GUIDELINES:
- For PieChart: SELECT category_field, SUM(metric) AS value ... GROUP BY category_field LIMIT 10
- For LineChart: SELECT date_field, SUM(metric) AS value ... ORDER BY date_field LIMIT 50
- For BarChart: SELECT category_field, SUM(metric) AS value ... GROUP BY category_field ORDER BY value DESC LIMIT 20
- For GeoChart: SELECT state, SUM(m.metric) AS value FROM metrics m JOIN location l ON m.location = l.location ... GROUP BY state
- For ScatterChart: SELECT numeric_field_1, numeric_field_2 LIMIT 100
- Always use appropriate aggregation (SUM, AVG, COUNT)
- Always include LIMIT clause
- Use clear field aliases (AS category, AS value, AS date)

Generate the SQL query optimized for {chart_type}:
"""

        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": chart_prompt}
            ],
            temperature=0.1,
            max_tokens=400
        )
        
        sql_query = response.choices[0].message.content.strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        # Ensure LIMIT exists
        if "LIMIT" not in sql_query.upper():
            if chart_type == "PieChart":
                sql_query += " LIMIT 10"
            elif chart_type in ["BarChart", "ColumnChart"]:
                sql_query += " LIMIT 20"
            elif chart_type == "LineChart":
                sql_query += " LIMIT 50"
            elif chart_type == "ScatterChart":
                sql_query += " LIMIT 100"
            else:
                sql_query += " LIMIT 50"
        
        return sql_query

    def _normalize_value(self, value: Any) -> Any:
        """Convert database values into JSON-serializable primitives"""
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        if isinstance(value, Decimal):
            numeric_value = float(value)
            return int(numeric_value) if numeric_value.is_integer() else numeric_value
        if isinstance(value, (int, float, str, bool)):
            return value
        return str(value)
    
    def analyze_results(self, user_query: str, data: List[Dict], sql_query: str) -> str:
        """Generate natural language answer from query results"""
        try:
            if not data:
                return "No data found matching your query. Please try rephrasing or checking different parameters."
            
            # Format data for LLM
            data_summary = f"Query returned {len(data)} rows.\n\nSample data:\n"
            for i, row in enumerate(data[:5]):
                data_summary += f"\nRow {i+1}: {row}"
            
            prompt = f"""User asked: {user_query}

SQL Query executed:
{sql_query}

Results:
{data_summary}

Provide a clear, insightful answer to the user's question based on this data.
Include specific numbers, trends, and recommendations."""

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a supply chain analyst. Provide clear insights from database query results."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Result analysis failed: {e}")
            return f"Found {len(data)} records. SQL query: {sql_query}"
