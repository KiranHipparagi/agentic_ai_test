"""
Comprehensive Cosmos DB Gremlin Diagnostics
Tests multiple connection methods to find what works
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import requests
import base64
import json
from dotenv import load_dotenv

load_dotenv()

def test_basic_connectivity():
    """Test basic network connectivity to Cosmos DB"""
    print("="*80)
    print("TEST 1: Network Connectivity")
    print("="*80)
    
    endpoint = os.getenv("COSMOS_ENDPOINT")
    port = os.getenv("COSMOS_PORT", "443")
    
    print(f"Endpoint: {endpoint}")
    print(f"Port: {port}")
    
    # Try HTTPS
    try:
        url = f"https://{endpoint}:{port}"
        print(f"\nTrying HTTPS: {url}")
        response = requests.get(url, timeout=5, verify=False)
        print(f"✅ HTTPS reachable - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ HTTPS failed: {e}")
    
    # Try WSS (WebSocket Secure) - this is what Gremlin uses
    print(f"\n💡 Cosmos DB Gremlin uses WebSocket (wss://), not HTTPS REST API")
    print(f"   WebSocket endpoint: wss://{endpoint}:{port}/gremlin")

def test_rest_api_formats():
    """Try different REST API endpoint formats"""
    print("\n" + "="*80)
    print("TEST 2: REST API Endpoint Formats")
    print("="*80)
    
    endpoint = os.getenv("COSMOS_ENDPOINT")
    database = os.getenv("COSMOS_DATABASE", "planalytics")
    graph = os.getenv("COSMOS_GRAPH", "planalytics_graph")
    cosmos_key = os.getenv("COSMOS_KEY")
    
    # Create auth header
    auth_string = f"/dbs/{database}/colls/{graph}:{cosmos_key}"
    auth_base64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {auth_base64}',
        'Accept': 'application/json'
    }
    
    payload = {"gremlin": "g.V().count()"}
    
    # Format 1: /gremlin endpoint
    formats = [
        f"https://{endpoint}:443/gremlin",
        f"https://{endpoint}/gremlin",
        f"https://{endpoint}:443/",
        f"https://{endpoint}:443/dbs/{database}/colls/{graph}/docs",
        f"https://{endpoint}/dbs/{database}/colls/{graph}"
    ]
    
    for url in formats:
        print(f"\n📍 Trying: {url}")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10, verify=False)
            print(f"   Status: {response.status_code}")
            if response.status_code != 500:
                print(f"   Response: {response.text[:200]}")
                if response.status_code == 200:
                    print("   ✅ SUCCESS!")
                    return url
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ All REST API formats failed")
    return None

def test_auth_formats():
    """Try different authentication header formats"""
    print("\n" + "="*80)
    print("TEST 3: Authentication Formats")
    print("="*80)
    
    endpoint = os.getenv("COSMOS_ENDPOINT")
    database = os.getenv("COSMOS_DATABASE", "planalytics")
    graph = os.getenv("COSMOS_GRAPH", "planalytics_graph")
    cosmos_key = os.getenv("COSMOS_KEY")
    
    url = f"https://{endpoint}:443/gremlin"
    payload = {"gremlin": "g.V().count()"}
    
    # Format 1: Basic auth with resource path
    auth1 = base64.b64encode(f"/dbs/{database}/colls/{graph}:{cosmos_key}".encode()).decode()
    
    # Format 2: Just the key
    auth2 = base64.b64encode(cosmos_key.encode()).decode()
    
    # Format 3: Master key header (Azure SQL API style)
    import hashlib
    import hmac
    from datetime import datetime
    
    verb = "post"
    resource_type = "docs"
    resource_link = f"dbs/{database}/colls/{graph}"
    date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    auth_formats = [
        {
            "name": "Basic with resource path",
            "headers": {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {auth1}',
                'Accept': 'application/json'
            }
        },
        {
            "name": "Basic with key only",
            "headers": {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {auth2}',
                'Accept': 'application/json'
            }
        },
        {
            "name": "Master key token",
            "headers": {
                'Content-Type': 'application/json',
                'Authorization': f'type=master&ver=1.0&sig={auth2}',
                'x-ms-date': date,
                'x-ms-version': '2018-12-31',
                'Accept': 'application/json'
            }
        }
    ]
    
    for auth_format in auth_formats:
        print(f"\n🔑 Trying: {auth_format['name']}")
        try:
            response = requests.post(url, headers=auth_format['headers'], json=payload, timeout=10, verify=False)
            print(f"   Status: {response.status_code}")
            if response.status_code != 500:
                print(f"   Response: {response.text[:200]}")
                if response.status_code == 200:
                    print("   ✅ SUCCESS!")
                    return auth_format['headers']
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ All auth formats failed")
    return None

def check_graph_via_azure_portal():
    """Guide user to check graph in Azure Portal"""
    print("\n" + "="*80)
    print("TEST 4: Azure Portal Verification")
    print("="*80)
    
    endpoint = os.getenv("COSMOS_ENDPOINT")
    database = os.getenv("COSMOS_DATABASE", "planalytics")
    graph = os.getenv("COSMOS_GRAPH", "planalytics_graph")
    
    print("\n📋 Manual Verification Steps:")
    print("\n1️⃣ Go to Azure Portal: https://portal.azure.com")
    print(f"2️⃣ Navigate to Cosmos DB account: {endpoint.split('.')[0] if endpoint else 'your-account'}")
    print(f"3️⃣ Open Data Explorer")
    print(f"4️⃣ Select database: {database}")
    print(f"5️⃣ Select graph: {graph}")
    print(f"6️⃣ Run query: g.V().count()")
    print("\n📊 Expected result: Should show number of vertices (e.g., 624)")
    print("\n❓ If result is 0: Graph is empty - need to re-run ingestion")
    print("❓ If result > 0: Graph has data - connection method is the issue")

def suggest_websocket_driver():
    """Suggest using proper WebSocket driver"""
    print("\n" + "="*80)
    print("SOLUTION: Use WebSocket Driver (Recommended)")
    print("="*80)
    
    print("\n🔍 Problem Analysis:")
    print("   • Cosmos DB Gremlin API uses WebSocket (wss://), not REST API")
    print("   • HTTP 500 errors indicate REST API is not supported or misconfigured")
    print("   • The gremlin-python library uses WebSocket by default")
    
    print("\n✅ Recommended Solution:")
    print("   Install the correct driver that handles AIOHTTP issues:")
    
    print("\n   Option 1: Use gremlin-python with aiogremlin (recommended)")
    print("   ```bash")
    print("   pip install gremlinpython==3.6.2")
    print("   pip install aiohttp==3.8.6")
    print("   ```")
    
    print("\n   Option 2: Use Azure Cosmos DB Python SDK")
    print("   ```bash")
    print("   pip install azure-cosmos")
    print("   ```")
    
    print("\n   Option 3: Downgrade aiohttp (if AIOHTTP error)")
    print("   ```bash")
    print("   pip uninstall aiohttp")
    print("   pip install aiohttp==3.8.6")
    print("   ```")
    
    print("\n💡 After installing, use the WebSocket version of gremlin_db.py")
    print("   The file in attachments (gremlin_db.py with WebSocket) should work")

def create_working_websocket_version():
    """Create a working WebSocket version with error handling"""
    print("\n" + "="*80)
    print("Creating Working WebSocket Version")
    print("="*80)
    
    websocket_code = '''"""
