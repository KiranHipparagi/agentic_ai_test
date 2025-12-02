# Planalytics AI - Complete Code Walkthrough

## Executive Summary

This document provides a step-by-step explanation of how the Planalytics AI system processes user queries and generates intelligent responses using a **multi-agent architecture** with **real-time database access**.

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Data Flow: Query to Answer](#data-flow-query-to-answer)
3. [Step-by-Step Execution Walkthrough](#step-by-step-execution-walkthrough)
4. [File Structure & Components](#file-structure--components)
5. [MCP Integration (Optional Enhancement)](#mcp-integration-optional-enhancement)
6. [Example Query Flow](#example-query-flow)

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                    (Frontend - Next.js/React)                    │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI)                       │
│                         main.py                                  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT (Brain)                    │
│              orchestrator_agent.py (LangGraph)                   │
│  • Intent Detection (conversation vs data query vs chart)        │
│  • Agent Selection (which specialized agents to activate)        │
│  • Chart Type Detection (if visualization needed)                │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SPECIALIZED AGENTS (Workers)                  │
├─────────────────────────────────────────────────────────────────┤
│  DATABASE AGENT (Primary - Gets Real Data)                      │
│  • Context Resolver (Azure AI Search + Neo4j/Gremlin)           │
│  • SQL Generator (Azure OpenAI LLM)                              │
│  • Query Executor (PostgreSQL)                                   │
│                                                                  │
│  WEATHER AGENT • Analyzes weather impact                        │
│  EVENTS AGENT  • Analyzes holiday/event impact                  │
│  LOCATION AGENT • Geographic analysis                           │
│  INVENTORY AGENT • Stock optimization                           │
│  VISUALIZATION AGENT • Chart generation (LLM-powered)           │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE TOOLS & DATABASES                   │
├─────────────────────────────────────────────────────────────────┤
│  AZURE AI SEARCH • Entity resolution (products, locations)       │
│  NEO4J/GREMLIN   • Knowledge graph (relationships)               │
│  POSTGRESQL      • Transactional data (sales, inventory)         │
│  AZURE OPENAI    • LLM (SQL generation, analysis, charts)        │
└─────────────────────────────────────────────────────────────────┘
```

**Key Note:** Data ingestion (Excel → PostgreSQL, Azure AI Search, Gremlin) is handled separately. This system only **queries** existing data.

---

## 2. Data Flow: Query to Answer

### High-Level Flow

```
User Query 
    ↓
FastAPI Endpoint (routes/chatbot.py)
    ↓
Orchestrator Agent (orchestrator_agent.py) - LangGraph Workflow
    ↓
Intent Detection (conversation? data? chart?)
    ↓
    ├─→ Simple Conversation → Direct LLM Response
    │
    ├─→ Data Query → Database Agent
    │       ↓
    │   Context Resolver (services/context_resolver.py)
    │       ↓
    │   Azure AI Search (resolve "Pepsi" → product_id)
    │   Neo4j/Gremlin (expand context: related products)
    │       ↓
    │   SQL Generator (LLM writes SQL with context)
    │       ↓
    │   PostgreSQL Execution (fetch real data)
    │       ↓
    │   Analysis (LLM interprets results)
    │
    └─→ Chart Request → Database Agent + Visualization Agent
            ↓
        Get Data (same as above)
            ↓
        Generate Chart Config (LLM creates chart JSON)
            ↓
        Return Chart + Data
            ↓
Final Answer + Chart (if applicable)
    ↓
Frontend Renders Response
```

---

## 3. Step-by-Step Execution Walkthrough

### **STEP 1: User Sends Query**

**File:** `frontend/components/ChatBox.tsx`

**What Happens:**
- User types: *"Show me sales for Pepsi in the Northeast region"*
- Frontend sends POST request to `/api/v1/chat`

```typescript
const response = await fetch('http://localhost:8000/api/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    query: "Show me sales for Pepsi in the Northeast region",
    product_id: null,
    location_id: null
  })
});
```

---

### **STEP 2: FastAPI Receives Request**

**File:** `backend/routes/chatbot.py`

**What Happens:**
- FastAPI endpoint receives the query
- Builds context object
- Calls the **Enhanced Orchestrator**

```python
@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    context = {
        "product_id": request.product_id or "default",
        "location_id": request.location_id or "default",
        "session_id": request.session_id
    }
    
    # Call Enhanced Orchestrator (LangGraph)
    result = await enhanced_orchestrator.orchestrate(request.query, context)
    
    return ChatResponse(
        query=request.query,
        answer=result.get("answer"),
        sql_query=result.get("sql_query"),
        visualization=result.get("visualization"),
        ...
    )
```

---

### **STEP 3: Orchestrator Agent (Brain) - Intent Detection**

**File:** `backend/agents/orchestrator_agent.py`

**What Happens:**
- LangGraph state machine starts
- **Node 1: Intent Detection** - LLM analyzes the query

```python
def _detect_intent(self, state: AgentState) -> AgentState:
    """Use LLM to detect user intent"""
    
    system_prompt = """You are an intent classifier for a supply chain chatbot.
    Classify queries into:
    - conversation: greetings, thanks, casual chat
    - data_query: questions needing database lookup
    - visualization: requests for charts/graphs
    - analysis: deep analytical questions
    """
    
    response = self.llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["query"])
    ])
    
    # LLM returns: "data_query" for "Show me sales for Pepsi"
    state["intent"] = "data_query"
    state["needs_chart"] = False  # No explicit chart request
    
    return state
