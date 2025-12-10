"""
Build Planalytics Knowledge Graph in Azure Cosmos DB (Gremlin API)
Reads data from PostgreSQL planalytics_db and creates knowledge graph

New Schema:
- product_hierarchy (dept -> category -> product)
- perishable (separate perishable product info)
- location, calendar, events (same as before)
- metrics, weather (relationships/metadata only)
"""
import os
import psycopg2
import time
from dotenv import load_dotenv
from gremlin_python.driver import client, serializer
from pathlib import Path

load_dotenv()

# CONFIGURATION
SAMPLE_SIZE = None  # Set to None for all data, or number for testing
BATCH_SIZE = 50  # Process records in batches
MAX_RETRIES = 5  # Retry attempts for rate limits


class PlanalyticsGremlinBuilder:
    def __init__(self):
        # Cosmos DB connection
        self.endpoint = os.getenv("COSMOS_ENDPOINT")
        self.cosmos_key = os.getenv("COSMOS_KEY")
        self.cosmos_database = os.getenv("COSMOS_DATABASE", "planalytics")
        self.cosmos_graph = os.getenv("COSMOS_GRAPH", "planalytics_graph")
        self.cosmos_port = int(os.getenv("COSMOS_PORT", "443"))
        
        # PostgreSQL connection
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': 'planalytics_db',
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        
        # Initialize Gremlin client
        self.gremlin_client = client.Client(
            f'wss://{self.cosmos_endpoint}:{self.cosmos_port}/',
            'g',
            username=f"/dbs/{self.cosmos_database}/colls/{self.cosmos_graph}",
            password=self.cosmos_key,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )
        
        print(f"✅ Connected to Cosmos DB Gremlin at {self.cosmos_endpoint}")
    
    def close(self):
        """Close Gremlin client"""
        if self.gremlin_client:
            self.gremlin_client.close()
    
    def escape_string(self, s):
        """Escape strings for Gremlin queries"""
        if s is None:
            return ""
        return str(s).replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
    
    def safe_string_for_id(self, s):
        """Create safe ID strings"""
        if s is None:
            return "unknown"
        return str(s).replace(" ", "_").replace(",", "").replace("'", "").replace('"', '')
    
    def submit_query(self, query, max_retries=5):
        """Submit Gremlin query with retry logic"""
        for attempt in range(max_retries):
            try:
                callback = self.gremlin_client.submitAsync(query)
                result = callback.result()
                return result.all().result()
            except Exception as e:
                if "429" in str(e) or "TooManyRequests" in str(e):
                    wait_time = (2 ** attempt) * 0.5
                    print(f"   ⏳ Rate limited, waiting {wait_time}s...", end='\r')
                    time.sleep(wait_time)
                else:
                    print(f"\n   ❌ Query error: {e}")
                    print(f"   Query: {query[:200]}...")
                    raise
        raise Exception("Max retries exceeded")
    
    def drop_graph(self):
        """Drop all vertices and edges"""
        print("\n🗑️  Dropping existing graph...")
        self.submit_query("g.V().drop()")
        print("   ✅ Graph cleared")
    
    def load_product_hierarchy(self):
        """Load product hierarchy from PostgreSQL"""
        print("\n📦 Loading product hierarchy...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT dept FROM product_hierarchy ORDER BY dept;")
        depts = [row[0] for row in cursor.fetchall()]
        
        print(f"   📥 Creating {len(depts)} departments...")
        for dept in depts:
            dept_id = self.safe_string_for_id(dept)
            dept_name = self.escape_string(dept)
            query = f"g.addV('Department').property('id', '{dept_id}').property('name', '{dept_name}')"
            self.submit_query(query)
        
        cursor.execute("SELECT DISTINCT category, dept FROM product_hierarchy ORDER BY category;")
        categories = cursor.fetchall()
        
        print(f"   📥 Creating {len(categories)} categories...")
        for category, dept in categories:
            cat_id = self.safe_string_for_id(category)
            cat_name = self.escape_string(category)
            dept_id = self.safe_string_for_id(dept)
            
            query = f"g.addV('Category').property('id', '{cat_id}').property('name', '{cat_name}')"
            self.submit_query(query)
            
            # Link to department
            edge_query = f"g.V().hasLabel('Category').has('id', '{cat_id}').addE('IN_DEPARTMENT').to(g.V().hasLabel('Department').has('id', '{dept_id}'))"
            self.submit_query(edge_query)
        
        cursor.execute("SELECT product_id, product, category FROM product_hierarchy ORDER BY product_id;")
        products = cursor.fetchall()
        
        print(f"   📥 Creating {len(products)} products...")
        for product_id, product, category in products:
            prod_id = f"P_{product_id}"
            prod_name = self.escape_string(product)
            cat_id = self.safe_string_for_id(category)
            
            query = f"g.addV('Product').property('id', '{prod_id}').property('product_id', {product_id}).property('name', '{prod_name}')"
            self.submit_query(query)
            
            # Link to category
            edge_query = f"g.V().hasLabel('Product').has('id', '{prod_id}').addE('IN_CATEGORY').to(g.V().hasLabel('Category').has('id', '{cat_id}'))"
            self.submit_query(edge_query)
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Loaded product hierarchy")
    
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
        
        print(f"   📥 Creating {len(rows)} perishable items...")
        
        for id_val, product, perishable_id, min_period, max_period, period_metric, storage in rows:
            perish_id = f"PERISH_{id_val}"
            prod_name = self.escape_string(product)
            min_p = self.escape_string(str(min_period) if min_period else "")
            max_p = self.escape_string(str(max_period) if max_period else "")
            metric = self.escape_string(period_metric or "")
            stor = self.escape_string(storage or "")
            
            query = f"""g.addV('Perishable').property('id', '{perish_id}')
                .property('product', '{prod_name}')
                .property('perishable_id', {perishable_id or 0})
                .property('min_period', '{min_p}')
                .property('max_period', '{max_p}')
                .property('period_metric', '{metric}')
                .property('storage', '{stor}')"""
            
            self.submit_query(query)
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Loaded {len(rows)} perishable items")
    
    def load_locations(self):
        """Load location hierarchy"""
        print("\n📍 Loading locations...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Create regions
        cursor.execute("SELECT DISTINCT region FROM location ORDER BY region;")
        regions = [row[0] for row in cursor.fetchall()]
        
        print(f"   📥 Creating {len(regions)} regions...")
        for region in regions:
            reg_id = self.safe_string_for_id(region)
            reg_name = self.escape_string(region)
            query = f"g.addV('Region').property('id', '{reg_id}').property('name', '{reg_name}')"
            self.submit_query(query)
        
        # Create states
        cursor.execute("SELECT DISTINCT state, region FROM location ORDER BY state;")
        states = cursor.fetchall()
        
        print(f"   📥 Creating {len(states)} states...")
        for state, region in states:
            state_id = self.safe_string_for_id(state)
            state_name = self.escape_string(state)
            reg_id = self.safe_string_for_id(region)
            
            query = f"g.addV('State').property('id', '{state_id}').property('name', '{state_name}')"
            self.submit_query(query)
            
            # Link to region
            edge_query = f"g.V().hasLabel('State').has('id', '{state_id}').addE('IN_REGION').to(g.V().hasLabel('Region').has('id', '{reg_id}'))"
            self.submit_query(edge_query)
        
        # Create markets
        cursor.execute("SELECT DISTINCT market, state FROM location ORDER BY market;")
        markets = cursor.fetchall()
        
        print(f"   📥 Creating {len(markets)} markets...")
        for market, state in markets:
            mkt_id = self.safe_string_for_id(market)
            mkt_name = self.escape_string(market)
            state_id = self.safe_string_for_id(state)
            
            query = f"g.addV('Market').property('id', '{mkt_id}').property('name', '{mkt_name}')"
            self.submit_query(query)
            
            # Link to state
            edge_query = f"g.V().hasLabel('Market').has('id', '{mkt_id}').addE('IN_STATE').to(g.V().hasLabel('State').has('id', '{state_id}'))"
            self.submit_query(edge_query)
        
        # Create stores
        cursor.execute("""
            SELECT location, market, latitude, longitude 
            FROM location ORDER BY id;
        """)
        stores = cursor.fetchall()
        
        print(f"   📥 Creating {len(stores)} stores...")
        for location, market, latitude, longitude in stores:
            store_id = self.escape_string(location)
            mkt_id = self.safe_string_for_id(market)
            lat = float(latitude) if latitude else 0.0
            lon = float(longitude) if longitude else 0.0
            
            query = f"g.addV('Store').property('id', '{store_id}').property('store_id', '{store_id}').property('latitude', {lat}).property('longitude', {lon})"
            self.submit_query(query)
            
            # Link to market
            edge_query = f"g.V().hasLabel('Store').has('id', '{store_id}').addE('IN_MARKET').to(g.V().hasLabel('Market').has('id', '{mkt_id}'))"
            self.submit_query(edge_query)
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Loaded location hierarchy")
    
    def load_calendar(self):
        """Load calendar data (sample)"""
        print("\n📅 Loading calendar...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Create years
        cursor.execute("SELECT DISTINCT year FROM calendar ORDER BY year;")
        years = [row[0] for row in cursor.fetchall()]
        
        print(f"   📥 Creating {len(years)} years...")
        for year in years:
            query = f"g.addV('Year').property('id', 'Y_{year}').property('year', {year})"
            self.submit_query(query)
        
        # Create seasons
        seasons = ['Spring', 'Summer', 'Fall', 'Winter']
        print(f"   📥 Creating {len(seasons)} seasons...")
        for season in seasons:
            query = f"g.addV('Season').property('id', '{season}').property('name', '{season}')"
            self.submit_query(query)
        
        # Create dates (sample - first 100)
        cursor.execute("""
            SELECT id, end_date, year, quarter, month, week, season 
            FROM calendar ORDER BY end_date LIMIT 100;
        """)
        dates = cursor.fetchall()
        
        print(f"   📥 Creating {len(dates)} dates (sample)...")
        for id_val, end_date, year, quarter, month, week, season in dates:
            date_id = f"D_{id_val}"
            date_str = str(end_date)
            month_esc = self.escape_string(month)
            
            query = f"""g.addV('Date').property('id', '{date_id}')
                .property('date', '{date_str}')
                .property('year', {year})
                .property('quarter', {quarter})
                .property('month', '{month_esc}')
                .property('week', {week})
                .property('season', '{season}')"""
            
            self.submit_query(query)
            
            # Link to year and season
            edge_query1 = f"g.V().hasLabel('Date').has('id', '{date_id}').addE('IN_YEAR').to(g.V().hasLabel('Year').has('id', 'Y_{year}'))"
            self.submit_query(edge_query1)
            
            edge_query2 = f"g.V().hasLabel('Date').has('id', '{date_id}').addE('IN_SEASON').to(g.V().hasLabel('Season').has('id', '{season}'))"
            self.submit_query(edge_query2)
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Loaded calendar data")
    
    def load_events(self):
        """Load events (sample)"""
        print("\n🎉 Loading events...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, event, event_type, event_date, store_id 
            FROM events ORDER BY event_date LIMIT 500;
        """)
        events = cursor.fetchall()
        
        print(f"   📥 Creating {len(events)} events (sample)...")
        
        for id_val, event, event_type, event_date, store_id in events:
            evt_id = f"EVT_{id_val}"
            evt_name = self.escape_string(event)
            evt_type = self.escape_string(event_type)
            date_str = str(event_date)
            store = self.escape_string(store_id)
            
            query = f"""g.addV('Event').property('id', '{evt_id}')
                .property('name', '{evt_name}')
                .property('event_type', '{evt_type}')
                .property('event_date', '{date_str}')"""
            
            self.submit_query(query)
            
            # Link to store
            edge_query = f"g.V().hasLabel('Event').has('id', '{evt_id}').addE('AFFECTED').to(g.V().hasLabel('Store').has('id', '{store}'))"
            try:
                self.submit_query(edge_query)
            except:
                pass  # Store might not exist in sample
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Loaded {len(events)} events")
    
    def load_metrics_relationships(self):
        """Create product-store metric relationships (sample)"""
        print("\n📈 Creating metrics relationships...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT store_id, product_id
            FROM metrics
            WHERE store_id IS NOT NULL AND product_id IS NOT NULL
            LIMIT 500;
        """)
        rows = cursor.fetchall()
        
        print(f"   📥 Creating {len(rows)} metric relationships (sample)...")
        
        for store_id, product_id in rows:
            store = self.escape_string(store_id)
            prod_id = f"P_{product_id}"
            
            edge_query = f"g.V().hasLabel('Store').has('id', '{store}').addE('HAS_METRIC').to(g.V().hasLabel('Product').has('id', '{prod_id}'))"
            try:
                self.submit_query(edge_query)
            except:
                pass  # Might fail if vertex doesn't exist
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Created metric relationships")
    
    def verify_graph(self):
        """Verify the created graph"""
        print("\n✅ Graph verification:")
        
        vertex_labels = ['Department', 'Category', 'Product', 'Perishable', 
                         'Region', 'State', 'Market', 'Store', 
                         'Year', 'Season', 'Date', 'Event']
        
        for label in vertex_labels:
            try:
                result = self.submit_query(f"g.V().hasLabel('{label}').count()")
                count = result[0] if result else 0
                print(f"   {label}: {count:,}")
            except Exception as e:
                print(f"   {label}: Error - {e}")
        
        # Count edges
        try:
            result = self.submit_query("g.E().count()")
            count = result[0] if result else 0
            print(f"   Total Edges: {count:,}")
        except Exception as e:
            print(f"   Total Edges: Error - {e}")


def main():
    print("="*80)
    print("🏗️  PLANALYTICS GREMLIN KNOWLEDGE GRAPH BUILDER")
    print("="*80)
    print("\nReading from PostgreSQL database: planalytics_db")
    print("Creating knowledge graph in Cosmos DB Gremlin\n")
    
    builder = PlanalyticsGremlinBuilder()
    
    try:
        builder.drop_graph()
        
        # Load master data
        builder.load_product_hierarchy()
        builder.load_perishable()
        builder.load_locations()
        builder.load_calendar()
        builder.load_events()
        
        # Load relationship metadata
        builder.load_metrics_relationships()
        
        # Verify
        builder.verify_graph()
        
        print("\n" + "="*80)
        print("✅ GREMLIN KNOWLEDGE GRAPH COMPLETE!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        builder.close()


if __name__ == "__main__":
    main()
