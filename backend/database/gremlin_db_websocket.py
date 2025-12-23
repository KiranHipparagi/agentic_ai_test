"""
Cosmos DB Gremlin Connection - WebSocket Version
Handles common AIOHTTP/connection issues gracefully
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
        
    def _connect(self):
        """Establish WebSocket connection to Cosmos DB Gremlin API"""
        if self._connected:
            return

        try:
            # WebSocket URL format: wss://endpoint:port/gremlin
            url = f"wss://{settings.COSMOS_ENDPOINT}:{settings.COSMOS_PORT}/gremlin"
            
            # Username format: /dbs/database/colls/graph
            username = f"/dbs/{settings.COSMOS_DATABASE}/colls/{settings.COSMOS_GRAPH}"
            password = settings.COSMOS_KEY
            
            logger.info(f"Connecting to Cosmos DB Gremlin...")
            logger.info(f"   Endpoint: wss://{settings.COSMOS_ENDPOINT}:{settings.COSMOS_PORT}/gremlin")
            logger.info(f"   Database: {settings.COSMOS_DATABASE}")
            logger.info(f"   Graph: {settings.COSMOS_GRAPH}")
            
            # Create WebSocket connection
            self.conn = DriverRemoteConnection(
                url, 
                'g',
                username=username,
                password=password,
                message_serializer=None  # Use default serializer
            )
            
            # Create traversal source
            self.g = traversal().withRemote(self.conn)
            
            # Test connection with simple query
            try:
                count = self.g.V().count().next()
                self._connected = True
                logger.info(f"✅ Cosmos DB Gremlin connected successfully - {count} vertices found")
            except Exception as test_error:
                logger.error(f"❌ Connection test failed: {test_error}")
                raise
            
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"❌ Gremlin WebSocket connection failed: {e}")
            
            # Provide helpful troubleshooting tips
            if "aiohttp" in error_msg or "asyncio" in error_msg:
                logger.error("   💡 AIOHTTP version issue detected")
                logger.error("   💡 Try: pip uninstall aiohttp && pip install aiohttp==3.8.6")
                logger.error("   💡 Or: pip uninstall aiohttp && pip install aiohttp==3.8.3")
            elif "authentication" in error_msg or "401" in error_msg or "unauthorized" in error_msg:
                logger.error("   💡 Authentication failed - check COSMOS_KEY in .env")
                logger.error("   💡 Verify key format: should be base64 string from Azure Portal")
            elif "network" in error_msg or "connection refused" in error_msg or "timeout" in error_msg:
                logger.error("   💡 Network/firewall issue")
                logger.error("   💡 Check Azure Portal → Cosmos DB → Networking → Firewall")
                logger.error("   💡 Add your IP address to allowed list")
            elif "404" in error_msg or "not found" in error_msg:
                logger.error(f"   💡 Database or graph not found")
                logger.error(f"   💡 Verify in Azure Portal: {settings.COSMOS_DATABASE}/{settings.COSMOS_GRAPH}")
            
            self.conn = None
            self.g = None
            self._connected = False

    def ensure_connected(self) -> bool:
        """Ensure connection is established, return success status"""
        if not self._connected:
            self._connect()
        return self._connected

    def close(self):
        """Close Gremlin connection"""
        if self.conn:
            try:
                self.conn.close()
                logger.info("Gremlin connection closed")
            except:
                pass
        self._connected = False

    def expand_product_context(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """Expand product context by finding related products in same category"""
        if not self.ensure_connected() or not product_ids:
            return []
        
        # Convert Azure Search IDs (PROD_1 → P_1) to match graph structure
        gremlin_ids = []
        for pid in product_ids:
            try:
                if isinstance(pid, str) and pid.startswith('PROD_'):
                    gremlin_ids.append(f"P_{pid.replace('PROD_', '')}")
                elif isinstance(pid, int):
                    gremlin_ids.append(f"P_{pid}")
                else:
                    gremlin_ids.append(str(pid))
            except:
                pass
        
        if not gremlin_ids:
            return []
        
        try:
            # Use WebSocket traversal API (not string queries)
            results = (self.g.V()
                .hasLabel('Product')
                .has('id', P.within(gremlin_ids))
                .out('IN_CATEGORY').as_('c')
                .in_('IN_CATEGORY')
                .hasLabel('Product')
                .dedup()
                .project('product_id', 'product_name', 'category')
                    .by('product_id')
                    .by('name')
                    .by(__.select('c').values('name'))
                .limit(50)
                .toList())
            
            logger.info(f"Gremlin product expansion: Found {len(results)} related products")
            return results
        except Exception as e:
            logger.error(f"Gremlin expand product error: {e}")
            return []

    def expand_location_context(self, location_ids: List[str]) -> List[Dict[str, Any]]:
        """Expand location context by finding all stores in same region/market"""
        if not self.ensure_connected() or not location_ids:
            return []
        
        try:
            # Use WebSocket traversal API
            results = (self.g.V()
                .hasLabel('Store')
                .has('id', P.within(location_ids[:3]))  # Limit to 3 for performance
                .out('IN_MARKET').as_('m')
                .in_('IN_MARKET')
                .hasLabel('Store')
                .dedup()
                .project('store_id', 'store_name', 'market')
                    .by('id')
                    .by('name')
                    .by(__.select('m').values('name'))
                .limit(200)
                .toList())
            
            logger.info(f"Gremlin location expansion: Found {len(results)} related stores")
            return results
        except Exception as e:
            logger.error(f"Gremlin expand location error: {e}")
            return []

    def find_related_events(self, location_ids: List[str], dates: List[str]) -> List[Dict[str, Any]]:
        """Find event types (metadata only - full event occurrences in PostgreSQL)"""
        if not self.ensure_connected():
            return []
            
        try:
            # Return EventType metadata only
            results = (self.g.V()
                .hasLabel('EventType')
                .project('event_name', 'event_type')
                    .by('name')
                    .by('type')
                .limit(100)
                .toList())
            
            logger.info(f"Gremlin events: Found {len(results)} event types")
            return results
        except Exception as e:
            logger.error(f"Gremlin find events error: {e}")
            return []

    def get_product_hierarchy(self, product_id: str) -> Dict[str, Any]:
        """Get full hierarchy for a product"""
        if not self.ensure_connected():
            return {}
        
        # Convert to Gremlin ID format (P_1, P_2, etc.)
        gremlin_id = f"P_{product_id}" if not product_id.startswith('P_') else product_id
            
        try:
            result = (self.g.V()
                .has('Product', 'id', gremlin_id).as_('p')
                .out('IN_CATEGORY').as_('c')
                .out('IN_DEPARTMENT').as_('d')
                .project('product_id', 'product_name', 'category', 'department')
                    .by(__.select('p').values('product_id'))
                    .by(__.select('p').values('name'))
                    .by(__.select('c').values('name'))
                    .by(__.select('d').values('name'))
                .next())
            
            return result
        except Exception as e:
            logger.error(f"Gremlin get product hierarchy error: {e}")
            return {}

    def get_location_hierarchy(self, store_id: str) -> Dict[str, Any]:
        """Get full hierarchy for a location"""
        if not self.ensure_connected():
            return {}
            
        try:
            result = (self.g.V()
                .has('Store', 'id', store_id).as_('s')
                .out('IN_MARKET').as_('m')
                .out('IN_STATE').as_('st')
                .out('IN_REGION').as_('r')
                .project('store_id', 'store_name', 'market', 'state', 'region')
                    .by(__.select('s').values('id'))
                    .by(__.select('s').values('name'))
                    .by(__.select('m').values('name'))
                    .by(__.select('st').values('name'))
                    .by(__.select('r').values('name'))
                .next())
            
            return result
        except Exception as e:
            logger.error(f"Gremlin get location hierarchy error: {e}")
            return {}

# Global Gremlin instance
gremlin_conn = GremlinConnection()
