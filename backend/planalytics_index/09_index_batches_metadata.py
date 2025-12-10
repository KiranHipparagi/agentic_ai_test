"""
Batches Metadata Indexing for Azure AI Search
Strategy: Index metadata about batch inventory data, not full records (94K rows)
Allows the agent to understand batch tracking schema and construct SQL queries
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


class BatchesMetadataIndexer:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.index_name = "planalytics-index-batches-metadata"
        
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': os.getenv('POSTGRES_DB', 'planalytics_database'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        
        transport = RequestsTransport(connection_verify=False)
        credential = AzureKeyCredential(self.key)
        
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=credential,
            transport=transport
        )
        
    def create_index(self):
        """Create the batches metadata index"""
        print("\n" + "="*80)
        print("Creating Batches Metadata Index Schema...")
        print("="*80 + "\n")
        
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="metadata_type", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SearchableField(name="table_name", type=SearchFieldDataType.String),
            SimpleField(name="row_count", type=SearchFieldDataType.Int64),
            SearchableField(name="sample_data", type=SearchFieldDataType.String),
            SearchableField(name="date_range", type=SearchFieldDataType.String),
            SearchableField(name="columns", type=SearchFieldDataType.String),
        ]
        
        index = SearchIndex(name=self.index_name, fields=fields)
        result = self.index_client.create_or_update_index(index)
        print(f"✓ Index '{self.index_name}' created/updated")
        
    def generate_metadata(self):
        """Generate metadata documents from PostgreSQL"""
        print("\n" + "="*80)
        print("Generating Batches Metadata...")
        print("="*80 + "\n")
        
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        # Get row count
        cur.execute("SELECT COUNT(*) FROM batches")
        row_count = cur.fetchone()[0]
        print(f"Total batch records: {row_count:,}")
        
        # Get date range
        cur.execute("SELECT MIN(transaction_date), MAX(transaction_date) FROM batches")
        min_date, max_date = cur.fetchone()
        date_range = f"{min_date} to {max_date}"
        
        # Get expiring soon batches
        cur.execute("""
            SELECT 
                batch_id,
                store_code,
                product_code,
                expiry_date,
                stock_at_week_end
            FROM batches
            WHERE expiry_date IS NOT NULL 
              AND expiry_date >= CURRENT_DATE
              AND expiry_date <= CURRENT_DATE + INTERVAL '30 days'
              AND stock_at_week_end > 0
            ORDER BY expiry_date
            LIMIT 10
        """)
        expiring_batches = cur.fetchall()
        
        # Get batch statistics by product
        cur.execute("""
            SELECT 
                product_code,
                COUNT(DISTINCT batch_id) as batch_count,
                SUM(received_qty) as total_received,
                SUM(stock_at_week_end) as current_stock,
                AVG(unit_price) as avg_unit_price
            FROM batches
            GROUP BY product_code
            ORDER BY batch_count DESC
            LIMIT 10
        """)
        product_batch_stats = cur.fetchall()
        
        # Get batch turnover rate
        cur.execute("""
            SELECT 
                store_code,
                COUNT(DISTINCT batch_id) as batch_count,
                SUM(received_qty) as total_received,
                SUM(stock_at_week_end) as remaining_stock,
                ROUND(100.0 * SUM(stock_at_week_end) / NULLIF(SUM(received_qty), 0), 2) as stock_retention_pct
            FROM batches
            GROUP BY store_code
            ORDER BY batch_count DESC
            LIMIT 10
        """)
        store_batch_stats = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Create metadata documents
        documents = []
        
        # Document 1: Table Schema
        documents.append({
            'id': 'batches_schema',
            'metadata_type': 'schema',
            'description': 'Batches table tracks product batches with expiry dates and stock levels',
            'table_name': 'batches',
            'row_count': row_count,
            'columns': 'id, batch_id, store_code, product_code, transaction_date, expiry_date, unit_price, total_value, received_qty, mfg_date, week_end_date, stock_received, stock_at_week_start, stock_at_week_end',
            'sample_data': 'Schema: PK=id, Indexed: batch_id, store_code, product_code, expiry_date, week_end_date',
            'date_range': date_range
        })
        
        # Document 2: Expiring Batches
        if expiring_batches:
            expiring_str = "\n".join([
                f"Batch {b[0]}: Store {b[1]}, Product {b[2]}, Expires {b[3]}, Stock: {b[4]}"
                for b in expiring_batches
            ])
            documents.append({
                'id': 'batches_expiring_soon',
                'metadata_type': 'statistics',
                'description': 'Batches expiring in next 30 days with remaining stock',
                'table_name': 'batches',
                'row_count': len(expiring_batches),
                'sample_data': expiring_str,
                'columns': 'batch_id, store_code, product_code, expiry_date, stock_at_week_end',
                'date_range': date_range
            })
        
        # Document 3: Product Batch Statistics
        product_stats_str = "\n".join([
            f"Product {p[0]}: {p[1]} batches, {p[2]:,} received, {p[3]:,} in stock, ${p[4]:.2f} avg price"
            for p in product_batch_stats
        ])
        documents.append({
            'id': 'batches_by_product',
            'metadata_type': 'statistics',
            'description': 'Batch statistics grouped by product',
            'table_name': 'batches',
            'row_count': len(product_batch_stats),
            'sample_data': product_stats_str,
            'columns': 'product_code, batch_count, total_received, current_stock, avg_unit_price',
            'date_range': date_range
        })
        
        # Document 4: Store Batch Statistics
        store_stats_str = "\n".join([
            f"Store {s[0]}: {s[1]} batches, {s[2]:,} received, {s[3]:,} remaining ({s[4]}% retention)"
                for s in store_batch_stats
        ])
        documents.append({
            'id': 'batches_by_store',
            'metadata_type': 'statistics',
            'description': 'Batch statistics grouped by store',
            'table_name': 'batches',
            'row_count': len(store_batch_stats),
            'sample_data': store_stats_str,
            'columns': 'store_code, batch_count, total_received, remaining_stock, retention_pct',
            'date_range': date_range
        })
        
        # Document 5: Query Examples
        documents.append({
            'id': 'batches_query_examples',
            'metadata_type': 'examples',
            'description': 'Common SQL query patterns for batches table',
            'table_name': 'batches',
            'row_count': 0,
            'sample_data': '''
            Example queries:
            - SELECT * FROM batches WHERE expiry_date <= CURRENT_DATE + INTERVAL '7 days' AND stock_at_week_end > 0
            - SELECT product_code, SUM(stock_at_week_end) FROM batches GROUP BY product_code
            - SELECT batch_id, received_qty - stock_at_week_end as sold_qty FROM batches
            - SELECT store_code, AVG(EXTRACT(DAY FROM expiry_date - mfg_date)) FROM batches GROUP BY store_code
            ''',
            'columns': 'All columns available for filtering and aggregation',
            'date_range': date_range
        })
        
        return documents
    
    def upload_documents(self, documents):
        """Upload metadata documents to Azure AI Search"""
        print("\n" + "="*80)
        print("Uploading Batches Metadata Documents...")
        print("="*80 + "\n")
        
        transport = RequestsTransport(connection_verify=False)
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.key),
            transport=transport
        )
        
        result = search_client.upload_documents(documents=documents)
        print(f"✓ Uploaded {len(documents)} metadata documents")
        
        for doc in result:
            print(f"  - {doc.key}: {doc.succeeded}")


def main():
    print("\n" + "="*80)
    print("📦 BATCHES METADATA INDEXING FOR AZURE AI SEARCH")
    print("="*80)
    
    indexer = BatchesMetadataIndexer()
    indexer.create_index()
    documents = indexer.generate_metadata()
    indexer.upload_documents(documents)
    
    print("\n" + "="*80)
    print("✅ BATCHES METADATA INDEXING COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
