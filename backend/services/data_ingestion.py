from typing import List, Dict, Any
from datetime import datetime
from database.postgres_db import get_db, Metrics, WeatherData, EventsData
from database.azure_search import azure_search
from core.logger import logger
import uuid


class DataIngestionService:
    """Service for data ingestion - NOTE: All data is pre-loaded in planalytics_database"""
    
    def ingest_sales_data(self, records: List[Dict[str, Any]]) -> int:
        """Data already loaded in PostgreSQL - this method is deprecated"""
        logger.info("Sales data is already loaded in metrics table")
        return 0
    
    def ingest_inventory_data(self, records: List[Dict[str, Any]]) -> int:
        """Inventory data not available - metrics table contains sales data only"""
        logger.info("Inventory table does not exist - use metrics table for sales data")
        return 0
    
    def ingest_weather_data(self, records: List[Dict[str, Any]]) -> int:
        """Weather data already loaded in PostgreSQL"""
        logger.info("Weather data is already loaded in weekly_weather table")
        return 0
    
    def ingest_events_data(self, records: List[Dict[str, Any]]) -> int:
        """Events data already loaded in PostgreSQL"""
        logger.info("Events data is already loaded in events table")
        return 0
    
    def index_documents_for_search(self, documents: List[Dict[str, Any]], index_type: str = "sales") -> None:
        """Index documents into specific Azure AI Search index"""
        try:
            # Add IDs if not present
            for doc in documents:
                if "id" not in doc:
                    doc["id"] = str(uuid.uuid4())
            
            azure_search.index_documents(documents, index_type=index_type)
            logger.info(f"Indexed {len(documents)} documents into '{index_type}' index")
        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            raise


# Global ingestion service
data_ingestion = DataIngestionService()
