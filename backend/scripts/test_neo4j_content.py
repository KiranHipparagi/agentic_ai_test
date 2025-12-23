"""
Test what's actually in the Neo4j database
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database.neo4j_db import neo4j_conn

print("="*80)
print("Testing Neo4j Database Content")
print("="*80)

if not neo4j_conn.ensure_connected():
    print("❌ Failed to connect to Neo4j")
    sys.exit(1)

print("✅ Connected to Neo4j\n")

# Test 1: Check if there's any data at all
print("Test 1: Total node count")
print("-"*80)
with neo4j_conn.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    total_nodes = result.single()['count']
    print(f"Total nodes in database: {total_nodes}")

if total_nodes == 0:
    print("\n⚠️  Database is EMPTY! You need to run the builder first:")
    print("   python planalytics_neo4j/build_planalytics_neo4j_async.py")
    sys.exit(0)

# Test 2: What node labels exist?
print("\n\nTest 2: Node labels that exist")
print("-"*80)
with neo4j_conn.session() as session:
    result = session.run("CALL db.labels()")
    labels = [record['label'] for record in result]
    print(f"Labels found: {labels}")

# Test 3: Count nodes by label
print("\n\nTest 3: Count by label")
print("-"*80)
for label in labels:
    with neo4j_conn.session() as session:
        result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
        count = result.single()['count']
        print(f"  {label}: {count}")

# Test 4: What relationships exist?
print("\n\nTest 4: Relationship types")
print("-"*80)
with neo4j_conn.session() as session:
    result = session.run("CALL db.relationshipTypes()")
    rel_types = [record['relationshipType'] for record in result]
    print(f"Relationships found: {rel_types}")

# Test 5: Sample Product nodes
print("\n\nTest 5: Sample Product nodes (first 3)")
print("-"*80)
with neo4j_conn.session() as session:
    result = session.run("MATCH (p:Product) RETURN p LIMIT 3")
    for record in result:
        node = record['p']
        print(f"  Product: {dict(node)}")

# Test 6: Sample Store nodes
print("\n\nTest 6: Sample Store nodes (first 3)")
print("-"*80)
with neo4j_conn.session() as session:
    result = session.run("MATCH (s:Store) RETURN s LIMIT 3")
    for record in result:
        node = record['s']
        print(f"  Store: {dict(node)}")

# Test 7: Test a product relationship traversal
print("\n\nTest 7: Product relationship traversal")
print("-"*80)
with neo4j_conn.session() as session:
    result = session.run("""
        MATCH (p:Product)-[r]->(related)
        RETURN p.name as product, type(r) as relationship, labels(related) as related_labels
        LIMIT 3
    """)
    for record in result:
        print(f"  {record['product']} -[:{record['relationship']}]-> {record['related_labels']}")

# Test 8: Test a store relationship traversal
print("\n\nTest 8: Store relationship traversal")
print("-"*80)
with neo4j_conn.session() as session:
    result = session.run("""
        MATCH (s:Store)-[r]->(related)
        RETURN s.store_id as store, type(r) as relationship, labels(related) as related_labels
        LIMIT 3
    """)
    for record in result:
        print(f"  {record['store']} -[:{record['relationship']}]-> {record['related_labels']}")

print("\n" + "="*80)
print("✅ Neo4j Content Test Complete")
print("="*80)
