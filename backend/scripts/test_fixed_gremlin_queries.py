"""
Test the FIXED Gremlin queries for Azure Cosmos DB
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database.gremlin_db import gremlin_conn

print("="*80)
print("Testing FIXED Gremlin Queries (Azure Cosmos DB)")
print("="*80)

if not gremlin_conn.ensure_connected():
    print("❌ Failed to connect to Cosmos DB Gremlin API")
    print("\nℹ️  This is expected if you're on the local machine (Cosmos DB only in office)")
    print("   To test, you need:")
    print("   - COSMOS_ENDPOINT in .env")
    print("   - COSMOS_KEY in .env")
    print("   - COSMOS_DATABASE=planalytics")
    print("   - COSMOS_GRAPH=planalytics_graph")
    sys.exit(1)

print("✅ Connected to Cosmos DB Gremlin API\n")

# Test 1: Expand product context (like Azure Search returns product IDs)
print("Test 1: Expand Product Context")
print("-"*80)
print("Simulating Azure Search returning: PROD_1 (Hamburgers)")
result = gremlin_conn.expand_product_context(['PROD_1'])
print(f"Found {len(result)} related products:")
for item in result:
    print(f"  - {item.get('product_name', 'N/A')} (ID: {item.get('product_id', 'N/A')}, Category: {item.get('category', 'N/A')})")

if len(result) == 0:
    print("  (Trying with Gremlin ID: P_1)")
    result = gremlin_conn.expand_product_context(['P_1'])
    print(f"  Found {len(result)} related products:")
    for item in result:
        print(f"    - {item.get('product_name', 'N/A')} (ID: {item.get('product_id', 'N/A')}, Category: {item.get('category', 'N/A')})")

# Test 2: Expand location context
print("\n\nTest 2: Expand Location Context")
print("-"*80)
print("Querying for stores related to: ST6111 (Chicago store)")
result = gremlin_conn.expand_location_context(['ST6111'])
print(f"Found {len(result)} related stores in same market:")
for item in result:
    print(f"  - Store {item.get('store_id', 'N/A')} in Market: {item.get('market', 'N/A')}")

# Test 3: Find related events
print("\n\nTest 3: Find Related Events")
print("-"*80)
print("Querying for event types (metadata only)...")
result = gremlin_conn.find_related_events(['ST6111'], ['2026-01-01'])
print(f"Found {len(result)} event types:")
for item in result[:10]:  # Show first 10
    print(f"  - {item.get('event_name', 'N/A')} ({item.get('event_type', 'N/A')})")

# Test 4: Get product hierarchy
print("\n\nTest 4: Get Product Hierarchy")
print("-"*80)
print("Querying for product hierarchy: Product ID 1 (Hamburgers)")
result = gremlin_conn.get_product_hierarchy('1')
if result:
    print(f"  Product: {result.get('product_name', 'N/A')}")
    print(f"  Category: {result.get('category', 'N/A')}")
    print(f"  Department: {result.get('department', 'N/A')}")
else:
    print("  No hierarchy found (product may not have category/department)")

# Test 5: Get location hierarchy
print("\n\nTest 5: Get Location Hierarchy")
print("-"*80)
print("Querying for location hierarchy: ST6111 (Chicago)")
result = gremlin_conn.get_location_hierarchy('ST6111')
if result:
    print(f"  Store: {result.get('store_id', 'N/A')}")
    print(f"  Market: {result.get('market', 'N/A')}")
    print(f"  State: {result.get('state', 'N/A')}")
    print(f"  Region: {result.get('region', 'N/A')}")
else:
    print("  No hierarchy found")

# Test 6: Verify graph structure with manual query
print("\n\nTest 6: Manual Verification - Count nodes by label")
print("-"*80)
try:
    labels = ['Product', 'Store', 'Department', 'Category', 'Region', 'State', 'Market', 'EventType']
    for label in labels:
        count_traversal = gremlin_conn.g.V().hasLabel(label).count()
        count = count_traversal.next()
        if count > 0:
            print(f"  {label}: {count}")
except Exception as e:
    print(f"  Error counting nodes: {e}")

print("\n" + "="*80)
print("✅ Testing Complete!")
print("="*80)
print("\n📋 Summary:")
print("  - If Test 1 shows related products → Product expansion WORKS")
print("  - If Test 2 shows related stores → Location expansion WORKS")
print("  - If Test 3 shows event types → Event context WORKS")
print("  - Tests 4-5 verify hierarchy traversal")
print("  - Test 6 verifies the underlying graph structure")
print("\nℹ️  Note: Gremlin uses 'id' property for lookups, not 'product_id' or 'store_id'")
print("   Builder creates: P_1, P_2 for products; ST6111, ST4630 for stores")
