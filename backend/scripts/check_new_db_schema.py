"""Check the new database schema"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host='localhost',
    database='planalytics_database',
    user='postgres',
    password='password',
    port='5432'
)

cur = conn.cursor()

# Get all tables
print("="*80)
print("TABLES IN planalytics_database:")
print("="*80)
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public'
    ORDER BY table_name
""")
tables = cur.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n" + "="*80)
print("TABLE SCHEMAS:")
print("="*80)

# Get schema for each table
for table in tables:
    table_name = table[0]
    print(f"\n{table_name}:")
    cur.execute(f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    for col in columns:
        print(f"  {col[0]} ({col[1]}) - Nullable: {col[2]}")
    
    # Get row count
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cur.fetchone()[0]
    print(f"  → Row count: {count}")

conn.close()
