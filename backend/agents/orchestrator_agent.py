"""
Master Orchestrator using LangChain/LangGraph
Handles normal conversations and smart chart generation
Smart LLM-powered visualization option!
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from decimal import Decimal
from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from core.config import settings
from core.logger import logger
from .database_agent import DatabaseAgent
from .weather_agent import WeatherAgent
from .events_agent import EventsAgent
from .location_agent import LocationAgent
from .inventory_agent import InventoryAgent
from .visualization_agent import VisualizationAgent  # LLM-powered visualization
import json
import operator


class AgentState(TypedDict):
    """State for LangGraph agent orchestration"""
    query: str
    context: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    intent: str  # conversation, data_query, visualization, analysis
    needs_chart: bool
    chart_type: Optional[str]
    db_result: Optional[Dict[str, Any]]
    agent_results: Dict[str, Any]
    final_answer: str
    visualization: Optional[Dict[str, Any]]
    status: str


class OrchestratorAgent:
    """
    Orchestrator with LangChain/LangGraph
    
    Features:
    1. Intent Detection - Determines if user wants data, chart, or just chat
    2. LLM-Powered Chart Generation - Smart AI-driven visualization
    3. Multi-Chart Support - Maps, bar, pie, line, area, scatter
    4. Natural Conversations - Handles greetings and casual queries
    5. Context-Aware - Maintains conversation flow
    """
    
    def __init__(self):
        # Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.OPENAI_ENDPOINT
        )
        
        # LangChain LLM
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.OPENAI_ENDPOINT,
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            model=settings.OPENAI_MODEL_NAME,
            temperature=0.7
        )
        
        # Initialize specialized agents
        self.database_agent = DatabaseAgent()
        self.weather_agent = WeatherAgent()
        self.events_agent = EventsAgent()
        self.location_agent = LocationAgent()
        self.inventory_agent = InventoryAgent()
        
        # LLM-powered visualization agent
        self.visualization_agent = VisualizationAgent()
        
        logger.info(f"✅ Orchestrator initialized with LangGraph")
        logger.info(f"   Visualization Mode: SMART (LLM-Powered)")
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for agent orchestration"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("detect_intent", self._detect_intent)
        workflow.add_node("handle_conversation", self._handle_conversation)
        workflow.add_node("query_database", self._query_database)
        workflow.add_node("analyze_agents", self._analyze_with_agents)
        workflow.add_node("generate_chart", self._generate_chart)
        workflow.add_node("synthesize_response", self._synthesize_response)
        
        # Define edges (workflow)
        workflow.set_entry_point("detect_intent")
        
        workflow.add_conditional_edges(
            "detect_intent",
            self._route_by_intent,
            {
                "conversation": "handle_conversation",
                "data_query": "query_database",
                "visualization": "query_database",
                "analysis": "query_database"
            }
        )
        
        workflow.add_edge("handle_conversation", END)
        workflow.add_edge("query_database", "analyze_agents")
        
        workflow.add_conditional_edges(
            "analyze_agents",
            self._route_after_analysis,
            {
                "needs_chart": "generate_chart",
                "no_chart": "synthesize_response"
            }
        )
        
        workflow.add_edge("generate_chart", "synthesize_response")
        workflow.add_edge("synthesize_response", END)
        
        return workflow.compile()
    
    async def orchestrate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for orchestration"""
        try:
            print("\n" + "#"*80)
            print("🚀 ORCHESTRATOR - Multi-Agent Pipeline Started")
            print("#"*80)
            print(f"📥 Incoming Query: {query}")
            logger.info(f"🎯 Orchestrator received: {query[:100]}")
            
            # Initialize state
            initial_state: AgentState = {
                "query": query,
                "context": context,
                "conversation_history": [],
                "intent": "",
                "needs_chart": False,
                "chart_type": None,
                "db_result": None,
                "agent_results": {},
                "final_answer": "",
                "visualization": None,
                "status": "processing"
            }
            
            # Run workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # ✅ FORCE chart generation if query contains chart keywords OR data suggests a chart is useful
            query_lower = query.lower()
            chart_keywords = [
                "chart", "graph", "visualize", "plot", "map", "pie", "bar", "line", "area", "scatter",
                "trend", "compare", "distribution", "breakdown", "analysis", "performance", "vs", "versus",
                "top", "bottom", "highest", "lowest", "rank", "statistics", "stats", "impact"
            ]
            has_chart_keyword = any(word in query_lower for word in chart_keywords)
            
            db_result = final_state.get("db_result")
            has_data = db_result and db_result.get("data") and len(db_result.get("data")) > 0
            
            # Auto-detect if chart is useful (e.g. > 0 rows and has numbers)
            is_chartable = False
            if has_data:
                data = db_result.get("data")
                # Allow single row (e.g. Gauge/Card) up to 100 rows (Line/Scatter)
                if 0 < len(data) <= 100:
                    # Check if any value is numeric in the first row
                    first_row = data[0]
                    has_numbers = any(isinstance(v, (int, float, Decimal)) for v in first_row.values())
                    # If we have numbers, a chart is usually helpful
                    if has_numbers:
                        is_chartable = True
            
            needs_viz = final_state.get("visualization")
            
            print("\n📊 Step 3: Visualization Check")
            print(f"  Chart Keyword Detected: {has_chart_keyword}")
            print(f"  Data is Chartable: {is_chartable}")
            print(f"  Has Data: {has_data}")
            logger.info(f"🔍 Chart check: keyword={has_chart_keyword}, chartable={is_chartable}, has_data={has_data}")
            
            # Force generation if keyword present OR data is chartable (Smart Mode)
            if (has_chart_keyword or is_chartable) and has_data and (not needs_viz or not needs_viz.get("ready")):
                logger.warning("⚠️ Chart requested or suitable but not generated - forcing generation")
                final_state["needs_chart"] = True
                # Pass "auto" if no specific type detected, let Viz Agent decide
                detected_type = self._detect_chart_type(query_lower)
                final_state["chart_type"] = detected_type if detected_type != "auto" else "auto"
                
                chart_state = self._generate_chart(final_state)
                final_state["visualization"] = chart_state.get("visualization")
                logger.info(f"\u2705 Forced chart generation complete: ready={chart_state.get('visualization', {}).get('ready')}")
            
            # Build response
            print("\n" + "#"*80)
            print("\u2705 ORCHESTRATOR - Pipeline Completed Successfully")
            print("#"*80)
            print(f"\ud83d\udcca Intent: {final_state.get('intent')}")
            print(f"\ud83d\udcc8 Visualization: {'Yes' if final_state.get('visualization') else 'No'}")
            print(f"\ud83d\udcdd Row Count: {final_state.get('db_result', {}).get('row_count', 0) if final_state.get('db_result') else 0}")
            print("#"*80 + "\n")
            logger.info(f"Query processing complete. Intent: {final_state.get('intent')}")
            
            response = {
                "query": query,
                "answer": final_state.get("final_answer", "I'm here to help!"),
                "sql_query": final_state.get("db_result", {}).get("sql_query") if final_state.get("db_result") else None,
                "data_source": "postgres_database" if final_state.get("db_result") else "conversation",
                "row_count": final_state.get("db_result", {}).get("row_count", 0) if final_state.get("db_result") else 0,
                "raw_data": final_state.get("db_result", {}).get("data", [])[:10] if final_state.get("db_result") else None,
                "visualization": final_state.get("visualization"),
                "intent": final_state.get("intent"),
                "status": "success"
            }
            
            logger.info(f"📤 Final response: intent={response['intent']}, viz_included={response['visualization'] is not None}")
            if response['visualization']:
                logger.info(f"   Chart details: type={response['visualization'].get('chart_type')}, ready={response['visualization'].get('ready')}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}", exc_info=True)
            return {
                "query": query,
                "answer": f"I encountered an error: {str(e)}",
                "status": "error"
            }
    
    def _detect_intent(self, state: AgentState) -> AgentState:
        """Detect user intent using LLM"""
        query = state["query"]
        query_lower = query.lower()
        
        # Quick pattern matching for common intents
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings"]
        if any(greeting == query_lower.strip() for greeting in greetings):
            state["intent"] = "conversation"
            return state
        
        # ✅ Check for ANY visualization request
        viz_triggers = [
            "chart", "graph", "visualize", "visualization", "plot", "map", "diagram",
            "pie", "bar", "line", "area", "scatter", "histogram", "gauge", "table",
            "generate", "create", "show me", "display", "draw", "make"
        ]
        
        # Check if query is asking for visualization
        has_viz_trigger = any(trigger in query_lower for trigger in viz_triggers)
        
        # ✅ NEW: Also check for "give me", "show", etc. + data words
        data_words = ["sales", "inventory", "events", "products", "revenue", "stock", "data"]
        action_words = ["give me", "show", "display", "list", "get"]
        
        has_action = any(action in query_lower for action in action_words)
        has_data = any(data in query_lower for data in data_words)
        
        # If action + data + chart trigger → visualization intent
        if has_viz_trigger or (has_action and has_data and any(word in query_lower for word in ["chart", "graph", "visual"])):
            state["intent"] = "visualization"
            state["needs_chart"] = True
            state["chart_type"] = self._detect_chart_type(query_lower)
            logger.info(f"🎨 Visualization intent detected: {state['chart_type']} (trigger: {has_viz_trigger})")
            return state
        
        # Check for data queries
        data_keywords = [
            "how many", "what is", "show me", "list", "find", "get",
            "sales", "inventory", "events", "weather", "data", "records",
            "batch", "expir", "spoil", "waste", "movement", "transfer",
            "count", "total", "average", "sum"
        ]
        if any(keyword in query_lower for keyword in data_keywords):
            state["intent"] = "data_query"
            logger.info("📊 Data query intent detected")
            return state
        
        # Use LLM for complex intent detection
        try:
            prompt = f"""Classify the user's intent. Respond with ONLY ONE WORD:
- conversation (greetings, small talk, questions about capabilities)
- data_query (requesting data, facts, numbers)
- visualization (explicitly asking for charts/graphs/maps OR "give me chart")
- analysis (requesting insights, recommendations, forecasts)

User query: "{query}"

Intent:"""
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            intent = response.choices[0].message.content.strip().lower()
            state["intent"] = intent if intent in ["conversation", "data_query", "visualization", "analysis"] else "data_query"
            
            # If LLM detected visualization, mark it
            if state["intent"] == "visualization":
                state["needs_chart"] = True
                state["chart_type"] = self._detect_chart_type(query_lower)
            
            logger.info(f"🧠 LLM detected intent: {state['intent']}")
            
        except Exception as e:
            logger.warning(f"Intent detection failed, defaulting to data_query: {e}")
            state["intent"] = "data_query"
        
        return state
    
    def _detect_chart_type(self, query: str) -> str:
        """chart type detection with better keyword matching"""
        query_lower = query.lower()
        
        # Priority 1: Explicit chart type mentions
        if any(word in query_lower for word in ["pie chart", "pie graph", "donut"]):
            return "PieChart"
        elif any(word in query_lower for word in ["bar chart", "bar graph", "horizontal bar"]):
            return "BarChart"
        elif any(word in query_lower for word in ["column chart", "column graph", "vertical bar"]):
            return "ColumnChart"
        elif any(word in query_lower for word in ["line chart", "line graph", "trend line", "time series"]):
            return "LineChart"
        elif any(word in query_lower for word in ["area chart", "area graph", "filled"]):
            return "AreaChart"
        elif any(word in query_lower for word in ["scatter", "correlation", "relationship between"]):
            return "ScatterChart"
        elif any(word in query_lower for word in ["map", "geographical", "geography", "by state", "by region"]):
            return "GeoChart"
        elif any(word in query_lower for word in ["histogram", "distribution"]):
            return "Histogram"
        elif any(word in query_lower for word in ["table", "list all", "show all"]):
            return "Table"
        
        # Priority 2: Intent-based detection
        elif any(word in query_lower for word in ["proportion", "percentage", "share of", "breakdown by"]):
            return "PieChart"
        elif any(word in query_lower for word in ["compare", "comparison", "versus", "vs", "top", "rank"]):
            return "ColumnChart"  # Column better for comparisons
        elif any(word in query_lower for word in ["trend", "over time", "daily", "weekly", "monthly", "progression", "timeline", "history"]):
            return "LineChart"
        elif any(word in query_lower for word in ["by location", "across states", "regional", "by state"]):
            return "GeoChart"
        
        # Default: auto-detect based on data
        return "auto"
    
    def _route_by_intent(self, state: AgentState) -> str:
        """Route based on detected intent"""
        return state["intent"]
    
    def _handle_conversation(self, state: AgentState) -> AgentState:
        """Handle conversational queries (greetings, chitchat)"""
        query = state["query"]
        query_lower = query.lower().strip()
        
        # Predefined responses for common greetings
        greetings_map = {
            "hi": "Hello! I'm Plan IQ, your supply chain intelligence assistant. How can I help you today?",
            "hello": "Hi there! I'm here to help with supply chain insights, data analysis, and visualizations. What would you like to know?",
            "hey": "Hey! Ready to assist with your supply chain questions. What can I do for you?",
            "good morning": "Good morning! How can I assist with your supply chain operations today?",
            "good afternoon": "Good afternoon! What supply chain insights can I help you with?",
            "good evening": "Good evening! How may I help with your supply chain analysis?",
        }
        
        # Check for exact matches
        for greeting, response in greetings_map.items():
            if query_lower == greeting:
                state["final_answer"] = response
                state["status"] = "success"
                return state
        
        # Use LLM for other conversational queries
        try:
            system_msg = """You are Plan IQ, a friendly RETAIL supply chain intelligence assistant.
Handle conversational queries naturally. Be helpful and concise.

=== CURRENT DATE CONTEXT (CRITICAL) ===
This Weekend (Current Week End Date): November 8, 2025 (2025-11-08)
- "Next week" means week ending November 15, 2025
- "Last week" means week ending November 1, 2025
- "Next month" means December 2025
- "Last month" means October 2025
- Current Year: 2025 | Last Year (LY): 2024

=== NRF CALENDAR CONTEXT ===
- You work with retail industry data using NRF (National Retail Federation) Calendar
- NRF calendar uses 4-5-4 week patterns per quarter (retail standard)
- All week references are based on NRF calendar, not standard ISO weeks
- Weeks end on Saturday (end_date), start on Sunday
- You serve retail supply chain managers and planners

=== SEASONS (NRF) ===
- Spring: Feb/Mar/Apr | Summer: May/Jun/Jul
- Fall: Aug/Sep/Oct | Winter: Nov/Dec/Jan

Your capabilities:
- Analyze retail supply chain data (sales, inventory, events, weather)
- Generate visualizations (charts, graphs, maps) with NRF calendar context
- Calculate WDD (Weather Driven Demand) impacts
- Provide insights and recommendations for retail operations
Keep responses brief and professional.
"""
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": query}
                ],
                temperature=0.8,
                max_tokens=200
            )
            
            state["final_answer"] = response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Conversation handling failed: {e}")
            state["final_answer"] = "Hello! I'm Plan IQ. How can I help you with supply chain intelligence today?"
        
        state["status"] = "success"
        return state
    
    def _query_database(self, state: AgentState) -> AgentState:
        """database query with chart-aware logic"""
        try:
            query = state["query"]
            context = state["context"]
            chart_type = state.get("chart_type", "auto")
            
            logger.info(f"🔍 Querying database for chart type: {chart_type}")
            
            # If chart type is known and not 'auto', use chart-specific query
            if chart_type != "auto":
                chart_type_map = {
                    "pie": "PieChart",
                    "bar": "BarChart",
                    "line": "LineChart",
                    "area": "AreaChart",
                    "scatter": "ScatterChart",
                    "map": "GeoChart",
                    "histogram": "Histogram",
                    "table": "Table"
                }
                google_chart_type = chart_type_map.get(chart_type, "auto")
                
                if google_chart_type != "auto":
                    # Use chart-specific query
                    db_result = self.database_agent.query_database_for_chart(
                        query, 
                        google_chart_type,
                        context
                    )
                else:
                    # Fallback to standard query
                    db_result = self.database_agent.query_database(query, context)
            else:
                # Standard query
                db_result = self.database_agent.query_database(query, context)
            
            state["db_result"] = db_result
            
            if db_result.get("status") != "success" or not db_result.get("data"):
                logger.warning("⚠️ No data found")
                state["final_answer"] = f"I couldn't find data matching your query. Try rephrasing or using different filters.\n\nSQL: {db_result.get('sql_query', 'N/A')}"
                state["status"] = "no_data"
            else:
                logger.info(f"✅ Found {len(db_result.get('data', []))} records for {chart_type}")
                state["status"] = "data_found"
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            state["final_answer"] = f"Database query failed: {str(e)}"
            state["status"] = "error"
        
        return state
    
    def _analyze_with_agents(self, state: AgentState) -> AgentState:
        """Run specialized agents for deeper analysis"""
        if state.get("status") != "data_found":
            return state
        
        query = state["query"]
        context = state["context"]
        query_lower = query.lower()
        
        agent_results = {}
        
        # Weather analysis
        if any(word in query_lower for word in ["weather", "temperature", "climate", "rain"]):
            try:
                weather_result = self.weather_agent.analyze(query, context.get("location_id", ""))
                agent_results["weather"] = weather_result
            except Exception as e:
                logger.warning(f"Weather agent failed: {e}")
        
        # Events analysis
        if any(word in query_lower for word in ["event", "holiday", "festival", "calendar"]):
            try:
                events_result = self.events_agent.analyze(query, context.get("location_id", ""))
                agent_results["events"] = events_result
            except Exception as e:
                logger.warning(f"Events agent failed: {e}")
        
        # Inventory analysis (batch tracking, spoilage, sales transactions, stock movements)
        if any(word in query_lower for word in [
            "inventory", "stock", "batch", "expir", "shelf life", 
            "spoil", "waste", "loss", "damage", "perishable",
            "sales transaction", "revenue by batch", "batch sale",
            "movement", "transfer", "adjustment", "stock tracking"
        ]):
            try:
                inventory_result = self.inventory_agent.analyze(
                    query,
                    context.get("product_id", ""),
                    context.get("location_id", "")
                )
                agent_results["inventory"] = inventory_result
            except Exception as e:
                logger.warning(f"Inventory agent failed: {e}")
        
        state["agent_results"] = agent_results
        return state
    
    def _route_after_analysis(self, state: AgentState) -> str:
        """Decide if chart generation is needed"""
        # Only generate chart if explicitly requested OR intent is visualization
        if state.get("needs_chart") or state.get("intent") == "visualization":
            return "needs_chart"
        return "no_chart"
    
    def _generate_chart(self, state: AgentState) -> AgentState:
        """Generate chart configuration with proper data type conversion"""
        try:
            if not state.get("db_result") or not state["db_result"].get("data"):
                logger.warning("⚠️ No data for chart generation")
                state["visualization"] = {
                    "ready": False,
                    "message": "No data available to visualize"
                }
                return state
            
            logger.info(f"📊 Generating {state.get('chart_type', 'auto')} chart from {len(state['db_result']['data'])} rows...")
            
            # ✅ CRITICAL FIX: Ensure ALL numeric fields are converted to float/int
            clean_data = []
            for row in state["db_result"]["data"]:
                clean_row = {}
                for key, value in row.items():
                    if hasattr(value, 'isoformat'):  # DateTime object
                        clean_row[key] = value.isoformat()
                    elif isinstance(value, Decimal):
                        numeric_value = float(value)
                        clean_row[key] = int(numeric_value) if numeric_value.is_integer() else numeric_value
                    elif isinstance(value, str):
                        # Try to convert string numbers to actual numbers
                        try:
                            # Check if it's a number string
                            if value.replace(',', '').replace('.', '').replace('-', '').isdigit():
                                # Remove commas and convert to float
                                clean_value = float(value.replace(',', ''))
                                # Convert to int if it's a whole number
                                clean_row[key] = int(clean_value) if clean_value.is_integer() else clean_value
                            else:
                                clean_row[key] = value
                        except (ValueError, AttributeError):
                            clean_row[key] = value
                    elif isinstance(value, (int, float, bool, type(None))):
                        clean_row[key] = value
                    else:
                        clean_row[key] = str(value)
                clean_data.append(clean_row)
            
            # ✅ Log cleaned data for debugging
            logger.info(f"📊 Cleaned data sample: {clean_data[0] if clean_data else 'No data'}")
            
            # Build db_result with clean data
            db_result_clean = {
                "data": clean_data,
                "sql_query": state["db_result"].get("sql_query"),
                "status": "success"
            }
            
            # Get chart type - already in Google Charts format from _detect_chart_type
            google_chart_type = state.get("chart_type", "auto")
            
            # LLM-powered visualization
            logger.info(f"🤖 Using LLM-powered visualization agent for {google_chart_type}")
            viz_result = self.visualization_agent.generate_chart_config(
                db_result_clean,
                chart_type=google_chart_type,
                query=state["query"]
            )
            # Wrap result in expected format if needed
            if viz_result and "chartType" in viz_result:
                viz_result = {
                    "agent": "smart_visualization",
                    "chart_type": viz_result["chartType"],
                    "chart_config": viz_result,
                    "ready": True
                }
            
            state["visualization"] = viz_result
            logger.info(f"✅ Chart generated: {viz_result.get('chart_type', 'unknown')}, ready={viz_result.get('ready', False)}")
            
        except Exception as e:
            logger.error(f"Chart generation failed: {e}", exc_info=True)
            state["visualization"] = {
                "ready": False,
                "error": str(e),
                "message": "Failed to generate chart"
            }
        
        return state
    
    def _synthesize_response(self, state: AgentState) -> AgentState:
        """Synthesize final response using LLM"""
        try:
            query = state["query"]
            db_result = state.get("db_result", {})
            agent_results = state.get("agent_results", {})
            
            # Build context
            context_parts = []
            
            if db_result and db_result.get("data"):
                data_count = len(db_result['data'])
                data_summary = f"Database returned {data_count} records.\n"
                
                # If small dataset, provide all data for table generation
                if data_count <= 50:
                    data_summary += f"Full Data:\n"
                    for i, row in enumerate(db_result["data"], 1):
                        data_summary += f"{i}. {row}\n"
                else:
                    data_summary += f"Sample data (first 10 rows):\n"
                    for i, row in enumerate(db_result["data"][:10], 1):
                        data_summary += f"{i}. {row}\n"
                
                context_parts.append(data_summary)
            
            if agent_results:
                for agent_name, result in agent_results.items():
                    insight = result.get("answer", result.get("analysis", ""))
                    if insight:
                        context_parts.append(f"{agent_name.title()} Analysis:\n{insight}")
            
            full_context = "\n\n".join(context_parts)
            
            # System prompt
            system_prompt = """You are Plan IQ, a professional supply chain intelligence expert.

Provide clear, well-structured insights in a professional business format.

**CRITICAL FORMATTING RULES:**

1. **Use Markdown Tables** for ANY data with multiple items:
   - Always create tables with proper | separators
   - Include header row with column names
   - Align data in rows
   - Example:
     ```
     | Region | Sales | Change |
     |--------|-------|--------|
     | Northeast | $1,200,000 | +12% |
     | Southeast | $950,000 | +8% |
     ```

2. **Structure Your Response:**
   - **Executive Summary** (2-3 sentences at top)
   - **Detailed Analysis** (with data table if applicable)
   - **Key Insights** (bullet points)
   - **Recommendations** (actionable next steps)

3. **Professional Tone:**
   - Use business language
   - Include specific numbers and percentages
   - Cite data sources when relevant
   - Be concise but comprehensive

4. **Visual Hierarchy:**
   - Use ## for main sections
   - Use ### for subsections
   - Use **bold** for key metrics
   - Use bullet points for lists

5. **If Chart Requested:**
   - Mention "A visualization is provided below" at the end
   - Do NOT describe what the chart should look like
   - Focus on insights the chart reveals

Example Response Format (When Data Has Values):
```
## Weather Impact Analysis

**Executive Summary:** Analysis of 15 store locations shows mixed weather-driven demand patterns. Store ST0050 exhibits the highest positive impact (+22%), while Store ST0551 shows the largest decline (-15%). The majority of stores (8 locations) show zero weather impact, indicating stable demand conditions.

### Store-Level Weather Impact

| Store ID | Region | State | WDD Change | Interpretation |
|----------|--------|-------|------------|----------------|
| ST0050 | Northeast | MA | +22.0% | Strong positive weather impact |
| ST4961 | Mountain | CO | +18.0% | Significant weather-driven uplift |
| ST0551 | Southeast | FL | -15.0% | Weather suppressing demand |
| ST0100 | Northeast | MA | 0.0% | No weather impact detected |

### Key Insights
- **High Impact Stores**: 2 stores show significant positive weather effects (>15%)
- **Negative Impact**: 1 store experiencing weather-driven demand decline
- **Stable Stores**: 8 stores show zero weather impact (normal demand patterns)
- **Regional Variation**: Northeast and Mountain regions more weather-sensitive

### Recommendations
1. **ST0050 & ST4961**: Increase inventory 15-20% to capitalize on weather-driven demand surge
2. **ST0551**: Reduce seasonal inventory, shift marketing to weather-resilient products
3. **Zero-Impact Stores**: Maintain normal inventory levels, monitor for pattern changes

A visualization is provided below.
```

Example Response Format (When ALL Values Are Zero):
```
## Weather Impact Analysis

**Executive Summary:** Analysis of 25 products across 10 Northeast stores shows zero weather-driven demand variation for the upcoming month. All products maintain wdd_uplift_ratio of 0.0, indicating demand is expected to match normal patterns with no weather-related deviations.

### Product Weather Impact Summary

| Product | Category | Store Count | WDD Uplift Ratio | Interpretation |
|---------|----------|-------------|------------------|----------------|
| Milk | Perishable | 10 stores | 0.0 | No weather impact |
| Ice Cream | Perishable | 8 stores | 0.0 | No weather impact |
| Grocery Sector | N/A | 10 stores | 0.0 | No weather impact |

### Key Insights
- **Stable Demand**: No products show weather-driven uplift for the next month
- **Normal Planning**: Standard forecasting models apply (no weather adjustments needed)
- **Consistent Pattern**: All Northeast stores show identical zero-impact trend

### Recommendations
1. **Inventory Planning**: Use normal demand forecasts (metric_nrm) without weather premiums
2. **Monitor Changes**: Re-evaluate if weather patterns shift significantly
3. **Focus on Other Factors**: Prioritize promotions, events, and seasonality over weather
```

Remember: Zero values ARE valid data insights - they mean "no weather impact" not "no data"!
"""
            
            user_prompt = f"""User Query: {query}

Database Query Results and Analysis:
{full_context}

**CRITICAL INSTRUCTIONS:**
1. Use ONLY the data provided above from the database query results
2. Do NOT invent or hallucinate any store names, locations, numbers, or statistics
3. If the data contains store IDs (e.g., ST0050), use those EXACT IDs - do NOT convert to city names
4. Create a markdown table showing the EXACT data from the query results
5. Base all insights and recommendations ONLY on the actual data provided

**DATA INTERPRETATION RULES:**
6. IF the database returned rows with values → THAT IS VALID DATA, analyze it!
7. ONLY say "No data available" if the query returned ZERO rows (empty result set)
8. If you see values like "wdd_uplift_ratio: 0" or "wdd_vs_normal_pct_change: 0.0":
   - This means ZERO WEATHER IMPACT (no demand change)
   - It does NOT mean "no data" - it's a valid business insight!
   - Interpret: "No significant weather-driven demand change detected"
9. If you see NULL or missing values in specific columns, mention those specific columns are unavailable
10. Always analyze the data you DO have, even if some expected changes are zero

**WEATHER-DRIVEN DEMAND (WDD) INTERPRETATION:**
- **wdd_vs_normal_pct_change** or **wdd_uplift_ratio** = (WDD Sales - Normal Sales) / Normal Sales
- Positive value (e.g., 0.22) = +22% increase due to weather
- Negative value (e.g., -0.15) = -15% decrease due to weather  
- Zero value (0.0) = No weather impact detected (demand matches normal)
- This is calculated using either metric_nrm (< 4 weeks) or metric_ly (> 4 weeks)

Provide a comprehensive answer with insights and recommendations based STRICTLY on the actual database results."""
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature to reduce hallucination
                max_tokens=1000  # Increased for detailed tables
            )
            
            state["final_answer"] = response.choices[0].message.content
            state["status"] = "success"
            
        except Exception as e:
            logger.error(f"Response synthesis failed: {e}")
            # Fallback to simple answer
            if state.get("db_result") and state["db_result"].get("data"):
                state["final_answer"] = f"Found {len(state['db_result']['data'])} records in the database."
            else:
                state["final_answer"] = "I processed your query but couldn't generate a detailed response."
            state["status"] = "partial_success"
        
        return state


# Global instance
orchestrator = OrchestratorAgent()
