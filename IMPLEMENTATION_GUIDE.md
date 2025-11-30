# Enhanced RAG Pipeline - Implementation Guide

## 🎯 Overview

The chatbot has been upgraded from **hardcoded schema prompts** to a **scalable hybrid RAG architecture** using:
- **Azure AI Search** for entity resolution (products, locations, dates, events)
- **Neo4j Knowledge Graph** for context expansion (hierarchies, relationships)
- **PostgreSQL** for transactional data queries

This makes the system **scalable** - adding new tables or data doesn't require changing prompts.

---

## 🏗️ Architecture

### Old Approach (Hardcoded)
```
User Query → LLM with hardcoded schema → SQL → PostgreSQL → Answer
```
**Problem**: LLM must memorize exact table/column names. Fails on vague queries.

### New Approach (Hybrid RAG)
```
User Query 
  ↓
Azure AI Search (resolve entities: "Pepsi" → product_ids)
  ↓
Neo4j Graph (expand context: find all soda products, all Texas stores)
  ↓
LLM (generate SQL with full context)
  ↓
PostgreSQL (execute query)
  ↓
Answer
```

---

## 📁 New Files Created

### 1. `backend/database/azure_search.py`
**Purpose**: Azure AI Search client for all 7 indexes

**Key Features**:
- Vector search with embeddings (1536 dimensions)
- 7 indexes: products, locations, events, calendar, sales-metadata, weather-metadata, metrics-metadata
- Entity resolution: "Pepsi" → exact product IDs
- Semantic search: handles synonyms and variations

**Usage**:
```python
from database.azure_search import azure_search

# Search for products
products = azure_search.search_products("Diet Pepsi", top_k=5)
# Returns: [{"id": "P-101", "product_name": "Diet Pepsi 12oz", ...}, ...]

# Search for locations
stores = azure_search.search_locations("Texas", top_k=20)
# Returns: [{"id": "ST0001", "store_name": "Dallas Store 1", "state": "Texas", ...}, ...]

# Resolve all entities at once
entities = azure_search.resolve_entities("Show me Pepsi sales in Texas during summer")
# Returns: {
#   "products": [...],
#   "locations": [...],
#   "dates": [...],
#   "events": [...]
# }
```

### 2. `backend/services/context_resolver.py`
**Purpose**: Orchestrates Azure Search + Neo4j for context resolution

**Key Features**:
- Combines Azure Search entity resolution with Neo4j graph expansion
- Generates comprehensive prompts for SQL generation
- Formats context summaries for logging/debugging

**Usage**:
```python
from services.context_resolver import context_resolver

# Resolve full context for a query
context = context_resolver.resolve_query_context(
    "What are ice cream sales in California stores during summer?"
)

# Returns:
# {
#   "products": {
#     "resolved": [{"id": "P-15", "product_name": "Vanilla Ice Cream"}],
#     "expanded": [{"product_id": "P-15"}, {"product_id": "P-16"}, ...]  # All ice cream products
#   },
#   "locations": {
#     "resolved": [{"id": "ST0050", "store_name": "Los Angeles Store"}],
#     "expanded": [{"store_id": "ST0050"}, {"store_id": "ST0051"}, ...]  # All CA stores
#   },
#   "dates": {
#     "resolved": [...],
#     "date_range": ("2023-06-01", "2023-08-31")  # Summer dates
#   },
#   ...
# }

# Generate SQL prompt with context
prompt = context_resolver.get_sql_generation_prompt(user_query, context)
```

### 3. `backend/database/neo4j_db.py` (Enhanced)
**Purpose**: Neo4j knowledge graph with context expansion methods

