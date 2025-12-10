"""
Master Script to Run All Planalytics Azure AI Search Indexing

This script executes all 7 indexing processes in order:
1. Products (product_hierarchy) - Full data with embeddings
2. Perishable - Full data with embeddings
3. Locations - Full data with embeddings
4. Calendar - Full data with embeddings
5. Events - Full data with embeddings
6. Weather - Metadata only
7. Metrics - Metadata only

All indexes are named: planalytics-index-*
"""
import subprocess
import sys
from pathlib import Path

def run_script(script_name: str, description: str) -> bool:
    """Run a Python script and return success status"""
    print(f"\n{'='*80}")
    print(f"▶️  {description}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=Path(__file__).parent,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    print("="*80)
    print("🚀 PLANALYTICS AZURE AI SEARCH - COMPLETE INDEXING")
    print("="*80)
    print("\nThis will create 7 indexes under 'planalytics-index-*' naming convention")
    print("Reading all data from PostgreSQL database 'planalytics_database'\n")
    
    scripts = [
        ("01_index_products.py", "📦 [1/7] Indexing Products (Master Data)"),
        ("02_index_perishable.py", "🥬 [2/7] Indexing Perishable Items (Master Data)"),
        ("03_index_locations.py", "📍 [3/7] Indexing Locations (Master Data)"),
        ("04_index_calendar.py", "📅 [4/7] Indexing Calendar (Master Data)"),
        ("05_index_events.py", "🎉 [5/7] Indexing Events (Master Data)"),
        ("06_index_weather_metadata.py", "🌤️  [6/7] Indexing Weather Metadata"),
        ("07_index_metrics_metadata.py", "📈 [7/7] Indexing Metrics Metadata"),
    ]
    
    results = []
    
    for script, description in scripts:
        success = run_script(script, description)
        results.append((description, success))
        
        if not success:
            print(f"\n⚠️  Warning: {script} failed. Continue? (yes/no)")
            response = input().lower()
            if response != 'yes':
                print("\n🛑 Indexing stopped by user")
                break
    
    # Summary
    print("\n" + "="*80)
    print("📊 INDEXING SUMMARY")
    print("="*80)
    
    for desc, success in results:
        status = "✅ Success" if success else "❌ Failed"
        print(f"{status} - {desc}")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"\n{success_count}/{total_count} indexes completed successfully")
    
    if success_count == total_count:
        print("\n" + "="*80)
        print("🎉 ALL INDEXING COMPLETE!")
        print("="*80)
        print("\n📋 Created indexes:")
        print("   - planalytics-index-products (with embeddings)")
        print("   - planalytics-index-perishable (with embeddings)")
        print("   - planalytics-index-locations (with embeddings)")
        print("   - planalytics-index-calendar (with embeddings)")
        print("   - planalytics-index-events (with embeddings)")
        print("   - planalytics-index-weather-metadata")
        print("   - planalytics-index-metrics-metadata")
        print("\n✨ Your Hybrid Architecture is ready!")


if __name__ == "__main__":
    main()
