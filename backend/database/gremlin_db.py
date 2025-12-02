from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T, P, Order, Column, Operator
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from core.config import settings
from core.logger import logger
import sys

class GremlinConnection:
    """Cosmos DB Gremlin API connection manager"""
    
    def __init__(self):
        self.g = None
        self.conn = None
        self._connected = False
        
    def _connect(self):
        """Establish connection to Cosmos DB Gremlin API"""
        if self._connected:
            return

        try:
            # Construct the connection URL
            # wss://<endpoint>:<port>/gremlin
            url = f"wss://{settings.COSMOS_ENDPOINT}:{settings.COSMOS_PORT}/gremlin"
            
            # Create the connection
            # Username is usually /dbs/<db>/colls/<coll>
            username = f"/dbs/{settings.COSMOS_DATABASE}/colls/{settings.COSMOS_GRAPH}"
            password = settings.COSMOS_KEY
            
            self.conn = DriverRemoteConnection(url, 'g', username=username, password=password)
            self.g = traversal().withRemote(self.conn)
            self._connected = True
            logger.info("✅ Cosmos DB Gremlin connection established successfully")
        except Exception as e:
            logger.warning(f"⚠️ Gremlin connection failed: {e}")
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
            self.conn.close()
            self._connected = False
            logger.info("Gremlin connection closed")

    def create_supply_chain_graph(self, data: Dict[str, Any]) -> None:
        """Create supply chain relationships"""
        if not self.ensure_connected():
            logger.warning("Skipping graph creation - Gremlin unavailable")
            return
            
        try:
            # Simplified creation - in production use coalesce for upsert
            # Creating vertices
            g = self.g
            
            # Product
            g.V().has('Product', 'id', data['product_id']).fold().coalesce(
                __.unfold(), 
                __.addV('Product').property('id', data['product_id']).property('name', data['product_name'])
            ).next()
            
            # Location
            g.V().has('Location', 'id', data['location_id']).fold().coalesce(
                __.unfold(), 
                __.addV('Location').property('id', data['location_id']).property('name', data['location_name'])
            ).next()
            
            # Weather (simplified, usually time-bound)
            g.addV('Weather').property('conditions', data['weather_conditions']).property('temp', data['temperature']).next()
            
            # Event
            g.V().has('Event', 'name', data['event_name']).fold().coalesce(
                __.unfold(), 
                __.addV('Event').property('name', data['event_name']).property('type', data['event_type'])
            ).next()
            
            # Edges
            # Product -> Location
            g.V().has('Product', 'id', data['product_id']).as_('p').V().has('Location', 'id', data['location_id']).as_('l').coalesce(
                __.outE('STORED_AT').where(__.inV().as_('l')),
                __.addE('STORED_AT').from_('p').to('l')
            ).next()
            
            # Location -> Weather (simplified)
            # Location -> Event
            
            logger.info(f"Created graph nodes for {data['product_id']}")
            
        except Exception as e:
            logger.error(f"Gremlin graph creation error: {e}")

    def query_supply_chain_impact(self, product_id: str, location_id: str) -> List[Dict]:
        """Query supply chain impact factors"""
        if not self.ensure_connected():
            return []
            
        try:
            # Equivalent to:
            # MATCH (p:Product {id: $product_id})-[:STORED_AT]->(l:Location {id: $location_id})
            # ...
            
            result = self.g.V().has('Product', 'id', product_id).out('STORED_AT').has('Location', 'id', location_id).project('product', 'location').by(__.valueMap()).by(__.valueMap()).toList()
            
            # This is a simplified return. In a real app we'd traverse to weather/events
            return result
        except Exception as e:
            logger.error(f"Gremlin query error: {e}")
            return []

    def expand_product_context(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """Expand product context by finding related products in same category"""
        if not self.ensure_connected():
            return []
        
        try:
            # g.V().hasLabel('Product').has('product_id', within(ids)).out('IN_CATEGORY').in('IN_CATEGORY')...
            traversal = self.g.V().hasLabel('Product').has('product_id', P.within(product_ids)).out('IN_CATEGORY').as_('c').in_('IN_CATEGORY').hasLabel('Product').project('product_id', 'product_name', 'category').by('product_id').by('name').by(__.select('c').values('name'))
            
            results = traversal.limit(50).toList()
            return results
        except Exception as e:
            logger.error(f"Gremlin expand product error: {e}")
            return []

    def expand_location_context(self, location_ids: List[str]) -> List[Dict[str, Any]]:
        """Expand location context by finding all stores in same region/market"""
        if not self.ensure_connected():
            return []
        
        try:
            # Similar logic to Neo4j query
            traversal = self.g.V().hasLabel('Store').has('store_id', P.within(location_ids)).out('IN_MARKET').as_('m').in_('IN_MARKET').hasLabel('Store').project('store_id', 'store_name', 'market').by('store_id').by('name').by(__.select('m').values('name'))
            
            results = traversal.limit(200).toList()
            return results
        except Exception as e:
            logger.error(f"Gremlin expand location error: {e}")
            return []

    def find_related_events(self, location_ids: List[str], dates: List[str]) -> List[Dict[str, Any]]:
        """Find events that occurred at specified locations during specified dates"""
        if not self.ensure_connected() or not dates:
            return []
            
        try:
            min_date = min(dates)
            max_date = max(dates)
            
            traversal = self.g.V().hasLabel('Event').has('date', P.gte(min_date)).has('date', P.lte(max_date)).where(__.out('AT_STORE').has('store_id', P.within(location_ids))).project('event_name', 'date', 'event_type').by('event_name').by('date').by('event_type')
            
            results = traversal.limit(100).toList()
            return results
        except Exception as e:
            logger.error(f"Gremlin find events error: {e}")
            return []

    def get_product_hierarchy(self, product_id: str) -> Dict[str, Any]:
        """Get full hierarchy for a product"""
        if not self.ensure_connected():
            return {}
            
        try:
            result = self.g.V().has('Product', 'product_id', product_id).as_('p').out('IN_CATEGORY').as_('c').out('IN_DEPARTMENT').as_('d').project('product_id', 'product_name', 'category', 'department').by(__.select('p').values('product_id')).by(__.select('p').values('name')).by(__.select('c').values('name')).by(__.select('d').values('name')).next()
            
            return result
        except Exception as e:
            # StopIteration if next() fails
            return {}

    def get_location_hierarchy(self, store_id: str) -> Dict[str, Any]:
        """Get full hierarchy for a location"""
        if not self.ensure_connected():
            return {}
            
        try:
            result = self.g.V().has('Store', 'store_id', store_id).as_('s').out('IN_MARKET').as_('m').out('IN_STATE').as_('st').out('IN_REGION').as_('r').project('store_id', 'store_name', 'market', 'state', 'region').by(__.select('s').values('store_id')).by(__.select('s').values('name')).by(__.select('m').values('name')).by(__.select('st').values('name')).by(__.select('r').values('name')).next()
            
            return result
        except Exception as e:
            return {}

# Global Gremlin instance
gremlin_conn = GremlinConnection()
