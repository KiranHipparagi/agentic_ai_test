"""
Build Planalytics Knowledge Graph in Neo4j
Reads data from PostgreSQL planalytics_db and creates knowledge graph

New Schema:
- product_hierarchy (dept -> category -> product)
- perishable (separate perishable product info)
- location, calendar, events (same as before)
- metrics, weather (relationships/metadata only)
"""
import os
import psycopg2
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pathlib import Path

load_dotenv()


class PlanalyticsNeo4jBuilder:
    def __init__(self):
        # Neo4j connection
        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "planalytics")
        
        # PostgreSQL connection
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': 'planalytics_db',
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            print(f"✅ Connected to Neo4j at {self.neo4j_uri}")
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            raise
    
    def close(self):
        """Close Neo4j driver"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
    
    def run_query(self, query, parameters=None):
        """Execute Cypher query"""
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            return session.run(query, parameters or {})
    
    def clear_database(self):
        """Clear all nodes and relationships"""
        print("\n🗑️  Clearing existing Neo4j database...")
        self.run_query("MATCH (n) DETACH DELETE n;")
        print("   ✅ Database cleared")
    
    def create_constraints(self):
        """Create uniqueness constraints"""
        print("\n🔒 Creating constraints...")
        
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Department) REQUIRE d.name IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Store) REQUIRE s.store_id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Region) REQUIRE r.name IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Market) REQUIRE m.name IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (st:State) REQUIRE st.name IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Date) REQUIRE d.date IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (y:Year) REQUIRE y.year IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Season) REQUIRE s.name IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Perishable) REQUIRE p.id IS UNIQUE;",
        ]
        
        for constraint in constraints:
            try:
                self.run_query(constraint)
            except Exception as e:
                print(f"   ⚠️  {e}")
        
        print("   ✅ Constraints created")
    
    def load_product_hierarchy(self):
        """Load product hierarchy from PostgreSQL"""
        print("\n📦 Loading product hierarchy...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT product_id, dept, category, product FROM product_hierarchy ORDER BY product_id;")
        rows = cursor.fetchall()
        
        print(f"   📥 Fetched {len(rows)} products")
        
        # Create product hierarchy
        for product_id, dept, category, product in rows:
            self.run_query("""
                MERGE (d:Department {name: $dept})
                MERGE (c:Category {name: $category})
                MERGE (p:Product {product_id: $product_id, name: $product})
                MERGE (p)-[:IN_CATEGORY]->(c)
                MERGE (c)-[:IN_DEPARTMENT]->(d)
            """, {
                'product_id': product_id,
                'dept': dept,
                'category': category,
                'product': product
            })
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Loaded {len(rows)} products")
    
    def load_perishable(self):
        """Load perishable product information"""
        print("\n🥬 Loading perishable products...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, product, perishable_id, min_period, max_period, period_metric, storage 
            FROM perishable ORDER BY id;
        """)
        rows = cursor.fetchall()
        
        print(f"   📥 Fetched {len(rows)} perishable items")
        
        for id_val, product, perishable_id, min_period, max_period, period_metric, storage in rows:
            self.run_query("""
                MERGE (p:Perishable {id: $id, product: $product, perishable_id: $perishable_id})
                SET p.min_period = $min_period,
                    p.max_period = $max_period,
                    p.period_metric = $period_metric,
                    p.storage = $storage
            """, {
                'id': id_val,
                'product': product,
                'perishable_id': perishable_id or 0,
                'min_period': str(min_period) if min_period else "",
                'max_period': str(max_period) if max_period else "",
                'period_metric': period_metric or "",
                'storage': storage or ""
            })
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Loaded {len(rows)} perishable items")
    
    def load_locations(self):
        """Load location hierarchy"""
        print("\n📍 Loading locations...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, location, region, market, state, latitude, longitude 
            FROM location ORDER BY id;
        """)
        rows = cursor.fetchall()
        
        print(f"   📥 Fetched {len(rows)} locations")
        
        for id_val, location, region, market, state, latitude, longitude in rows:
            self.run_query("""
                MERGE (r:Region {name: $region})
                MERGE (st:State {name: $state})
                MERGE (m:Market {name: $market})
                MERGE (s:Store {store_id: $location})
                SET s.latitude = $latitude,
                    s.longitude = $longitude
                MERGE (s)-[:IN_MARKET]->(m)
                MERGE (m)-[:IN_STATE]->(st)
                MERGE (st)-[:IN_REGION]->(r)
            """, {
                'location': location,
                'region': region,
                'market': market,
                'state': state,
                'latitude': float(latitude) if latitude else 0.0,
                'longitude': float(longitude) if longitude else 0.0
            })
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Loaded {len(rows)} locations")
    
    def get_season(self, month: str) -> str:
        """Get season from month name"""
        season_map = {
            'February': 'Spring', 'March': 'Spring', 'April': 'Spring',
            'May': 'Summer', 'June': 'Summer', 'July': 'Summer',
            'August': 'Fall', 'September': 'Fall', 'October': 'Fall',
            'November': 'Winter', 'December': 'Winter', 'January': 'Winter'
        }
        return season_map.get(month, 'Unknown')
    
    def load_calendar(self):
        """Load calendar data"""
        print("\n📅 Loading calendar...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, end_date, year, quarter, month, week, season 
            FROM calendar ORDER BY end_date;
        """)
        rows = cursor.fetchall()
        
        print(f"   📥 Fetched {len(rows)} calendar entries")
        
        for id_val, end_date, year, quarter, month, week, season in rows:
            self.run_query("""
                MERGE (y:Year {year: $year})
                MERGE (s:Season {name: $season})
                MERGE (d:Date {date: date($end_date)})
                SET d.year = $year,
                    d.quarter = $quarter,
                    d.month = $month,
                    d.week = $week,
                    d.season = $season
                MERGE (d)-[:IN_YEAR]->(y)
                MERGE (d)-[:IN_SEASON]->(s)
            """, {
                'end_date': str(end_date),
                'year': year,
                'quarter': quarter,
                'month': month,
                'week': week,
                'season': season
            })
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Loaded {len(rows)} calendar entries")
    
    def load_events(self):
        """Load events"""
        print("\n🎉 Loading events...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, event, event_type, event_date, store_id, region, market, state 
            FROM events ORDER BY event_date
            LIMIT 1000;
        """)
        rows = cursor.fetchall()
        
        print(f"   📥 Fetched {len(rows)} events (sample)")
        
        for id_val, event, event_type, event_date, store_id, region, market, state in rows:
            self.run_query("""
                MERGE (e:Event {id: $id})
                SET e.name = $event,
                    e.event_type = $event_type,
                    e.event_date = date($event_date)
                WITH e
                MATCH (d:Date {date: date($event_date)})
                MERGE (e)-[:HAPPENED_ON]->(d)
                WITH e
                MATCH (s:Store {store_id: $store_id})
                MERGE (e)-[:AFFECTED]->(s)
            """, {
                'id': id_val,
                'event': event,
                'event_type': event_type,
                'event_date': str(event_date),
                'store_id': store_id
            })
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Loaded {len(rows)} events")
    
    def load_metrics_relationships(self):
        """Create product-store relationships based on metrics (sample)"""
        print("\n📈 Creating metrics relationships...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Get distinct product-store combinations (sample)
        cursor.execute("""
            SELECT DISTINCT store_id, product_id
            FROM metrics
            WHERE store_id IS NOT NULL AND product_id IS NOT NULL
            LIMIT 1000;
        """)
        rows = cursor.fetchall()
        
        print(f"   📥 Fetched {len(rows)} product-store combinations (sample)")
        
        for store_id, product_id in rows:
            self.run_query("""
                MATCH (s:Store {store_id: $store_id})
                MATCH (p:Product {product_id: $product_id})
                MERGE (s)-[:HAS_METRIC]->(p)
            """, {
                'store_id': str(store_id),
                'product_id': product_id
            })
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Created {len(rows)} metric relationships")
    
    def load_weather_relationships(self):
        """Create store-date relationships for weather (sample)"""
        print("\n🌤️  Creating weather relationships...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Get sample weather records with extreme conditions
        cursor.execute("""
            SELECT DISTINCT store_id, week_end_date
            FROM weekly_weather
            WHERE (heatwave_flag = true OR cold_spell_flag = true 
                   OR heavy_rain_flag = true OR snow_flag = true)
            AND store_id IS NOT NULL
            LIMIT 500;
        """)
        rows = cursor.fetchall()
        
        print(f"   📥 Fetched {len(rows)} extreme weather events (sample)")
        
        for store_id, week_end_date in rows:
            self.run_query("""
                MATCH (s:Store {store_id: $store_id})
                MATCH (d:Date {date: date($week_end_date)})
                MERGE (s)-[:HAD_WEATHER]->(d)
            """, {
                'store_id': str(store_id),
                'week_end_date': str(week_end_date)
            })
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Created {len(rows)} weather relationships")
    
    def verify_graph(self):
        """Verify the created graph"""
        print("\n✅ Graph verification:")
        
        queries = [
            ("Departments", "MATCH (d:Department) RETURN count(d) as count"),
            ("Categories", "MATCH (c:Category) RETURN count(c) as count"),
            ("Products", "MATCH (p:Product) RETURN count(p) as count"),
            ("Perishable Items", "MATCH (p:Perishable) RETURN count(p) as count"),
            ("Regions", "MATCH (r:Region) RETURN count(r) as count"),
            ("States", "MATCH (s:State) RETURN count(s) as count"),
            ("Markets", "MATCH (m:Market) RETURN count(m) as count"),
            ("Stores", "MATCH (s:Store) RETURN count(s) as count"),
            ("Years", "MATCH (y:Year) RETURN count(y) as count"),
            ("Seasons", "MATCH (s:Season) RETURN count(s) as count"),
            ("Dates", "MATCH (d:Date) RETURN count(d) as count"),
            ("Events", "MATCH (e:Event) RETURN count(e) as count"),
            ("Total Relationships", "MATCH ()-[r]->() RETURN count(r) as count"),
        ]
        
        for label, query in queries:
            result = list(self.run_query(query))
            count = result[0]['count'] if result else 0
            print(f"   {label}: {count:,}")


def main():
    print("="*80)
    print("🏗️  PLANALYTICS NEO4J KNOWLEDGE GRAPH BUILDER")
    print("="*80)
    print("\nReading from PostgreSQL database: planalytics_db")
    print("Creating knowledge graph in Neo4j database: planalytics\n")
    
    builder = PlanalyticsNeo4jBuilder()
    
    try:
        builder.clear_database()
        builder.create_constraints()
        
        # Load master data
        builder.load_product_hierarchy()
        builder.load_perishable()
        builder.load_locations()
        builder.load_calendar()
        builder.load_events()
        
        # Load relationship metadata
        builder.load_metrics_relationships()
        builder.load_weather_relationships()
        
        # Verify
        builder.verify_graph()
        
        print("\n" + "="*80)
        print("✅ NEO4J KNOWLEDGE GRAPH COMPLETE!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        builder.close()


if __name__ == "__main__":
    main()
