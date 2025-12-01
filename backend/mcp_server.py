"""
MCP Server for Planalytics AI
Exposes the RAG pipeline and agents as MCP tools for external AI consumption.
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from mcp.server.fastmcp import FastMCP
from agents.database_agent import DatabaseAgent
from agents.weather_agent import WeatherAgent
from agents.events_agent import EventsAgent
from agents.location_agent import LocationAgent
from agents.inventory_agent import InventoryAgent
from core.logger import logger

# Initialize agents
db_agent = DatabaseAgent()
weather_agent = WeatherAgent()
events_agent = EventsAgent()
location_agent = LocationAgent()
inventory_agent = InventoryAgent()

# Create MCP Server
mcp = FastMCP("Planalytics AI")

@mcp.tool()
def query_supply_chain_data(query: str) -> str:
    """
    Query the Planalytics Supply Chain Database using natural language.
    Use this for questions about sales, inventory, products, or general data analysis.
    
    Args:
        query: The natural language question (e.g., "How many QSR products do we have?")
    """
    try:
        logger.info(f"MCP Tool Call: query_supply_chain_data('{query}')")
        result = db_agent.query_database(query)
        return str(result.get("answer", "No answer generated."))
    except Exception as e:
        return f"Error executing query: {str(e)}"

@mcp.tool()
def analyze_weather_impact(location_id: str, days: int = 30) -> str:
    """
    Analyze weather impact on supply chain for a specific location.
    
    Args:
        location_id: The Store ID (e.g., 'ST8500')
        days: Number of days to analyze (default: 30)
    """
    try:
        logger.info(f"MCP Tool Call: analyze_weather_impact('{location_id}')")
        result = weather_agent.analyze(f"Analyze weather for {location_id}", location_id)
        return str(result)
    except Exception as e:
        return f"Error analyzing weather: {str(e)}"

@mcp.tool()
def analyze_event_impact(query: str, location_id: str = None) -> str:
    """
    Analyze the impact of events (holidays, festivals) on demand.
    
    Args:
        query: Description of the event or analysis needed
        location_id: Optional Store ID to focus on
    """
    try:
        logger.info(f"MCP Tool Call: analyze_event_impact('{query}')")
        result = events_agent.analyze(query, location_id)
        return str(result)
    except Exception as e:
        return f"Error analyzing events: {str(e)}"

@mcp.tool()
def get_inventory_recommendations(product_id: str, location_id: str) -> str:
    """
    Get inventory optimization recommendations for a product at a location.
    
    Args:
        product_id: The Product ID
        location_id: The Store ID
    """
    try:
        logger.info(f"MCP Tool Call: get_inventory_recommendations('{product_id}', '{location_id}')")
        result = inventory_agent.analyze(f"Check inventory for {product_id}", product_id, location_id)
        return str(result)
    except Exception as e:
        return f"Error analyzing inventory: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
