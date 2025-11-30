# Planalytics Agentic AI - Integration Guide
**Architecture**: Azure AI Search → Neo4j Knowledge Graph → PostgreSQL

---

## 🔧 Environment Configuration

### Azure AI Search Configuration
```bash
AZURE_SEARCH_ENDPOINT=https://u7zxunxhadcs001.search.windows.net
AZURE_SEARCH_KEY=YOUR_AZURE_SEARCH_KEY
```

### Azure OpenAI Embeddings Configuration
```bash
AZURE_OPENAI_ENDPOINT=https://genai-sharedservice-americas.pwc.com
AZURE_OPENAI_API_KEY=YOUR_AZURE_OPENAI_API_KEY
AZURE_OPENAI_DEPLOYMENT_NAME=azure.text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=azure.text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2024-08-06
```

### Neo4j Knowledge Graph Configuration
```bash
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

### PostgreSQL Database Configuration
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=planalytics_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
```

### LLM Configuration
```bash
OPENAI_ENDPOINT=https://genai-sharedservice-americas.pwc.com
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL_NAME=openai.gpt-4o
```

---

## 📊 Azure AI Search Indexes

### Master Data Indexes (Full Data + Embeddings - 1536 dimensions)

#### 1. Products Index
- **Index Name**: `planalytics-data-index-products`
- **Document Count**: 27 products
- **Purpose**: Translate product names to product IDs
- **Fields**: 
  - `id` (product_id)
  - `product_name` (searchable)
  - `category` (filterable)
  - `department` (filterable)
  - `description` (searchable with embedding vector)

#### 2. Locations Index
- **Index Name**: `planalytics-data-index-locations`
- **Document Count**: 183 stores
- **Purpose**: Translate location names to store IDs
- **Fields**:
  - `id` (store_id)
  - `store_name` (searchable)
  - `market` (filterable)
  - `state` (filterable)
  - `region` (filterable)
  - `description` (searchable with embedding vector)

#### 3. Events Index
- **Index Name**: `planalytics-data-index-events`
- **Document Count**: 17,695 events
- **Purpose**: Find events by name or date
- **Fields**:
  - `id` (event_id)
  - `event_name` (searchable)
  - `date` (filterable)
  - `store_id` (filterable)
  - `description` (searchable with embedding vector)

#### 4. Calendar Index
- **Index Name**: `planalytics-data-index-calendar`
- **Document Count**: 469 dates
- **Purpose**: Resolve date ranges and seasons
- **Fields**:
  - `id` (date_id)
  - `date` (filterable)
  - `year` (filterable)
  - `month` (filterable)
  - `quarter` (filterable)
  - `season` (filterable: Spring, Summer, Fall, Winter)
  - `description` (searchable with embedding vector)

### Metadata Indexes (Schema + Aggregations - No Embeddings)

#### 5. Sales/Inventory Metadata Index
- **Index Name**: `planalytics-data-index-sales-metadata`
- **Document Count**: 4,792 store-product combinations
- **Purpose**: Understand what sales data exists (NOT the actual sales data)
- **What's Stored**:
  - Store-Product combinations that have data
  - Date ranges per combination
  - Schema information (column names)
  - Record counts
- **Fields**:
  - `id` (metadata_id)
  - `entity_type` (StoreProductCombination or DatasetSchema)
  - `store_id`
  - `product_id`
  - `min_date`, `max_date`
  - `record_count`
  - `available_metrics`
  - `description`

#### 6. Weather Metadata Index
- **Index Name**: `planalytics-data-index-weather-metadata`
- **Document Count**: 158 weather metadata documents
- **Purpose**: Understand what weather data exists (NOT the actual weather data)
- **What's Stored**:
  - Available weather conditions
  - Store-date coverage
  - Heatwave/coldspell flags
  - Schema information
- **Fields**:
  - `id` (metadata_id)
  - `entity_type` (StoreWeatherCoverage or DatasetSchema)
  - `store_id`
  - `min_date`, `max_date`
  - `record_count`
  - `available_conditions`
  - `description`