```

**Decision:** Query is a **data_query** → Route to Database Agent

---

### **STEP 4: Database Agent - Context Resolution**

**File:** `backend/agents/database_agent.py`

**What Happens:**
- Database Agent calls **Context Resolver** to understand vague terms

```python
def query_database(self, user_query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    # Step 1: Resolve entities using Azure AI Search + Neo4j
    resolved_context = self.resolver.resolve_query_context(user_query)
    
    # Step 2: Generate SQL with enriched context
    sql_query = self._generate_sql_with_context(user_query, resolved_context)
    
    # Step 3: Execute SQL
    # Step 4: Analyze results
```

#### **STEP 4A: Context Resolver - Entity Resolution**

**File:** `backend/services/context_resolver.py`

**What Happens:**
- **Azure AI Search** resolves "Pepsi" to exact product IDs
- **Neo4j/Gremlin** expands context (e.g., all Pepsi variants)

```python
def resolve_query_context(self, user_query: str) -> Dict[str, Any]:
    # 1. Search Azure AI Search for products
    products = self.search.search_products(
        query="Pepsi",
        top_k=5,
        use_semantic=True
    )
    # Returns: [
    #   {"product_id": "P12345", "product": "Pepsi Cola", "dept": "Beverages"},
    #   {"product_id": "P12346", "product": "Pepsi Diet", "dept": "Beverages"}
    # ]
    
    # 2. Search Azure AI Search for locations
    locations = self.search.search_locations(
        query="Northeast region",
        top_k=10
    )
    # Returns: [
    #   {"location": "ST8500", "region": "northeast", "state": "NY"},
    #   {"location": "ST8501", "region": "northeast", "state": "MA"}
    # ]
    
    # 3. Expand via Neo4j/Gremlin graph
    expanded = self._expand_context_via_graph({
        "products": [p["product_id"] for p in products],
        "locations": [l["location"] for l in locations]
    })
    # Neo4j finds: related products in same category, nearby stores, etc.
    
    return {
        "products": {"resolved": products, "expanded": expanded["products"]},
        "locations": {"resolved": locations, "expanded": expanded["locations"]},
        "metadata": {...}
    }
```

**File Reference:**
- Azure AI Search client: `backend/database/azure_search.py`
- Neo4j/Gremlin client: `backend/database/neo4j_db.py`

---

#### **STEP 4B: SQL Generation with LLM**

**File:** `backend/agents/database_agent.py`

**What Happens:**
- LLM (Azure OpenAI GPT-4) writes SQL using enriched context

```python
def _generate_sql_with_context(self, user_query: str, resolved_context: Dict) -> str:
    # Build prompt with schema + resolved entities
    prompt = f"""
    You are a PostgreSQL expert. Generate SQL query.
    
    USER QUERY: {user_query}
    
    RESOLVED CONTEXT:
    Products: Pepsi Cola (P12345), Pepsi Diet (P12346)
    Locations: Northeast region stores (ST8500, ST8501, ...)
    
    AVAILABLE TABLES:
    - metrics (sales_units, sales_dollars, location, product_id, week_end_date)
    - phier (product_id, product, dept, category)
    - locdim (location, region, state)
    
    Generate SELECT query to answer the user's question.
    """
    
    response = self.client.chat.completions.create(
        model="azure.gpt-4.1",
        messages=[
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    
    sql_query = response.choices[0].message.content
    # Returns:
    # SELECT p.product, SUM(m.sales_units) as total_sales
    # FROM metrics m
    # JOIN phier p ON m.product_id = p.product_id
    # JOIN locdim l ON m.location = l.location
    # WHERE p.product_id IN ('P12345', 'P12346')
    #   AND l.region = 'northeast'
    # GROUP BY p.product
    
    return sql_query
```

---

#### **STEP 4C: Execute SQL on PostgreSQL**

**File:** `backend/agents/database_agent.py`

**What Happens:**
- Execute generated SQL against PostgreSQL

```python
def query_database(self, user_query: str, context: Dict) -> Dict[str, Any]:
    # ... (context resolution + SQL generation from above)
    
    # Execute SQL
    with get_db() as db:
        result = db.execute(text(sql_query))
        rows = result.fetchall()
        columns = result.keys()
        
        data = [dict(zip(columns, row)) for row in rows]
        # Returns:
        # [
        #   {"product": "Pepsi Cola", "total_sales": 125000},
        #   {"product": "Pepsi Diet", "total_sales": 98000}
        # ]
    
    # Analyze results with LLM
    analysis = self.analyze_results(user_query, data, sql_query)
    
    return {
        "answer": analysis,  # Natural language summary
        "sql_query": sql_query,
        "data": data,
        "row_count": len(data),
        "data_source": "PostgreSQL"
    }
```

**File Reference:** `backend/database/postgres_db.py` (SQLAlchemy models + connection)

---

#### **STEP 4D: LLM Analysis of Results**

**File:** `backend/agents/database_agent.py`

**What Happens:**
- LLM converts raw data into natural language

```python
def analyze_results(self, user_query: str, data: List[Dict], sql_query: str) -> str:
    prompt = f"""
    USER ASKED: {user_query}
    
    SQL EXECUTED: {sql_query}
    
    RESULTS:
    {json.dumps(data, indent=2)}
    
    Provide a clear, concise answer summarizing the data.
    """
    
    response = self.client.chat.completions.create(
        model="azure.gpt-4.1",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Returns:
    # "Based on the data, Pepsi Cola had total sales of 125,000 units 
    #  in the Northeast region, while Pepsi Diet had 98,000 units."
    
    return response.choices[0].message.content
```

---

### **STEP 5: Orchestrator Compiles Final Response**

**File:** `backend/agents/orchestrator_agent.py`

**What Happens:**
- Orchestrator receives Database Agent results
- Formats final response

```python
async def orchestrate(self, query: str, context: Dict) -> Dict[str, Any]:
    # ... (workflow execution)
    
    final_state = self.workflow.invoke(initial_state)
    
    return {
        "query": query,
        "answer": final_state["final_answer"],
        "sql_query": final_state["db_result"]["sql_query"],
        "data_source": "PostgreSQL",
        "row_count": final_state["db_result"]["row_count"],
        "raw_data": final_state["db_result"]["data"],
        "visualization": final_state.get("visualization"),
        "status": "success"
    }
```

---

### **STEP 6: Response Sent to Frontend**

**File:** `backend/routes/chatbot.py` → `frontend/components/ChatBox.tsx`

**What Happens:**
- FastAPI returns JSON response
- Frontend displays answer + optional chart

```json
{
  "query": "Show me sales for Pepsi in the Northeast region",
  "answer": "Pepsi Cola had 125,000 units sold in the Northeast region, while Pepsi Diet had 98,000 units.",
  "sql_query": "SELECT p.product, SUM(m.sales_units) as total_sales FROM metrics m JOIN phier p ON m.product_id = p.product_id JOIN locdim l ON m.location = l.location WHERE p.product_id IN ('P12345', 'P12346') AND l.region = 'northeast' GROUP BY p.product",
  "data_source": "PostgreSQL",
  "row_count": 2,
  "raw_data": [
    {"product": "Pepsi Cola", "total_sales": 125000},
    {"product": "Pepsi Diet", "total_sales": 98000}
  ],
  "visualization": null,
  "status": "success"
}
```

---

## 4. File Structure & Components

### **Core Files (Main Workflow)**

| File Path | Purpose | Key Responsibilities |
|-----------|---------|---------------------|
| `backend/main.py` | **Application Entry Point** | FastAPI app initialization, CORS, middleware |
| `backend/routes/chatbot.py` | **Chat API Endpoint** | Receives user queries, calls orchestrator |
| `backend/agents/orchestrator_agent.py` | **Master Brain (LangGraph)** | Intent detection, agent routing, workflow management |
| `backend/agents/database_agent.py` | **Primary Data Agent** | Context resolution, SQL generation, query execution |
| `backend/services/context_resolver.py` | **Entity Resolution** | Azure AI Search + Neo4j/Gremlin integration |
| `backend/database/azure_search.py` | **Vector Search Client** | Semantic search for products, locations, events |
| `backend/database/neo4j_db.py` | **Graph Database Client** | Knowledge graph queries (Gremlin-compatible) |
| `backend/database/postgres_db.py` | **SQL Database** | PostgreSQL models (metrics, phier, locdim, events, weather) |

### **Specialized Agents (Supporting Workers)**

| File Path | Purpose |
|-----------|---------|
| `backend/agents/weather_agent.py` | Analyzes weather impact on supply chain |
| `backend/agents/events_agent.py` | Analyzes holiday/event impact on demand |
| `backend/agents/location_agent.py` | Geographic and regional analysis |
| `backend/agents/inventory_agent.py` | Stock optimization recommendations |
| `backend/agents/visualization_agent.py` | LLM-powered chart generation |

### **Configuration & Utilities**

| File Path | Purpose |
|-----------|---------|
| `backend/core/config.py` | Environment variables (DB credentials, API keys) |
| `backend/core/logger.py` | Structured JSON logging |
| `backend/core/security.py` | JWT authentication (optional) |

---

## 5. MCP Integration (Optional Enhancement)

### **What is MCP?**

**MCP (Model Context Protocol)** is a standardized way to expose tools/functions to external AI systems (like Claude Desktop, ChatGPT plugins, etc.).

### **Current System (Without MCP)**

```
User → Frontend → FastAPI → Orchestrator → Agents → Response
```

**Works perfectly** for the web application.

### **With MCP Enhancement**

**File:** `backend/mcp_server.py`

```
External AI (Claude Desktop, etc.) → MCP Server → Agents → Response
```

**What MCP Adds:**
- Exposes agents as **callable tools** for external AI systems
- No changes to core logic
- Parallel capability to web API

**Example MCP Tool:**

```python
@mcp.tool()
def query_supply_chain_data(query: str) -> str:
    """
    Query Planalytics database using natural language.
    Accessible by external AI assistants via MCP protocol.
    """
    result = db_agent.query_database(query)
    return str(result.get("answer"))
```

**Key Points for Manager:**
1. **Core system works independently** - MCP is optional
2. **No changes to existing agents** - Same code, different interface
3. **Additional capability** - External AI systems can now use our tools
4. **Standard protocol** - Industry-standard (Anthropic, OpenAI support it)

**When to explain this:**
> "Our system is fully functional as a web application. MCP is an **optional enhancement** that allows external AI assistants (like Claude Desktop) to use our agents as tools. It's a parallel interface to the same backend logic - no core changes needed."

---

## 6. Example Query Flow (Complete)

### **Query:** *"Show me a bar chart of sales by region"*

#### **Step-by-Step:**

1. **Frontend** (`components/ChatBox.tsx`)
   - User types query → POST to `/api/v1/chat`

2. **API Endpoint** (`routes/chatbot.py`)
   - Receives request → Calls orchestrator

3. **Orchestrator** (`agents/orchestrator_agent.py`)
   - **Intent Detection:** LLM identifies "visualization" intent
   - **Chart Type Detection:** LLM identifies "bar" chart
   - **Route to:** Database Agent + Visualization Agent

4. **Database Agent** (`agents/database_agent.py`)
   - **Context Resolution** (`services/context_resolver.py`):
     - Azure AI Search: No specific products → Use all
     - Neo4j/Gremlin: Expand to get region metadata
   - **SQL Generation:** LLM writes:
     ```sql
     SELECT l.region, SUM(m.sales_dollars) as total_sales
     FROM metrics m
     JOIN locdim l ON m.location = l.location
     GROUP BY l.region
     ORDER BY total_sales DESC
     ```
   - **Execute:** PostgreSQL returns:
     ```json
     [
       {"region": "northeast", "total_sales": 5200000},
       {"region": "southeast", "total_sales": 4800000},
       {"region": "midwest", "total_sales": 4500000}
     ]
     ```

5. **Visualization Agent** (`agents/visualization_agent.py`)
   - **LLM-Powered Chart Config Generation:**
     ```python
     # LLM analyzes data + user intent
     # Generates Google Charts config:
     {
       "type": "BarChart",
       "data": [
         ["Region", "Sales"],
         ["Northeast", 5200000],
         ["Southeast", 4800000],
         ["Midwest", 4500000]
       ],
       "options": {
         "title": "Sales by Region",
         "hAxis": {"title": "Total Sales ($)"},
         "vAxis": {"title": "Region"}
       }
     }
     ```

6. **Orchestrator Compiles Response**
   - Combines data + chart config + natural language answer

7. **Frontend Renders**
   - `components/GoogleChart.tsx` displays bar chart
   - Chat displays: *"Here's the sales breakdown by region. Northeast leads with $5.2M in sales."*

---

## 7. Key Technologies Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend Framework** | FastAPI (Python) | REST API, async support |
| **Orchestration** | LangGraph | Multi-agent workflow management |
| **LLM** | Azure OpenAI GPT-4 | Intent detection, SQL generation, analysis |
| **Vector Search** | Azure AI Search | Semantic entity resolution |
| **Knowledge Graph** | Neo4j (Gremlin API) | Relationship expansion |
| **Database** | PostgreSQL | Transactional data storage |
| **Frontend** | Next.js + React | User interface |
| **Charts** | Google Charts | Data visualization |
| **Optional** | MCP (FastMCP) | External AI tool exposure |

---

## 8. Talking Points for Manager

### **Without MCP (Current Fully Functional System):**

1. **User Query Processing:**
   - "When a user asks a question, our orchestrator uses LangGraph to detect intent and route to the right agents."

2. **Smart Entity Resolution:**
   - "We don't just search databases directly. First, Azure AI Search resolves vague terms like 'Pepsi' to exact product IDs. Then, our Neo4j graph expands context - finding related products in the same category."

3. **AI-Powered SQL Generation:**
   - "Instead of hardcoding queries, Azure OpenAI GPT-4 writes SQL dynamically based on the user's question and the resolved context. This handles unlimited query variations."

4. **Real Data from PostgreSQL:**
   - "All answers come from actual data in PostgreSQL - no mock data. We query metrics, product hierarchy, locations, events, and weather tables."

5. **Intelligent Visualization:**
   - "If a user asks for a chart, our Visualization Agent uses the LLM to analyze the data and generate optimal chart configurations - no hardcoded rules."

### **With MCP (Optional Enhancement):**

6. **MCP as a Parallel Interface:**
   - "MCP doesn't change our core system. It's a standardized protocol that exposes our existing agents as tools for external AI assistants like Claude Desktop."

7. **Same Logic, Different Entry Point:**
   - "The same Database Agent, Weather Agent, etc., work identically. MCP is just another way to call them - alongside our web API."

8. **Future-Proofing:**
   - "MCP is becoming an industry standard (Anthropic, OpenAI support it). Adding it now positions us to integrate with any MCP-compatible AI system in the future."

---

## 9. Quick Reference: Where is What?

**"How do we handle user queries?"**
- Entry: `backend/routes/chatbot.py` (line 28)
- Orchestration: `backend/agents/orchestrator_agent.py` (line 128)

**"How do we resolve vague terms like 'Pepsi'?"**
- Azure AI Search: `backend/database/azure_search.py` (line 52)
- Context Resolver: `backend/services/context_resolver.py` (line 21)

**"How do we generate SQL queries?"**
- Database Agent: `backend/agents/database_agent.py` (line 112)
- Uses Azure OpenAI GPT-4 to write SQL dynamically

**"How do we connect to PostgreSQL?"**
- Database Models: `backend/database/postgres_db.py` (line 1)
- Connection Manager: Same file (line 134)

**"How do we expand context using the knowledge graph?"**
- Neo4j/Gremlin Client: `backend/database/neo4j_db.py` (line 105)
- Called by Context Resolver: `backend/services/context_resolver.py` (line 90)

**"How do we generate charts?"**
- Visualization Agent: `backend/agents/visualization_agent.py` (line 96)
- Uses LLM to analyze data and create chart configs

**"What's MCP and where is it?"**
- MCP Server: `backend/mcp_server.py` (line 1)
- Optional - exposes agents to external AI systems
- Doesn't modify core logic

---

## 10. Data Ingestion (Separate Process)

**Important Note:** Data ingestion (Excel → Databases) is **handled separately**.

**Process (Not in this codebase):**
1. Excel files uploaded manually or via ETL pipeline
2. Data extracted and transformed
3. Stored in:
   - **PostgreSQL** (metrics, phier, locdim, events, weather tables)
   - **Azure AI Search** (indexed for semantic search)
   - **Neo4j/Gremlin** (knowledge graph relationships)

**This System Only Queries Existing Data:**
- We assume data is already in the databases
- Our agents **read and analyze** - no writes during query processing

**Files That Handle Ingestion (For Reference Only):**
- `backend/services/data_ingestion.py` (legacy - not actively used in query flow)
- Actual ingestion likely done by separate ETL tools

---

## Conclusion

This system demonstrates a **production-grade multi-agent AI architecture** with:

✅ **Intelligent Query Understanding** (LangGraph orchestration)  
✅ **Smart Entity Resolution** (Azure AI Search + Neo4j/Gremlin)  
✅ **Dynamic SQL Generation** (Azure OpenAI GPT-4)  
✅ **Real-Time Data Access** (PostgreSQL)  
✅ **AI-Powered Visualizations** (LLM-generated charts)  
✅ **Optional External Integration** (MCP protocol)

**Key Message for Manager:**
> "Our system uses cutting-edge AI agents to intelligently understand queries, resolve entities, generate SQL dynamically, and fetch real data from PostgreSQL. MCP is an optional enhancement that exposes these same capabilities to external AI systems - no changes to core logic required."

---

**Document Version:** 1.0  
**Last Updated:** December 2, 2025  
**Author:** Development Team
