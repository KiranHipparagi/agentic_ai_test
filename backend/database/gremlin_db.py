from gremlin_python.driver import client, serializer
from typing import List, Dict, Any, Optional
from core.config import settings
from core.logger import logger


class GremlinConnection:
    """Cosmos DB Gremlin API connection manager using Client (same as build script)"""
    
    def __init__(self):
        self.gremlin_client = None
        self._connected = False
        
    def _connect(self):
        """Establish connection to Cosmos DB Gremlin API"""
        if self._connected:
            return

        try:
            # Get endpoint from settings (same as build_planalytics_gremlin_async.py)
            # COSMOS_ENDPOINT is just the host: your-cosmos-account.gremlin.cosmos.azure.com
            endpoint = settings.COSMOS_ENDPOINT
            cosmos_key = settings.COSMOS_KEY
            cosmos_database = settings.COSMOS_DATABASE
            cosmos_graph = settings.COSMOS_GRAPH
            cosmos_port = settings.COSMOS_PORT
            
            # If endpoint is empty or placeholder, skip connection
            if not endpoint or endpoint == "" or "your-cosmos" in endpoint:
                logger.warning("⚠️ Gremlin endpoint not configured - skipping connection")
                self._connected = False
                return
            
            # Connection URL format: wss://<host>:<port>/gremlin
            url = f"wss://{endpoint}:{cosmos_port}/gremlin"
            
            # Username format: /dbs/<database>/colls/<graph>
            username = f"/dbs/{cosmos_database}/colls/{cosmos_graph}"
            
            # Use the same Client approach as build_planalytics_gremlin_async.py
            self.gremlin_client = client.Client(
                url,
                'g',
                username=username,
                password=cosmos_key,
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
            
            self._connected = True
            logger.info(f"✅ Cosmos DB Gremlin connection established: {endpoint}")
        except Exception as e:
            logger.warning(f"⚠️ Gremlin connection failed: {e}")
            self.gremlin_client = None
            self._connected = False

    def ensure_connected(self) -> bool:
        """Ensure connection is established, return success status"""
        if not self._connected:
            self._connect()
        return self._connected

    def close(self):
        """Close Gremlin connection"""
        if self.gremlin_client:
            self.gremlin_client.close()
            self._connected = False
            logger.info("Gremlin connection closed")

    def submit_query(self, query: str) -> List[Dict]:
        """Submit a Gremlin query and return results"""
        if not self.ensure_connected():
            return []
        
        try:
            result_set = self.gremlin_client.submit(query)
            results = result_set.all().result()
            return results
        except Exception as e:
            logger.error(f"Gremlin query error: {e}")
            return []

    def create_supply_chain_graph(self, data: Dict[str, Any]) -> None:
        """Create supply chain relationships"""
        if not self.ensure_connected():
            logger.warning("Skipping graph creation - Gremlin unavailable")
            return
            
        try:
            # Create Product vertex
            product_query = f"g.V().has('Product', 'id', '{data['product_id']}').fold().coalesce(unfold(), addV('Product').property('id', '{data['product_id']}').property('name', '{data.get('product_name', '')}'))"
            self.submit_query(product_query)
            
            # Create Location vertex
            location_query = f"g.V().has('Location', 'id', '{data['location_id']}').fold().coalesce(unfold(), addV('Location').property('id', '{data['location_id']}').property('name', '{data.get('location_name', '')}'))"
            self.submit_query(location_query)
            
            logger.info(f"Created graph nodes for {data['product_id']}")
            
        except Exception as e:
            logger.error(f"Gremlin graph creation error: {e}")

    def query_supply_chain_impact(self, product_id: str, location_id: str) -> List[Dict]:
        """Query supply chain impact factors"""
        if not self.ensure_connected():
            return []
            
        try:
            query = f"g.V().has('Product', 'id', '{product_id}').out('STORED_AT').has('Location', 'id', '{location_id}').valueMap(true)"
            results = self.submit_query(query)
            return results
        except Exception as e:
            logger.error(f"Gremlin query error: {e}")
            return []

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
            # Build query: Find products → traverse to category → find other products in same category
            ids_str = "', '".join(gremlin_ids)
            query = f"""g.V().hasLabel('Product').has('id', within('{ids_str}'))
                .out('IN_CATEGORY').as('c')
                .in('IN_CATEGORY').hasLabel('Product').dedup()
                .project('product_id', 'product_name', 'category')
                .by('product_id').by('name').by(select('c').values('name'))
                .limit(50)"""
            results = self.submit_query(query)
            return results
        except Exception as e:
            logger.error(f"Gremlin expand product error: {e}")
            return []

    def expand_location_context(self, location_ids: List[str]) -> List[Dict[str, Any]]:
        """Expand location context by finding all stores in same region/market"""
        if not self.ensure_connected() or not location_ids:
            return []
        
        try:
            # Build query: Find stores → traverse to market → find other stores in same market
            ids_str = "', '".join(location_ids)
            query = f"""g.V().hasLabel('Store').has('id', within('{ids_str}'))
                .out('IN_MARKET').as('m')
                .in('IN_MARKET').hasLabel('Store').dedup()
                .project('store_id', 'store_name', 'market')
                .by('id').by('name').by(select('m').values('name'))
                .limit(200)"""
            results = self.submit_query(query)
            return results
        except Exception as e:
            logger.error(f"Gremlin expand location error: {e}")
            return []

    def find_related_events(self, location_ids: List[str], dates: List[str]) -> List[Dict[str, Any]]:
        """Find event types (metadata only - full event occurrences in PostgreSQL)"""
        if not self.ensure_connected():
            return []
            
        try:
            # Graph stores EventType metadata only, full event data is in PostgreSQL
            query = """g.V().hasLabel('EventType')
                .project('event_name', 'event_type')
                .by('name').by('type')
                .limit(100)"""
            results = self.submit_query(query)
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
            query = f"""g.V().has('Product', 'id', '{gremlin_id}').as('p')
                .out('IN_CATEGORY').as('c')
                .out('IN_DEPARTMENT').as('d')
                .project('product_id', 'product_name', 'category', 'department')
                .by(select('p').values('product_id'))
                .by(select('p').values('name'))
                .by(select('c').values('name'))
                .by(select('d').values('name'))"""
            results = self.submit_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Gremlin get product hierarchy error: {e}")
            return {}

    def get_location_hierarchy(self, store_id: str) -> Dict[str, Any]:
        """Get full hierarchy for a location"""
        if not self.ensure_connected():
            return {}
            
        try:
            query = f"""g.V().has('Store', 'id', '{store_id}').as('s')
                .out('IN_MARKET').as('m')
                .out('IN_STATE').as('st')
                .out('IN_REGION').as('r')
                .project('store_id', 'store_name', 'market', 'state', 'region')
                .by(select('s').values('id'))
                .by(select('s').values('name'))
                .by(select('m').values('name'))
                .by(select('st').values('name'))
                .by(select('r').values('name'))"""
            results = self.submit_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Gremlin get location hierarchy error: {e}")
            return {}

# Global Gremlin instance
gremlin_conn = GremlinConnection()
