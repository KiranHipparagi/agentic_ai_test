from .weather_agent import WeatherAgent
from .events_agent import EventsAgent
from .location_agent import LocationAgent
from .inventory_agent import InventoryAgent
from .database_agent import DatabaseAgent
from typing import Dict, Any, List
from core.logger import logger


class AgentController:
    """Main orchestrator for multi-agent system"""
    
    def __init__(self):
        self.weather_agent = WeatherAgent()
        self.events_agent = EventsAgent()
        self.location_agent = LocationAgent()
        self.inventory_agent = InventoryAgent()
        self.database_agent = DatabaseAgent()
        logger.info("Agent controller initialized with 5 specialized agents")
    
    async def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate multi-agent response with real database queries"""
        try:
            product_id = context.get("product_id", "")
            location_id = context.get("location_id", "")
            
            # ALWAYS query database first for real data
            db_result = self.database_agent.query_database(query, context)
            
            # Generate AI analysis from real data
            if db_result.get("status") == "success" and db_result.get("data"):
                answer = self.database_agent.analyze_results(
                    query, 
                    db_result["data"], 
                    db_result["sql_query"]
                )
            else:
                # Fallback to specialized agents if database query fails
                active_agents = self._select_agents(query)
                results = {}
                
                if "events" in active_agents:
                    results["events"] = self.events_agent.analyze(query, location_id)
                if "weather" in active_agents:
                    results["weather"] = self.weather_agent.analyze(query, location_id)
                if "inventory" in active_agents:
                    results["inventory"] = self.inventory_agent.analyze(query, product_id, location_id)
                
                answer = self._compile_agent_answers(results)
            
            return {
                "query": query,
                "answer": answer,
                "sql_query": db_result.get("sql_query"),
                "data_source": "mysql_database",
                "row_count": db_result.get("row_count", 0),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Agent orchestration failed: {e}")
            return {
                "error": str(e), 
                "status": "failed",
                "answer": "I encountered an error processing your query. Please try rephrasing."
            }
    
    def _select_agents(self, query: str) -> List[str]:
        """Determine which agents to activate"""
        query_lower = query.lower()
        agents = []
        
        if any(word in query_lower for word in ["weather", "temperature", "rain", "climate", "hot", "cold"]):
            agents.append("weather")
        if any(word in query_lower for word in ["event", "holiday", "festival"]):
            agents.append("events")
        if any(word in query_lower for word in ["location", "region", "area", "store"]):
            agents.append("location")
        if any(word in query_lower for word in ["inventory", "stock", "demand", "forecast", "dairy", "product", "sales"]):
            agents.append("inventory")
        
        return agents or ["events", "inventory"]
    
    def _compile_agent_answers(self, results: Dict[str, Any]) -> str:
        """Compile answers from multiple agents"""
        answers = []
        for agent_name, result in results.items():
            if "answer" in result:
                answers.append(result["answer"])
            elif "analysis" in result:
                answers.append(result["analysis"])
        
        return "\n\n".join(answers) if answers else "I couldn't find relevant information. Please try rephrasing your question."


# Global controller instance
agent_controller = AgentController()
