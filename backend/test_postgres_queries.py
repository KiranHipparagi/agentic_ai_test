"""Test PostgreSQL database queries"""
from database.postgres_db import get_db, EventsData, WeatherData, InventoryData, Metrics, ProductHierarchy, LocationDimension
from sqlalchemy import func

print("=" * 60)
print("Testing PostgreSQL Database Queries")
print("=" * 60)

try:
    with get_db() as db:
        # Test 1: Count events
        events_count = db.query(func.count(EventsData.event)).scalar()
        print(f"\n✅ Events table: {events_count} records")
        
        # Test 2: Sample events
        sample_events = db.query(EventsData).limit(3).all()
        print("\nSample Events:")
        for event in sample_events:
            print(f"  - {event.event} ({event.event_type}) on {event.event_date}")
        
        # Test 3: Count weather records
        weather_count = db.query(func.count(WeatherData.week_end_date)).scalar()
        print(f"\n✅ Weather table: {weather_count} records")
        
        # Test 4: Count inventory records
        inventory_count = db.query(func.count(InventoryData.store_id)).scalar()
        print(f"✅ Inventory table: {inventory_count} records")
        
        # Test 5: Count metrics/sales records
        metrics_count = db.query(func.count(Metrics.product_id)).scalar()
        print(f"✅ Metrics table: {metrics_count} records")
        
        # Test 6: Count products
        products_count = db.query(func.count(ProductHierarchy.product_id)).scalar()
        print(f"✅ Products table: {products_count} records")
        
        # Test 7: Count locations
        locations_count = db.query(func.count(LocationDimension.location)).scalar()
        print(f"✅ Locations table: {locations_count} records")
        
        # Test 8: Sample product
        sample_product = db.query(ProductHierarchy).first()
        if sample_product:
            print(f"\nSample Product:")
            print(f"  - ID: {sample_product.product_id}")
            print(f"  - Name: {sample_product.product}")
            print(f"  - Category: {sample_product.category}")
            print(f"  - Price: ${sample_product.unit_price}")
        
        # Test 9: Sample location
        sample_location = db.query(LocationDimension).first()
        if sample_location:
            print(f"\nSample Location:")
            print(f"  - Location: {sample_location.location}")
            print(f"  - Region: {sample_location.region}")
            print(f"  - State: {sample_location.state}")
        
        print("\n" + "=" * 60)
        print("✅ All database queries successful!")
        print("=" * 60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
