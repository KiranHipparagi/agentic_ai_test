"""
🚀 VISUALIZATION AGENT - LLM-Powered Chart Generation
Uses Azure OpenAI to dynamically generate chart configs instead of hard-coded logic
~100 lines vs 1000+ lines of hard-coded rules
"""

from typing import Dict, Any, List
from openai import AzureOpenAI
from core.config import settings
from core.logger import logger
import json


class VisualizationAgent:
    """
    LLM-powered visualization agent that generates chart configs dynamically
    NO hard-coded rules - the LLM analyzes data and creates optimal charts
    """
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.OPENAI_ENDPOINT
        )
        
        self.system_prompt = """You are an expert Google Charts configuration generator.

## Your Task
Analyze the user's query and provided data, then generate a valid Google Charts JSON configuration.
You must be "smart" about selecting the chart type if not specified.

## CRITICAL FORMAT RULES
1. Return ONLY valid JSON - no markdown, no code blocks, no explanations
2. Data MUST be a 2D array: [["Header1", "Header2"], ["Value1", number], ...]
3. First row = headers (all strings)
4. Data rows: first column = label (string), remaining = numbers
5. ALL numeric values must be actual numbers (int/float), NEVER strings

## Smart Chart Type Selection (Auto-Detect)
If chart_type is "auto" or unspecified, use these rules:
1. **Time Series Data** (Dates/Months/Years) → **LineChart** or **AreaChart**
2. **Category Comparison** (Products, Regions, Stores):
   - Few categories (< 10) → **ColumnChart**
   - Many categories (> 10) → **BarChart** (Horizontal is better for readability)
   - "Share", "Distribution", "%" → **PieChart** (if < 10 slices)
3. **Geographic Data** (States, Countries) → **GeoChart**
4. **Correlation** (Two numeric variables) → **ScatterChart**
5. **Ranking** ("Top 10", "Best") → **BarChart** (Sorted)

## Required JSON Structure
```json
{
  "chartType": "ColumnChart",
  "data": [
    ["Region", "Sales"],
    ["Northeast", 25000],
    ["Southeast", 18000]
  ],
  "options": {
    "title": "Sales by Region",
    "colors": ["#D04A02", "#3B82F6", "#10B981"],
    "legend": {"position": "top"},
    "chartArea": {"width": "85%", "height": "75%"},
    "hAxis": {"title": "Region"},
    "vAxis": {"title": "Sales"}
  }
}
```

## Data Preparation Guidelines
- **Aggressively clean data**: Convert string numbers ("1,200", "$50") to floats (1200, 50).
- **Limit rows**: If > 20 rows, show top 20 by value (unless it's a time series).
- **Sort**: Sort Bar/Column charts by value DESC for better readability.
- **Time**: Ensure time columns are sorted chronologically.
- **GeoChart**: Use full state names (e.g., "New York") if possible, or standard codes (US-NY).

## Quality Checklist
✓ JSON is valid and parseable
✓ chartType is a valid Google Charts type
✓ data is 2D array with headers
✓ All numbers are numeric (not quoted)
✓ Labels are descriptive
✓ Title describes the visualization
✓ Data is sorted meaningfully

Return ONLY the JSON object. No markdown fences, no explanations.
"""
    
    def generate_chart_config(
        self, 
        db_result: Dict[str, Any], 
        chart_type: str = "auto", 
        query: str = ""
    ) -> Dict[str, Any]:
        """
        Generate chart configuration using LLM intelligence
        
        Args:
            db_result: Database query result with 'data' field
            chart_type: Requested chart type or "auto" for LLM to decide
            query: Original user query for context
            
        Returns:
            Google Charts configuration dict
        """
        try:
            # Validate input
            if not db_result or not db_result.get("data"):
                logger.error("❌ No data in db_result")
                return self._error_chart("No data available")
            
            data = db_result["data"]
            if not data:
                logger.error("❌ Empty data array")
                return self._error_chart("Empty data")
            
            logger.info(f"🎨 Smart Viz Agent: Generating chart for {len(data)} rows")
            logger.info(f"   Query: '{query}'")
            logger.info(f"   Requested type: {chart_type}")
            logger.info(f"   Sample data: {data[:2]}")
            
            # Prepare data summary for LLM (limit to manageable size)
            max_sample_rows = 10 if len(data) > 100 else min(len(data), 20)
            data_summary = {
                "total_rows": len(data),
                "columns": list(data[0].keys()) if data else [],
                "sample_rows": data[:max_sample_rows],
                "all_data": data if len(data) <= 50 else None  # Include all if small dataset
            }
            
            # Build LLM prompt with explicit examples
            user_prompt = f"""User Query: "{query}"
Requested Chart Type: {chart_type if chart_type != 'auto' else 'Choose best type'}

Data Overview:
- Total Records: {data_summary['total_rows']}
- Available Columns: {', '.join(data_summary['columns'])}

Data Sample (first {max_sample_rows} rows):
{json.dumps(data_summary['sample_rows'], indent=2, default=str)}

Instructions:
1. Analyze the data structure and user intent
2. Select the most appropriate chart type:
   - Use BarChart if query contains "bar chart" or "horizontal"
   - Use ColumnChart for "compare", "top N", category comparisons
   - Use LineChart for "trend", "over time", temporal data
   - Use PieChart for "distribution", "breakdown", "share"
   - Use GeoChart for "map", "by state", "by region" with location names
   - Use ScatterChart for "correlation", "relationship"
3. Transform data into [["Header", "Header"], [value, number], ...] format
4. Ensure ALL numeric columns are actual numbers (not strings)
5. Limit to 50 data points max (take top N if needed)
6. Sort data meaningfully (DESC for comparisons)
7. Use clear, business-friendly column names

Generate the complete Google Charts JSON config now:
"""
            
            # Call LLM with strict JSON mode if available
            logger.info("🤖 Calling LLM to generate chart config...")
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Very low temperature for consistent JSON structure
                max_tokens=3000,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            llm_output = response.choices[0].message.content.strip()
            logger.info(f"🤖 LLM Response length: {len(llm_output)} chars")
            logger.info(f"🤖 LLM Response preview: {llm_output[:300]}...")
            
            # Parse JSON from LLM response (already in JSON mode, no markdown)
            try:
                chart_config = json.loads(llm_output)
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parse error even with json_object mode: {e}")
                logger.error(f"   Full output: {llm_output}")
                return self._fallback_chart(data, chart_type, query)
            
            # Validate the generated config
            if not self._validate_chart_config(chart_config):
                logger.error("❌ LLM generated invalid chart config")
                return self._fallback_chart(data, chart_type, query)
            
            logger.info(f"✅ Smart Viz Agent generated {chart_config['chartType']} with {len(chart_config['data'])} rows")
            logger.info(f"   Data preview: {chart_config['data'][:3] if chart_config['data'] else 'No data'}")
            return chart_config
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM JSON output: {e}")
            if 'llm_output' in locals():
                logger.error(f"   Raw output: {llm_output[:500]}")
            return self._fallback_chart(data, chart_type, query)
            
        except Exception as e:
            logger.error(f"❌ Smart Viz Agent error: {e}")
            return self._fallback_chart(data if 'data' in locals() else [], chart_type, query)
    
    def _validate_chart_config(self, config: Dict[str, Any]) -> bool:
        """Validate chart configuration structure"""
        try:
            if "chartType" not in config:
                logger.error("Missing chartType")
                return False
            if "data" not in config or not isinstance(config["data"], list):
                logger.error("Missing or invalid data")
                return False
            if len(config["data"]) < 2:
                logger.error("Insufficient data rows")
                return False
            if not isinstance(config["data"][0], list):
                logger.error("Data must be 2D array")
                return False
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def _fallback_chart(self, data: List[Dict], chart_type: str, query: str) -> Dict[str, Any]:
        """
        Fallback to simple rule-based chart generation if LLM fails
        Uses smart heuristics to create valid Google Charts configs
        """
        logger.warning("⚠️ Using fallback chart generation")
        
        if not data:
            return self._error_chart("No data")
        
        first_row = data[0]
        columns = list(first_row.keys())
        
        if len(columns) < 2:
            return self._error_chart("Insufficient columns")
        
        # Detect column types
        label_col = columns[0]  # First column is typically the label/category
        value_cols = []
        
        # Find numeric columns
        for col in columns[1:]:
            if isinstance(first_row.get(col), (int, float)):
                value_cols.append(col)
        
        if not value_cols:
            # If no numeric columns found, try to convert
            value_cols = columns[1:2]
        
        # Build chart data - CRITICAL: ensure proper types
        headers = [label_col.replace('_', ' ').title()] + [col.replace('_', ' ').title() for col in value_cols[:2]]
        chart_data = [headers]
        
        # Limit rows and ensure numeric values
        for row in data[:30]:  # Max 30 rows
            label_value = str(row.get(label_col, 'Unknown'))
            chart_row = [label_value]
            
            for col in value_cols[:2]:  # Max 2 value columns
                val = row.get(col, 0)
                # Force numeric conversion
                try:
                    if isinstance(val, str):
                        val = float(val.replace(',', '')) if val else 0
                    elif val is None:
                        val = 0
                    # Convert to int if whole number, else float
                    numeric_val = float(val)
                    chart_row.append(int(numeric_val) if numeric_val.is_integer() else numeric_val)
                except (ValueError, AttributeError):
                    chart_row.append(0)
            
            chart_data.append(chart_row)
        
        # Intelligently select chart type
        query_lower = query.lower()
        if chart_type == "auto":
            if "bar" in query_lower:
                selected_type = "BarChart"
            elif "line" in query_lower or "trend" in query_lower:
                selected_type = "LineChart"
            elif "pie" in query_lower or "donut" in query_lower:
                selected_type = "PieChart"
            elif "map" in query_lower or "geo" in query_lower:
                selected_type = "GeoChart"
            else:
                selected_type = "ColumnChart"
        else:
            selected_type = chart_type
        
        return {
            "chartType": selected_type,
            "data": chart_data,
            "options": {
                "title": query[:60] if query else "Data Visualization",
                "colors": ["#D04A02", "#3B82F6", "#10B981", "#F59E0B"],
                "legend": {"position": "top" if len(value_cols) > 1 else "none"},
                "chartArea": {"width": "85%", "height": "75%"},
                "animation": {"startup": True, "duration": 500}
            }
        }
    
    def _error_chart(self, message: str) -> Dict[str, Any]:
        """Return error chart configuration"""
        return {
            "chartType": "Table",
            "data": [["Error"], [message]],
            "options": {"title": "Chart Error"}
        }


# Test function
def test_visualization_agent():
    """Test the visualization agent"""
    logger.info("🧪 Testing Visualization Agent...")
    
    # Sample data
    sample_data = {
        "data": [
            {"region": "northeast", "event_count": 299},
            {"region": "southeast", "event_count": 278},
            {"region": "midwest", "event_count": 267},
            {"region": "west", "event_count": 256},
            {"region": "southwest", "event_count": 234}
        ],
        "row_count": 5
    }
    
    agent = VisualizationAgent()
    result = agent.generate_chart_config(
        db_result=sample_data,
        chart_type="auto",
        query="show me bar chart which region has highest events"
    )
    
    logger.info(f"✅ Test result: {json.dumps(result, indent=2)}")
    return result


if __name__ == "__main__":
    test_visualization_agent()
