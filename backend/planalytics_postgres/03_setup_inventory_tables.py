"""
Setup Inventory Tables and Load Data from CSV
This script:
1. Creates tables for 4 inventory CSV files (sales, batches, batch_stock_tracking, spoilage_report)
2. Loads data from CSV files into PostgreSQL
3. Creates proper indexes for query performance

These are FACT tables (high volume, transactional data)
"""
import psycopg2
from psycopg2 import sql
import csv
import os
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
    'sales': """
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            batch_id VARCHAR(50) NOT NULL,
            store_code VARCHAR(20) NOT NULL,
            product_code INTEGER NOT NULL,
            transaction_date DATE NOT NULL,
            sales_units INTEGER NOT NULL,
            sales_amount NUMERIC(10,2),
            discount_amount NUMERIC(10,2),
            total_amount NUMERIC(10,2)
        )
    """,
    
    'batches': """
        CREATE TABLE IF NOT EXISTS batches (
            id SERIAL PRIMARY KEY,
            batch_id VARCHAR(50) NOT NULL,
            store_code VARCHAR(20) NOT NULL,
            product_code INTEGER NOT NULL,
            transaction_date DATE NOT NULL,
            expiry_date DATE,
            unit_price NUMERIC(10,2),
            total_value NUMERIC(10,2),
            received_qty INTEGER,
            mfg_date DATE,
            week_end_date DATE,
            stock_received INTEGER,
            stock_at_week_start INTEGER,
            stock_at_week_end INTEGER
        )
    """,
    
    'batch_stock_tracking': """
        CREATE TABLE IF NOT EXISTS batch_stock_tracking (
            record_id SERIAL PRIMARY KEY,
            batch_id VARCHAR(50) NOT NULL,
            store_code VARCHAR(20) NOT NULL,
            product_code INTEGER NOT NULL,
            transaction_type VARCHAR(50) NOT NULL,
            transaction_date DATE NOT NULL,
            qty_change INTEGER NOT NULL,
            stock_after_transaction INTEGER,
            unit_price NUMERIC(10,2)
        )
    """,
    
    'spoilage_report': """
        CREATE TABLE IF NOT EXISTS spoilage_report (
            id SERIAL PRIMARY KEY,
            batch_id VARCHAR(50) NOT NULL,
            store_code VARCHAR(20) NOT NULL,
            product_code INTEGER NOT NULL,
            qty INTEGER NOT NULL,
            spoilage_qty INTEGER,
            spoilage_pct NUMERIC(5,2),
            spoilage_case INTEGER
        )
    """
}

# Index definitions
TABLE_INDEXES = {
    'sales': [
        'CREATE INDEX IF NOT EXISTS idx_sales_batch ON sales(batch_id)',
        'CREATE INDEX IF NOT EXISTS idx_sales_store ON sales(store_code)',
        'CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_code)',
        'CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(transaction_date)',
        'CREATE INDEX IF NOT EXISTS idx_sales_store_product_date ON sales(store_code, product_code, transaction_date)'
    ],
    'batches': [
        'CREATE INDEX IF NOT EXISTS idx_batches_batch ON batches(batch_id)',
        'CREATE INDEX IF NOT EXISTS idx_batches_store ON batches(store_code)',
        'CREATE INDEX IF NOT EXISTS idx_batches_product ON batches(product_code)',
        'CREATE INDEX IF NOT EXISTS idx_batches_expiry ON batches(expiry_date)',
        'CREATE INDEX IF NOT EXISTS idx_batches_week_end ON batches(week_end_date)',
        'CREATE INDEX IF NOT EXISTS idx_batches_store_product ON batches(store_code, product_code)'
    ],
    'batch_stock_tracking': [
        'CREATE INDEX IF NOT EXISTS idx_tracking_batch ON batch_stock_tracking(batch_id)',
        'CREATE INDEX IF NOT EXISTS idx_tracking_store ON batch_stock_tracking(store_code)',
        'CREATE INDEX IF NOT EXISTS idx_tracking_product ON batch_stock_tracking(product_code)',
        'CREATE INDEX IF NOT EXISTS idx_tracking_type ON batch_stock_tracking(transaction_type)',
        'CREATE INDEX IF NOT EXISTS idx_tracking_date ON batch_stock_tracking(transaction_date)',
        'CREATE INDEX IF NOT EXISTS idx_tracking_batch_date ON batch_stock_tracking(batch_id, transaction_date)'
    ],
    'spoilage_report': [
        'CREATE INDEX IF NOT EXISTS idx_spoilage_batch ON spoilage_report(batch_id)',
        'CREATE INDEX IF NOT EXISTS idx_spoilage_store ON spoilage_report(store_code)',
        'CREATE INDEX IF NOT EXISTS idx_spoilage_product ON spoilage_report(product_code)',
        'CREATE INDEX IF NOT EXISTS idx_spoilage_store_product ON spoilage_report(store_code, product_code)'
    ]
}

