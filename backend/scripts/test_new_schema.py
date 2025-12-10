"""
Test script to verify the updated schema works correctly
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database.postgres_db import get_db, Calendar, ProductHierarchy, Perishable, LocationDimension, EventsData, WeatherData, Metrics
from sqlalchemy import func

print("="*80)
print("Testing New PostgreSQL Schema - planalytics_database")
print("="*80)

with get_db() as db:
    # Test each table
    print("\n1. Calendar table:")
    calendar_count = db.query(func.count(Calendar.id)).scalar()
    print(f"   ✓ Count: {calendar_count} rows")
    sample = db.query(Calendar).first()
    if sample:
        print(f"   ✓ Sample: end_date={sample.end_date}, week={sample.week}, season={sample.season}")
    
    print("\n2. Product Hierarchy table:")
    product_count = db.query(func.count(ProductHierarchy.product_id)).scalar()
    print(f"   ✓ Count: {product_count} rows")
    sample = db.query(ProductHierarchy).first()
    if sample:
        print(f"   ✓ Sample: product_id={sample.product_id}, product={sample.product}, category={sample.category}, dept={sample.dept}")
    
    print("\n3. Perishable table:")
    perishable_count = db.query(func.count(Perishable.id)).scalar()
    print(f"   ✓ Count: {perishable_count} rows")
    sample = db.query(Perishable).first()
    if sample:
        print(f"   ✓ Sample: product={sample.product}, storage={sample.storage}, min_period={sample.min_period}")
    
    print("\n4. Location table:")
    location_count = db.query(func.count(LocationDimension.id)).scalar()
    print(f"   ✓ Count: {location_count} rows")
    sample = db.query(LocationDimension).first()
    if sample:
        print(f"   ✓ Sample: location={sample.location}, region={sample.region}, market={sample.market}, state={sample.state}")
    
    print("\n5. Events table:")
    events_count = db.query(func.count(EventsData.id)).scalar()
    print(f"   ✓ Count: {events_count} rows")
    sample = db.query(EventsData).first()
    if sample:
        print(f"   ✓ Sample: event={sample.event}, event_type={sample.event_type}, event_date={sample.event_date}, store_id={sample.store_id}")
    
    print("\n6. Weekly Weather table:")
    weather_count = db.query(func.count(WeatherData.id)).scalar()
    print(f"   ✓ Count: {weather_count} rows")
    sample = db.query(WeatherData).first()
    if sample:
        print(f"   ✓ Sample: week_end_date={sample.week_end_date}, store_id={sample.store_id}, avg_temp_f={sample.avg_temp_f}")
    
    print("\n7. Metrics table:")
    metrics_count = db.query(func.count(Metrics.id)).scalar()
    print(f"   ✓ Count: {metrics_count} rows")
    sample = db.query(Metrics).first()
    if sample:
        print(f"   ✓ Sample: product={sample.product}, location={sample.location}, end_date={sample.end_date}, metric={sample.metric}")

print("\n" + "="*80)
print("✅ All tables verified successfully!")
print("="*80)
