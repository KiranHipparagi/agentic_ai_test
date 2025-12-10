"""
Setup Planalytics Database Tables and Load Data from CSV
This script:
1. Creates tables for all 7 CSV files (excluding insert_at, updated_at columns)
2. Loads data from CSV files into PostgreSQL
3. Creates proper indexes for query performance
"""
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': 'planalytics_database',
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

# Path to data folder
DATA_DIR = Path(__file__).parent.parent / 'data'

# Table schemas (excluding insert_at, updated_at)
TABLE_SCHEMAS = {
    'calendar': """
        CREATE TABLE calendar (
            id INTEGER PRIMARY KEY,
            end_date DATE NOT NULL,
            year INTEGER,
            quarter INTEGER,
            month VARCHAR(50),
            week INTEGER,
            season VARCHAR(20)
        );
    """,
    
    'events': """
        CREATE TABLE events (
            id INTEGER PRIMARY KEY,
            event VARCHAR(255),
            event_type VARCHAR(100),
            event_date DATE,
            store_id VARCHAR(50),
            region VARCHAR(100),
            market VARCHAR(100),
            state VARCHAR(100)
        );
    """,
    
    'location': """
        CREATE TABLE location (
            id INTEGER PRIMARY KEY,
            location VARCHAR(50) UNIQUE NOT NULL,
            region VARCHAR(100),
            market VARCHAR(100),
            state VARCHAR(100),
            latitude DECIMAL(10, 6),
            longitude DECIMAL(10, 6)
        );
    """,
    
    'metrics': """
        CREATE TABLE metrics (
            id SERIAL PRIMARY KEY,
            product VARCHAR(255),
            location VARCHAR(50),
            end_date DATE,
            metric DECIMAL(15, 4),
            metric_nrm DECIMAL(15, 4),
            metric_ly DECIMAL(15, 4)
        );
    """,
    
    'perishable': """
        CREATE TABLE perishable (
            id INTEGER PRIMARY KEY,
            product VARCHAR(255),
            perishable_id INTEGER,
            min_period VARCHAR(50),
            max_period VARCHAR(50),
            period_metric VARCHAR(50),
            storage VARCHAR(100)
        );
    """,
    
    'product_hierarchy': """
        CREATE TABLE product_hierarchy (
            product_id INTEGER PRIMARY KEY,
            dept VARCHAR(100),
            category VARCHAR(100),
            product VARCHAR(255)
        );
    """,
    
    'weekly_weather': """
        CREATE TABLE weekly_weather (
            id INTEGER PRIMARY KEY,
            week_end_date DATE,
            avg_temp_f DECIMAL(6, 2),
            temp_anom_f DECIMAL(6, 2),
            tmax_f DECIMAL(6, 2),
            tmin_f DECIMAL(6, 2),
            precip_in DECIMAL(6, 2),
            precip_anom_in DECIMAL(6, 2),
            heatwave_flag BOOLEAN,
            cold_spell_flag BOOLEAN,
            heavy_rain_flag BOOLEAN,
            snow_flag BOOLEAN,
            store_id VARCHAR(50)
        );
    """
}

# Columns to exclude from CSV import
EXCLUDE_COLUMNS = ['insert_at', 'updated_at']


def get_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(**DB_CONFIG)


def drop_all_tables(cursor, conn):
    """Drop all existing tables"""
    print("\n🗑️  Dropping existing tables...")
    for table_name in TABLE_SCHEMAS.keys():
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
            print(f"   ✅ Dropped {table_name}")
        except Exception as e:
            print(f"   ⚠️  Could not drop {table_name}: {e}")
    conn.commit()


def create_tables(cursor, conn):
    """Create all tables"""
    print("\n📊 Creating tables...")
    for table_name, schema in TABLE_SCHEMAS.items():
        try:
            cursor.execute(schema)
            print(f"   ✅ Created {table_name}")
        except Exception as e:
            print(f"   ❌ Error creating {table_name}: {e}")
            raise
    conn.commit()


def convert_boolean_flags(value):
    """Convert 't'/'f' strings to boolean"""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        return value.lower() == 't'
    return bool(value)


