"""
Product Hierarchy Indexing for Azure AI Search
Reads from PostgreSQL planalytics_database and indexes into Azure AI Search
"""
import os
import ssl
import psycopg2
from dotenv import load_dotenv
from typing import List
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType,
    VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile, SearchField
)
from azure.core.pipeline.transport import RequestsTransport
from azure.core.credentials import AzureKeyCredential
from langchain_openai import AzureOpenAIEmbeddings
from openai import RateLimitError

load_dotenv()
ssl._create_default_https_context = ssl._create_unverified_context


class ProductHierarchyIndexer:
    def __init__(self):
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = "planalytics-index-products"
        
        # PostgreSQL config
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': 'planalytics_database',
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        
        # OpenAI config
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            api_version="2024-02-01"
        )
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Azure Search clients"""
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
        """Create or update the search index"""
        print(f"\n📊 Creating index: {self.index_name}")
        
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="product_id", type=SearchFieldDataType.Int32, filterable=True),
            SearchableField(name="dept", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="category", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="product", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SearchField(
                name="description_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="product-vector-profile"
            )
        ]
        
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="product-hnsw-config")],
            profiles=[VectorSearchProfile(
                name="product-vector-profile",
                algorithm_configuration_name="product-hnsw-config"
            )]
        )
        
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        self.index_client.create_or_update_index(index)
        print(f"   ✅ Index created/updated")
    
    def generate_description(self, row) -> str:
        """Generate natural language description for embedding"""
        return f"{row['product']} is a product in the {row['category']} category under the {row['dept']} department."
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(RateLimitError)
    )
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with retry logic"""
        return self.embeddings.embed_documents(texts)
    
    def index_products(self):
        """Read from PostgreSQL and index products"""
        print(f"\n📥 Reading product_hierarchy from PostgreSQL...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT product_id, dept, category, product FROM product_hierarchy ORDER BY product_id;")
        rows = cursor.fetchall()
        
        print(f"   ✅ Fetched {len(rows)} products")
        
        # Prepare documents
        documents = []
        descriptions = []
        
        for row in rows:
            product_id, dept, category, product = row
            description = f"{product} is a product in the {category} category under the {dept} department."
            descriptions.append(description)
            
            documents.append({
                'id': f"P-{product_id}",
                'product_id': product_id,
                'dept': dept or "",
                'category': category or "",
                'product': product or "",
                'description': description
            })
        
        cursor.close()
        conn.close()
        
        # Generate embeddings in batches
        print(f"\n🔄 Generating embeddings...")
        batch_size = 20
        
        for i in range(0, len(descriptions), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_descs = descriptions[i:i+batch_size]
            
            embeddings = self.generate_embeddings(batch_descs)
            
            for doc, embedding in zip(batch_docs, embeddings):
                doc['description_vector'] = embedding
            
            print(f"   ⏳ Generated embeddings for {min(i+batch_size, len(descriptions))}/{len(descriptions)} products...", end='\r')
        
        print(f"\n   ✅ All embeddings generated")
        
        # Upload to Azure Search
        print(f"\n☁️  Uploading to Azure AI Search...")
        upload_batch_size = 50
        
        for i in range(0, len(documents), upload_batch_size):
            batch = documents[i:i+upload_batch_size]
            self.search_client.upload_documents(documents=batch)
            print(f"   ⏳ Uploaded {min(i+upload_batch_size, len(documents))}/{len(documents)} products...", end='\r')
        
        print(f"\n   ✅ Upload complete!")


def main():
    print("="*80)
    print("🏭 PLANALYTICS - PRODUCT HIERARCHY INDEXING")
    print("="*80)
    
    indexer = ProductHierarchyIndexer()
    indexer.create_index()
    indexer.index_products()
    
    print("\n" + "="*80)
    print("✅ PRODUCT INDEXING COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()