#### 7. Metrics (WDD) Metadata Index
- **Index Name**: `planalytics-data-index-metrics-metadata`
- **Document Count**: 1 schema document
- **Purpose**: Understand WDD metrics schema (NOT the actual WDD data)
- **What's Stored**:
  - Schema information for WDD metrics
  - Weather-sensitive product-store combinations
  - WDD ranges (high/low)
- **Fields**:
  - `id` (metadata_id)
  - `entity_type` (DatasetSchema)
  - `record_count`
  - `available_metrics`
  - `description`

---

## 🕸️ Neo4j Knowledge Graph

### What's Stored in Neo4j
**Purpose**: Store hierarchical relationships and context (NOT transactional data)

### Node Types & Counts

#### 1. Location Hierarchy (183 stores total)
```cypher
# Node Structure:
Region (n=10)
  └─> State (n=50)
      └─> Market (n=75)
          └─> Store (n=183)

# Relationships:
(Store)-[:IN_MARKET]->(Market)
(Market)-[:IN_STATE]->(State)
(State)-[:IN_REGION]->(Region)

# Example Query:
MATCH (s:Store)-[:IN_MARKET]->(m:Market)-[:IN_STATE]->(st:State {name: 'Texas'})
RETURN s.store_id, s.name
# Returns: All stores in Texas
```

#### 2. Product Hierarchy (27 products total)
```cypher
# Node Structure:
Department (n=5)
  └─> Category (n=15)
      └─> Product (n=27)

# Relationships:
(Product)-[:IN_CATEGORY]->(Category)
(Category)-[:IN_DEPARTMENT]->(Department)

# Example Query:
MATCH (p:Product)-[:IN_CATEGORY]->(c:Category {name: 'Soda'})
RETURN p.product_id, p.name
# Returns: All soda products
```

#### 3. Calendar Hierarchy (469 dates)
```cypher
# Node Structure:
Year (n=3: 2023, 2024, 2025)
  └─> Quarter (n=12)
      └─> Month (n=36)
          └─> Week (n=156)
              └─> Date (n=469)

# Relationships:
(Date)-[:IN_WEEK]->(Week)
(Week)-[:IN_MONTH]->(Month)
(Month)-[:IN_QUARTER]->(Quarter)
(Quarter)-[:IN_YEAR]->(Year)

# Properties:
Date.season = 'Spring' | 'Summer' | 'Fall' | 'Winter'
Date.date = '2023-01-01'

# Example Query:
MATCH (d:Date)-[:IN_MONTH]->(m:Month {name: 'March'})
WHERE d.season = 'Spring'
RETURN d.date
# Returns: All March dates in Spring
```

#### 4. Events (17,695 events)
```cypher
# Node Structure:
Event (n=17,695)

# Relationships:
(Event)-[:OCCURS_ON]->(Date)
(Event)-[:AT_STORE]->(Store)

# Properties:
Event.event_name = 'Super Bowl'
Event.event_id = unique identifier
Event.date = '2023-02-12'
Event.store_id = 'ST0001'

# Example Query:
MATCH (e:Event {event_name: 'Super Bowl'})-[:AT_STORE]->(s:Store)
RETURN s.store_id, s.name, e.date
# Returns: All stores with Super Bowl events
```

### Neo4j Use Cases
1. **Geographic Expansion**: Find all stores in a region/state/market
2. **Product Categories**: Find all products in a department/category
3. **Date Ranges**: Find all dates in a quarter/month/season
4. **Event Context**: Find which stores had which events on which dates

---

## 🐘 PostgreSQL Tables

### What's Stored in PostgreSQL
**Purpose**: Store ALL transactional data for aggregations and calculations

### Tables & Row Counts

#### 1. SalesInventory Table
- **Table Name**: `inventory`
- **Row Count**: ~208,000 rows
- **Columns**:
  - `store_id` (FK to stores)
  - `product_id` (FK to products)
  - `end_date` (date of record)
  - `sales` (units sold)
  - `inventory_start` (beginning inventory)
  - `inventory_end` (ending inventory)
- **Use Case**: Calculate total sales, average inventory, turnover rates