def load_csv_to_table(table_name, csv_file, cursor, conn):
    """Load data from CSV file to PostgreSQL table"""
    print(f"\n📥 Loading {table_name} from {csv_file.name}...")
    
    # Read CSV
    df = pd.read_csv(csv_file)
    original_count = len(df)
    print(f"   📄 Read {original_count:,} rows")
    
    # Remove excluded columns
    df = df.drop(columns=[col for col in EXCLUDE_COLUMNS if col in df.columns], errors='ignore')
    
    # Get column names
    columns = list(df.columns)
    print(f"   📋 Columns: {', '.join(columns)}")
    
    # Convert boolean flags for weekly_weather
    if table_name == 'weekly_weather':
        bool_cols = ['heatwave_flag', 'cold_spell_flag', 'heavy_rain_flag', 'snow_flag']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].apply(convert_boolean_flags)
    
    # Prepare insert statement
    placeholders = ', '.join(['%s'] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    # Insert data in batches
    batch_size = 5000
    total_inserted = 0
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        # Replace NaN with None for SQL NULL
        batch = batch.where(pd.notna(batch), None)
        values = [tuple(row) for row in batch.values]
        
        try:
            cursor.executemany(insert_sql, values)
            conn.commit()
            total_inserted += len(values)
            print(f"   ⏳ Inserted {total_inserted:,}/{original_count:,} rows...", end='\r')
        except Exception as e:
            print(f"\n   ❌ Error inserting batch: {e}")
            conn.rollback()
            raise
    
    print(f"\n   ✅ Loaded {total_inserted:,} rows into {table_name}")


def create_indexes(cursor, conn):
    """Create indexes for better query performance"""
    print("\n🔍 Creating indexes...")
    
    indexes = [
        # Calendar indexes
        "CREATE INDEX idx_calendar_date ON calendar(end_date);",
        "CREATE INDEX idx_calendar_year ON calendar(year);",
        "CREATE INDEX idx_calendar_season ON calendar(season);",
        
        # Events indexes
        "CREATE INDEX idx_events_date ON events(event_date);",
        "CREATE INDEX idx_events_store ON events(store_id);",
        "CREATE INDEX idx_events_type ON events(event_type);",
        
        # Location indexes
        "CREATE INDEX idx_location_store ON location(location);",
        "CREATE INDEX idx_location_region ON location(region);",
        "CREATE INDEX idx_location_market ON location(market);",
        "CREATE INDEX idx_location_state ON location(state);",
        
        # Metrics indexes
        "CREATE INDEX idx_metrics_date ON metrics(end_date);",
        "CREATE INDEX idx_metrics_location ON metrics(location);",
        "CREATE INDEX idx_metrics_product ON metrics(product);",
        "CREATE INDEX idx_metrics_location_product ON metrics(location, product);",
        
        # Product hierarchy indexes
        "CREATE INDEX idx_product_dept ON product_hierarchy(dept);",
        "CREATE INDEX idx_product_category ON product_hierarchy(category);",
        
        # Weather indexes
        "CREATE INDEX idx_weather_date ON weekly_weather(week_end_date);",
        "CREATE INDEX idx_weather_store ON weekly_weather(store_id);",
        "CREATE INDEX idx_weather_store_date ON weekly_weather(store_id, week_end_date);",
    ]
    
    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
            print(f"   ✅ {idx_sql.split('CREATE INDEX ')[1].split(' ON')[0]}")
        except Exception as e:
            print(f"   ⚠️  {e}")
    
    conn.commit()


def verify_data(cursor):
    """Verify loaded data"""
    print("\n✅ Data verification:")
    for table_name in TABLE_SCHEMAS.keys():
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"   {table_name}: {count:,} rows")


def main():
    print("="*80)
    print("🏗️  PLANALYTICS DATABASE SETUP AND DATA LOADING")
    print("="*80)
    
    try:
        # Connect to database
        print(f"\n📊 Connecting to database '{DB_CONFIG['database']}'...")
        conn = get_connection()
        cursor = conn.cursor()
        print("   ✅ Connected!")
        
        # Drop existing tables
        drop_all_tables(cursor, conn)
        
        # Create tables
        create_tables(cursor, conn)
        
        # Load data from CSV files
        csv_files = {
            'calendar': DATA_DIR / 'calendar.csv',
            'events': DATA_DIR / 'events.csv',
            'location': DATA_DIR / 'location.csv',
            'metrics': DATA_DIR / 'metrics.csv',
            'perishable': DATA_DIR / 'perishable.csv',
            'product_hierarchy': DATA_DIR / 'product_hierarchy.csv',
            'weekly_weather': DATA_DIR / 'weekly_weather.csv',
        }
        
        for table_name, csv_file in csv_files.items():
            if csv_file.exists():
                load_csv_to_table(table_name, csv_file, cursor, conn)
            else:
                print(f"\n⚠️  CSV file not found: {csv_file}")
        
        # Create indexes
        create_indexes(cursor, conn)
        
        # Verify data
        verify_data(cursor)
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✅ PLANALYTICS DATABASE SETUP COMPLETE!")
        print("="*80)
        print("\n📝 Next steps:")
        print("   1. Run Azure AI Search indexing scripts")
        print("   2. Run Neo4j knowledge graph builder")
        print("   3. Run Gremlin knowledge graph builder")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
