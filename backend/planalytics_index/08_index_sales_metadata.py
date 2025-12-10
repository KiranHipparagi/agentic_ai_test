"""
Sales Metadata Indexing for Azure AI Search
Strategy: Index metadata about sales data, not full records (916K rows)
Allows the agent to understand sales schema and construct SQL queries
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


class SalesMetadataIndexer:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.index_name = "planalytics-index-sales-metadata"
        
        # Database connection
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': os.getenv('POSTGRES_DB', 'planalytics_database'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        
        # Create clients
        transport = RequestsTransport(connection_verify=False)
        credential = AzureKeyCredential(self.key)
        
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=credential,
            transport=transport
        )
        
    def create_index(self):
        """Create the sales metadata index"""
        print("\n" + "="*80)
        print("Creating Sales Metadata Index Schema...")
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
        print("Generating Sales Metadata...")
        print("="*80 + "\n")
        
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        # Get row count
        cur.execute("SELECT COUNT(*) FROM sales")
        row_count = cur.fetchone()[0]
        print(f"Total sales records: {row_count:,}")
        
        # Get date range
        cur.execute("SELECT MIN(transaction_date), MAX(transaction_date) FROM sales")
        min_date, max_date = cur.fetchone()
        date_range = f"{min_date} to {max_date}"
        
        # Get sample data for top products
        cur.execute("""
            SELECT 
                product_code,
                COUNT(*) as transaction_count,
                SUM(sales_units) as total_units_sold,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_transaction_value
            FROM sales
            GROUP BY product_code
            ORDER BY total_revenue DESC
            LIMIT 10
        """)
        top_products = cur.fetchall()
        
        # Get sample data for top stores
        cur.execute("""
            SELECT 
                store_code,
                COUNT(*) as transaction_count,
                SUM(sales_units) as total_units,
                SUM(total_amount) as total_revenue
            FROM sales
            GROUP BY store_code
            ORDER BY total_revenue DESC
            LIMIT 10
        """)
        top_stores = cur.fetchall()
        
        # Get batch statistics
        cur.execute("""
            SELECT 
                batch_id,
                COUNT(*) as transaction_count,
                SUM(sales_units) as total_units,
                SUM(total_amount) as total_revenue
            FROM sales
            GROUP BY batch_id
            ORDER BY total_revenue DESC
            LIMIT 5
        """)
        batch_stats = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Create metadata documents
        documents = []
        
        # Document 1: Table Schema
        documents.append({
            'id': 'sales_schema',
            'metadata_type': 'schema',
            'description': 'Sales table contains individual transaction-level sales records',
            'table_name': 'sales',
            'row_count': row_count,
            'columns': 'id, batch_id, store_code, product_code, transaction_date, sales_units, sales_amount, discount_amount, total_amount',
            'sample_data': 'Schema: PK=id, Indexed: batch_id, store_code, product_code, transaction_date',
            'date_range': date_range
        })
        
        # Document 2: Top Products
        top_products_str = "\n".join([
            f"Product {p[0]}: {p[1]:,} transactions, {p[2]:,} units, ${p[3]:,.2f} revenue, ${p[4]:.2f} avg"
            for p in top_products
        ])
        documents.append({
            'id': 'sales_top_products',
            'metadata_type': 'statistics',
            'description': 'Top 10 products by revenue in sales table',
            'table_name': 'sales',
            'row_count': len(top_products),
            'sample_data': top_products_str,
            'columns': 'product_code, transaction_count, total_units, total_revenue, avg_value',
            'date_range': date_range
        })
        
        # Document 3: Top Stores
        top_stores_str = "\n".join([
            f"Store {s[0]}: {s[1]:,} transactions, {s[2]:,} units, ${s[3]:,.2f} revenue"
            for s in top_stores
        ])
        documents.append({
            'id': 'sales_top_stores',
            'metadata_type': 'statistics',
            'description': 'Top 10 stores by revenue in sales table',
            'table_name': 'sales',
            'row_count': len(top_stores),
            'sample_data': top_stores_str,
            'columns': 'store_code, transaction_count, total_units, total_revenue',
            'date_range': date_range
        })
        
        # Document 4: Batch Statistics
        batch_stats_str = "\n".join([
            f"Batch {b[0]}: {b[1]:,} transactions, {b[2]:,} units, ${b[3]:,.2f} revenue"
            for b in batch_stats
        ])
        documents.append({
            'id': 'sales_batch_stats',
            'metadata_type': 'statistics',
            'description': 'Top batches by revenue in sales table',
            'table_name': 'sales',
            'row_count': len(batch_stats),
            'sample_data': batch_stats_str,
            'columns': 'batch_id, transaction_count, total_units, total_revenue',
            'date_range': date_range
        })
        
        # Document 5: Query Examples
        documents.append({
            'id': 'sales_query_examples',
            'metadata_type': 'examples',
            'description': 'Common SQL query patterns for sales table',
            'table_name': 'sales',
            'row_count': 0,
            'sample_data': '''
            Example queries:
            - SELECT SUM(total_amount) FROM sales WHERE product_code = X
            - SELECT store_code, SUM(sales_units) FROM sales GROUP BY store_code
            - SELECT product_code, COUNT(*) FROM sales WHERE transaction_date >= 'YYYY-MM-DD' GROUP BY product_code
            - SELECT batch_id, SUM(total_amount) - SUM(discount_amount) FROM sales GROUP BY batch_id
            ''',
            'columns': 'All columns available for filtering and aggregation',
            'date_range': date_range
        })
        
        return documents
    
    def upload_documents(self, documents):
        """Upload metadata documents to Azure AI Search"""
        print("\n" + "="*80)
        print("Uploading Sales Metadata Documents...")
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
    print("📊 SALES METADATA INDEXING FOR AZURE AI SEARCH")
    print("="*80)
    
    indexer = SalesMetadataIndexer()
    
    # Create index
    indexer.create_index()
    
    # Generate metadata
    documents = indexer.generate_metadata()
    
    # Upload documents
    indexer.upload_documents(documents)
    
    print("\n" + "="*80)
    print("✅ SALES METADATA INDEXING COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
