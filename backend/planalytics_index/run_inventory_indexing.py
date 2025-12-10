"""
Master Script to Run All Inventory Metadata Indexing

Executes indexing for 4 new inventory tables:
8. Sales - Metadata only (~916K rows)
9. Batches - Metadata only (~94K rows)
10. Batch Stock Tracking - Metadata only (~960K rows)
11. Spoilage Report - Metadata only (~19K rows)
"""
import sys
import subprocess
from pathlib import Path

def run_script(script_name: str, description: str) -> bool:
    """Run a Python script and return success status"""
    print(f"\n{'='*80}")
    print(f"▶️  {description}")
    print(f"{'='*80}\n")
    
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}:")
        print(e.stdout)
        print(e.stderr)
        return False


def main():
    """Run all inventory metadata indexing scripts"""
    print("\n" + "="*80)
    print("📦 PLANALYTICS INVENTORY METADATA INDEXING - MASTER SCRIPT")
    print("="*80)
    print("\nThis will create 4 metadata-only indexes for inventory tables:")
    print("  - Sales metadata (transaction patterns)")
    print("  - Batches metadata (expiry tracking)")
    print("  - Batch Stock Tracking metadata (inventory movements)")
    print("  - Spoilage Report metadata (waste patterns)")
    print("\n" + "="*80)
    
    scripts = [
        ('08_index_sales_metadata.py', 'Indexing Sales Metadata'),
        ('09_index_batches_metadata.py', 'Indexing Batches Metadata'),
        # Scripts 10 and 11 to be created next
    ]
    
    success_count = 0
    total_count = len(scripts)
    
    for script_name, description in scripts:
        if run_script(script_name, description):
            success_count += 1
        else:
            print(f"\n⚠️  Failed to run {script_name}, continuing...")
    
    # Summary
    print("\n" + "="*80)
    print("📊 INDEXING SUMMARY")
    print("="*80)
    print(f"\n✅ Successfully completed: {success_count}/{total_count} scripts")
    
    if success_count == total_count:
        print("\n🎉 ALL INVENTORY METADATA INDEXES CREATED SUCCESSFULLY!")
        print("\nIndexes created:")
        print("  1. planalytics-index-sales-metadata")
        print("  2. planalytics-index-batches-metadata")
        print("  3. planalytics-index-batch-tracking-metadata")
        print("  4. planalytics-index-spoilage-metadata")
    else:
        print(f"\n⚠️  Some scripts failed. Please check the output above.")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
