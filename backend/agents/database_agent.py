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
        
        # Simplified system prompt (schema is now dynamic via context)
        self.system_prompt = """You are a PostgreSQL SQL expert for a supply chain analytics database.
        
Your task is to generate accurate PostgreSQL SELECT queries based on:
1. User's natural language query
2. Resolved entity context (products, locations, dates, events)
3. Database schema information

CRITICAL RULES:
- This is PostgreSQL: use LIMIT (not TOP), || for concatenation
- For SALES data: Query the 'metrics' table, use SUM(metric) or SUM(metric_nrm)
- The 'metric' column IS the sales value itself - DO NOT use WHERE metric='sales'!
- Use provided Product IDs and Store IDs in WHERE clauses
- Always include descriptive columns (names, not just IDs)
- Use appropriate JOINs, GROUP BY, ORDER BY clauses
- Maximum 100 rows in results (use LIMIT)
- **NEVER put semicolon (;) before LIMIT clause** - Correct: "WHERE x=1 LIMIT 50" NOT "WHERE x=1; LIMIT 50"
- **NEVER hallucinate or invent data** - Only return what query actually finds
- Return ONLY the SQL query without explanation or formatting"""
    
    def query_database(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate SQL query from natural language and execute it
        
        NEW APPROACH: Uses Azure Search + Gremlin for context before SQL generation
        """
        print("\n" + "="*80)
        print("🗄️  STEP 2: DATABASE AGENT - SQL Generation & Execution")
        print("="*80)
        try:
            # Step 1: Resolve entities and expand context via Azure Search + Gremlin
            print("\n🔄 Step 2.1: Resolving context (Azure Search + Gremlin)...")
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
        """
        DEPRECATED: Old method with hardcoded schema
        Keeping for backward compatibility but redirects to new context-aware method
        """
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
- For GeoChart: SELECT state, SUM(metric) AS value FROM metrics JOIN locdim ... GROUP BY state
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
