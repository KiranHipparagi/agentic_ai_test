# Planalytics AI - File-by-File Explanation Guide

This document provides a concise explanation of every key Python file in the backend. Use this as a cheat sheet when your manager asks, *"What does this file do?"*

---

## 📂 Root Directory (`backend/`)

### `main.py`
**"The Entry Point"**
- **Purpose:** This is the heart of the application. It initializes the FastAPI server.
- **Key Functions:**
  - Sets up the API application (`app = FastAPI(...)`).
  - Configures CORS (so the frontend can talk to it).
  - Includes all the routers (chat, analytics, reports).
  - Handles startup/shutdown events (like connecting to databases).

### `mcp_server.py`
**"The External Interface"**
- **Purpose:** Runs the Model Context Protocol (MCP) server.
- **Key Functions:**
  - Exposes our internal agents (`query_supply_chain_data`, `analyze_weather_impact`) as "tools".
  - Allows external AI apps (like Claude Desktop) to use our system without going through the frontend.

---

## 📂 Core Configuration (`backend/core/`)

### `config.py`
**"The Settings Manager"**
- **Purpose:** Loads and manages all environment variables and configuration settings.
- **Key Functions:**
  - Stores database credentials (Postgres, Neo4j, Azure).
  - Stores API keys (OpenAI, Azure Search).
  - Defines app constants (Debug mode, API versions).

### `logger.py`
**"The Recorder"**
- **Purpose:** Sets up structured logging for the application.
- **Key Functions:**
  - Configures how logs look (JSON format for production).
  - Ensures logs are saved or printed to the console for debugging.

### `security.py`
**"The Bouncer"**
- **Purpose:** Handles authentication and security (if enabled).
- **Key Functions:**
  - Generates and verifies JWT tokens.
  - Hashes passwords for secure storage.

---

## 📂 Agents (`backend/agents/`)

### `orchestrator_agent.py`
**"The Brain"**
- **Purpose:** The master agent that controls the flow of every request.
- **Key Functions:**
  - **Intent Detection:** Decides if the user wants a chart, data, or just a chat.
  - **Routing:** Sends the task to the right specialized agent (Database, Weather, etc.).
  - **Response Compilation:** Puts everything together into the final answer.

### `database_agent.py`
**"The Data Fetcher"**
- **Purpose:** The most important worker. It gets real data from the database.
- **Key Functions:**
  - Calls `context_resolver` to understand what "Pepsi" or "Northeast" means.
  - Uses GPT-4 to write SQL queries dynamically.
  - Executes the SQL on PostgreSQL.
  - Explains the data results in plain English.

### `visualization_agent.py`
**"The Artist"**
- **Purpose:** Generates charts and graphs dynamically.
- **Key Functions:**
  - Looks at the data returned by the Database Agent.
  - Uses LLM to decide the best chart type (Bar, Line, Pie).
  - Creates the JSON configuration for Google Charts.

### `weather_agent.py`
**"The Meteorologist"**
- **Purpose:** Analyzes weather data.
- **Key Functions:**
  - Fetches weather records from the database.
  - Uses LLM to analyze impacts (e.g., "Heavy rain might slow down deliveries").

### `events_agent.py`
**"The Planner"**
- **Purpose:** Analyzes holidays and events.
- **Key Functions:**
  - Checks for upcoming events (Christmas, Super Bowl).
  - Predicts demand spikes based on historical event data.

### `location_agent.py`
**"The Geographer"**
- **Purpose:** Analyzes location-specific data.
- **Key Functions:**
  - Uses the Knowledge Graph to find relationships between stores and regions.
  - Analyzes regional performance.

### `inventory_agent.py`
**"The Stock Manager"**
- **Purpose:** Manages stock levels.
- **Key Functions:**
  - Checks current inventory levels.
  - Recommends reordering if stock is low.

---

## 📂 Services (`backend/services/`)

### `context_resolver.py`
**"The Translator"**
- **Purpose:** Converts vague user words into specific database IDs.
- **Key Functions:**
  - **Azure Search:** Finds "Pepsi" -> `Product_ID: 123`.
  - **Neo4j:** Finds related items (e.g., "Other sodas").
  - Prepares the "Context" so the SQL generator knows exactly what to look for.

### `rag_pipeline.py`
**"The Researcher"**
- **Purpose:** Handles Retrieval-Augmented Generation (searching text documents).
- **Key Functions:**
  - Searches vector indexes for relevant text/documents.
  - Sends that text to the LLM to answer general questions.

### `graph_builder.py`
**"The Connector"**
- **Purpose:** Builds relationships in the Neo4j Knowledge Graph.
- **Key Functions:**
  - Connects Products to Locations, Events to Dates, etc.
  - Helps the system understand how things are related.

### `data_ingestion.py`
**"The Loader"**
- **Purpose:** Handles loading data into the system (usually a background process).
- **Key Functions:**
  - Reads data (like Excel/CSV).
  - Saves it to PostgreSQL and Azure Search.

---

## 📂 Database (`backend/database/`)

### `postgres_db.py`
**"The SQL Handler"**
- **Purpose:** Manages the connection to the PostgreSQL database.
- **Key Functions:**
  - Defines the "Models" (Tables): `Metrics`, `ProductHierarchy`, `LocationDimension`.
  - Creates the database engine and session.

### `azure_search.py`
**"The Search Engine"**
- **Purpose:** Manages the connection to Azure AI Search.
- **Key Functions:**
  - Performs "Fuzzy Search" (finding things even if spelled slightly wrong).
  - Handles Vector Search for semantic understanding.

### `neo4j_db.py`
**"The Graph Handler"**
- **Purpose:** Manages the connection to the Neo4j Graph Database.
- **Key Functions:**
  - Runs Cypher/Gremlin queries to find relationships.
  - Expands context (e.g., "Find all stores in this market").

---

## 📂 Routes (`backend/routes/`)

### `chatbot.py`
**"The Chat API"**
- **Purpose:** Defines the API endpoints for the chat interface.
- **Key Functions:**
  - `POST /chat`: Receives the user's message and sends it to the Orchestrator.
  - Returns the final answer and chart to the frontend.

### `analytics.py`
**"The Dashboard API"**
- **Purpose:** Endpoints for dashboard widgets (KPIs, trends).
- **Key Functions:**
  - `GET /kpis`: Calculates total sales, revenue, etc.
  - `GET /trends`: Fetches historical data for line charts.

### `reports.py`
**"The Reporting API"**
- **Purpose:** Handles data upload and report generation.
- **Key Functions:**
  - `POST /ingest`: Endpoint to upload new data.
  - `GET /forecast`: Generates simple demand forecasts.
