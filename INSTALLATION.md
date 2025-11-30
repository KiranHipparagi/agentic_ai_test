# Enhanced RAG Pipeline - Installation Instructions

## ✅ Pre-requisites Checklist

Before installing, ensure you have:
- ✅ Python 3.10+ installed
- ✅ PostgreSQL running with `planalytics_db` database
- ✅ Neo4j running (local or cloud)
- ✅ Azure AI Search indexes populated (7 indexes)
- ✅ Azure OpenAI API access

---

## 🚀 Installation Steps

### Step 1: Navigate to Backend Directory
```bash
cd backend
```

### Step 2: Activate Virtual Environment (if using one)
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (web framework)
- SQLAlchemy & psycopg2-binary (PostgreSQL)
- neo4j (knowledge graph)
- openai (Azure OpenAI client)
- **azure-search-documents** (NEW - Azure AI Search)
- **azure-core** (NEW - Azure SDK core)
- **azure-identity** (NEW - Azure authentication)
- Other utilities (httpx, python-dotenv, etc.)

**Note**: If installation is slow, the Azure packages might take a few minutes. Be patient.

### Step 4: Configure Environment Variables
```bash
# Copy the example .env file
copy .env.example .env
```

**Edit `.env` file** with your credentials:
```env
# PostgreSQL
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password-here
POSTGRES_DB=planalytics_db

# Neo4j
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password-here
NEO4J_ENABLED=true

# Azure OpenAI (Main LLM)
OPENAI_ENDPOINT=https://genai-sharedservice-americas.pwc.com
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL_NAME=openai.gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-06

# Azure OpenAI Embeddings
AZURE_OPENAI_ENDPOINT=https://genai-sharedservice-americas.pwc.com
AZURE_OPENAI_API_KEY=YOUR_AZURE_OPENAI_API_KEY
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=azure.text-embedding-ada-002

# Azure AI Search (NEW - Required!)
AZURE_SEARCH_ENDPOINT=https://u7zxunxhadcs001.search.windows.net
AZURE_SEARCH_KEY=YOUR_AZURE_SEARCH_KEY

# Security
SECRET_KEY=your-secret-key-change-this-in-production
```

### Step 5: Verify Azure AI Search Indexes

Ensure all 7 indexes exist and are populated:
1. `planalytics-data-index-products` (27 documents)
2. `planalytics-data-index-locations` (183 documents)
3. `planalytics-data-index-events` (17,695 documents)
4. `planalytics-data-index-calendar` (469 documents)
5. `planalytics-data-index-sales-metadata` (4,792 documents)
6. `planalytics-data-index-weather-metadata` (158 documents)
7. `planalytics-data-index-metrics-metadata` (1 document)

**Check in Azure Portal**:
- Navigate to Azure AI Search resource
- Click "Indexes" in left menu
- Verify all 7 indexes are listed with document counts

### Step 6: Verify Neo4j Knowledge Graph

Ensure Neo4j has the following nodes:
- **Product nodes**: 27 products with IN_CATEGORY relationships
- **Location nodes**: 183 stores with IN_MARKET → IN_STATE → IN_REGION hierarchy
- **Date nodes**: 469 dates with IN_WEEK → IN_MONTH → IN_QUARTER → IN_YEAR
- **Event nodes**: 17,695 events with AT_STORE and OCCURS_ON relationships

**Test Neo4j Connection**:
```bash
# Run this Cypher query in Neo4j Browser
MATCH (n) RETURN count(n) AS total_nodes
```
Expected: ~18,000+ nodes

### Step 7: Test the Enhanced RAG Pipeline
```bash
python test_rag_pipeline.py
```

**Expected Output**:
```
================================================================================
ENHANCED RAG PIPELINE TEST SUITE
Azure AI Search + Neo4j Knowledge Graph + PostgreSQL
================================================================================

================================================================================
TEST 1: Entity Resolution (Azure AI Search)
================================================================================

📝 Query: Show me Pepsi sales in Texas

✓ Products found: 2
  - Diet Pepsi 12oz Can (ID: P-101)
  - Pepsi 2L Bottle (ID: P-102)

✓ Locations found: 25
  - Dallas Store 1 (Texas) (ID: ST0001)
  - Houston Store 1 (Texas) (ID: ST0002)
  ...

================================================================================
TEST 2: Context Expansion (Neo4j Knowledge Graph)
================================================================================
...

================================================================================
TEST 3: Full RAG Pipeline (Search → Graph → SQL → PostgreSQL)
================================================================================
...

✅ ALL TESTS COMPLETED
```

