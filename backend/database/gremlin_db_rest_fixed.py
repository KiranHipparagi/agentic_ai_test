import requests
import json
from typing import List, Dict, Any, Optional
from core.config import settings
from core.logger import logger
import base64
import urllib3

# Disable SSL warnings when verification is disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GremlinConnection:
    """Cosmos DB Gremlin API connection manager using REST API"""
    
    def __init__(self):
        self._connected = False
        self.endpoint = None
        self.headers = None
        self._setup_connection()
        
    def _setup_connection(self):
        """Setup connection parameters for Cosmos DB Gremlin REST API"""
        try:
            # Cosmos DB Gremlin REST API endpoint
            self.endpoint = f"https://{settings.COSMOS_ENDPOINT}:{settings.COSMOS_PORT}/gremlin"
            
            # Create authorization header
            auth_string = f"/dbs/{settings.COSMOS_DATABASE}/colls/{settings.COSMOS_GRAPH}:{settings.COSMOS_KEY}"
            auth_bytes = auth_string.encode('utf-8')
            auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            self.headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {auth_base64}',
                'x-ms-date': '',
                'Accept': 'application/json'
            }
            
            # Test connection with a simple query
            test_result = self._execute_query("g.V().count()")
            if test_result is not None:
                self._connected = True
                logger.info(f"✅ Cosmos DB Gremlin connection established successfully (REST API) - {test_result[0] if test_result else 0} vertices")
            else:
                logger.warning("⚠️ Gremlin test query failed")
                
        except Exception as e:
            logger.warning(f"⚠️ Gremlin connection setup failed: {e}")
            self._connected = False

    def ensure_connected(self) -> bool:
        """Ensure connection is established, return success status"""
        if not self._connected:
            self._setup_connection()
        return self._connected

    def close(self):
        """Close Gremlin connection (no-op for REST API)"""
        self._connected = False
        logger.info("Gremlin connection closed")

    def _execute_query(self, query: str, bindings: Dict[str, Any] = None) -> List[Any]:
        """Execute a Gremlin query via REST API"""
        if not self.endpoint or not self.headers:
            return []
        
        try:
            payload = {
                "gremlin": query
            }
            
            if bindings:
                payload["bindings"] = bindings
            
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=30,
                verify=False  # Disable SSL verification
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cosmos DB returns results in 'result' field
                return result.get('result', {}).get('data', result.get('result', []))
            else:
                logger.error(f"Gremlin query failed: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error("Gremlin query timeout")
            return []
        except Exception as e:
            logger.error(f"Gremlin execution error: {e}")
            return []

    def create_supply_chain_graph(self, data: Dict[str, Any]) -> None:
        """Create supply chain relationships"""
        if not self.ensure_connected():
            logger.warning("Skipping graph creation - Gremlin unavailable")
            return
            
        try:
            # Create Product vertex
            query = f"""g.V().has('Product', 'id', '{data['product_id']}').fold().coalesce(unfold(), addV('Product').property('id', '{data['product_id']}').property('name', '{data['product_name']}'))"""
            self._execute_query(query)
            
            # Create Location vertex
            query = f"""g.V().has('Location', 'id', '{data['location_id']}').fold().coalesce(unfold(), addV('Location').property('id', '{data['location_id']}').property('name', '{data['location_name']}'))"""
            self._execute_query(query)
            
            # Create Weather vertex
            query = f"""g.addV('Weather').property('conditions', '{data['weather_conditions']}').property('temp', {data['temperature']})"""
            self._execute_query(query)
            
            # Create Event vertex
            query = f"""g.V().has('Event', 'name', '{data['event_name']}').fold().coalesce(unfold(), addV('Event').property('name', '{data['event_name']}').property('type', '{data['event_type']}'))"""
            self._execute_query(query)
            
            # Create edge: Product -> Location
            query = f"""g.V().has('Product', 'id', '{data['product_id']}').as('p').V().has('Location', 'id', '{data['location_id']}').as('l').coalesce(outE('STORED_AT').where(inV().as('l')), addE('STORED_AT').from('p').to('l'))"""
            self._execute_query(query)
            
            logger.info(f"Created graph nodes for {data['product_id']}")
            
        except Exception as e:
            logger.error(f"Gremlin graph creation error: {e}")

    def query_supply_chain_impact(self, product_id: str, location_id: str) -> List[Dict]:
        """Query supply chain impact factors"""
        if not self.ensure_connected():
            return []
            
        try:
            query = f"""g.V().has('Product', 'id', '{product_id}').out('STORED_AT').has('Location', 'id', '{location_id}').project('product', 'location').by(valueMap()).by(valueMap())"""
            
            results = self._execute_query(query)
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
            # FIX: Use proper array notation for within()
            # Cosmos DB Gremlin REST API expects: within(['P_1','P_2','P_3'])
            ids_formatted = ",".join([f"'{id}'" for id in gremlin_ids])
            
            query = f"""g.V().hasLabel('Product').has('id', within({ids_formatted})).out('IN_CATEGORY').as('c').in('IN_CATEGORY').hasLabel('Product').dedup().project('product_id', 'product_name', 'category').by('product_id').by('name').by(select('c').values('name')).limit(50)"""
            
            results = self._execute_query(query)
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
            # FIX: Use proper array notation for within()
            ids_formatted = ",".join([f"'{id}'" for id in location_ids[:3]])  # Limit to first 3 for performance
            
            query = f"""g.V().hasLabel('Store').has('id', within({ids_formatted})).out('IN_MARKET').as('m').in('IN_MARKET').hasLabel('Store').dedup().project('store_id', 'store_name', 'market').by('id').by('name').by(select('m').values('name')).limit(200)"""
            
            results = self._execute_query(query)
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
            # Builder creates: EventType nodes (metadata only, no dates/locations)
            # Full event data with dates/stores is in PostgreSQL events table
            query = """g.V().hasLabel('EventType').project('event_name', 'event_type').by('name').by('type').limit(100)"""
            
            results = self._execute_query(query)
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
            # Builder creates: Product with 'id' property (P_1, P_2, etc.)
            query = f"""g.V().has('Product', 'id', '{gremlin_id}').as('p').out('IN_CATEGORY').as('c').out('IN_DEPARTMENT').as('d').project('product_id', 'product_name', 'category', 'department').by(select('p').values('product_id')).by(select('p').values('name')).by(select('c').values('name')).by(select('d').values('name'))"""
            
            results = self._execute_query(query)
            return results[0] if results else {}
            
        except Exception as e:
            logger.error(f"Gremlin get product hierarchy error: {e}")
            return {}

    def get_location_hierarchy(self, store_id: str) -> Dict[str, Any]:
        """Get full hierarchy for a location"""
        if not self.ensure_connected():
            return {}
            
        try:
            # Builder creates: Store with 'id' property (store_id from location.location)
            query = f"""g.V().has('Store', 'id', '{store_id}').as('s').out('IN_MARKET').as('m').out('IN_STATE').as('st').out('IN_REGION').as('r').project('store_id', 'store_name', 'market', 'state', 'region').by(select('s').values('id')).by(select('s').values('name')).by(select('m').values('name')).by(select('st').values('name')).by(select('r').values('name'))"""
            
            results = self._execute_query(query)
            return results[0] if results else {}
            
        except Exception as e:
            logger.error(f"Gremlin get location hierarchy error: {e}")
            return {}

# Global Gremlin instance
gremlin_conn = GremlinConnection()
