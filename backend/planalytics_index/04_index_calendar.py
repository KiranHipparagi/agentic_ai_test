"""
Calendar Indexing for Azure AI Search
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


class CalendarIndexer:
    def __init__(self):
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = "planalytics-index-calendar"
        
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
            SimpleField(name="end_date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
            SimpleField(name="year", type=SearchFieldDataType.Int32, filterable=True),
            SimpleField(name="quarter", type=SearchFieldDataType.Int32, filterable=True),
            SearchableField(name="month", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="week", type=SearchFieldDataType.Int32, filterable=True),
            SearchableField(name="season", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SearchField(
                name="description_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="calendar-vector-profile"
            )
        ]
        
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="calendar-hnsw-config")],
            profiles=[VectorSearchProfile(
                name="calendar-vector-profile",
                algorithm_configuration_name="calendar-hnsw-config"
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
    
    def index_calendar(self):
        print(f"\n📥 Reading calendar from PostgreSQL...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, end_date, year, quarter, month, week, season 
            FROM calendar ORDER BY end_date;
        """)
        rows = cursor.fetchall()
        
        print(f"   ✅ Fetched {len(rows)} calendar entries")
        
        documents = []
        descriptions = []
        
        for row in rows:
            id_val, end_date, year, quarter, month, week, season = row
            
            description = f"Week {week} ending on {end_date} ({month} {year}, Q{quarter}, {season} season)"
            descriptions.append(description)
            
            documents.append({
                'id': f"CAL-{id_val}",
                'end_date': end_date.isoformat() + 'Z',
                'year': year or 0,
                'quarter': quarter or 0,
                'month': month or "",
                'week': week or 0,
                'season': season or "",
                'description': description
            })
        
        cursor.close()
        conn.close()
        
        # Generate embeddings in batches
        print(f"\n🔄 Generating embeddings...")
        batch_size = 50
        
        for i in range(0, len(descriptions), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_descs = descriptions[i:i+batch_size]
            
            embeddings = self.generate_embeddings(batch_descs)
            
            for doc, embedding in zip(batch_docs, embeddings):
                doc['description_vector'] = embedding
            
            print(f"   ⏳ Generated {min(i+batch_size, len(descriptions))}/{len(descriptions)} embeddings...", end='\r')
        
        print(f"\n   ✅ Embeddings generated")
        
        # Upload
        print(f"\n☁️  Uploading to Azure AI Search...")
        upload_batch_size = 100
        
        for i in range(0, len(documents), upload_batch_size):
            batch = documents[i:i+upload_batch_size]
            self.search_client.upload_documents(documents=batch)
            print(f"   ⏳ Uploaded {min(i+upload_batch_size, len(documents))}/{len(documents)} entries...", end='\r')
        
        print(f"\n   ✅ Upload complete!")


def main():
    print("="*80)
    print("📅 PLANALYTICS - CALENDAR INDEXING")
    print("="*80)
    
    indexer = CalendarIndexer()
    indexer.create_index()
    indexer.index_calendar()
    
    print("\n" + "="*80)
    print("✅ CALENDAR INDEXING COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()
