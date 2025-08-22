"""
RAG System API Endpoints
FastAPI endpoints for knowledge base querying and management
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from functools import lru_cache
import logging

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
import redis
from ratelimit import limits, sleep_and_retry
import hashlib

from knowledge.rag_system import EnterpriseRAGSystem, RAGQuery, RAGResponse
from knowledge.knowledge_base import EnterpriseKnowledgeBase

logger = logging.getLogger(__name__)

# Request/Response Models
class KnowledgeQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="The question to ask")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    query_type: str = Field(default="general", description="Type of query: general, code, architecture, troubleshooting")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of context chunks")
    temperature: float = Field(default=0.3, ge=0.0, le=1.0, description="Response creativity (0-1)")
    include_sources: bool = Field(default=True, description="Include source citations")
    user_id: Optional[str] = Field(None, description="User identifier for personalization")
    session_id: Optional[str] = Field(None, description="Session identifier")

class KnowledgeResponse(BaseModel):
    answer: str
    confidence: float
    query_id: str
    response_time_ms: int
    sources: List[Dict[str, Any]]
    reasoning: Optional[str] = None
    suggested_followups: List[str] = []
    cached: bool = False

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)
    category: Optional[str] = None
    service: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    query_time_ms: int

class DocumentUpload(BaseModel):
    title: str
    content: str
    url: Optional[str] = None
    service: Optional[str] = None
    category: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScrapeRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")

class HealthCheck(BaseModel):
    status: str
    rag_system_available: bool
    knowledge_base_docs: int
    cache_status: str
    last_updated: str

# Cache and Rate Limiting
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_available = redis_client.ping()
except:
    redis_client = None
    redis_available = False

def get_cache_key(query: str, context: Dict[str, Any], query_type: str) -> str:
    """Generate cache key for query"""
    content = f"{query}:{query_type}:{sorted(context.items())}"
    return f"rag_cache:{hashlib.md5(content.encode()).hexdigest()}"

@lru_cache(maxsize=128)
def get_rag_system() -> EnterpriseRAGSystem:
    """Get RAG system instance (cached)"""
    return EnterpriseRAGSystem()

async def get_knowledge_base() -> EnterpriseKnowledgeBase:
    """Get knowledge base instance"""
    rag_system = get_rag_system()
    return rag_system.knowledge_base

# Rate limiting decorator
@sleep_and_retry
@limits(calls=100, period=60)  # 100 calls per minute
def rate_limit():
    pass

# Router
router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge & RAG"])

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Check RAG system health"""
    try:
        rag_system = get_rag_system()
        knowledge_base = await get_knowledge_base()
        
        # Check if system is available
        is_available = rag_system is not None and knowledge_base is not None
        
        # Get document count (mock for now)
        doc_count = 1000  # Would query actual KB
        
        return HealthCheck(
            status="healthy" if is_available else "degraded",
            rag_system_available=is_available,
            knowledge_base_docs=doc_count,
            cache_status="available" if redis_available else "unavailable",
            last_updated=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="RAG system unavailable")

@router.post("/query", response_model=KnowledgeResponse)
async def query_knowledge(
    query: KnowledgeQuery,
    background_tasks: BackgroundTasks,
    api_key: str = Query(None, description="API key for authentication")
):
    """Query the knowledge base using RAG"""
    rate_limit()  # Apply rate limiting
    
    start_time = time.time()
    query_id = str(uuid.uuid4())
    
    try:
        # Check cache first
        cache_key = get_cache_key(query.query, query.context, query.query_type)
        cached_result = None
        
        if redis_available and redis_client:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                cached_data = eval(cached_result)  # In production, use json.loads
                cached_data['cached'] = True
                cached_data['query_id'] = query_id
                return KnowledgeResponse(**cached_data)
        
        # Create RAG query
        rag_query = RAGQuery(
            query=query.query,
            context=query.context,
            user_id=query.user_id or "anonymous",
            session_id=query.session_id or query_id,
            query_type=query.query_type,
            max_context_chunks=query.max_results,
            temperature=query.temperature,
            include_sources=query.include_sources
        )
        
        # Process query
        rag_system = get_rag_system()
        rag_response = await rag_system.process_query(rag_query)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Create response
        response_data = rag_response.to_dict()
        response_data.update({
            'query_id': query_id,
            'response_time_ms': response_time_ms,
            'cached': False
        })
        
        response = KnowledgeResponse(**response_data)
        
        # Cache the result (expire in 1 hour)
        if redis_available and redis_client:
            background_tasks.add_task(
                redis_client.setex,
                cache_key, 
                3600,  # 1 hour
                str(response_data)
            )
        
        # Log query for analytics
        background_tasks.add_task(
            log_query_analytics,
            query_id,
            query.query,
            query.query_type,
            response_time_ms,
            response.confidence
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    search: SearchQuery,
    api_key: str = Query(None, description="API key for authentication")
):
    """Search documents in knowledge base"""
    rate_limit()
    
    start_time = time.time()
    
    try:
        knowledge_base = await get_knowledge_base()
        
        # Perform search
        results = await knowledge_base.search_documents(
            query=search.query,
            limit=search.limit,
            category_filter=search.category,
            service_filter=search.service
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'title': result.title,
                'content_preview': result.content[:300] + '...' if len(result.content) > 300 else result.content,
                'url': result.url,
                'service': result.service,
                'category': result.category,
                'relevance_score': getattr(result, 'score', 0.0),
                'last_updated': result.last_updated.isoformat() if hasattr(result, 'last_updated') else None
            })
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            results=formatted_results,
            total_found=len(results),
            query_time_ms=query_time_ms
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/documents")
async def add_document(
    document: DocumentUpload,
    background_tasks: BackgroundTasks,
    api_key: str = Query(None, description="API key for authentication")
):
    """Add a document to the knowledge base"""
    # In production, add proper authentication
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        knowledge_base = await get_knowledge_base()
        
        # Add document in background
        background_tasks.add_task(
            knowledge_base.add_document,
            title=document.title,
            content=document.content,
            url=document.url,
            service=document.service,
            category=document.category,
            metadata=document.metadata
        )
        
        return {"message": "Document queued for processing", "status": "accepted"}
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