### Step 8: Start the Application
```bash
# Start FastAPI backend
uvicorn main:app --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
✅ Neo4j connection established successfully
✅ Connected to Azure Search index: planalytics-data-index-products
✅ Connected to Azure Search index: planalytics-data-index-locations
...
```

### Step 9: Test API Endpoint
```bash
# In another terminal or browser, test the chatbot endpoint
curl -X POST http://localhost:8000/api/v1/chatbot/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me Pepsi sales in Texas"}'
```

**Expected Response**:
```json
{
  "agent": "database",
  "sql_query": "SELECT ...",
  "data": [...],
  "row_count": 42,
  "context_summary": "✓ 2 products identified | ✓ Expanded to 5 related products | ...",
  "status": "success"
}
```

---

## 🔧 Troubleshooting

### Issue 1: "Import azure.search.documents failed"
**Solution**:
```bash
pip install --upgrade azure-search-documents azure-core azure-identity
```

### Issue 2: "AZURE_SEARCH_ENDPOINT not found"
**Solution**: Ensure `.env` file exists in `backend/` directory with correct values

### Issue 3: "Neo4j connection failed"
**Solution**: 
- Check Neo4j is running: `neo4j status`
- Verify credentials in `.env` file
- If Neo4j is optional, set `NEO4J_ENABLED=false` in `.env`

### Issue 4: "Azure Search index not found"
**Solution**: Verify index names match exactly:
- Expected: `planalytics-data-index-products`
- Check Azure Portal for actual index names

### Issue 5: "No products found" in tests
**Possible causes**:
- Azure Search indexes are empty → Re-run data ingestion
- Wrong API key → Check `AZURE_SEARCH_KEY` in `.env`
- Wrong endpoint → Check `AZURE_SEARCH_ENDPOINT` in `.env`

---

## 📊 Verification Checklist

After installation, verify:

- [ ] All Python packages installed successfully
- [ ] `.env` file configured with all required credentials
- [ ] Azure AI Search indexes are accessible
- [ ] Neo4j is running and populated
- [ ] PostgreSQL is running with data
- [ ] `test_rag_pipeline.py` runs without errors
- [ ] FastAPI application starts successfully
- [ ] API endpoint returns valid responses

---

## 🎯 Quick Test Commands

```bash
# 1. Test Python imports
python -c "from database.azure_search import azure_search; print('✅ Azure Search OK')"
python -c "from database.neo4j_db import neo4j_conn; print('✅ Neo4j OK')"
python -c "from services.context_resolver import context_resolver; print('✅ Context Resolver OK')"

# 2. Test database connections
python -c "from database.postgres_db import get_db; print('✅ PostgreSQL OK')"

# 3. Run full test suite
python test_rag_pipeline.py

# 4. Start application
uvicorn main:app --reload
```

---

## 📝 What Gets Installed

### Core Dependencies (Existing)
- `fastapi==0.115.0` - Web framework
- `uvicorn==0.32.0` - ASGI server
- `sqlalchemy==2.0.36` - PostgreSQL ORM
- `psycopg2-binary==2.9.11` - PostgreSQL driver
- `neo4j==5.26.0` - Neo4j driver
- `openai==1.55.3` - Azure OpenAI client

### NEW Dependencies (Added for RAG Pipeline)
- `azure-search-documents==11.6.0b7` - Azure AI Search SDK
- `azure-core==1.32.0` - Azure SDK core functionality
- `azure-identity==1.19.0` - Azure authentication

### Total Install Time
Approximately 2-5 minutes depending on internet speed.

---

## 🚀 Ready to Go!

Once installation is complete:
1. Backend runs on: `http://localhost:8000`
2. API docs available at: `http://localhost:8000/docs`
3. Frontend (if started): `http://localhost:3000`

**Test Query**:
```
User: "Show me Pepsi sales in Texas during summer"
System: Uses Azure Search → Neo4j → SQL → PostgreSQL
Result: Accurate, context-aware sales data
```

---

**Need Help?** Check `IMPLEMENTATION_GUIDE.md` for detailed architecture documentation.