**New Methods**:
```python
from database.neo4j_db import neo4j_conn

# Expand product context (find related products in same category)
product_ids = ["P-101", "P-102"]
related = neo4j_conn.expand_product_context(product_ids)
# Returns: All products in same category as Pepsi

# Expand location context (find all stores in same region/market)
store_ids = ["ST0001"]
all_stores = neo4j_conn.expand_location_context(store_ids)
# Returns: All stores in same market as ST0001

# Find related events
events = neo4j_conn.find_related_events(
    location_ids=["ST0001", "ST0002"],
    dates=["2023-02-12", "2023-02-13"]
)
# Returns: All events at those stores during those dates

# Get hierarchies
product_hierarchy = neo4j_conn.get_product_hierarchy("P-101")
# Returns: {"department": "Beverages", "category": "Soda", "product_name": "Pepsi"}

location_hierarchy = neo4j_conn.get_location_hierarchy("ST0001")
# Returns: {"region": "West", "state": "CA", "market": "Los Angeles", "store_name": "..."}
```

### 4. `backend/agents/database_agent.py` (Refactored)
**Purpose**: Database agent now uses RAG pipeline instead of hardcoded schema

**Changes**:
- ❌ Removed: Hardcoded schema in system prompt
- ✅ Added: Dynamic context resolution via Azure Search + Neo4j
- ✅ Added: Context-aware SQL generation
- ✅ Added: Context summary in responses

**New Workflow**:
```python
from agents.database_agent import DatabaseAgent

agent = DatabaseAgent()
result = agent.query_database("Show me Pepsi sales in Texas")

# Internally:
# 1. Resolves entities: "Pepsi" → ["P-101", "P-102"], "Texas" → ["ST0001", "ST0002", ...]
# 2. Expands via Neo4j: All soda products, all Texas stores
# 3. Generates SQL with full context
# 4. Executes on PostgreSQL
# 5. Returns results + context summary

print(result["context_summary"])
# Output: "✓ 2 products identified | ✓ Expanded to 5 related products | ✓ 25 locations identified..."
```

### 5. `backend/test_rag_pipeline.py`
**Purpose**: Comprehensive test suite for the RAG pipeline

**Run Tests**:
```bash
cd backend
python test_rag_pipeline.py
```

**Tests**:
1. **Entity Resolution**: Test Azure Search entity resolution
2. **Context Expansion**: Test Neo4j graph expansion
3. **Full Pipeline**: Test end-to-end (Search → Graph → SQL → PostgreSQL)

---

## 🔧 Configuration

### Updated `backend/core/config.py`
Added new settings:
```python
# Azure AI Search
AZURE_SEARCH_ENDPOINT: str
AZURE_SEARCH_KEY: str

# Azure OpenAI Embeddings
AZURE_OPENAI_ENDPOINT: str
AZURE_OPENAI_API_KEY: str
AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str
```

### Updated `backend/requirements.txt`
Added Azure SDK packages:
```txt
azure-search-documents==11.6.0b7
azure-core==1.32.0
azure-identity==1.19.0
```

### Environment Variables (`.env`)
Copy `.env.example` and configure:
```bash
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://u7zxunxhadcs001.search.windows.net
AZURE_SEARCH_KEY=YOUR_AZURE_SEARCH_KEY

# Azure OpenAI Embeddings
AZURE_OPENAI_ENDPOINT=https://genai-sharedservice-americas.pwc.com
AZURE_OPENAI_API_KEY=YOUR_AZURE_OPENAI_API_KEY
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=azure.text-embedding-ada-002
```

---

## 🚀 Installation & Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example and edit with your credentials
copy .env.example .env
# Edit .env with your Azure Search endpoint, keys, etc.
```

### 3. Verify Azure AI Search Indexes
All 7 indexes should be populated:
- ✅ `planalytics-data-index-products` (27 products)
- ✅ `planalytics-data-index-locations` (183 stores)
- ✅ `planalytics-data-index-events` (17,695 events)
- ✅ `planalytics-data-index-calendar` (469 dates)
- ✅ `planalytics-data-index-sales-metadata` (4,792 docs)
- ✅ `planalytics-data-index-weather-metadata` (158 docs)
- ✅ `planalytics-data-index-metrics-metadata` (1 doc)

### 4. Verify Neo4j Knowledge Graph
Ensure Neo4j is running and populated with:
- ✅ Product hierarchy (Department → Category → Product)
- ✅ Location hierarchy (Region → State → Market → Store)
- ✅ Calendar hierarchy (Year → Quarter → Month → Week → Date)
- ✅ Event nodes and relationships

### 5. Test the Pipeline
```bash
python test_rag_pipeline.py
```

Expected output:
```
TEST 1: Entity Resolution (Azure AI Search)
✓ Products found: 2
  - Diet Pepsi 12oz Can (ID: P-101)
  - Pepsi 2L Bottle (ID: P-102)
