from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from core.config import settings
from core.logger import logger


class Neo4jConnection:
    """Neo4j knowledge graph connection manager with lazy initialization"""
    
    def __init__(self):
        self.driver: Optional[GraphDatabase.driver] = None
        self._connected = False
    
    def _connect(self):
        """Establish connection to Neo4j"""
        if self._connected:
            return
            
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=120
            )
            self.driver.verify_connectivity()
            self._connected = True
            logger.info("✅ Neo4j connection established successfully")
        except Exception as e:
            logger.warning(f"⚠️ Neo4j connection failed (will operate without graph features): {e}")
            self.driver = None
            self._connected = False
    
    def ensure_connected(self) -> bool:
        """Ensure connection is established, return success status"""
        if not self._connected:
            self._connect()
        return self._connected
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self._connected = False
            logger.info("Neo4j connection closed")
    
    @contextmanager
    def session(self):
        """Neo4j session context manager"""
        if not self.ensure_connected():
            raise RuntimeError("Neo4j is not available")
            
        session = self.driver.session()
        try:
            yield session
        except Exception as e:
            logger.error(f"Neo4j session error: {e}")
            raise
        finally:
            session.close()
    
    def create_supply_chain_graph(self, data: Dict[str, Any]) -> None:
        """Create supply chain relationships"""
        if not self.ensure_connected():
            logger.warning("Skipping graph creation - Neo4j unavailable")
            return
            
        with self.session() as session:
            query = """
            MERGE (p:Product {id: $product_id, name: $product_name})
            MERGE (l:Location {id: $location_id, name: $location_name})
            MERGE (w:Weather {conditions: $weather_conditions, temp: $temperature})
            MERGE (e:Event {name: $event_name, type: $event_type})
            
            MERGE (p)-[:STORED_AT]->(l)
            MERGE (l)-[:HAS_WEATHER]->(w)
            MERGE (l)-[:HOSTS_EVENT]->(e)
            MERGE (w)-[:IMPACTS {coefficient: $weather_impact}]->(p)
            MERGE (e)-[:AFFECTS {impact_score: $event_impact}]->(p)
            """
            session.run(query, **data)
    
    def query_supply_chain_impact(self, product_id: str, location_id: str) -> List[Dict]:
        """Query supply chain impact factors"""
        if not self.ensure_connected():
            logger.warning("Returning empty results - Neo4j unavailable")
            return []
            
        with self.session() as session:
            query = """
            MATCH (p:Product {id: $product_id})-[:STORED_AT]->(l:Location {id: $location_id})
            OPTIONAL MATCH (l)-[:HAS_WEATHER]->(w:Weather)
            OPTIONAL MATCH (l)-[:HOSTS_EVENT]->(e:Event)
            OPTIONAL MATCH (w)-[wi:IMPACTS]->(p)
            OPTIONAL MATCH (e)-[ei:AFFECTS]->(p)
            
            RETURN p, l, w, e, wi.coefficient as weather_impact, ei.impact_score as event_impact
            """
            result = session.run(query, product_id=product_id, location_id=location_id)
            return [dict(record) for record in result]
    
    def expand_product_context(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Expand product context by finding related products in same category
        
        Args:
            product_ids: List of product IDs from Azure Search
            
        Returns:
            List of related product dictionaries with product_id, name, category
        """
        if not self.ensure_connected():
            logger.warning("Neo4j unavailable - returning original product list")
            return []
        
        with self.session() as session:
            query = """
            MATCH (p:Product)-[:IN_CATEGORY]->(c:Category)
            WHERE p.product_id IN $product_ids
            MATCH (c)<-[:IN_CATEGORY]-(related:Product)
            RETURN DISTINCT related.product_id AS product_id, 
                   related.name AS product_name,
                   c.name AS category
            LIMIT 50
            """
            result = session.run(query, product_ids=product_ids)
            return [dict(record) for record in result]
    
    def expand_location_context(self, location_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Expand location context by finding all stores in same region/market/state
        
        Args:
            location_ids: List of store IDs from Azure Search
            
        Returns:
            List of store dictionaries with store_id, name, market, state, region
        """
        if not self.ensure_connected():
            logger.warning("Neo4j unavailable - returning original location list")
            return []
        
        with self.session() as session:
            # Find all stores in the same markets as the initial stores
            query = """
            MATCH (s:Store)-[:IN_MARKET]->(m:Market)
            WHERE s.store_id IN $location_ids
            WITH COLLECT(DISTINCT m) AS markets
            UNWIND markets AS market
            MATCH (market)<-[:IN_MARKET]-(all_stores:Store)
            MATCH (all_stores)-[:IN_MARKET]->(m:Market)
            MATCH (m)-[:IN_STATE]->(st:State)
            MATCH (st)-[:IN_REGION]->(r:Region)
            RETURN DISTINCT all_stores.store_id AS store_id,
                   all_stores.name AS store_name,
                   m.name AS market,
                   st.name AS state,
                   r.name AS region
            LIMIT 200
            """
            result = session.run(query, location_ids=location_ids)
            return [dict(record) for record in result]
    
    def find_related_events(self, location_ids: List[str], dates: List[str]) -> List[Dict[str, Any]]:
        """
        Find events that occurred at specified locations during specified dates
        
        Args:
            location_ids: List of store IDs
            dates: List of date strings
            
        Returns:
            List of event dictionaries with event_name, date, store_id
        """
        if not self.ensure_connected():
            logger.warning("Neo4j unavailable - no event context available")
            return []
        
        with self.session() as session:
            # Extract min/max dates for range query
            if not dates:
                return []
            
            min_date = min(dates)
            max_date = max(dates)
            
            query = """
            MATCH (e:Event)-[:AT_STORE]->(s:Store)
            WHERE s.store_id IN $location_ids
              AND e.date >= $min_date
              AND e.date <= $max_date
            RETURN e.event_name AS event_name,
                   e.date AS date,
                   s.store_id AS store_id,
                   e.event_type AS event_type
            ORDER BY e.date
            LIMIT 100
            """
            result = session.run(query, 
                               location_ids=location_ids, 
                               min_date=min_date, 
                               max_date=max_date)
            return [dict(record) for record in result]
    
    def get_product_hierarchy(self, product_id: str) -> Dict[str, Any]:
        """
        Get full hierarchy for a product (Department -> Category -> Product)
        
        Args:
            product_id: Single product ID
            
        Returns:
            Dictionary with department, category, product information
        """
        if not self.ensure_connected():
            return {}
        
        with self.session() as session:
            query = """
            MATCH (p:Product {product_id: $product_id})-[:IN_CATEGORY]->(c:Category)
            MATCH (c)-[:IN_DEPARTMENT]->(d:Department)
            RETURN p.product_id AS product_id,
                   p.name AS product_name,
                   c.name AS category,
                   d.name AS department
            """
            result = session.run(query, product_id=product_id)
            record = result.single()
            return dict(record) if record else {}
    
    def get_location_hierarchy(self, store_id: str) -> Dict[str, Any]:
        """
        Get full hierarchy for a location (Region -> State -> Market -> Store)
        
        Args:
            store_id: Single store ID
            
        Returns:
            Dictionary with region, state, market, store information
        """
        if not self.ensure_connected():
            return {}
        
        with self.session() as session:
            query = """
            MATCH (s:Store {store_id: $store_id})-[:IN_MARKET]->(m:Market)
            MATCH (m)-[:IN_STATE]->(st:State)
            MATCH (st)-[:IN_REGION]->(r:Region)
            RETURN s.store_id AS store_id,
                   s.name AS store_name,
                   m.name AS market,
                   st.name AS state,
                   r.name AS region
            """
            result = session.run(query, store_id=store_id)
            record = result.single()
            return dict(record) if record else {}


# Global Neo4j instance (lazy initialization - won't connect until first use)
neo4j_conn = Neo4jConnection()

