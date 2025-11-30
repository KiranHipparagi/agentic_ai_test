"""Azure AI Search client for entity resolution and semantic search"""
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
from core.config import settings
from core.logger import logger


class AzureSearchService:
    """Azure AI Search service for all Planalytics indexes"""
    
    # Index name mappings
    INDEXES = {
        "products": "planalytics-data-index-products",
        "locations": "planalytics-data-index-locations",
        "events": "planalytics-data-index-events",
        "calendar": "planalytics-data-index-calendar",
        "sales_metadata": "planalytics-data-index-sales-metadata",
        "weather_metadata": "planalytics-data-index-weather-metadata",
        "metrics_metadata": "planalytics-data-index-metrics-metadata"
    }
    
    def __init__(self):
        """Initialize Azure Search clients"""
        self.endpoint = settings.AZURE_SEARCH_ENDPOINT
        self.credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        
        # Initialize OpenAI client for embeddings
        self.embedding_client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        # Initialize search clients for each index
        self.clients = {}
        for key, index_name in self.INDEXES.items():
            try:
                self.clients[key] = SearchClient(
                    endpoint=self.endpoint,
                    index_name=index_name,
                    credential=self.credential
                )
                logger.info(f"✅ Connected to Azure Search index: {index_name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to connect to index {index_name}: {e}")
                self.clients[key] = None
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text using Azure OpenAI"""
        try:
            response = self.embedding_client.embeddings.create(
                input=text,
                model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []
    
    def search_products(
        self, 
        query: str, 
        top_k: int = 5,
        filter_expr: Optional[str] = None,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """Search products index with semantic/vector search"""
        return self._search_index("products", query, top_k, filter_expr, use_semantic)
    
    def search_locations(
        self, 
        query: str, 
        top_k: int = 10,
        filter_expr: Optional[str] = None,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """Search locations index with semantic/vector search"""
        return self._search_index("locations", query, top_k, filter_expr, use_semantic)
    
    def search_events(
        self, 
        query: str, 
        top_k: int = 10,
        filter_expr: Optional[str] = None,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """Search events index with semantic/vector search"""
        return self._search_index("events", query, top_k, filter_expr, use_semantic)
    
    def search_calendar(
        self, 
        query: str, 
        top_k: int = 20,
        filter_expr: Optional[str] = None,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """Search calendar index for date resolution"""
        return self._search_index("calendar", query, top_k, filter_expr, use_semantic)
    
    def search_sales_metadata(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search sales metadata to understand what sales data exists"""
        return self._search_index("sales_metadata", query, top_k, use_semantic=False)
    
    def search_weather_metadata(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search weather metadata to understand what weather data exists"""
        return self._search_index("weather_metadata", query, top_k, use_semantic=False)
    
    def search_metrics_metadata(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search metrics (WDD) metadata to understand schema"""
        return self._search_index("metrics_metadata", query, top_k, use_semantic=False)
    
    def _search_index(
        self,
        index_key: str,
        query: str,
        top_k: int = 5,
        filter_expr: Optional[str] = None,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """Generic search method for any index"""
        client = self.clients.get(index_key)
        if not client:
            logger.warning(f"Index {index_key} not available")
            return []
        
        try:
            # Use vector search for indexes with embeddings
            if use_semantic and index_key in ["products", "locations", "events", "calendar"]:
                vector = self._generate_embedding(query)
                if vector:
                    # Map index to correct vector field name
                    vector_field_map = {
                        "products": "product_embedding",
                        "locations": "location_embedding",
                        "events": "event_embedding",
                        "calendar": "vector"
                    }
                    vector_field = vector_field_map.get(index_key, "description_vector")
                    
                    vector_query = VectorizedQuery(
                        vector=vector,
                        k_nearest_neighbors=top_k,
                        fields=vector_field
                    )
                    
                    results = client.search(
                        search_text=query,
                        vector_queries=[vector_query],
                        filter=filter_expr,
                        top=top_k,
                        select=["id", "product_id", "product", "category", "dept"] if index_key == "products"
                               else ["id", "location", "market", "state", "region"] if index_key == "locations"
                               else ["id", "event", "event_date", "store_id", "event_type"] if index_key == "events"
                               else ["id", "date", "year", "month", "quarter", "season"]
                    )
                else:
                    # Fallback to text search if embedding fails
                    results = client.search(
                        search_text=query,
                        filter=filter_expr,
                        top=top_k
                    )
            else:
                # Text-only search for metadata indexes
                results = client.search(
                    search_text=query,
                    filter=filter_expr,
                    top=top_k
                )
            
            # Convert to list of dicts
            documents = []
            for result in results:
                doc = dict(result)
                # Remove internal fields and vector embeddings
                doc.pop('@search.score', None)
                doc.pop('@search.reranker_score', None)
                doc.pop('description_vector', None)
                doc.pop('product_embedding', None)
                doc.pop('location_embedding', None)
                doc.pop('event_embedding', None)
                doc.pop('vector', None)
                documents.append(doc)
            
            logger.info(f"Found {len(documents)} results in {self.INDEXES[index_key]}")
            return documents
            
        except Exception as e:
            logger.error(f"Search failed for index {index_key}: {e}")
            return []
    
    def resolve_entities(self, query: str) -> Dict[str, Any]:
        """
        Resolve all entities from a natural language query
        Returns: {
            "products": [...],
            "locations": [...],
            "events": [...],
            "dates": [...]
        }
        """
        logger.info(f"🔍 Resolving entities from query: {query}")
        
        entities = {
            "products": self.search_products(query, top_k=5),
            "locations": self.search_locations(query, top_k=10),
            "events": self.search_events(query, top_k=5),
            "dates": self.search_calendar(query, top_k=20)
        }
        
        # Log what was found
        logger.info(f"✅ Resolved: {len(entities['products'])} products, "
                   f"{len(entities['locations'])} locations, "
                   f"{len(entities['events'])} events, "
                   f"{len(entities['dates'])} dates")
        
        return entities
    
    def get_schema_context(self, query: str) -> Dict[str, Any]:
        """
        Get schema/metadata context to understand what data exists
        Returns metadata about sales, weather, and metrics datasets
        """
        logger.info(f"📊 Retrieving schema context for query: {query}")
        
        context = {
            "sales_metadata": self.search_sales_metadata(query, top_k=5),
            "weather_metadata": self.search_weather_metadata(query, top_k=3),
            "metrics_metadata": self.search_metrics_metadata(query, top_k=1)
        }
        
        return context


# Global instance
azure_search = AzureSearchService()
