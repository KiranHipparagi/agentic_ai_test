from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from agents.orchestrator_agent import enhanced_orchestrator 
from core.logger import logger

router = APIRouter(prefix="/api/v1/chat", tags=["chatbot"])


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    product_id: Optional[str] = None
    location_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    query: str
    answer: str
    sql_query: Optional[str] = None
    data_source: str
    row_count: int = 0
    raw_data: Optional[list] = None
    visualization: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None 
    status: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chatbot endpoint with enhanced chart generation"""
    try:
        logger.info(f"💬 Chat request: {request.query[:100]}...")
        
        # Build context
        context = {
            "product_id": request.product_id or "default",
            "location_id": request.location_id or "default",
            "session_id": request.session_id
        }
        
        # Use Enhanced Orchestrator
        result = await enhanced_orchestrator.orchestrate(request.query, context)
        
        # Debug logging
        visualization = result.get("visualization")
        if visualization:
            logger.info(f"✅ Chart generated: type={visualization.get('chart_type')}, ready={visualization.get('ready')}, points={visualization.get('data_points')}")
            if not visualization.get('ready'):
                logger.warning(f"⚠️ Chart not ready: {visualization.get('message')}")
        else:
            logger.warning("⚠️ No visualization in response")
        
        return ChatResponse(
            query=result.get("query", request.query),
            answer=result.get("answer", "I couldn't process your request."),
            sql_query=result.get("sql_query"),
            data_source=result.get("data_source", "conversation"),
            row_count=result.get("row_count", 0),
            raw_data=result.get("raw_data"),
            visualization=visualization,
            intent=result.get("intent"),
            status=result.get("status", "success")
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        return ChatResponse(
            query=request.query,
            answer=f"An error occurred: {str(e)}",
            data_source="error",
            status="error"
        )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Retrieve chat history"""
    return {
        "session_id": session_id,
        "message": "Chat history feature coming soon with session management"
    }


@router.get("/stats")
async def get_stats():
    """Get orchestrator statistics"""
    return {
        "message": "Statistics available",
        "orchestrator": "Enhanced LangGraph Orchestrator",
        "features": ["Intent Detection", "Smart Chart Generation", "Natural Conversations"]
    }
