"""
Performance Optimization Module
Epic 7: Performance Optimization
"""

from .cache_manager import (
    CacheManager,
    CachedFunction,
    QueryOptimizer,
    ConnectionPoolManager,
    ResponseTimeMonitor,
    cache_manager,
    query_optimizer,
    connection_pool_manager,
    response_monitor,
    cached
)

from .vector_search_optimizer import (
    VectorSearchOptimizer,
    RAGOptimizer,
    BatchProcessor,
    VectorDocument,
    vector_optimizer,
    rag_optimizer,
    batch_processor
)

from .performance_integration import (
    PerformanceOptimizer,
    AgentPerformanceWrapper,
    optimize_agent,
    FastAPIPerformanceMiddleware,
    setup_performance_optimization,
    cached_agent_call,
    optimized_rag_query,
    batch_embed_documents,
    configure_performance
)

from .benchmark import (
    PerformanceBenchmark,
    BenchmarkResult,
    CacheBenchmark,
    VectorSearchBenchmark,
    EndToEndBenchmark,
    run_full_benchmark_suite
)

__all__ = [
    # Cache Manager
    'CacheManager',
    'CachedFunction',
    'QueryOptimizer',
    'ConnectionPoolManager',
    'ResponseTimeMonitor',
    'cache_manager',
    'query_optimizer',
    'connection_pool_manager',
    'response_monitor',
    'cached',
    
    # Vector Search
    'VectorSearchOptimizer',
    'RAGOptimizer',
    'BatchProcessor',
    'VectorDocument',
    'vector_optimizer',
    'rag_optimizer',
    'batch_processor',
    
    # Performance Integration
    'PerformanceOptimizer',
    'AgentPerformanceWrapper',
    'optimize_agent',
    'FastAPIPerformanceMiddleware',
    'setup_performance_optimization',
    'cached_agent_call',
    'optimized_rag_query',
    'batch_embed_documents',
    'configure_performance',
    
    # Benchmarking
    'PerformanceBenchmark',
    'BenchmarkResult',
    'CacheBenchmark',
    'VectorSearchBenchmark',
    'EndToEndBenchmark',
    'run_full_benchmark_suite'
]

# Package version
__version__ = '1.0.0'