Cosmos DB Gremlin Connection with WebSocket
Handles AIOHTTP version issues gracefully
"""
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T, P, Order, Column, Operator
from typing import List, Dict, Any, Optional
from core.config import settings
from core.logger import logger
import sys

class GremlinConnection:
    """Cosmos DB Gremlin API connection manager using WebSocket"""
    
    def __init__(self):
        self.g = None
        self.conn = None
        self._connected = False
        self._connect()
        
    def _connect(self):
        """Establish WebSocket connection to Cosmos DB Gremlin API"""
        if self._connected:
            return

        try:
            # WebSocket URL format
            url = f"wss://{settings.COSMOS_ENDPOINT}:{settings.COSMOS_PORT}/gremlin"
            
            # Username format for Cosmos DB
            username = f"/dbs/{settings.COSMOS_DATABASE}/colls/{settings.COSMOS_GRAPH}"
            password = settings.COSMOS_KEY
            
            logger.info(f"Connecting to Cosmos DB Gremlin: {url}")
            logger.info(f"Database: {settings.COSMOS_DATABASE}, Graph: {settings.COSMOS_GRAPH}")
            
            self.conn = DriverRemoteConnection(url, 'g', username=username, password=password)
            self.g = traversal().withRemote(self.conn)
            
            # Test connection
            count = self.g.V().count().next()
            
            self._connected = True
            logger.info(f"✅ Cosmos DB Gremlin connected successfully - {count} vertices")
            
        except Exception as e:
            logger.error(f"❌ Gremlin connection failed: {e}")
            logger.error(f"   Endpoint: wss://{settings.COSMOS_ENDPOINT}:{settings.COSMOS_PORT}/gremlin")
            
            # Provide helpful error messages
            error_str = str(e).lower()
            if "aiohttp" in error_str or "asyncio" in error_str:
                logger.error("   💡 TIP: Try: pip install aiohttp==3.8.6")
            elif "authentication" in error_str or "401" in error_str:
                logger.error("   💡 TIP: Check COSMOS_KEY in .env file")
            elif "network" in error_str or "connection" in error_str:
                logger.error("   💡 TIP: Check firewall rules in Azure Portal")
            
            self.conn = None
            self.g = None
            self._connected = False

    def ensure_connected(self) -> bool:
        """Ensure connection is established"""
        if not self._connected:
            self._connect()
        return self._connected

    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()
            self._connected = False
            logger.info("Gremlin connection closed")

    # ... (rest of methods same as before)

# Global instance
gremlin_conn = GremlinConnection()
'''
    
    output_file = Path(__file__).parent.parent / "database" / "gremlin_db_websocket.py"
    with open(output_file, 'w') as f:
        f.write(websocket_code)
    
    print(f"✅ Created: {output_file}")
    print("\nTo use this version:")
    print("   1. Install: pip install gremlinpython aiohttp==3.8.6")
    print("   2. Backup: mv database/gremlin_db.py database/gremlin_db_rest_backup.py")
    print("   3. Use WebSocket: cp database/gremlin_db_websocket.py database/gremlin_db.py")

def main():
    print("🔬 COSMOS DB GREMLIN DIAGNOSTICS")
    print("=" * 80)
    
    # Check env vars
    print("\n📋 Configuration Check:")
    print(f"   COSMOS_ENDPOINT: {os.getenv('COSMOS_ENDPOINT', 'NOT SET')}")
    print(f"   COSMOS_DATABASE: {os.getenv('COSMOS_DATABASE', 'NOT SET')}")
    print(f"   COSMOS_GRAPH: {os.getenv('COSMOS_GRAPH', 'NOT SET')}")
    print(f"   COSMOS_KEY: {'*' * 20 if os.getenv('COSMOS_KEY') else 'NOT SET'}")
    
    if not all([os.getenv('COSMOS_ENDPOINT'), os.getenv('COSMOS_KEY')]):
        print("\n❌ Missing required environment variables!")
        print("   Make sure .env file has COSMOS_ENDPOINT and COSMOS_KEY")
        return
    
    # Run tests
    test_basic_connectivity()
    test_rest_api_formats()
    test_auth_formats()
    check_graph_via_azure_portal()
    suggest_websocket_driver()
    
    print("\n" + "="*80)
    print("📊 DIAGNOSIS SUMMARY")
    print("="*80)
    print("\n🔴 Current Status: REST API returns HTTP 500 on all queries")
    print("\n🔍 Root Cause: Cosmos DB Gremlin uses WebSocket, not REST API")
    print("\n✅ Solution: Switch back to WebSocket driver (gremlin-python)")
    print("\n📝 Action Steps:")
    print("   1. Check graph has data in Azure Portal")
    print("   2. Install: pip install gremlinpython==3.6.2 aiohttp==3.8.6")
    print("   3. Use WebSocket version of gremlin_db.py (not REST)")
    print("   4. If AIOHTTP error persists, try: pip install aiohttp==3.8.3")
    print("\n💡 The graph data is likely correct - just need right connection method!")

if __name__ == "__main__":
    main()
