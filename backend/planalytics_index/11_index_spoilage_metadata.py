"""
Spoilage Report Metadata Indexing for Azure AI Search
Strategy: Index metadata about spoilage data, not full records (19K rows)
Allows the agent to understand spoilage patterns and construct SQL queries
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


class SpoilageMetadataIndexer:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.index_name = "planalytics-index-spoilage-metadata"
        
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
        """Create the spoilage metadata index"""
        print("\n" + "="*80)
        print("Creating Spoilage Report Metadata Index Schema...")
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
        print("Generating Spoilage Report Metadata...")
        print("="*80 + "\n")
        
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        # Get row count
        cur.execute("SELECT COUNT(*) FROM spoilage_report")
        row_count = cur.fetchone()[0]
        print(f"Total spoilage records: {row_count:,}")
        
        # Get batches with spoilage
        cur.execute("SELECT COUNT(*) FROM spoilage_report WHERE spoilage_qty > 0")
        spoilage_count = cur.fetchone()[0]
        print(f"Batches with spoilage: {spoilage_count:,}")
        
        # Get products with highest spoilage
        cur.execute("""
            SELECT 
                product_code,
                COUNT(*) as batch_count,
                SUM(qty) as total_qty,
                SUM(spoilage_qty) as total_spoilage,
                ROUND(AVG(spoilage_pct), 2) as avg_spoilage_pct,
                SUM(spoilage_case) as total_spoilage_cases
            FROM spoilage_report
            WHERE spoilage_qty > 0
            GROUP BY product_code
            ORDER BY total_spoilage DESC
            LIMIT 10
        """)
        product_spoilage = cur.fetchall()
        
        # Get stores with highest spoilage
        cur.execute("""
            SELECT 
                store_code,
                COUNT(*) as batch_count,
                SUM(spoilage_qty) as total_spoilage,
                ROUND(AVG(spoilage_pct), 2) as avg_spoilage_pct
            FROM spoilage_report
            WHERE spoilage_qty > 0
            GROUP BY store_code
            ORDER BY total_spoilage DESC
            LIMIT 10
        """)
        store_spoilage = cur.fetchall()
        
        # Get spoilage severity distribution
        cur.execute("""
            SELECT 
                CASE 
                    WHEN spoilage_pct = 0 THEN 'No Spoilage'
                    WHEN spoilage_pct < 5 THEN 'Low (0-5%)'
                    WHEN spoilage_pct < 10 THEN 'Medium (5-10%)'
                    WHEN spoilage_pct < 20 THEN 'High (10-20%)'
                    ELSE 'Critical (20%+)'
                END as severity,
                COUNT(*) as batch_count,
                SUM(spoilage_qty) as total_spoilage
            FROM spoilage_report
            GROUP BY 
                CASE 
                    WHEN spoilage_pct = 0 THEN 'No Spoilage'
                    WHEN spoilage_pct < 5 THEN 'Low (0-5%)'
                    WHEN spoilage_pct < 10 THEN 'Medium (5-10%)'
                    WHEN spoilage_pct < 20 THEN 'High (10-20%)'
                    ELSE 'Critical (20%+)'
                END
            ORDER BY batch_count DESC
        """)
        severity_distribution = cur.fetchall()
        
        # Get overall statistics
        cur.execute("""
            SELECT 
                COUNT(*) as total_batches,
                SUM(qty) as total_qty,
                SUM(spoilage_qty) as total_spoilage,
                ROUND(100.0 * SUM(spoilage_qty) / NULLIF(SUM(qty), 0), 2) as overall_spoilage_pct,
                SUM(spoilage_case) as total_spoilage_cases
            FROM spoilage_report
        """)
        overall_stats = cur.fetchone()
        
        cur.close()
        conn.close()
        
        # Create metadata documents
        documents = []
        
        # Document 1: Table Schema
        documents.append({
            'id': 'spoilage_schema',
            'metadata_type': 'schema',
            'description': 'Spoilage report table tracks product waste and spoilage by batch',
            'table_name': 'spoilage_report',
            'row_count': row_count,
            'columns': 'id, batch_id, store_code, product_code, qty, spoilage_qty, spoilage_pct, spoilage_case',
            'sample_data': f'Total batches: {overall_stats[0]:,}, Total spoilage: {overall_stats[2]:,} ({overall_stats[3]}%), Cases: {overall_stats[4]}',
            'date_range': 'All batches tracked'
        })
        
        # Document 2: Products with Highest Spoilage
        product_spoilage_str = "\n".join([
            f"Product {p[0]}: {p[1]} batches, {p[2]:,} total qty, {p[3]:,} spoiled ({p[4]}%), {p[5]} cases"
            for p in product_spoilage
        ])
        documents.append({
            'id': 'spoilage_by_product',
            'metadata_type': 'statistics',
            'description': 'Products with highest spoilage rates',
            'table_name': 'spoilage_report',
            'row_count': len(product_spoilage),
            'sample_data': product_spoilage_str,
            'columns': 'product_code, batch_count, total_qty, total_spoilage, avg_spoilage_pct, total_spoilage_cases',
            'date_range': 'All batches'
        })
        
        # Document 3: Stores with Highest Spoilage
        store_spoilage_str = "\n".join([
            f"Store {s[0]}: {s[1]} batches, {s[2]:,} spoiled ({s[3]}% avg)"
            for s in store_spoilage
        ])
        documents.append({
            'id': 'spoilage_by_store',
            'metadata_type': 'statistics',
            'description': 'Stores with highest spoilage quantities',
            'table_name': 'spoilage_report',
            'row_count': len(store_spoilage),
            'sample_data': store_spoilage_str,
            'columns': 'store_code, batch_count, total_spoilage, avg_spoilage_pct',
            'date_range': 'All batches'
        })
        
        # Document 4: Spoilage Severity Distribution
        severity_str = "\n".join([
            f"{s[0]}: {s[1]:,} batches, {s[2]:,} total spoilage"
            for s in severity_distribution
        ])
        documents.append({
            'id': 'spoilage_severity_distribution',
            'metadata_type': 'statistics',
            'description': 'Distribution of spoilage severity across batches',
            'table_name': 'spoilage_report',
            'row_count': len(severity_distribution),
            'sample_data': severity_str,
            'columns': 'severity, batch_count, total_spoilage',
            'date_range': 'All batches'
        })
        
        # Document 5: Query Examples
        documents.append({
            'id': 'spoilage_query_examples',
            'metadata_type': 'examples',
            'description': 'Common SQL query patterns for spoilage_report table',
            'table_name': 'spoilage_report',
            'row_count': 0,
            'sample_data': '''
            Example queries:
            - SELECT * FROM spoilage_report WHERE spoilage_pct > 10 ORDER BY spoilage_pct DESC
            - SELECT product_code, SUM(spoilage_qty) FROM spoilage_report GROUP BY product_code
            - SELECT store_code, AVG(spoilage_pct) FROM spoilage_report WHERE spoilage_qty > 0 GROUP BY store_code
            - SELECT batch_id FROM spoilage_report WHERE spoilage_case = 1
            - SELECT product_code, COUNT(*) as spoilage_incidents FROM spoilage_report WHERE spoilage_qty > 0 GROUP BY product_code
            - SELECT store_code, product_code, spoilage_pct FROM spoilage_report WHERE spoilage_pct = (SELECT MAX(spoilage_pct) FROM spoilage_report)
            ''',
            'columns': 'All columns available for filtering and aggregation',
            'date_range': 'All batches'
        })
        
        return documents
    
    def upload_documents(self, documents):
        """Upload metadata documents to Azure AI Search"""
        print("\n" + "="*80)
        print("Uploading Spoilage Report Metadata Documents...")
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
    print("⚠️  SPOILAGE REPORT METADATA INDEXING FOR AZURE AI SEARCH")
    print("="*80)
    
    indexer = SpoilageMetadataIndexer()
    indexer.create_index()
    documents = indexer.generate_metadata()
    indexer.upload_documents(documents)
    
    print("\n" + "="*80)
    print("✅ SPOILAGE REPORT METADATA INDEXING COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