#### 2. Weather Table
- **Table Name**: `weather`
- **Row Count**: ~26,000 rows
- **Columns**:
  - `store_id` (FK to stores)
  - `end_date` (date of record)
  - `temp_high` (daily high temperature)
  - `temp_low` (daily low temperature)
  - `precipitation` (rainfall amount)
  - `condition` (sunny, rainy, etc.)
  - `is_heatwave` (boolean)
  - `is_coldspell` (boolean)
- **Use Case**: Analyze weather impact on sales

#### 3. Metrics (WDD) Table
- **Table Name**: `metrics`
- **Row Count**: ~1,000,000 rows
- **Columns**:
  - `store_id` (FK to stores)
  - `product_id` (FK to products)
  - `end_date` (date of record)
  - `wdd_value` (weather-driven demand metric)
  - `demand_category` (high/medium/low)
- **Use Case**: Calculate weather-driven demand patterns

#### 4. Master Tables
- **stores** (183 rows): Store master data
- **products** (27 rows): Product master data
- **calendar** (469 rows): Date dimension

---

## 🤖 Agent Workflow (Three-Step Architecture)

### Current Approach (Direct SQL - Not Scalable)
```
User Query → LLM → SQL Query → PostgreSQL → Answer
```
**Problem**: LLM must know exact table/column names, doesn't handle vague queries well

### Recommended Approach (Hybrid RAG - Scalable)
```
User Query → Azure AI Search → Neo4j Graph → SQL Generator → PostgreSQL → Answer
```

### Step-by-Step Process

#### Step 1: Entity Resolution (Azure AI Search)
**Purpose**: Translate vague user terms to exact IDs

```python
# Example User Query: "Show me Pepsi sales in Texas stores during summer"

# Step 1A: Search for Products
from azure.search.documents import SearchClient

product_client = SearchClient(
    endpoint="https://u7zxunxhadcs001.search.windows.net",
    index_name="planalytics-data-index-products",
    credential=AzureKeyCredential("YOUR_AZURE_SEARCH_KEY")
)

results = product_client.search(search_text="Pepsi", top=5)
# Returns: product_id='P-101', product_name='Diet Pepsi 12oz Can'
#          product_id='P-102', product_name='Pepsi 2L Bottle'

# Step 1B: Search for Locations
location_client = SearchClient(
    endpoint="https://u7zxunxhadcs001.search.windows.net",
    index_name="planalytics-data-index-locations",
    credential=AzureKeyCredential("YOUR_AZURE_SEARCH_KEY")
)

results = location_client.search(
    search_text="Texas",
    filter="state eq 'Texas'",
    top=100
)
# Returns: store_id='ST0001', store_id='ST0002', ... (all Texas stores)

# Step 1C: Search for Date Ranges
calendar_client = SearchClient(
    endpoint="https://u7zxunxhadcs001.search.windows.net",
    index_name="planalytics-data-index-calendar",
    credential=AzureKeyCredential("YOUR_AZURE_SEARCH_KEY")
)

results = calendar_client.search(
    search_text="summer",
    filter="season eq 'Summer' and year eq 2023",
    top=100
)
# Returns: All summer dates in 2023
```

#### Step 2: Context Expansion (Neo4j Knowledge Graph)
**Purpose**: Find related entities using relationships

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "neo4j://127.0.0.1:7687",
    auth=("neo4j", "password")
)

# Step 2A: Expand Product Context
with driver.session() as session:
    result = session.run("""
        MATCH (p:Product {product_id: 'P-101'})-[:IN_CATEGORY]->(c:Category)
        MATCH (c)<-[:IN_CATEGORY]-(related:Product)
        RETURN related.product_id, related.name
    """)
    # Returns: All products in the same category as Pepsi

# Step 2B: Expand Location Context
with driver.session() as session:
    result = session.run("""
        MATCH (s:Store)-[:IN_STATE]->(st:State {name: 'Texas'})
        RETURN s.store_id, s.name
    """)
    # Returns: All 25 stores in Texas (not just matching search term)

# Step 2C: Check Event Context
with driver.session() as session:
    result = session.run("""
        MATCH (e:Event)-[:OCCURS_ON]->(d:Date)
        WHERE d.date >= '2023-06-01' AND d.date <= '2023-08-31'
        MATCH (e)-[:AT_STORE]->(s:Store)
        WHERE s.store_id IN ['ST0001', 'ST0002', ...]
        RETURN e.event_name, e.date, s.store_id
    """)
    # Returns: All events during summer at Texas stores
