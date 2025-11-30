"""
Test script for the enhanced RAG pipeline (Azure Search + Neo4j + PostgreSQL)

This script demonstrates how the new context-aware database agent works:
1. User asks a natural language question
2. Azure AI Search resolves entities (products, locations, dates)
3. Neo4j expands context via knowledge graph
4. LLM generates SQL with full context
5. PostgreSQL executes the query
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from agents.database_agent import DatabaseAgent
from services.context_resolver import context_resolver
from core.logger import logger


def test_entity_resolution():
    """Test Azure Search entity resolution"""
    print("\n" + "="*80)
    print("TEST 1: Entity Resolution (Azure AI Search)")
    print("="*80)
    
    test_queries = [
        "Show me Pepsi sales in Texas",
        "Ice cream sales during summer",
        "What were the sales during Super Bowl in California stores?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        try:
            context = context_resolver.resolver.search.resolve_entities(query)
            
            print(f"\n✓ Products found: {len(context.get('products', []))}")
            for p in context.get('products', [])[:3]:
                print(f"  - {p.get('product_name', 'N/A')} (ID: {p.get('id', 'N/A')})")
            
            print(f"\n✓ Locations found: {len(context.get('locations', []))}")
            for l in context.get('locations', [])[:3]:
                print(f"  - {l.get('store_name', 'N/A')} ({l.get('state', 'N/A')}) (ID: {l.get('id', 'N/A')})")
            
            print(f"\n✓ Dates found: {len(context.get('dates', []))}")
            for d in context.get('dates', [])[:3]:
                print(f"  - {d.get('date', 'N/A')} ({d.get('season', 'N/A')})")
            
            print(f"\n✓ Events found: {len(context.get('events', []))}")
            for e in context.get('events', [])[:3]:
                print(f"  - {e.get('event_name', 'N/A')} on {e.get('date', 'N/A')}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")


def test_context_expansion():
    """Test Neo4j context expansion"""
    print("\n" + "="*80)
    print("TEST 2: Context Expansion (Neo4j Knowledge Graph)")
    print("="*80)
    
    query = "Show me soda sales in California"
    print(f"\n📝 Query: {query}")
    
    try:
        # Get initial context from Azure Search
        entities = context_resolver.resolver.search.resolve_entities(query)
        
        print("\n1️⃣ Initial entities from Azure Search:")
        print(f"   Products: {len(entities.get('products', []))}")
        print(f"   Locations: {len(entities.get('locations', []))}")
        
        # Expand via Neo4j
        expanded = context_resolver.resolver._expand_context_via_graph(entities)
        
        print("\n2️⃣ After Neo4j expansion:")
        print(f"   Expanded Products: {len(expanded.get('expanded_products', []))}")
        print(f"   Expanded Locations: {len(expanded.get('expanded_locations', []))}")
        print(f"   Related Events: {len(expanded.get('related_events', []))}")
        
        # Show sample expanded data
        if expanded.get('expanded_products'):
            print("\n   Sample expanded products:")
            for p in expanded['expanded_products'][:5]:
                print(f"   - {p.get('product_name', 'N/A')} ({p.get('category', 'N/A')})")
        
        if expanded.get('expanded_locations'):
            print("\n   Sample expanded locations:")
            for l in expanded['expanded_locations'][:5]:
                print(f"   - {l.get('store_name', 'N/A')} ({l.get('state', 'N/A')})")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_full_pipeline():
    """Test complete pipeline: Azure Search + Neo4j + SQL Generation + PostgreSQL"""
    print("\n" + "="*80)
    print("TEST 3: Full RAG Pipeline (Search → Graph → SQL → PostgreSQL)")
    print("="*80)
    
    test_queries = [
        "What are the total sales for Pepsi products in Texas?",
        "Show me ice cream sales by state during summer 2023",
        "Compare sales before and during Super Bowl events"
    ]
    
    agent = DatabaseAgent()
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 80)
        
        try:
            # Execute full pipeline
            result = agent.query_database(query)
            
            if result.get("status") == "success":
                print(f"\n✅ SUCCESS")
                print(f"\n📊 Context: {result.get('context_summary', 'N/A')}")
                print(f"\n💾 Generated SQL:\n{result.get('sql_query', 'N/A')}")
                print(f"\n📈 Results: {result.get('row_count', 0)} rows returned")
                
                # Show sample data
                if result.get('data'):
                    print(f"\n🔍 Sample data (first 3 rows):")
                    for i, row in enumerate(result['data'][:3], 1):
                        print(f"   Row {i}: {row}")
            else:
                print(f"\n❌ FAILED")
                print(f"Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"\n❌ Exception: {e}")
        
        print("\n" + "-" * 80)


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("ENHANCED RAG PIPELINE TEST SUITE")
    print("Azure AI Search + Neo4j Knowledge Graph + PostgreSQL")
    print("="*80)
    
    try:
        # Test 1: Entity Resolution
        test_entity_resolution()
        
        # Test 2: Context Expansion
        test_context_expansion()
        
        # Test 3: Full Pipeline
        test_full_pipeline()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