✓ Locations found: 25
  - Dallas Store 1 (Texas) (ID: ST0001)
  ...

TEST 2: Context Expansion (Neo4j Knowledge Graph)
1️⃣ Initial entities from Azure Search:
   Products: 2
   Locations: 25
2️⃣ After Neo4j expansion:
   Expanded Products: 5
   Expanded Locations: 50
   ...

TEST 3: Full RAG Pipeline
✅ SUCCESS
📊 Context: ✓ 2 products identified | ✓ Expanded to 5 related products | ✓ 25 locations identified
💾 Generated SQL:
SELECT ...
📈 Results: 42 rows returned
```

---

## 📊 How It Works - Example Query

### User Query
```
"Show me Pepsi sales in Texas during summer 2023"
```

### Step 1: Azure AI Search - Entity Resolution
```python
entities = azure_search.resolve_entities(query)

# Results:
# products: [
#   {"id": "P-101", "product_name": "Diet Pepsi 12oz"},
#   {"id": "P-102", "product_name": "Pepsi 2L"}
# ]
# locations: [
#   {"id": "ST0001", "store_name": "Dallas Store 1", "state": "Texas"},
#   {"id": "ST0002", "store_name": "Houston Store 1", "state": "Texas"},
#   ... (25 Texas stores)
# ]
# dates: [
#   {"date": "2023-06-01", "season": "Summer"},
#   {"date": "2023-06-02", "season": "Summer"},
#   ... (92 summer dates)
# ]
```

### Step 2: Neo4j - Context Expansion
```python
expanded = neo4j_conn.expand_product_context(["P-101", "P-102"])

# Results:
# expanded_products: [
#   {"product_id": "P-101", "category": "Soda"},
#   {"product_id": "P-102", "category": "Soda"},
#   {"product_id": "P-103", "category": "Soda"},  # Related: Coca-Cola
#   {"product_id": "P-104", "category": "Soda"},  # Related: Sprite
#   {"product_id": "P-105", "category": "Soda"}   # Related: Dr Pepper
# ]
# expanded_locations: All 50 stores in Texas market
```

### Step 3: LLM - SQL Generation with Context
```python
prompt = f"""
User Query: Show me Pepsi sales in Texas during summer 2023

Resolved Entities:
- Products: P-101 (Diet Pepsi), P-102 (Pepsi 2L) (expanded to 5 soda products)
- Stores: ST0001, ST0002, ... (25 stores in Texas)
- Date Range: 2023-06-01 to 2023-08-31 (Summer)

Database Schema:
- metrics (product, location, end_date, metric, metric_nrm, product_id)
  * 'metric' = sales value (use SUM(metric) for total sales)
- locdim (location, region, market, state)
- phier (product_id, dept, category, product)

Generate PostgreSQL SELECT query:
"""

# LLM generates:
sql = """
SELECT 
    p.product AS product_name,
    l.state,
    SUM(m.metric) AS total_sales
FROM metrics m
JOIN locdim l ON m.location = l.location
JOIN phier p ON m.product_id = p.product_id
WHERE m.product_id IN ('P-101', 'P-102')
  AND l.state = 'Texas'
  AND m.end_date BETWEEN '2023-06-01' AND '2023-08-31'
GROUP BY p.product, l.state
ORDER BY total_sales DESC
LIMIT 50
"""
```

### Step 4: PostgreSQL - Execute Query
```python
results = execute_sql(sql)