```

#### Step 3: SQL Generation & Execution (PostgreSQL)
**Purpose**: Generate accurate SQL with full context

```python
import psycopg

# Context from Steps 1 & 2:
product_ids = ['P-101', 'P-102']  # From Azure Search
store_ids = ['ST0001', 'ST0002', ...]  # From Neo4j Graph
date_range = ('2023-06-01', '2023-08-31')  # From Calendar Search
events = [('Super Bowl', '2023-02-12'), ...]  # From Graph

# Generate SQL with LLM using context
llm_prompt = f"""
Given the following context:
- Products: {product_ids}
- Stores: {store_ids}
- Date Range: {date_range}
- Events during period: {events}

Generate a SQL query to calculate total sales for these products at these stores during the date range.

Available tables:
- inventory (store_id, product_id, end_date, sales, inventory_start, inventory_end)
- weather (store_id, end_date, temp_high, temp_low, condition)
- metrics (store_id, product_id, end_date, wdd_value)

Generate the SQL query:
"""

# LLM generates:
sql_query = """
SELECT 
    s.store_name,
    p.product_name,
    SUM(i.sales) as total_sales,
    AVG(w.temp_high) as avg_temp
FROM inventory i
JOIN stores s ON i.store_id = s.store_id
JOIN products p ON i.product_id = p.product_id
LEFT JOIN weather w ON i.store_id = w.store_id AND i.end_date = w.end_date
WHERE i.product_id IN ('P-101', 'P-102')
  AND i.store_id IN ('ST0001', 'ST0002', ...)
  AND i.end_date BETWEEN '2023-06-01' AND '2023-08-31'
GROUP BY s.store_name, p.product_name
ORDER BY total_sales DESC
"""

# Execute on PostgreSQL
conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="planalytics_db",
    user="postgres",
    password="password"
)

with conn.cursor() as cur:
    cur.execute(sql_query)
    results = cur.fetchall()
    
# Return formatted answer to user
```

---

## 📋 Data Distribution Summary

| Data Type | Azure AI Search | Neo4j Graph | PostgreSQL |
|-----------|----------------|-------------|------------|
| **Products (27)** | ✅ Full data + embeddings | ✅ Hierarchy nodes | ✅ Master table |
| **Locations (183)** | ✅ Full data + embeddings | ✅ Hierarchy nodes | ✅ Master table |
| **Events (17,695)** | ✅ Full data + embeddings | ✅ Event nodes + relationships | ❌ Not stored |
| **Calendar (469)** | ✅ Full data + embeddings | ✅ Hierarchy nodes | ✅ Master table |
| **Sales (208K)** | ⚠️ Metadata only (4,792 docs) | ❌ Not stored | ✅ Full transactional data |
| **Weather (26K)** | ⚠️ Metadata only (158 docs) | ❌ Not stored | ✅ Full transactional data |
| **Metrics (1M)** | ⚠️ Metadata only (1 doc) | ❌ Not stored | ✅ Full transactional data |

### Why This Architecture?

#### Azure AI Search
- **Fast semantic search** for vague terms ("Pepsi" → exact product IDs)
- **Vector embeddings** handle synonyms and variations
- **Metadata indexes** tell agent what data exists without storing millions of rows

#### Neo4j Knowledge Graph
- **Relationship traversal** (find all stores in a region)
- **Context expansion** (find related products/categories)
- **Hierarchical queries** (drill up/down location/product/time hierarchies)

#### PostgreSQL
- **Aggregation performance** (SUM, AVG, COUNT over millions of rows)
- **Relational integrity** (enforced foreign keys)
- **Complex analytics** (window functions, CTEs, JOINs)

---

## 🔄 Migration from Current Code

### Current Code Pattern (Direct SQL)
```python
# Your current approach (schema-based)
prompt = f"""
Database Schema:
- inventory table: store_id, product_id, end_date, sales
- stores table: store_id, store_name, state, region
- products table: product_id, product_name, category

User Query: {user_query}

Generate SQL:
"""
sql = llm.generate(prompt)
results = execute_sql(sql)
```

### Recommended Code Pattern (Hybrid RAG)
```python
# Step 1: Resolve entities with Azure AI Search
def resolve_entities(user_query: str):
    # Search products
    products = search_azure_index("planalytics-data-index-products", user_query)
    
    # Search locations
    locations = search_azure_index("planalytics-data-index-locations", user_query)
    
    # Search dates/seasons
    dates = search_azure_index("planalytics-data-index-calendar", user_query)
    
    return {
        "product_ids": [p['id'] for p in products],
        "store_ids": [l['id'] for l in locations],
        "date_range": extract_date_range(dates)
    }

