"""Test QSR category query"""
from database.postgres_db import get_db
from sqlalchemy import text

with get_db() as db:
    # Test the exact query
    result = db.execute(text("SELECT COUNT(DISTINCT product_id) AS product_count FROM phier WHERE category = 'QSR'"))
    count = result.fetchone()[0]
    print(f"✅ QSR Products in database: {count}")
    
    # Also show the actual products
    result2 = db.execute(text("SELECT product_id, product, dept FROM phier WHERE category = 'QSR' ORDER BY product"))
    print("\nQSR Products:")
    for row in result2:
        print(f"  - {row.product_id}: {row.product} (Dept: {row.dept})")