# CSV column mappings (excluding insert_at, updated_at)
CSV_COLUMNS = {
    'sales': ['id', 'batch_id', 'store_code', 'product_code', 'transaction_date', 
              'sales_units', 'sales_amount', 'discount_amount', 'total_amount'],
    'batches': ['id', 'batch_id', 'store_code', 'product_code', 'transaction_date', 
                'expiry_date', 'unit_price', 'total_value', 'received_qty', 'mfg_date',
                'week_end_date', 'stock_received', 'stock_at_week_start', 'stock_at_week_end'],
    'batch_stock_tracking': ['record_id', 'batch_id', 'store_code', 'product_code', 
                             'transaction_type', 'transaction_date', 'qty_change', 
                             'stock_after_transaction', 'unit_price'],
    'spoilage_report': ['id', 'batch_id', 'store_code', 'product_code', 'qty', 
                        'spoilage_qty', 'spoilage_pct', 'spoilage_case']
}


def create_tables(conn):
    """Create all inventory tables"""
    cur = conn.cursor()
    
    print("\n" + "="*80)
    print("📦 CREATING INVENTORY TABLES")
    print("="*80 + "\n")
    
    for table_name, schema in TABLE_SCHEMAS.items():
        print(f"Creating table: {table_name}")
        cur.execute(schema)
        conn.commit()
        print(f"  ✓ {table_name} created successfully")
    
    cur.close()


def load_csv_data(conn, table_name, csv_file):
    """Load CSV data into PostgreSQL table"""
    cur = conn.cursor()
    
    csv_path = DATA_DIR / csv_file
    
    if not csv_path.exists():
        print(f"  ⚠️  CSV file not found: {csv_path}")
        return 0
    
    # Get CSV columns for this table
    columns = CSV_COLUMNS[table_name]
    
    # Read and load CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Filter out insert_at and updated_at columns
        rows_loaded = 0
        batch_size = 10000
        batch_data = []
        
        for row in reader:
            # Extract only the columns we need
            values = []
            for col in columns:
                val = row.get(col, '')
                
                # Handle empty values
                if val == '' or val == 'NULL':
                    values.append(None)
                else:
                    values.append(val)
            
            batch_data.append(values)
            
            # Insert in batches
            if len(batch_data) >= batch_size:
                insert_batch(cur, table_name, columns, batch_data)
                rows_loaded += len(batch_data)
                print(f"  → Loaded {rows_loaded:,} rows...", end='\r')
                batch_data = []
        
        # Insert remaining rows
        if batch_data:
            insert_batch(cur, table_name, columns, batch_data)
            rows_loaded += len(batch_data)
        
        conn.commit()
    
    cur.close()
    return rows_loaded


def insert_batch(cur, table_name, columns, batch_data):
    """Insert batch of data using COPY command for speed"""
    # Use parameterized INSERT for safety
    placeholders = ','.join(['%s'] * len(columns))
    insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
    
    cur.executemany(insert_query, batch_data)


def create_indexes(conn):
    """Create indexes for all tables"""
    cur = conn.cursor()
    
    print("\n" + "="*80)
    print("🔍 CREATING INDEXES")
    print("="*80 + "\n")
    
    for table_name, indexes in TABLE_INDEXES.items():
        print(f"Creating indexes for {table_name}...")
        for idx_query in indexes:
            cur.execute(idx_query)
        conn.commit()
        print(f"  ✓ {len(indexes)} indexes created for {table_name}")
    
    cur.close()


def verify_data(conn):
    """Verify loaded data"""
    cur = conn.cursor()
    
    print("\n" + "="*80)
    print("✅ VERIFICATION")
    print("="*80 + "\n")
    
    for table_name in TABLE_SCHEMAS.keys():
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        print(f"{table_name:25s}: {count:,} rows")
    
    cur.close()


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("📦 PLANALYTICS INVENTORY TABLES SETUP")
    print("="*80 + "\n")
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("  ✓ Connected to planalytics_database\n")
        
        # Create tables
        create_tables(conn)
        
        # Load data
        print("\n" + "="*80)
        print("📊 LOADING DATA FROM CSV FILES")
        print("="*80 + "\n")
        
        csv_files = {
            'sales': 'sales.csv',
            'batches': 'batches.csv',
            'batch_stock_tracking': 'batch_stock_tracking.csv',
            'spoilage_report': 'spoilage_report.csv'
        }
        
        for table_name, csv_file in csv_files.items():
            print(f"\nLoading {table_name} from {csv_file}...")
            rows = load_csv_data(conn, table_name, csv_file)
            print(f"  ✓ Loaded {rows:,} rows into {table_name}")
        
        # Create indexes
        create_indexes(conn)
        
        # Verify
        verify_data(conn)
        
        # Close connection
        conn.close()
        
        print("\n" + "="*80)
        print("✅ INVENTORY TABLES SETUP COMPLETE!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