# Step 2: Expand context with Neo4j
def expand_context(entities: dict):
    # Get all related products (same category)
    all_products = query_neo4j(f"""
        MATCH (p:Product)-[:IN_CATEGORY]->(c:Category)
        WHERE p.product_id IN {entities['product_ids']}
        MATCH (c)<-[:IN_CATEGORY]-(related:Product)
        RETURN related.product_id
    """)
    
    # Get all stores in same region/market
    all_stores = query_neo4j(f"""
        MATCH (s:Store)-[:IN_MARKET]->(m:Market)
        WHERE s.store_id IN {entities['store_ids']}
        MATCH (m)<-[:IN_MARKET]-(other:Store)
        RETURN other.store_id
    """)
    
    # Check for events in date range
    events = query_neo4j(f"""
        MATCH (e:Event)-[:OCCURS_ON]->(d:Date)
        WHERE d.date >= '{entities['date_range'][0]}'
          AND d.date <= '{entities['date_range'][1]}'
        RETURN e.event_name, d.date
    """)
    
    return {
        "expanded_products": all_products,
        "expanded_stores": all_stores,
        "relevant_events": events
    }

# Step 3: Generate SQL with full context
def generate_sql_with_context(user_query: str, entities: dict, context: dict):
    prompt = f"""
    User Query: {user_query}
    
    Resolved Entities:
    - Products: {entities['product_ids']} (expanded to {context['expanded_products']})
    - Stores: {entities['store_ids']} (expanded to {context['expanded_stores']})
    - Date Range: {entities['date_range']}
    - Events during period: {context['relevant_events']}
    
    Database Schema:
    - inventory (store_id, product_id, end_date, sales, inventory_start, inventory_end)
    - weather (store_id, end_date, temp_high, temp_low, condition)
    - metrics (store_id, product_id, end_date, wdd_value)
    
    Generate accurate SQL query:
    """
    
    return llm.generate(prompt)

# Full workflow
def answer_query(user_query: str):
    entities = resolve_entities(user_query)
    context = expand_context(entities)
    sql = generate_sql_with_context(user_query, entities, context)
    results = execute_sql(sql)
    return format_answer(results)
```

---

## ✅ Benefits of This Approach

1. **Scalability**: Add more tables/data without retraining LLM
2. **Accuracy**: Graph ensures correct context (all Texas stores, not just "Dallas")
3. **Flexibility**: Handles vague queries ("summer sales" → exact date ranges)
4. **Performance**: Search + Graph are fast lookups, heavy lifting in PostgreSQL
5. **Maintainability**: Schema changes don't break entity resolution
6. **Context-Aware**: Knows about events, seasons, hierarchies automatically

---

## 📝 Example Queries Handled

| User Query | Azure AI Search | Neo4j Graph | PostgreSQL |
|------------|-----------------|-------------|------------|
| "Pepsi sales in Texas during summer" | Find Pepsi products, Texas stores, Summer dates | Expand to all Texas stores, all summer dates | Calculate SUM(sales) |
| "Ice cream performance during heatwaves" | Find ice cream category | Get all ice cream products | JOIN with weather WHERE is_heatwave=true |
| "Compare East vs West regions" | Find East/West stores | Get all stores in both regions | GROUP BY region |
| "Super Bowl impact on snacks" | Find Super Bowl event, snack category | Get event dates, all snack products | Compare sales before/during/after |

---

**Last Updated**: November 30, 2025
**Status**: ✅ All indexes populated, Neo4j graph built, ready for agent integration
