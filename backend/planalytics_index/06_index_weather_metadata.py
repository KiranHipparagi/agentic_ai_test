"""
Weather Metadata Indexing for Azure AI Search
Strategy: Index metadata about weather data, not full records
Allows the agent to understand weather schema and construct SQL queries
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


class WeatherMetadataIndexer:
    def __init__(self):
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = "planalytics-index-weather-metadata"
        
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
            SimpleField(name="date_from", type=SearchFieldDataType.DateTimeOffset, filterable=True),
            SimpleField(name="date_to", type=SearchFieldDataType.DateTimeOffset, filterable=True),
            SimpleField(name="record_count", type=SearchFieldDataType.Int32),
            SearchableField(name="weather_conditions", type=SearchFieldDataType.String),
            SearchableField(name="description", type=SearchFieldDataType.String),
        ]
        
        index = SearchIndex(name=self.index_name, fields=fields)
        self.index_client.create_or_update_index(index)
        print(f"   ✅ Index created/updated")
    
    def sanitize_id(self, raw_id: str) -> str:
        """Sanitize ID for Azure Search (alphanumeric, dash, underscore only)"""
        import re
        return re.sub(r'[^a-zA-Z0-9_-]', '_', raw_id)
    
    def index_weather_metadata(self):
        print(f"\n📥 Analyzing weather data in PostgreSQL...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Get schema metadata
        cursor.execute("""
            SELECT MIN(week_end_date) as min_date, 
                   MAX(week_end_date) as max_date,
                   COUNT(*) as total_records
            FROM weekly_weather;
        """)
        min_date, max_date, total_records = cursor.fetchone()
        
        # Get per-store date ranges
        cursor.execute("""
            SELECT store_id,
                   MIN(week_end_date) as date_from,
                   MAX(week_end_date) as date_to,
                   COUNT(*) as record_count
            FROM weekly_weather
            WHERE store_id IS NOT NULL
            GROUP BY store_id
            ORDER BY store_id;
        """)
        store_ranges = cursor.fetchall()
        
        # Get weather condition flags summary
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN heatwave_flag THEN 1 ELSE 0 END) as heatwave_count,
                SUM(CASE WHEN cold_spell_flag THEN 1 ELSE 0 END) as cold_spell_count,
                SUM(CASE WHEN heavy_rain_flag THEN 1 ELSE 0 END) as heavy_rain_count,
                SUM(CASE WHEN snow_flag THEN 1 ELSE 0 END) as snow_count
            FROM weekly_weather;
        """)
        heatwave_cnt, cold_cnt, rain_cnt, snow_cnt = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Analyzed {total_records:,} weather records")
        print(f"   📅 Date range: {min_date} to {max_date}")
        print(f"   🏪 Store coverage: {len(store_ranges)} stores")
        
        # Create metadata documents
        documents = []
        
        # 1. Overall schema document
        weather_conditions = []
        if heatwave_cnt > 0:
            weather_conditions.append(f"Heatwave ({heatwave_cnt:,} occurrences)")
        if cold_cnt > 0:
            weather_conditions.append(f"Cold Spell ({cold_cnt:,} occurrences)")
        if rain_cnt > 0:
            weather_conditions.append(f"Heavy Rain ({rain_cnt:,} occurrences)")
        if snow_cnt > 0:
            weather_conditions.append(f"Snow ({snow_cnt:,} occurrences)")
        
        documents.append({
            'id': 'WEATHER-SCHEMA',
            'metadata_type': 'schema',
            'store_id': 'ALL',
            'date_from': min_date.isoformat() + 'Z',
            'date_to': max_date.isoformat() + 'Z',
            'record_count': total_records,
            'weather_conditions': ', '.join(weather_conditions),
            'description': f"Weather data covers {len(store_ranges)} stores from {min_date} to {max_date}. " +
                          f"Available metrics: avg_temp_f, temp_anom_f, tmax_f, tmin_f, precip_in, precip_anom_in. " +
                          f"Weather flags: {', '.join(weather_conditions)}."
        })
        
        # 2. Per-store metadata (limit to sample for large datasets)
        for store_id, date_from, date_to, record_count in store_ranges[:100]:  # Limit to 100 stores
            doc_id = self.sanitize_id(f"WEATHER-STORE-{store_id}")
            documents.append({
                'id': doc_id,
                'metadata_type': 'store_coverage',
                'store_id': store_id,
                'date_from': date_from.isoformat() + 'Z',
                'date_to': date_to.isoformat() + 'Z',
                'record_count': record_count,
                'weather_conditions': 'All conditions available',
                'description': f"Weather data for store {store_id} from {date_from} to {date_to} ({record_count} weeks)"
            })
        
        print(f"\n☁️  Uploading {len(documents)} metadata documents to Azure AI Search...")
        self.search_client.upload_documents(documents=documents)
        print(f"   ✅ Upload complete!")


def main():
    print("="*80)
    print("🌤️  PLANALYTICS - WEATHER METADATA INDEXING")
    print("="*80)
    
    indexer = WeatherMetadataIndexer()
    indexer.create_index()
    indexer.index_weather_metadata()
    
    print("\n" + "="*80)
    print("✅ WEATHER METADATA INDEXING COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()