@router.post("/scrape")
async def scrape_and_add_document(
    scrape_request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Query(None, description="API key for authentication")
):
    """Scrape a URL and add its content to the knowledge base"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        knowledge_base = await get_knowledge_base()
        
        # Scrape and add document in background
        background_tasks.add_task(
            knowledge_base.scrape_and_add_document,
            url=scrape_request.url,
        )
        
        return {"message": "Scraping and ingestion initiated", "status": "accepted"}
        
    except Exception as e:
        logger.error(f"Scraping request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping request failed: {str(e)}")

@router.get("/documents")
async def list_documents(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = Query(None),
    service: Optional[str] = Query(None)
):
    """List documents in knowledge base"""
    try:
        knowledge_base = await get_knowledge_base()
        
        # Get documents (mock implementation)
        documents = await knowledge_base.list_documents(
            limit=limit,
            offset=offset,
            category_filter=category,
            service_filter=service
        )
        
        return {
            'documents': [
                {
                    'id': doc.id,
                    'title': doc.title,
                    'service': doc.service,
                    'category': doc.category,
                    'url': doc.url,
                    'last_updated': doc.last_updated.isoformat() if hasattr(doc, 'last_updated') else None
                }
                for doc in documents
            ],
            'total': len(documents),
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document listing failed: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    api_key: str = Query(None, description="API key for authentication")
):
    """Delete a document from knowledge base"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        knowledge_base = await get_knowledge_base()
        
        # Delete document
        success = await knowledge_base.delete_document(document_id)
        
        if success:
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document deletion failed: {str(e)}")

@router.post("/reindex")
async def trigger_reindex(
    background_tasks: BackgroundTasks,
    api_key: str = Query(None, description="API key for authentication")
):
    """Trigger knowledge base reindexing"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    try:
        knowledge_base = await get_knowledge_base()
        
        # Trigger reindex in background
        background_tasks.add_task(knowledge_base.reindex_all)
        
        return {"message": "Reindexing started", "status": "accepted"}
        
    except Exception as e:
        logger.error(f"Reindex trigger failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")

@router.get("/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        knowledge_base = await get_knowledge_base()
        
        # Get statistics (mock implementation)
        stats = await knowledge_base.get_statistics()
        
        return {
            'total_documents': stats.get('document_count', 0),
            'total_chunks': stats.get('chunk_count', 0),
            'categories': stats.get('categories', {}),
            'services': stats.get('services', {}),
            'last_updated': datetime.now().isoformat(),
            'cache_hit_rate': 0.85 if redis_available else 0.0,  # Mock
            'avg_query_time_ms': 250  # Mock
        }
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

# Background task functions
async def log_query_analytics(query_id: str, query: str, query_type: str, response_time: int, confidence: float):
    """Log query analytics for monitoring"""
    try:
        analytics_data = {
            'query_id': query_id,
            'query': query[:100],  # Truncate for privacy
            'query_type': query_type,
            'response_time_ms': response_time,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        # In production, this would send to analytics service
        logger.info(f"Query analytics: {analytics_data}")
        
    except Exception as e:
        logger.error(f"Analytics logging failed: {e}")

# Fallback handlers for when RAG system is unavailable
@router.get("/fallback/query")
async def fallback_query(query: str):
    """Fallback query handler when RAG system is down"""
    return {
        'answer': 'The knowledge system is temporarily unavailable. Please try again later.',
        'confidence': 0.0,
        'sources': [],
        'fallback': True
    }