"""
Test the chatbot with the new database schema
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from agents.database_agent import DatabaseAgent

print("="*80)
print("Testing Database Agent with New Schema")
print("="*80)

agent = DatabaseAgent()

# Test query 1: Simple sales query
print("\n\nTest 1: Total sales for Hamburgers")
print("-"*80)
result = agent.query_database("What are the total sales for Hamburgers?")
print(f"Status: {result['status']}")
print(f"SQL Query: {result.get('sql_query', 'N/A')}")
print(f"Rows returned: {result.get('row_count', 0)}")
if result.get('data'):
    print(f"Sample data: {result['data'][:2]}")

# Test query 2: Location-based query
print("\n\nTest 2: Sales by region")
print("-"*80)
result = agent.query_database("Show me sales by region")
print(f"Status: {result['status']}")
print(f"SQL Query: {result.get('sql_query', 'N/A')}")
print(f"Rows returned: {result.get('row_count', 0)}")
if result.get('data'):
    print(f"Sample data: {result['data'][:2]}")

# Test query 3: Product category query
print("\n\nTest 3: Top selling products")
print("-"*80)
result = agent.query_database("What are the top 10 selling products?")
print(f"Status: {result['status']}")
print(f"SQL Query: {result.get('sql_query', 'N/A')}")
print(f"Rows returned: {result.get('row_count', 0)}")
if result.get('data'):
    print(f"Sample data: {result['data'][:3]}")

print("\n" + "="*80)
print("✅ Database Agent Tests Complete!")
print("="*80)
