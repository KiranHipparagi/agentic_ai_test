"""
Create Planalytics PostgreSQL Database
Run this first to create the new database
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters (connect to default 'postgres' database first)
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

# New database name
NEW_DB_NAME = 'planalytics_database'

def create_database():
    """Create the planalytics database if it doesn't exist"""
    print("\n" + "="*80)
    print("🗄️  PLANALYTICS DATABASE CREATION")
    print("="*80 + "\n")
    
    try:
        # Connect to default postgres database
        print(f"📊 Connecting to PostgreSQL server at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            database='postgres'
        )
        
        # Set autocommit mode
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print(f"✅ Connected successfully!\n")
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (NEW_DB_NAME,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"⚠️  Database '{NEW_DB_NAME}' already exists.")
            response = input(f"   Drop and recreate? (yes/no): ").lower()
            if response == 'yes':
                print(f"\n🗑️  Dropping existing database '{NEW_DB_NAME}'...")
                cursor.execute(f"DROP DATABASE {NEW_DB_NAME};")
                print(f"   ✅ Dropped")
                
                print(f"\n📦 Creating database '{NEW_DB_NAME}'...")
                cursor.execute(f"CREATE DATABASE {NEW_DB_NAME};")
                print(f"   ✅ Created successfully!")
            else:
                print(f"   Using existing database.")
        else:
            print(f"📦 Creating database '{NEW_DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {NEW_DB_NAME};")
            print(f"   ✅ Created successfully!")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✅ DATABASE READY!")
        print("="*80)
        print()
        print("📝 Next steps:")
        print(f"   1. Run: python 02_setup_planalytics_tables.py")
        print()
        
        return True
        
    except psycopg2.OperationalError as e:
        print("\n❌ Connection Error!")
        print(f"   {str(e)}")
        print("\n💡 Troubleshooting:")
        print(f"   1. Is PostgreSQL running?")
        print(f"   2. Check .env file credentials:")
        print(f"      POSTGRES_HOST={DB_CONFIG['host']}")
        print(f"      POSTGRES_PORT={DB_CONFIG['port']}")
        print(f"      POSTGRES_USER={DB_CONFIG['user']}")
        print(f"   3. Can you connect manually?")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        create_database()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
