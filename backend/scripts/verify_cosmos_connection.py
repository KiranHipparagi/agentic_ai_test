"""
Quick verification: Check if graph has data in Cosmos DB
Run this FIRST before testing queries
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_websocket_connection():
    """Test WebSocket connection and count vertices"""
    print("="*80)
    print("COSMOS DB GREMLIN - WEBSOCKET CONNECTION TEST")
    print("="*80)
    
    try:
        from database.gremlin_db_websocket import gremlin_conn
        
        print("\n1️⃣ Testing WebSocket connection...")
        
        if not gremlin_conn.ensure_connected():
            print("❌ Connection failed")
            print("\n💡 Troubleshooting:")
            print("   1. Check .env file has COSMOS_ENDPOINT, COSMOS_KEY, etc.")
            print("   2. Run: pip install aiohttp==3.8.6")
            print("   3. Check Azure Portal firewall rules")
            return False
        
        print("✅ Connected successfully!")
        
        # Count vertices by label
        print("\n2️⃣ Counting vertices...")
        
        labels_to_check = [
            'Product', 'Category', 'Department',
            'Store', 'Market', 'State', 'Region',
            'EventType', 'PerishableInfo'
        ]
        
        total = 0
        for label in labels_to_check:
            try:
                count = gremlin_conn.g.V().hasLabel(label).count().next()
                if count > 0:
                    print(f"   {label}: {count}")
                    total += count
            except Exception as e:
                print(f"   {label}: Error - {e}")
        
        print(f"\n✅ Total vertices: {total}")
        
        if total == 0:
            print("\n❌ Graph is EMPTY!")
            print("   Need to run ingestion: python planalytics_gremlin/build_planalytics_gremlin_async.py")
            return False
        
        # Test a simple query
        print("\n3️⃣ Testing sample query...")
        try:
            sample = gremlin_conn.g.V().hasLabel('Product').limit(1).valueMap().next()
            print(f"✅ Sample product: {sample}")
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return False
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED - Graph is ready to use!")
        print("="*80)
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Make sure to:")
        print("   1. Install: pip install gremlinpython aiohttp==3.8.6")
        print("   2. Copy: cp database\\gremlin_db_websocket.py database\\gremlin_db.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_aiohttp_version():
    """Check AIOHTTP version compatibility"""
    print("\n" + "="*80)
    print("AIOHTTP VERSION CHECK")
    print("="*80)
    
    try:
        import aiohttp
        print(f"✅ AIOHTTP installed: {aiohttp.__version__}")
        
        # Check if version is compatible
        version = aiohttp.__version__
        major, minor = map(int, version.split('.')[:2])
        
        if major == 3 and minor >= 8:
            print("✅ Version is compatible")
        else:
            print(f"⚠️  Version {version} might cause issues")
            print("   Recommended: pip install aiohttp==3.8.6")
            
    except ImportError:
        print("❌ AIOHTTP not installed")
        print("   Run: pip install aiohttp==3.8.6")
    except Exception as e:
        print(f"⚠️  Could not check version: {e}")

def check_environment():
    """Check required environment variables"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("\n" + "="*80)
    print("ENVIRONMENT VARIABLES CHECK")
    print("="*80)
    
    required = [
        'COSMOS_ENDPOINT',
        'COSMOS_DATABASE',
        'COSMOS_GRAPH',
        'COSMOS_KEY',
        'COSMOS_PORT'
    ]
    
    all_good = True
    for var in required:
        value = os.getenv(var)
        if value:
            if 'KEY' in var:
                print(f"✅ {var}: {'*' * 20}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_good = False
    
    if not all_good:
        print("\n⚠️  Missing environment variables in .env file!")
    
    return all_good

if __name__ == "__main__":
    print("🔍 COSMOS DB GREMLIN QUICK VERIFICATION")
    print("This script checks if everything is configured correctly\n")
    
    # Step 1: Check environment
    if not check_environment():
        print("\n❌ Fix environment variables first!")
        sys.exit(1)
    
    # Step 2: Check AIOHTTP
    check_aiohttp_version()
    
    # Step 3: Test connection
    print()
    if test_websocket_connection():
        print("\n🎉 SUCCESS! Your Cosmos DB Gremlin is working!")
        print("\nYou can now:")
        print("   • Run chatbot: python main.py")
        print("   • Test queries: python scripts/test_fixed_gremlin_queries.py")
    else:
        print("\n❌ Tests failed. Check error messages above.")
        print("\n📖 Read COSMOS_DB_500_ERROR_FIX.md for detailed troubleshooting")
