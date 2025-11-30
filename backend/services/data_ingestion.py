from typing import List, Dict, Any
from datetime import datetime
from database.postgres_db import get_db, SalesData, InventoryData, WeatherData, EventsData  # ✅ Changed
from database.azure_index import azure_search
from core.logger import logger
import uuid


class DataIngestionService:
    """Service for ingesting and processing supply chain data"""
    
    def ingest_sales_data(self, records: List[Dict[str, Any]]) -> int:
        """Ingest sales records into MySQL and Azure Search"""
        try:
            with get_db() as db:
                for record in records:
                    sales = SalesData(
                        product_id=record["product_id"],
                        location_id=record["location_id"],
                        quantity=record["quantity"],
                        revenue=record["revenue"],
                        timestamp=datetime.fromisoformat(record["timestamp"])
                    )
                    db.add(sales)
            
            # Index into Azure Search (sales index)
            search_docs = []
            for record in records:
                doc = {
                    "id": str(uuid.uuid4()),
                    "product_id": record["product_id"],
                    "location_id": record["location_id"],
                    "quantity": record["quantity"],
                    "revenue": record["revenue"],
                    "timestamp": record["timestamp"],
                    "content": f"Sales: Product {record['product_id']} at Location {record['location_id']}, Quantity: {record['quantity']}, Revenue: ${record['revenue']}",
                    "metadata": str(record)
                }
                search_docs.append(doc)
            
            azure_search.index_documents(search_docs, index_type="sales")
            logger.info(f"Ingested {len(records)} sales records")
            return len(records)
        except Exception as e:
            logger.error(f"Sales data ingestion failed: {e}")
            raise
    
    def ingest_inventory_data(self, records: List[Dict[str, Any]]) -> int:
        """Ingest inventory records into MySQL and Azure Search"""
        try:
            with get_db() as db:
                for record in records:
                    inventory = InventoryData(
                        product_id=record["product_id"],
                        location_id=record["location_id"],
                        stock_level=record["stock_level"],
                        reorder_point=record["reorder_point"],
                        timestamp=datetime.fromisoformat(record["timestamp"])
                    )
                    db.add(inventory)
            
            # Index into Azure Search (inventory index)
            search_docs = []
            for record in records:
                doc = {
                    "id": str(uuid.uuid4()),
                    "product_id": record["product_id"],
                    "location_id": record["location_id"],
                    "stock_level": record["stock_level"],
                    "reorder_point": record["reorder_point"],
                    "timestamp": record["timestamp"],
                    "content": f"Inventory: Product {record['product_id']} at Location {record['location_id']}, Stock: {record['stock_level']}, Reorder Point: {record['reorder_point']}",
                    "metadata": str(record)
                }
                search_docs.append(doc)
            
            azure_search.index_documents(search_docs, index_type="inventory")
            logger.info(f"Ingested {len(records)} inventory records")
            return len(records)
        except Exception as e:
            logger.error(f"Inventory data ingestion failed: {e}")
            raise
    
    def ingest_weather_data(self, records: List[Dict[str, Any]]) -> int:
        """Ingest weather data into MySQL and Azure Search"""
        try:
            with get_db() as db:
                for record in records:
                    weather = WeatherData(
                        location_id=record["location_id"],
                        temperature=record["temperature"],
                        precipitation=record["precipitation"],
                        conditions=record["conditions"],
                        timestamp=datetime.fromisoformat(record["timestamp"])
                    )
                    db.add(weather)
            
            # Index into Azure Search (weather index)
            search_docs = []
            for record in records:
                doc = {
                    "id": str(uuid.uuid4()),
                    "location_id": record["location_id"],
                    "temperature": record["temperature"],
                    "precipitation": record["precipitation"],
                    "conditions": record["conditions"],
                    "timestamp": record["timestamp"],
                    "content": f"Weather at Location {record['location_id']}: {record['conditions']}, Temp: {record['temperature']}°F, Precipitation: {record['precipitation']}in",
                    "metadata": str(record)
                }
                search_docs.append(doc)
            
            azure_search.index_documents(search_docs, index_type="weather")
            logger.info(f"Ingested {len(records)} weather records")
            return len(records)
        except Exception as e:
            logger.error(f"Weather data ingestion failed: {e}")
            raise
    
    def ingest_events_data(self, records: List[Dict[str, Any]]) -> int:
        """Ingest events data into MySQL and Azure Search"""
        try:
            with get_db() as db:
                for record in records:
                    event = EventsData(
                        event_name=record["event_name"],
                        location_id=record["location_id"],
                        event_type=record.get("event_type"),
                        start_date=datetime.fromisoformat(record["start_date"]),
                        end_date=datetime.fromisoformat(record["end_date"]) if record.get("end_date") else None
                    )
                    db.add(event)
            
            # Index into Azure Search (events index)
            search_docs = []
            for record in records:
                doc = {
                    "id": str(uuid.uuid4()),
                    "event_name": record["event_name"],
                    "location_id": record["location_id"],
                    "event_type": record.get("event_type", ""),
                    "start_date": record["start_date"],
                    "end_date": record.get("end_date", ""),
                    "content": f"Event: {record['event_name']} ({record.get('event_type', 'Unknown')}) at Location {record['location_id']}, Date: {record['start_date']}",
                    "metadata": str(record)
                }
                search_docs.append(doc)
            
            azure_search.index_documents(search_docs, index_type="events")
            logger.info(f"Ingested {len(records)} event records")
            return len(records)
        except Exception as e:
            logger.error(f"Events data ingestion failed: {e}")
            raise
    
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
