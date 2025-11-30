"""Script to check PostgreSQL database structure"""
import sqlalchemy
from sqlalchemy import create_engine, inspect

# PostgreSQL connection
DATABASE_URL = "postgresql+psycopg2://postgres:admin123@localhost:5432/planalytics_db"

try:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print("=" * 60)
    print("PostgreSQL Database: planalytics_db")
    print("=" * 60)
    
    tables = inspector.get_table_names()
    print(f"\n✅ Found {len(tables)} tables:")
    for table in tables:
        print(f"\n📊 Table: {table}")
        print("-" * 60)
        columns = inspector.get_columns(table)
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            col_type = str(col['type'])
            default = f" DEFAULT {col.get('default', '')}" if col.get('default') else ""
            print(f"  • {col['name']:20s} {col_type:20s} {nullable}{default}")
    
    print("\n" + "=" * 60)
    print(f"✅ Total tables: {len(tables)}")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error connecting to PostgreSQL: {e}")
    print("\nMake sure:")
    print("1. PostgreSQL is running")
    print("2. Database 'planalytics_db' exists")
    print("3. Credentials are correct")
    print("4. psycopg2 is installed: pip install psycopg2-binary")
