"""
Test the FIXED Neo4j queries
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database.neo4j_db import neo4j_conn

print("="*80)
print("Testing FIXED Neo4j Queries")
print("="*80)

if not neo4j_conn.ensure_connected():
    print("❌ Failed to connect to Neo4j")
    sys.exit(1)

print("✅ Connected to Neo4j\n")

# Test 1: Expand product context (like Azure Search returns product IDs)
print("Test 1: Expand Product Context")
print("-"*80)
print("Simulating Azure Search returning: PROD_1 (Hamburgers)")
result = neo4j_conn.expand_product_context(['PROD_1'])
print(f"Found {len(result)} related products:")
for item in result:
    print(f"  - {item['product_name']} (ID: {item['product_id']}, Category: {item['category']})")

if len(result) == 0:
    print("  (Trying with numeric ID: 1)")
    result = neo4j_conn.expand_product_context([1])
    print(f"  Found {len(result)} related products:")
    for item in result:
        print(f"    - {item['product_name']} (ID: {item['product_id']}, Category: {item['category']})")

# Test 2: Expand location context
print("\n\nTest 2: Expand Location Context")
print("-"*80)
print("Querying for stores related to: ST6111 (Chicago store)")
result = neo4j_conn.expand_location_context(['ST6111'])
print(f"Found {len(result)} related stores in same market:")
for item in result:
    print(f"  - Store {item['store_id']} in Market: {item['market']}")

# Test 3: Find related events
print("\n\nTest 3: Find Related Events")
print("-"*80)
result = neo4j_conn.find_related_events(['ST6111'], ['2026-01-01'])
print(f"Found {len(result)} event types:")
for item in result:
    print(f"  - {item['event_name']} ({item['event_type']})")

# Test 4: Manual query to verify category expansion works
print("\n\nTest 4: Manual verification - Products in 'QSR' category")
print("-"*80)
with neo4j_conn.session() as session:
    result = session.run("""
        MATCH (p:Product)-[:IN_CATEGORY]->(c:Category {name: 'QSR'})
        RETURN p.product_id as id, p.name as name
        ORDER BY p.product_id
    """)
    qsr_products = [record.data() for record in result]
    print(f"Found {len(qsr_products)} QSR products:")
    for prod in qsr_products:
        print(f"  - {prod['name']} (ID: {prod['id']})")

# Test 5: Manual query to verify market relationships
print("\n\nTest 5: Manual verification - Stores in 'chicago, il' market")
print("-"*80)
with neo4j_conn.session() as session:
    result = session.run("""
        MATCH (s:Store)-[:IN_MARKET]->(m:Market {name: 'chicago, il'})
        RETURN s.store_id as store_id
        ORDER BY s.store_id
        LIMIT 5
    """)
    chicago_stores = [record.data() for record in result]
    print(f"Found {len(chicago_stores)} stores in Chicago:")
    for store in chicago_stores:
        print(f"  - {store['store_id']}")

print("\n" + "="*80)
print("✅ Testing Complete!")
print("="*80)
print("\n📋 Summary:")
print("  - If Test 1 shows related products → Product expansion WORKS")
print("  - If Test 2 shows related stores → Location expansion WORKS")
print("  - If Test 3 shows events → Event context WORKS")
print("  - Tests 4-5 verify the underlying graph structure")
