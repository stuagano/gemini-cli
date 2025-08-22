"""
Performance Optimization - Cache Manager
Implements efficient caching strategy for agent responses and knowledge retrieval
Epic 7: Story 7.1 - Agent Response Optimization
"""

import asyncio
import hashlib
import json
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from functools import wraps
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """High-performance cache manager with multiple strategies"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 300,
        max_connections: int = 50,
        enable_compression: bool = True
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.enable_compression = enable_compression
        
        # Connection pooling for performance
        self.pool = ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            decode_responses=False
        )
        self.redis_client = None
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'avg_response_time': 0
        }
        
        # Cache layers
        self.memory_cache = {}  # L1 cache - in-memory
        self.memory_cache_size = 100  # Max items in memory
        
    async def initialize(self):
        """Initialize cache connections"""
        self.redis_client = redis.Redis(connection_pool=self.pool)
        await self.redis_client.ping()
        logger.info("Cache manager initialized")
    
    async def close(self):
        """Close cache connections"""
        if self.redis_client:
            await self.redis_client.close()
        await self.pool.disconnect()
    
    def generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate deterministic cache key from parameters"""
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{param_hash}"
    
    async def get(
        self,
        key: str,
        check_memory: bool = True
    ) -> Optional[Any]:
        """Get value from cache with multi-level lookup"""
        start_time = time.time()
        
        try:
            # L1: Check memory cache first
            if check_memory and key in self.memory_cache:
                self.stats['hits'] += 1
                self._update_response_time(time.time() - start_time)
                return self.memory_cache[key]['value']
            
            # L2: Check Redis cache
            value = await self.redis_client.get(key)
            
            if value:
                self.stats['hits'] += 1
                
                # Deserialize
                if self.enable_compression:
                    import zlib
                    value = zlib.decompress(value)
                
                deserialized = pickle.loads(value)
                
                # Promote to memory cache
                if check_memory:
                    self._add_to_memory_cache(key, deserialized)
                
                self._update_response_time(time.time() - start_time)
                return deserialized
            
            self.stats['misses'] += 1
            self._update_response_time(time.time() - start_time)
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.stats['errors'] += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        add_to_memory: bool = True
    ) -> bool:
        """Set value in cache with multi-level storage"""
        try:
            ttl = ttl or self.default_ttl
            
            # Serialize value
            serialized = pickle.dumps(value)
            
            # Compress if enabled
            if self.enable_compression:
                import zlib
                serialized = zlib.compress(serialized)
            
            # L2: Store in Redis
            await self.redis_client.setex(key, ttl, serialized)
            
            # L1: Store in memory cache
            if add_to_memory:
                self._add_to_memory_cache(key, value, ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from all cache levels"""
        try:
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Remove from Redis
            await self.redis_client.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        count = 0
        cursor = 0
        
        while True:
            cursor, keys = await self.redis_client.scan(
                cursor, match=pattern, count=100
            )
            
            if keys:
                await self.redis_client.delete(*keys)
                count += len(keys)
                
                # Also clear from memory cache
                for key in list(self.memory_cache.keys()):
                    if pattern.replace('*', '') in key:
                        del self.memory_cache[key]
            
            if cursor == 0:
                break
        
        return count
    
    def _add_to_memory_cache(self, key: str, value: Any, ttl: int = None):
        """Add item to memory cache with LRU eviction"""
        # Evict oldest if at capacity
        if len(self.memory_cache) >= self.memory_cache_size:
            oldest = min(self.memory_cache.items(), 
                        key=lambda x: x[1]['accessed'])
            del self.memory_cache[oldest[0]]
        
        self.memory_cache[key] = {
            'value': value,
            'accessed': time.time(),
            'expires': time.time() + (ttl or self.default_ttl)
        }
    
    def _update_response_time(self, duration: float):
        """Update average response time statistics"""
        current_avg = self.stats['avg_response_time']
        total_requests = self.stats['hits'] + self.stats['misses']
        
        if total_requests > 0:
            self.stats['avg_response_time'] = (
                (current_avg * (total_requests - 1) + duration) / total_requests
            )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'errors': self.stats['errors'],
            'hit_rate': f"{hit_rate:.2f}%",
            'avg_response_time_ms': self.stats['avg_response_time'] * 1000,
            'memory_cache_size': len(self.memory_cache),
            'total_requests': total
        }

class CachedFunction:
    """Decorator for caching function results"""
    
    def __init__(
        self,
        cache_manager: CacheManager,
        prefix: str,
        ttl: int = 300,
        key_params: Optional[List[str]] = None
    ):
        self.cache_manager = cache_manager
        self.prefix = prefix
        self.ttl = ttl
        self.key_params = key_params
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if self.key_params:
                cache_params = {k: kwargs.get(k) for k in self.key_params}
            else:
                # Use all kwargs for cache key
                cache_params = kwargs
            
            cache_key = self.cache_manager.generate_cache_key(
                self.prefix, cache_params
            )
            
            # Try to get from cache
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing...")
            result = await func(*args, **kwargs)
            
            # Cache the result
            await self.cache_manager.set(cache_key, result, self.ttl)
            
            return result
        
        return wrapper

class QueryOptimizer:
    """Optimize database and API queries"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.query_cache = {}
        self.prepared_statements = {}
    
    async def optimize_query(self, query: str, params: Dict[str, Any]) -> str:
        """Optimize SQL or API query"""
        # Generate query hash
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # Check if we have an optimized version
        cache_key = f"optimized_query:{query_hash}"
        optimized = await self.cache_manager.get(cache_key)
        
        if optimized:
            return optimized
        
        # Apply optimizations
        optimized = self._apply_optimizations(query)
        
        # Cache optimized query
        await self.cache_manager.set(cache_key, optimized, ttl=3600)
        
        return optimized
    
    def _apply_optimizations(self, query: str) -> str:
        """Apply query optimization rules"""
        optimizations = [
            # Add indexes hints
            (r'SELECT \* FROM (\w+) WHERE', r'SELECT /*+ INDEX(\1) */ * FROM \1 WHERE'),
            # Limit subqueries
            (r'IN \(SELECT', r'IN (SELECT /*+ FIRST_ROWS(10) */'),
            # Use prepared statements for common patterns
            (r'WHERE id = \d+', r'WHERE id = ?'),
        ]
        
        optimized = query
        for pattern, replacement in optimizations:
            import re
            optimized = re.sub(pattern, replacement, optimized)
        
        return optimized

class ConnectionPoolManager:
    """Manage connection pools for various services"""
    
    def __init__(self):
        self.pools = {}
        self.pool_stats = {}
    
    async def get_connection(self, service: str) -> Any:
        """Get connection from pool"""
        if service not in self.pools:
            self.pools[service] = await self._create_pool(service)
        
        pool = self.pools[service]
        
        # Track pool statistics
        if service not in self.pool_stats:
            self.pool_stats[service] = {
                'connections': 0,
                'active': 0,
                'idle': 0
            }
        
        self.pool_stats[service]['connections'] += 1
        self.pool_stats[service]['active'] += 1
        
        return await pool.acquire()
    
    async def release_connection(self, service: str, connection: Any):
        """Release connection back to pool"""
        if service in self.pools:
            pool = self.pools[service]
            await pool.release(connection)
            
            self.pool_stats[service]['active'] -= 1
            self.pool_stats[service]['idle'] += 1
    
    async def _create_pool(self, service: str) -> Any:
        """Create connection pool for service"""
        if service == 'postgres':
            import asyncpg
            return await asyncpg.create_pool(
                host='localhost',
                database='gemini',
                user='postgres',
                min_size=5,
                max_size=20
            )
        elif service == 'redis':
            return ConnectionPool.from_url(
                'redis://localhost:6379',
                max_connections=50
            )
        else:
            raise ValueError(f"Unknown service: {service}")
    
    def get_pool_stats(self) -> Dict[str, Dict[str, int]]:
        """Get connection pool statistics"""
        return self.pool_stats

class ResponseTimeMonitor:
    """Monitor and optimize response times"""
    
    def __init__(self):
        self.response_times = {}
        self.thresholds = {
            'fast': 0.1,     # 100ms
            'normal': 0.5,   # 500ms
            'slow': 1.0,     # 1s
            'critical': 5.0  # 5s
        }
    
    async def track_response(
        self,
        operation: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track response time for operation"""
        if operation not in self.response_times:
            self.response_times[operation] = []
        
        self.response_times[operation].append({
            'duration': duration,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        })
        
        # Keep only last 1000 entries per operation
        if len(self.response_times[operation]) > 1000:
            self.response_times[operation] = self.response_times[operation][-1000:]
        
        # Check if optimization needed
        if duration > self.thresholds['slow']:
            await self._trigger_optimization(operation, duration)
    
    async def _trigger_optimization(self, operation: str, duration: float):
        """Trigger optimization for slow operations"""
        logger.warning(f"Slow operation detected: {operation} took {duration:.2f}s")
        
        # Analyze pattern
        recent_times = [
            r['duration'] for r in self.response_times.get(operation, [])[-10:]
        ]
        
        if recent_times and sum(recent_times) / len(recent_times) > self.thresholds['slow']:
            logger.error(f"Consistent slow performance for {operation}")
            # Could trigger auto-scaling or cache warming here
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all operations"""
        summary = {}
        
        for operation, times in self.response_times.items():
            if not times:
                continue
            
            durations = [t['duration'] for t in times]
            durations.sort()
            
            summary[operation] = {
                'count': len(durations),
                'avg': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations),
                'p50': durations[len(durations) // 2],
                'p95': durations[int(len(durations) * 0.95)] if len(durations) > 20 else max(durations),
                'p99': durations[int(len(durations) * 0.99)] if len(durations) > 100 else max(durations)
            }
        
        return summary

# Global cache instance
cache_manager = CacheManager()
query_optimizer = QueryOptimizer(cache_manager)
connection_pool_manager = ConnectionPoolManager()
response_monitor = ResponseTimeMonitor()

# Decorator for easy caching
def cached(prefix: str, ttl: int = 300, key_params: Optional[List[str]] = None):
    """Decorator to cache function results"""
    return CachedFunction(cache_manager, prefix, ttl, key_params)

# Example usage
@cached(prefix="agent_response", ttl=600, key_params=["agent_type", "action"])
async def get_agent_response(agent_type: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Example cached agent response function"""
    # This would be the actual agent processing
    return {"result": "processed", "agent": agent_type, "action": action}