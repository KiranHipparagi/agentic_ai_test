"""
Batch Stock Tracking Metadata Indexing for Azure AI Search
Strategy: Index metadata about stock movement data, not full records (960K rows)
Allows the agent to understand inventory movement patterns and construct SQL queries
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


class BatchStockTrackingMetadataIndexer:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.index_name = "planalytics-index-batch-tracking-metadata"
        
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
        """Create the batch stock tracking metadata index"""
        print("\n" + "="*80)
        print("Creating Batch Stock Tracking Metadata Index Schema...")
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
        print("Generating Batch Stock Tracking Metadata...")
        print("="*80 + "\n")
        
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        # Get row count
        cur.execute("SELECT COUNT(*) FROM batch_stock_tracking")
        row_count = cur.fetchone()[0]
        print(f"Total tracking records: {row_count:,}")
        
        # Get date range
        cur.execute("SELECT MIN(transaction_date), MAX(transaction_date) FROM batch_stock_tracking")
        min_date, max_date = cur.fetchone()
        date_range = f"{min_date} to {max_date}"
        
        # Get transaction type breakdown
        cur.execute("""
            SELECT 
                transaction_type,
                COUNT(*) as transaction_count,
                SUM(qty_change) as total_qty_change
            FROM batch_stock_tracking
            GROUP BY transaction_type
            ORDER BY transaction_count DESC
        """)
        transaction_types = cur.fetchall()
        
        # Get most active batches
        cur.execute("""
            SELECT 
                batch_id,
                COUNT(*) as movement_count,
                SUM(qty_change) as total_qty_change,
                MIN(transaction_date) as first_transaction,
                MAX(transaction_date) as last_transaction
            FROM batch_stock_tracking
            GROUP BY batch_id
            ORDER BY movement_count DESC
            LIMIT 10
        """)
        active_batches = cur.fetchall()
        
        # Get product movement statistics
        cur.execute("""
            SELECT 
                product_code,
                COUNT(*) as movement_count,
                COUNT(DISTINCT batch_id) as batch_count,
                SUM(CASE WHEN qty_change > 0 THEN qty_change ELSE 0 END) as total_inbound,
                SUM(CASE WHEN qty_change < 0 THEN ABS(qty_change) ELSE 0 END) as total_outbound
            FROM batch_stock_tracking
            GROUP BY product_code
            ORDER BY movement_count DESC
            LIMIT 10
        """)
        product_movements = cur.fetchall()
        
        # Get store movement statistics
        cur.execute("""
            SELECT 
                store_code,
                COUNT(*) as movement_count,
                COUNT(DISTINCT batch_id) as batch_count,
                SUM(CASE WHEN transaction_type = 'SALE' THEN ABS(qty_change) ELSE 0 END) as total_sales_qty
            FROM batch_stock_tracking
            GROUP BY store_code
            ORDER BY movement_count DESC
            LIMIT 10
        """)
        store_movements = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Create metadata documents
        documents = []
        
        # Document 1: Table Schema
        documents.append({
            'id': 'batch_tracking_schema',
            'metadata_type': 'schema',
            'description': 'Batch stock tracking table contains detailed transaction-level inventory movements',
            'table_name': 'batch_stock_tracking',
            'row_count': row_count,
            'columns': 'record_id, batch_id, store_code, product_code, transaction_type, transaction_date, qty_change, stock_after_transaction, unit_price',
            'sample_data': 'Transaction types: TRANSFER_IN, SALE, ADJUSTMENT, SPOILAGE, RETURN',
            'date_range': date_range
        })
        
        # Document 2: Transaction Type Breakdown
        transaction_str = "\n".join([
            f"{t[0]}: {t[1]:,} transactions, {t[2]:,} total qty change"
            for t in transaction_types
        ])
        documents.append({
            'id': 'batch_tracking_transaction_types',
            'metadata_type': 'statistics',
            'description': 'Transaction type breakdown for batch stock tracking',
            'table_name': 'batch_stock_tracking',
            'row_count': len(transaction_types),
            'sample_data': transaction_str,
            'columns': 'transaction_type, transaction_count, total_qty_change',
            'date_range': date_range
        })
        
        # Document 3: Most Active Batches
        active_batches_str = "\n".join([
            f"Batch {b[0]}: {b[1]} movements, {b[2]:,} qty change, {b[3]} to {b[4]}"
            for b in active_batches
        ])
        documents.append({
            'id': 'batch_tracking_active_batches',
            'metadata_type': 'statistics',
            'description': 'Most active batches by movement count',
            'table_name': 'batch_stock_tracking',
            'row_count': len(active_batches),
            'sample_data': active_batches_str,
            'columns': 'batch_id, movement_count, total_qty_change, first_transaction, last_transaction',
            'date_range': date_range
        })
        
        # Document 4: Product Movement Statistics
        product_movements_str = "\n".join([
            f"Product {p[0]}: {p[1]:,} movements across {p[2]} batches, {p[3]:,} inbound, {p[4]:,} outbound"
            for p in product_movements
        ])
        documents.append({
            'id': 'batch_tracking_product_movements',
            'metadata_type': 'statistics',
            'description': 'Product movement statistics showing inbound and outbound quantities',
            'table_name': 'batch_stock_tracking',
            'row_count': len(product_movements),
            'sample_data': product_movements_str,
            'columns': 'product_code, movement_count, batch_count, total_inbound, total_outbound',
            'date_range': date_range
        })
        
        # Document 5: Store Movement Statistics
        store_movements_str = "\n".join([
            f"Store {s[0]}: {s[1]:,} movements, {s[2]} batches, {s[3]:,} sales qty"
            for s in store_movements
        ])
        documents.append({
            'id': 'batch_tracking_store_movements',
            'metadata_type': 'statistics',
            'description': 'Store-level movement statistics',
            'table_name': 'batch_stock_tracking',
            'row_count': len(store_movements),
            'sample_data': store_movements_str,
            'columns': 'store_code, movement_count, batch_count, total_sales_qty',
            'date_range': date_range
        })
        
        # Document 6: Query Examples
        documents.append({
            'id': 'batch_tracking_query_examples',
            'metadata_type': 'examples',
            'description': 'Common SQL query patterns for batch_stock_tracking table',
            'table_name': 'batch_stock_tracking',
            'row_count': 0,
            'sample_data': '''
            Example queries:
            - SELECT * FROM batch_stock_tracking WHERE batch_id = 'BATCH_XXX' ORDER BY transaction_date
            - SELECT transaction_type, SUM(ABS(qty_change)) FROM batch_stock_tracking GROUP BY transaction_type
            - SELECT product_code, SUM(qty_change) FROM batch_stock_tracking WHERE transaction_type = 'SALE' GROUP BY product_code
            - SELECT store_code, COUNT(*) FROM batch_stock_tracking WHERE transaction_date >= 'YYYY-MM-DD' GROUP BY store_code
            - SELECT batch_id, stock_after_transaction FROM batch_stock_tracking WHERE product_code = X ORDER BY transaction_date DESC LIMIT 1
            ''',
            'columns': 'All columns available for filtering and aggregation',
            'date_range': date_range
        })
        
        return documents
    
    def upload_documents(self, documents):
        """Upload metadata documents to Azure AI Search"""
        print("\n" + "="*80)
        print("Uploading Batch Stock Tracking Metadata Documents...")
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
    print("📊 BATCH STOCK TRACKING METADATA INDEXING FOR AZURE AI SEARCH")
    print("="*80)
    
    indexer = BatchStockTrackingMetadataIndexer()
    indexer.create_index()
    documents = indexer.generate_metadata()
    indexer.upload_documents(documents)
    
    print("\n" + "="*80)
    print("✅ BATCH STOCK TRACKING METADATA INDEXING COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
