"""
Perishable Products Indexing for Azure AI Search
Reads from PostgreSQL planalytics_database and indexes into Azure AI Search
"""
import os
import ssl
import psycopg2
from dotenv import load_dotenv
from typing import List

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


class PerishableIndexer:
    def __init__(self):
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = "planalytics-index-perishable"
        
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': 'planalytics_database',
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            api_version="2024-02-01"
        )
        
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
            SearchableField(name="product", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="perishable_id", type=SearchFieldDataType.Int32, filterable=True),
            SearchableField(name="min_period", type=SearchFieldDataType.String),
            SearchableField(name="max_period", type=SearchFieldDataType.String),
            SearchableField(name="period_metric", type=SearchFieldDataType.String),
            SearchableField(name="storage", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SearchField(
                name="description_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="perishable-vector-profile"
            )
        ]
        
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="perishable-hnsw-config")],
            profiles=[VectorSearchProfile(
                name="perishable-vector-profile",
                algorithm_configuration_name="perishable-hnsw-config"
            )]
        )
        
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        self.index_client.create_or_update_index(index)
        print(f"   ✅ Index created/updated")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(RateLimitError)
    )
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def index_perishable(self):
        print(f"\n📥 Reading perishable from PostgreSQL...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, product, perishable_id, min_period, max_period, period_metric, storage 
            FROM perishable ORDER BY id;
        """)
        rows = cursor.fetchall()
        
        print(f"   ✅ Fetched {len(rows)} perishable items")
        
        documents = []
        descriptions = []
        
        for row in rows:
            id_val, product, perishable_id, min_period, max_period, period_metric, storage = row
            
            # Generate description
            desc_parts = [f"{product} is a perishable item"]
            if min_period and max_period and period_metric:
                desc_parts.append(f"with shelf life of {min_period} to {max_period} {period_metric}")
            if storage:
                desc_parts.append(f"requiring {storage} storage")
            
            description = " ".join(desc_parts) + "."
            descriptions.append(description)
            
            documents.append({
                'id': f"PERISH-{id_val}",
                'product': product or "",
                'perishable_id': perishable_id or 0,
                'min_period': str(min_period) if min_period else "",
                'max_period': str(max_period) if max_period else "",
                'period_metric': period_metric or "",
                'storage': storage or "",
                'description': description
            })
        
        cursor.close()
        conn.close()
        
        # Generate embeddings
        print(f"\n🔄 Generating embeddings...")
        embeddings = self.generate_embeddings(descriptions)
        
        for doc, embedding in zip(documents, embeddings):
            doc['description_vector'] = embedding
        
        print(f"   ✅ Embeddings generated")
        
        # Upload
        print(f"\n☁️  Uploading to Azure AI Search...")
        self.search_client.upload_documents(documents=documents)
        print(f"   ✅ Uploaded {len(documents)} items")


def main():
    print("="*80)
    print("🥬 PLANALYTICS - PERISHABLE PRODUCTS INDEXING")
    print("="*80)
    
    indexer = PerishableIndexer()
    indexer.create_index()
    indexer.index_perishable()
    
    print("\n" + "="*80)
    print("✅ PERISHABLE INDEXING COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()
