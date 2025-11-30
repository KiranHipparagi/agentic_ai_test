"""
Debug script to show exactly what Azure Search and Neo4j are returning
and how the SQL is generated.
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from database.azure_search import azure_search
from database.neo4j_db import neo4j_conn
from agents.database_agent import DatabaseAgent
from services.context_resolver import context_resolver
from core.logger import logger

def debug_pipeline(query):
    print(f"\n{'='*80}")
    print(f"🔎 DEBUGGING QUERY: '{query}'")
    print(f"{'='*80}\n")

    # 1. Azure Search Debug
    print(f"🔵 STEP 1: Azure AI Search (Entity Resolution)")
    print(f"{'-'*40}")
    try:
        # We'll call the internal search methods to see raw results
        products = azure_search.search_products(query, top_k=3)
        print(f"  Found {len(products)} products:")
        for p in products:
            print(f"    - {p.get('product', 'Unknown')} (ID: {p.get('product_id')}, Score: {p.get('@search.score', 'N/A')})")
            
        locations = azure_search.search_locations(query, top_k=3)
        print(f"  Found {len(locations)} locations:")
        for l in locations:
            print(f"    - {l.get('location', 'Unknown')} (ID: {l.get('id')})")
            
        # Full resolution
        resolved = azure_search.resolve_entities(query)
        print(f"\n  ✅ Resolved Entities Object: {resolved}")
    except Exception as e:
        print(f"  ❌ Azure Search Error: {e}")

    # 2. Neo4j Debug
    print(f"\n🟢 STEP 2: Neo4j Knowledge Graph (Context Expansion)")
    print(f"{'-'*40}")
    try:
        if neo4j_conn.ensure_connected():
            print("  ✅ Neo4j is connected.")
            # Try a simple expansion if we found products
            if resolved.get('products'):
                prod_ids = [p['product_id'] for p in resolved['products']]
                print(f"  Expanding context for Product IDs: {prod_ids}")
                expanded = neo4j_conn.expand_product_context(prod_ids)
                print(f"  Graph Expansion Result: {expanded}")
            else:
                print("  No products to expand in graph.")
        else:
            print("  ⚠️ Neo4j is NOT connected (Check .env and service status).")
    except Exception as e:
        print(f"  ❌ Neo4j Error: {e}")

    # 3. SQL Generation Debug
    print(f"\n🟠 STEP 3: SQL Generation (LLM)")
    print(f"{'-'*40}")
    try:
        agent = DatabaseAgent()
        # We use the resolver to get the full context first
        context = context_resolver.resolve_query_context(query)
        
        # Generate SQL
        sql = agent._generate_sql_with_context(query, context)
        
        # Apply the fix we added (semicolon removal)
        fixed_sql = sql.replace("; LIMIT", " LIMIT").replace(";LIMIT", " LIMIT")
        
        print(f"  📝 Generated SQL: {sql}")
        if sql != fixed_sql:
            print(f"  🔧 Fixed SQL:     {fixed_sql}")
        else:
            print(f"  ✅ SQL Syntax Check: OK")
            
    except Exception as e:
        print(f"  ❌ SQL Generation Error: {e}")

    # 4. Execution Debug
    print(f"\n🟣 STEP 4: Database Execution (PostgreSQL)")
    print(f"{'-'*40}")
    try:
        from database.postgres_db import get_db
        from sqlalchemy import text
        
        with get_db() as db:
            result = db.execute(text(fixed_sql))
            rows = result.fetchall()
            cols = result.keys()
            
            print(f"  ✅ Query Executed Successfully")
            print(f"  Columns: {list(cols)}")
            print(f"  Row Count: {len(rows)}")
            print(f"  Data:")
            for row in rows:
                print(f"    {row}")
    except Exception as e:
        print(f"  ❌ Execution Error: {e}")

if __name__ == "__main__":
    debug_pipeline("How many products are listed under the QSR category?")
