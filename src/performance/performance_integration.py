"""
Performance Integration Module
Integrates cache manager and vector search with existing system
Epic 7: Performance Optimization Integration
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from functools import wraps
import logging

from .cache_manager import (
    CacheManager,
    CachedFunction,
    QueryOptimizer,
    ConnectionPoolManager,
    ResponseTimeMonitor,
    cache_manager,
    query_optimizer,
    connection_pool_manager,
    response_monitor
)

from .vector_search_optimizer import (
    VectorSearchOptimizer,
    RAGOptimizer,
    BatchProcessor,
    vector_optimizer,
    rag_optimizer,
    batch_processor
)

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Central performance optimization orchestrator"""
    
    def __init__(self):
        self.cache_manager = cache_manager
        self.query_optimizer = query_optimizer
        self.connection_pool_manager = connection_pool_manager
        self.response_monitor = response_monitor
        self.vector_optimizer = vector_optimizer
        self.rag_optimizer = rag_optimizer
        self.batch_processor = batch_processor
        
        self.initialized = False
    
    async def initialize(self):
        """Initialize all performance components"""
        if self.initialized:
            return
        
        try:
            # Initialize cache manager
            await self.cache_manager.initialize()
            logger.info("Cache manager initialized")
            
            # Initialize vector search if configured
            if os.getenv('ENABLE_VECTOR_SEARCH', 'true').lower() == 'true':
                # Load existing index if available
                index_path = os.getenv('VECTOR_INDEX_PATH', '/tmp/vector_index')
                if os.path.exists(f"{index_path}.index"):
                    self.vector_optimizer.load_index(index_path)
                    logger.info("Vector index loaded")
                else:
                    logger.info("Vector index not found, starting fresh")
            
            self.initialized = True
            logger.info("Performance optimizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize performance optimizer: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown performance components gracefully"""
        try:
            # Save vector index
            if os.getenv('ENABLE_VECTOR_SEARCH', 'true').lower() == 'true':
                index_path = os.getenv('VECTOR_INDEX_PATH', '/tmp/vector_index')
                self.vector_optimizer.save_index(index_path)
                logger.info("Vector index saved")
            
            # Close cache connections
            await self.cache_manager.close()
            logger.info("Cache manager closed")
            
            self.initialized = False
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

class AgentPerformanceWrapper:
    """Wrapper to add performance optimization to agents"""
    
    def __init__(self, agent, performance_optimizer: PerformanceOptimizer):
        self.agent = agent
        self.optimizer = performance_optimizer
    
    async def analyze(self, *args, **kwargs):
        """Wrapped analyze method with caching and monitoring"""
        # Start monitoring
        start_time = asyncio.get_event_loop().time()
        
        # Generate cache key
        cache_key = self.optimizer.cache_manager.generate_cache_key(
            f"agent:{self.agent.__class__.__name__}:analyze",
            kwargs
        )
        
        # Check cache
        cached_result = await self.optimizer.cache_manager.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for {self.agent.__class__.__name__}")
            return cached_result
        
        # Execute analysis
        try:
            result = await self.agent.analyze(*args, **kwargs)
            
            # Cache result
            await self.optimizer.cache_manager.set(
                cache_key,
                result,
                ttl=600  # 10 minutes
            )
            
            # Track response time
            duration = asyncio.get_event_loop().time() - start_time
            await self.optimizer.response_monitor.track_response(
                f"agent_{self.agent.__class__.__name__}_analyze",
                duration,
                {'args': str(args)[:100], 'kwargs': str(kwargs)[:100]}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in agent analysis: {e}")
            raise

def optimize_agent(agent_class):
    """Decorator to optimize agent performance"""
    original_init = agent_class.__init__
    
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._performance_optimizer = PerformanceOptimizer()
    
    agent_class.__init__ = new_init
    
    # Wrap key methods
    for method_name in ['analyze', 'process', 'execute']:
        if hasattr(agent_class, method_name):
            original_method = getattr(agent_class, method_name)
            
            @wraps(original_method)
            async def wrapped_method(self, *args, **kwargs):
                if not self._performance_optimizer.initialized:
                    await self._performance_optimizer.initialize()
                
                wrapper = AgentPerformanceWrapper(self, self._performance_optimizer)
                return await wrapper.analyze(*args, **kwargs)
            
            setattr(agent_class, method_name, wrapped_method)
    
    return agent_class

class FastAPIPerformanceMiddleware:
    """Performance middleware for FastAPI applications"""
    
    def __init__(self, app):
        self.app = app
        self.optimizer = PerformanceOptimizer()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Track request
            path = scope["path"]
            start_time = asyncio.get_event_loop().time()
            
            # Process request
            await self.app(scope, receive, send)
            
            # Track response time
            duration = asyncio.get_event_loop().time() - start_time
            await self.optimizer.response_monitor.track_response(
                f"http_{path}",
                duration,
                {"method": scope["method"], "path": path}
            )
        else:
            await self.app(scope, receive, send)

def setup_performance_optimization(app):
    """Setup performance optimization for FastAPI app"""
    from fastapi import FastAPI
    
    # Add middleware
    app.add_middleware(FastAPIPerformanceMiddleware)
    
    # Add performance endpoints
    @app.get("/api/v1/performance/stats")
    async def get_performance_stats():
        """Get performance statistics"""
        optimizer = PerformanceOptimizer()
        
        return {
            "cache": optimizer.cache_manager.get_cache_stats(),
            "response_times": optimizer.response_monitor.get_performance_summary(),
            "connection_pools": optimizer.connection_pool_manager.get_pool_stats(),
            "vector_search": optimizer.vector_optimizer.get_performance_stats(),
            "rag": optimizer.rag_optimizer.get_performance_stats()
        }
    
    @app.post("/api/v1/performance/optimize")
    async def trigger_optimization():
        """Trigger performance optimization"""
        optimizer = PerformanceOptimizer()
        
        # Optimize vector index
        optimizer.vector_optimizer.optimize_index()
        
        # Clear old cache entries
        await optimizer.cache_manager.clear_pattern("*:old:*")
        
        return {"status": "optimization triggered"}
    
    @app.post("/api/v1/performance/cache/clear")
    async def clear_cache(pattern: str = "*"):
        """Clear cache by pattern"""
        optimizer = PerformanceOptimizer()
        count = await optimizer.cache_manager.clear_pattern(pattern)
        
        return {"cleared": count}
    
    # Add startup/shutdown events
    @app.on_event("startup")
    async def startup_performance():
        optimizer = PerformanceOptimizer()
        await optimizer.initialize()
    
    @app.on_event("shutdown")
    async def shutdown_performance():
        optimizer = PerformanceOptimizer()
        await optimizer.shutdown()
    
    return app

# Utility functions for agent integration
async def cached_agent_call(
    agent_name: str,
    method: str,
    *args,
    ttl: int = 300,
    **kwargs
) -> Any:
    """Make a cached call to an agent method"""
    optimizer = PerformanceOptimizer()
    
    if not optimizer.initialized:
        await optimizer.initialize()
    
    # Generate cache key
    cache_key = optimizer.cache_manager.generate_cache_key(
        f"agent:{agent_name}:{method}",
        {"args": str(args), "kwargs": str(kwargs)}
    )
    
    # Check cache
    result = await optimizer.cache_manager.get(cache_key)
    if result is not None:
        return result
    
    # Import and call agent
    module = __import__(f"agents.{agent_name}", fromlist=[agent_name.capitalize() + "Agent"])
    agent_class = getattr(module, agent_name.capitalize() + "Agent")
    agent = agent_class()
    
    # Call method
    method_func = getattr(agent, method)
    result = await method_func(*args, **kwargs)
    
    # Cache result
    await optimizer.cache_manager.set(cache_key, result, ttl)
    
    return result

async def optimized_rag_query(
    question: str,
    k: int = 5,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Execute optimized RAG query"""
    optimizer = PerformanceOptimizer()
    
    if not optimizer.initialized:
        await optimizer.initialize()
    
    if use_cache:
        # Check cache first
        cache_key = optimizer.cache_manager.generate_cache_key(
            "rag:query",
            {"question": question, "k": k}
        )
        
        cached = await optimizer.cache_manager.get(cache_key)
        if cached:
            return cached
    
    # Execute RAG query
    result = await optimizer.rag_optimizer.query(question, k)
    
    if use_cache:
        # Cache result
        await optimizer.cache_manager.set(cache_key, result, ttl=1800)  # 30 minutes
    
    return result

async def batch_embed_documents(
    documents: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Batch embed documents for efficient processing"""
    optimizer = PerformanceOptimizer()
    
    if not optimizer.initialized:
        await optimizer.initialize()
    
    # Extract texts
    texts = [doc.get('content', '') for doc in documents]
    
    # Generate embeddings in batches
    embeddings = await optimizer.batch_processor.process_batch_embeddings(texts)
    
    # Add embeddings to documents
    for i, doc in enumerate(documents):
        doc['embedding'] = embeddings[i]
    
    return documents

# Configuration helpers
def configure_performance(
    redis_url: Optional[str] = None,
    cache_ttl: Optional[int] = None,
    enable_vector_search: Optional[bool] = None,
    vector_dimension: Optional[int] = None
):
    """Configure performance optimization settings"""
    if redis_url:
        os.environ['REDIS_URL'] = redis_url
    
    if cache_ttl:
        os.environ['CACHE_TTL'] = str(cache_ttl)
    
    if enable_vector_search is not None:
        os.environ['ENABLE_VECTOR_SEARCH'] = str(enable_vector_search).lower()
    
    if vector_dimension:
        os.environ['VECTOR_DIMENSION'] = str(vector_dimension)
    
    logger.info("Performance configuration updated")

# Export main components
__all__ = [
    'PerformanceOptimizer',
    'AgentPerformanceWrapper',
    'optimize_agent',
    'FastAPIPerformanceMiddleware',
    'setup_performance_optimization',
    'cached_agent_call',
    'optimized_rag_query',
    'batch_embed_documents',
    'configure_performance'
]