# Returns:
# [
#   {"product_name": "Pepsi 2L Bottle", "state": "Texas", "total_sales": 15420},
#   {"product_name": "Diet Pepsi 12oz", "state": "Texas", "total_sales": 12350}
# ]
```

---

## ✅ Benefits of New Architecture

| Feature | Old (Hardcoded) | New (RAG Pipeline) |
|---------|----------------|-------------------|
| **Scalability** | ❌ Must update prompts for new tables | ✅ Automatically handles new data |
| **Accuracy** | ⚠️ Fails on vague queries | ✅ Resolves vague terms to exact IDs |
| **Context Awareness** | ❌ No hierarchy understanding | ✅ Expands via knowledge graph |
| **Maintainability** | ❌ Schema changes break prompts | ✅ Dynamic schema resolution |
| **Performance** | ⚠️ LLM must memorize schema | ✅ Fast lookups in Search + Graph |

---

## 🧪 Example Queries That Now Work Better

### Query 1: Vague Product Names
```
"Show me soda sales"
```
**Old**: LLM guesses product names, might miss some
**New**: Azure Search finds ALL soda products (Pepsi, Coke, Sprite, etc.)

### Query 2: Geographic Hierarchies
```
"Sales in the West region"
```
**Old**: LLM must know which states are in West region
**New**: Neo4j graph automatically expands to all West region states

### Query 3: Seasonal Queries
```
"Summer sales trends"
```
**Old**: LLM must calculate summer date ranges
**New**: Calendar index knows exactly which dates are Summer

### Query 4: Event Context
```
"Sales during Super Bowl"
```
**Old**: LLM doesn't know Super Bowl dates or locations
**New**: Events index + Neo4j graph knows exact dates and affected stores

---

## 📝 Backward Compatibility

**Good news**: Existing code still works! The refactored `database_agent.py` maintains the same public interface:

```python
# Old code (still works)
agent = DatabaseAgent()
result = agent.query_database("Show me sales")

# Returns same structure:
# {
#   "agent": "database",
#   "sql_query": "...",
#   "data": [...],
#   "status": "success"
# }
```

New field added:
```python
result["context_summary"]  # NEW: Shows what entities were resolved
```

---

## 🔍 Debugging & Monitoring

### Check Logs
```python
# Logs show the full pipeline:
# 🔍 Resolving context for query: ...
# 📊 Context: ✓ 2 products identified | ✓ Expanded to 5 related products | ...
# Generated SQL: SELECT ...
# ✅ Query returned 42 rows
```

### Test Individual Components
```python
# Test Azure Search only
from database.azure_search import azure_search
products = azure_search.search_products("Pepsi")

# Test Neo4j only
from database.neo4j_db import neo4j_conn
expanded = neo4j_conn.expand_product_context(["P-101"])

# Test context resolver only
from services.context_resolver import context_resolver
context = context_resolver.resolve_query_context("Pepsi sales in Texas")
```

---

## 🚨 Troubleshooting

### Issue: "Index not found"
**Solution**: Verify Azure Search indexes are created and populated
```bash
# Check .env file
AZURE_SEARCH_ENDPOINT=https://...
AZURE_SEARCH_KEY=...
```

### Issue: "Neo4j unavailable"
**Solution**: Ensure Neo4j is running
```bash
# Check Neo4j status
neo4j status

# Start if needed
neo4j start
```

### Issue: "No entities resolved"
**Solution**: Check if indexes have data
```python
from database.azure_search import azure_search
results = azure_search.search_products("test", top_k=1)
print(f"Found {len(results)} products")
```

---

## 📚 Next Steps

1. **Monitor Performance**: Track query latency (Search + Graph + SQL)
2. **Optimize Caching**: Cache frequently used entity resolutions
3. **Add More Indexes**: Create indexes for new data sources
4. **Enhance Graph**: Add more relationship types in Neo4j
5. **Fine-tune Prompts**: Adjust SQL generation prompts based on query patterns

---

**Status**: ✅ Fully implemented and tested
**Author**: GitHub Copilot
**Date**: November 30, 2025
