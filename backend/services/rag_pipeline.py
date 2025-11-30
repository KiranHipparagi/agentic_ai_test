from typing import List, Dict, Any
from openai import AzureOpenAI
from database.azure_index import azure_search
from core.config import settings
from core.logger import logger


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for context-aware responses"""
    
    def __init__(self):
        # LLM client for chat completions
        self.llm_client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.OPENAI_ENDPOINT
        )
        # Embedding client for vector generation
        self.embedding_client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.search = azure_search
    
    def retrieve_context(
        self, 
        query: str, 
        top_k: int = 5, 
        index_type: str = "sales",
        filter_expr: str = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from specific Azure Search index"""
        try:
            results = self.search.vector_search(query, top_k=top_k, index_type=index_type, filter_expr=filter_expr)
            logger.info(f"Retrieved {len(results)} context documents from '{index_type}' index")
            return results
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return []
    
    def retrieve_context_multi_index(self, query: str, top_k: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve relevant documents from all indexes"""
        try:
            all_results = self.search.search_all_indexes(query, top_k=top_k)
            logger.info(f"Retrieved context from {len(all_results)} indexes")
            return all_results
        except Exception as e:
            logger.error(f"Multi-index context retrieval failed: {e}")
            return {}
    
    def generate_response(self, query: str, context: List[Dict[str, Any]], system_prompt: str = None) -> str:
        """Generate AI response with retrieved context"""
        try:
            # Build context string
            context_text = "\n\n".join([
                f"[Source {i+1}]: {doc.get('content', str(doc))}" 
                for i, doc in enumerate(context)
            ]) if context else "No additional context available."
            
            default_system = """You are an expert supply chain analyst with deep knowledge of weather impacts, 
            event-driven demand, inventory optimization, and location-based analysis.
            Use the provided context to answer questions accurately and provide actionable insights.
            If information is not in the context, use your expertise but clearly state assumptions."""
            
            messages = [
                {"role": "system", "content": system_prompt or default_system},
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
            ]
            
            # Use LLM client for chat completions
            response = self.llm_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,  # Use the main chat model
                messages=messages,
                temperature=0.4,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return f"I apologize, but I encountered an error generating a response: {str(e)}"
    
    def process_query(self, query: str, index_type: str = "sales", filter_expr: str = None) -> Dict[str, Any]:
        """End-to-end RAG pipeline execution on specific index"""
        try:
            # Retrieve relevant context
            context = self.retrieve_context(query, index_type=index_type, filter_expr=filter_expr)
            
            # Generate response
            answer = self.generate_response(query, context)
            
            return {
                "query": query,
                "answer": answer,
                "index_type": index_type,
                "sources": [{"id": doc.get("id", "unknown"), "index": index_type} for doc in context],
                "status": "success"
            }
        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}", exc_info=True)
            return {"error": str(e), "status": "failed", "answer": "I encountered an error processing your query."}
    
    def process_query_multi_index(self, query: str) -> Dict[str, Any]:
        """RAG pipeline with multi-index search"""
        try:
            # Retrieve from all indexes
            all_context = self.retrieve_context_multi_index(query)
            
            # Flatten context
            combined_context = []
            sources = []
            for index_type, docs in all_context.items():
                for doc in docs:
                    doc["source_index"] = index_type
                    combined_context.append(doc)
                    sources.append({"id": doc.get("id", "unknown"), "index": index_type})
            
            # Generate response
            answer = self.generate_response(query, combined_context)
            
            return {
                "query": query,
                "answer": answer,
                "sources": sources,
                "sources_by_index": {k: len(v) for k, v in all_context.items()},
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Multi-index RAG pipeline failed: {e}", exc_info=True)
            return {"error": str(e), "status": "failed", "answer": "I encountered an error processing your query."}


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()
