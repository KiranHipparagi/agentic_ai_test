"""
Test Gremlin REST API queries with corrected syntax
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.gremlin_db_rest_fixed import gremlin_conn

def test_connection():
    """Test basic connection"""
    print("="*80)
    print("TEST 1: Connection Test")
    print("="*80)
    
    if gremlin_conn.ensure_connected():
        print("✅ Connected to Cosmos DB Gremlin")
        
        # Count total vertices
        result = gremlin_conn._execute_query("g.V().count()")
        if result:
            print(f"✅ Total vertices: {result[0]}")
        
        # Count by label
        labels = ['Product', 'Category', 'Department', 'Store', 'Market', 'State', 'Region', 'EventType']
        for label in labels:
            result = gremlin_conn._execute_query(f"g.V().hasLabel('{label}').count()")
            if result:
                print(f"   {label}: {result[0]}")
    else:
        print("❌ Connection failed")
        return False
    
    return True

def test_product_expansion():
    """Test expand_product_context with sample IDs"""
    print("\n" + "="*80)
    print("TEST 2: Product Context Expansion")
    print("="*80)
    
    # Test with IDs from Azure Search: PROD_16, PROD_12, PROD_9
    product_ids = ['PROD_16', 'PROD_12', 'PROD_9']
    print(f"Input IDs (Azure Search format): {product_ids}")
    
    # Should convert to: P_16, P_12, P_9
    results = gremlin_conn.expand_product_context(product_ids)
    
    if results:
        print(f"✅ Found {len(results)} related products:")
        for r in results[:5]:  # Show first 5
            print(f"   - Product ID: {r.get('product_id', 'N/A')}, Name: {r.get('product_name', 'N/A')}, Category: {r.get('category', 'N/A')}")
    else:
        print("❌ No products found - check query syntax!")
        
        # Debug: Check if products exist
        print("\n🔍 Debugging: Checking if products exist in graph...")
        for pid in ['P_16', 'P_12', 'P_9']:
            result = gremlin_conn._execute_query(f"g.V().hasLabel('Product').has('id', '{pid}').valueMap()")
            if result:
                print(f"   ✅ {pid} exists: {result[0]}")
            else:
                print(f"   ❌ {pid} NOT found")

def test_location_expansion():
    """Test expand_location_context with sample store IDs"""
    print("\n" + "="*80)
    print("TEST 3: Location Context Expansion")
    print("="*80)
    
    location_ids = ['ST0050', 'ST0481', 'ST0390']
    print(f"Input Store IDs: {location_ids}")
    
    results = gremlin_conn.expand_location_context(location_ids)
    
    if results:
        print(f"✅ Found {len(results)} related stores:")
        for r in results[:5]:
            print(f"   - Store ID: {r.get('store_id', 'N/A')}, Name: {r.get('store_name', 'N/A')}, Market: {r.get('market', 'N/A')}")
    else:
        print("❌ No stores found - check query syntax!")
        
        # Debug
        print("\n🔍 Debugging: Checking if stores exist in graph...")
        for sid in location_ids:
            result = gremlin_conn._execute_query(f"g.V().hasLabel('Store').has('id', '{sid}').valueMap()")
            if result:
                print(f"   ✅ {sid} exists: {result[0]}")
            else:
                print(f"   ❌ {sid} NOT found")

def test_event_types():
    """Test find_related_events (metadata only)"""
    print("\n" + "="*80)
    print("TEST 4: Event Types (Metadata)")
    print("="*80)
    
    results = gremlin_conn.find_related_events([], [])
    
    if results:
        print(f"✅ Found {len(results)} event types:")
        for r in results[:10]:
            print(f"   - Event: {r.get('event_name', 'N/A')}, Type: {r.get('event_type', 'N/A')}")
    else:
        print("❌ No events found")

def test_raw_queries():
    """Test raw Gremlin queries to diagnose syntax"""
    print("\n" + "="*80)
    print("TEST 5: Raw Query Syntax Tests")
    print("="*80)
    
    # Test 1: Simple has() with single value
    print("\n1️⃣ Single value lookup:")
    query = "g.V().hasLabel('Product').has('id', 'P_1').valueMap()"
    result = gremlin_conn._execute_query(query)
    print(f"   Query: {query}")
    print(f"   Result: {result}")
    
    # Test 2: within() with comma-separated values (no array brackets)
    print("\n2️⃣ within() with comma-separated values:")
    query = "g.V().hasLabel('Product').has('id', within('P_1','P_2','P_3')).valueMap()"
    result = gremlin_conn._execute_query(query)
    print(f"   Query: {query}")
    print(f"   Result count: {len(result) if result else 0}")
    
    # Test 3: Traversal with relationships
    print("\n3️⃣ Relationship traversal:")
    query = "g.V().hasLabel('Product').has('id', 'P_1').out('IN_CATEGORY').valueMap()"
    result = gremlin_conn._execute_query(query)
    print(f"   Query: {query}")
    print(f"   Result: {result}")

if __name__ == "__main__":
    print("🧪 GREMLIN REST API TESTING")
    print("Testing corrected query syntax for Cosmos DB")
    print()
    
    if not test_connection():
        print("\n❌ Connection failed - cannot proceed with tests")
        sys.exit(1)
    
    test_raw_queries()
    test_product_expansion()
    test_location_expansion()
    test_event_types()
    
    print("\n" + "="*80)
    print("✅ All tests completed")
    print("="*80)
    print("\n💡 If queries still fail:")
    print("   1. Check Cosmos DB firewall rules (allow your IP)")
    print("   2. Verify partition key configuration")
    print("   3. Check Cosmos DB query metrics in Azure Portal")
    print("   4. Try queries directly in Azure Portal Data Explorer")
