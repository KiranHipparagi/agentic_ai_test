"""
Metrics Metadata Indexing for Azure AI Search
Strategy: Index metadata about metrics data, not full records
Allows the agent to understand which products are weather-sensitive at which stores
"""
import os
import ssl
import psycopg2
from dotenv import load_dotenv

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType
)
from azure.core.pipeline.transport import RequestsTransport
from azure.core.credentials import AzureKeyCredential

load_dotenv()
ssl._create_default_https_context = ssl._create_unverified_context


class MetricsMetadataIndexer:
    def __init__(self):
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = "planalytics-index-metrics-metadata"
        
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': 'planalytics_database',
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        credential = AzureKeyCredential(self.search_key)
        transport = RequestsTransport(connection_verify=False)
        
        self.index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=credential,
            transport=transport
        )
        
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=credential,
            transport=transport
        )
    
    def create_index(self):
        print(f"\n📊 Creating index: {self.index_name}")
        
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="metadata_type", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="store_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="product_id", type=SearchFieldDataType.Int32, filterable=True),
            SearchableField(name="product_name", type=SearchFieldDataType.String, filterable=True, searchable=True),
            SimpleField(name="date_from", type=SearchFieldDataType.DateTimeOffset, filterable=True),
            SimpleField(name="date_to", type=SearchFieldDataType.DateTimeOffset, filterable=True),
            SimpleField(name="record_count", type=SearchFieldDataType.Int32),
            SimpleField(name="avg_metric", type=SearchFieldDataType.Double),
            SimpleField(name="avg_variance", type=SearchFieldDataType.Double),
            SearchableField(name="sensitivity_category", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
        ]
        
        index = SearchIndex(name=self.index_name, fields=fields)
        self.index_client.create_or_update_index(index)
        print(f"   ✅ Index created/updated")
    
    def sanitize_id(self, raw_id: str) -> str:
        """Sanitize ID for Azure Search"""
        import re
        return re.sub(r'[^a-zA-Z0-9_-]', '_', raw_id)
    
    def categorize_sensitivity(self, avg_variance: float) -> str:
        """Categorize weather sensitivity based on variance"""
        if avg_variance is None:
            return 'Unknown'
        elif avg_variance > 100:
            return 'High'
        elif avg_variance > 50:
            return 'Medium'
        else:
            return 'Low'
    
    def index_metrics_metadata(self):
        print(f"\n📥 Analyzing metrics data in PostgreSQL...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Get overall schema
        cursor.execute("""
            SELECT MIN(end_date) as min_date, 
                   MAX(end_date) as max_date,
                   COUNT(*) as total_records,
                   COUNT(DISTINCT location) as store_count,
                   COUNT(DISTINCT product) as product_count
            FROM metrics
            WHERE end_date IS NOT NULL;
        """)
        min_date, max_date, total_records, store_count, product_count = cursor.fetchone()
        
        print(f"   ✅ Analyzed {total_records:,} metric records")
        print(f"   📅 Date range: {min_date} to {max_date}")
        print(f"   🏪 {store_count} stores, 📦 {product_count} products")
        
        # Get product-store combinations with aggregated stats (sample top variance)
        print(f"\n🔍 Analyzing weather-sensitive product-store combinations...")
        cursor.execute("""
            SELECT 
                location as store_id,
                product as product_name,
                MIN(end_date) as date_from,
                MAX(end_date) as date_to,
                COUNT(*) as record_count,
                AVG(metric) as avg_metric,
                STDDEV(metric) as stddev_metric
            FROM metrics
            WHERE location IS NOT NULL AND product IS NOT NULL AND end_date IS NOT NULL
            GROUP BY location, product
            HAVING COUNT(*) > 10 AND STDDEV(metric) IS NOT NULL
            ORDER BY STDDEV(metric) DESC
            LIMIT 500;
        """)
        product_store_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Found {len(product_store_stats)} product-store combinations")
        
        # Create metadata documents
        documents = []
        
        # 1. Overall schema document
        documents.append({
            'id': 'METRICS-SCHEMA',
            'metadata_type': 'schema',
            'store_id': 'ALL',
            'product_id': 0,
            'date_from': min_date.isoformat() + 'Z' if min_date else '2000-01-01T00:00:00Z',
            'date_to': max_date.isoformat() + 'Z' if max_date else '2030-01-01T00:00:00Z',
            'record_count': total_records,
            'avg_metric': 0.0,
            'avg_variance': 0.0,
            'sensitivity_category': 'Schema',
            'description': f"Metrics data covers {store_count} stores and {product_count} products from {min_date} to {max_date}. " +
                          f"Total records: {total_records:,}. Available metrics: metric (current), metric_nrm (normalized), metric_ly (last year)."
        })
        
        # 2. Product-Store combinations (weather-sensitive items)
        for store_id, product_name, date_from, date_to, record_count, avg_metric, stddev_metric in product_store_stats:
            doc_id = self.sanitize_id(f"METRICS-{product_name}-{store_id}")
            avg_variance = float(stddev_metric) if stddev_metric else 0.0
            sensitivity = self.categorize_sensitivity(avg_variance)
            
            documents.append({
                'id': doc_id,
                'metadata_type': 'product_store_stats',
                'store_id': str(store_id),
                'product_id': 0,  # Using product name instead
                'product_name': product_name,
                'date_from': date_from.isoformat() + 'Z',
                'date_to': date_to.isoformat() + 'Z',
                'record_count': record_count,
                'avg_metric': float(avg_metric) if avg_metric else 0.0,
                'avg_variance': avg_variance,
                'sensitivity_category': sensitivity,
                'description': f"Product {product_name} at store {store_id}: {record_count} records, avg metric {avg_metric:.2f}, " +
                              f"variance {avg_variance:.2f} ({sensitivity} weather sensitivity)"
            })
        
        print(f"\n☁️  Uploading {len(documents)} metadata documents to Azure AI Search...")
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            self.search_client.upload_documents(documents=batch)
            print(f"   ⏳ Uploaded {min(i+batch_size, len(documents))}/{len(documents)} documents...", end='\r')
        
        print(f"\n   ✅ Upload complete!")


def main():
    print("="*80)
    print("📈 PLANALYTICS - METRICS METADATA INDEXING")
    print("="*80)
    
    indexer = MetricsMetadataIndexer()
    indexer.create_index()
    indexer.index_metrics_metadata()
    
    print("\n" + "="*80)
    print("✅ METRICS METADATA INDEXING COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()
