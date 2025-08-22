"""
Advanced Caching System for Gemini GitHub App
Implements multi-tier caching with Redis, memory, and smart invalidation
"""

import json
import hashlib
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

import redis.asyncio as redis
from cachetools import TTLCache, LRUCache
import pickle

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    created_at: datetime
    expires_at: Optional[datetime]
    hit_count: int = 0
    tags: List[str] = None
    size_bytes: int = 0

class CacheBackend(ABC):
    """Abstract cache backend"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        pass

class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend using cachetools"""
    
    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.metadata = {}  # Store metadata separately
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            entry = self.cache.get(key)
            if entry:
                # Update hit count
                if key in self.metadata:
                    self.metadata[key].hit_count += 1
                return entry
            return None
        except Exception as e:
            logger.error(f"Memory cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            self.cache[key] = value
            
            # Store metadata
            size_bytes = len(pickle.dumps(value)) if value else 0
            self.metadata[key] = CacheEntry(
                data=None,  # Don't duplicate data
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=ttl) if ttl else None,
                size_bytes=size_bytes
            )
            
            return True
        except Exception as e:
            logger.error(f"Memory cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            if key in self.cache:
                del self.cache[key]
            if key in self.metadata:
                del self.metadata[key]
            return True
        except Exception as e:
            logger.error(f"Memory cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        return key in self.cache
    
    async def clear(self) -> bool:
        try:
            self.cache.clear()
            self.metadata.clear()
            return True
        except Exception as e:
            logger.error(f"Memory cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_size = sum(meta.size_bytes for meta in self.metadata.values())
        total_hits = sum(meta.hit_count for meta in self.metadata.values())
        
        return {
            "type": "memory",
            "entries": len(self.cache),
            "max_size": self.cache.maxsize,
            "total_size_bytes": total_size,
            "total_hits": total_hits,
            "hit_rate": total_hits / max(len(self.cache), 1)
        }

class RedisCacheBackend(CacheBackend):
    """Redis cache backend"""
    
    def __init__(self, redis_url: str, key_prefix: str = "gemini:"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.client = None
    
    async def _get_client(self):
        """Get Redis client (lazy initialization)"""
        if not self.client:
            self.client = redis.from_url(self.redis_url, decode_responses=False)
        return self.client
    
    def _make_key(self, key: str) -> str:
        """Make Redis key with prefix"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            client = await self._get_client()
            redis_key = self._make_key(key)
            
            # Get data and metadata
            pipe = client.pipeline()
            pipe.hget(redis_key, "data")
            pipe.hget(redis_key, "metadata")
            pipe.hincrby(redis_key, "hit_count", 1)
            
            results = await pipe.execute()
            data_bytes, metadata_bytes, _ = results
            
            if data_bytes:
                data = pickle.loads(data_bytes)
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Redis cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            client = await self._get_client()
            redis_key = self._make_key(key)
            
            # Serialize data
            data_bytes = pickle.dumps(value)
            
            # Create metadata
            metadata = CacheEntry(
                data=None,  # Don't store data in metadata
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=ttl) if ttl else None,
                size_bytes=len(data_bytes)
            )
            metadata_bytes = pickle.dumps(asdict(metadata))
            
            # Store in Redis
            pipe = client.pipeline()
            pipe.hset(redis_key, mapping={
                "data": data_bytes,
                "metadata": metadata_bytes,
                "hit_count": 0
            })
            
            if ttl:
                pipe.expire(redis_key, ttl)
            
            await pipe.execute()
            return True
            
        except Exception as e:
            logger.error(f"Redis cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            client = await self._get_client()
            redis_key = self._make_key(key)
            result = await client.delete(redis_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            client = await self._get_client()
            redis_key = self._make_key(key)
            return await client.exists(redis_key) > 0
        except Exception as e:
            logger.error(f"Redis cache exists error: {e}")
            return False
    
    async def clear(self) -> bool:
        try:
            client = await self._get_client()
            # Delete all keys with our prefix
            keys = await client.keys(f"{self.key_prefix}*")
            if keys:
                await client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Redis cache clear error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            client = await self._get_client()
            keys = await client.keys(f"{self.key_prefix}*")
            
            total_size = 0
            total_hits = 0
            
            if keys:
                pipe = client.pipeline()
                for key in keys:
                    pipe.hlen(key)
                    pipe.hget(key, "hit_count")
                
                results = await pipe.execute()
                
                for i in range(0, len(results), 2):
                    size = results[i] or 0
                    hits = int(results[i + 1] or 0)
                    total_size += size
                    total_hits += hits
            
            return {
                "type": "redis",
                "entries": len(keys),
                "total_size_estimate": total_size,
                "total_hits": total_hits,
                "hit_rate": total_hits / max(len(keys), 1)
            }
            
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"type": "redis", "error": str(e)}

class MultiTierCache:
    """Multi-tier caching system with L1 (memory) and L2 (Redis)"""
    
    def __init__(self, 
                 l1_maxsize: int = 500,
                 l1_ttl: int = 300,
                 redis_url: Optional[str] = None,
                 l2_ttl: int = 3600):
        
        # L1 Cache (Memory)
        self.l1 = MemoryCacheBackend(maxsize=l1_maxsize, ttl=l1_ttl)
        
        # L2 Cache (Redis)
        self.l2 = RedisCacheBackend(redis_url) if redis_url else None
        
        self.l2_ttl = l2_ttl
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "promotions": 0  # L2 -> L1 promotions
        }
    
    def _make_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Create cache key from prefix and arguments"""
        # Create deterministic key from arguments
        key_parts = [prefix]
        
        # Add positional args
        key_parts.extend(str(arg) for arg in args)
        
        # Add keyword args (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        key_string = ":".join(key_parts)
        
        # Hash long keys
        if len(key_string) > 200:
            return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"
        
        return key_string
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 first, then L2)"""
        # Try L1 first
        value = await self.l1.get(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value
        
        # Try L2 if available
        if self.l2:
            value = await self.l2.get(key)
            if value is not None:
                self.stats["l2_hits"] += 1
                self.stats["promotions"] += 1
                
                # Promote to L1
                await self.l1.set(key, value)
                return value
        
        self.stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in both cache tiers"""
        success = True
        
        # Set in L1
        l1_success = await self.l1.set(key, value, ttl)
        success = success and l1_success
        
        # Set in L2 with longer TTL
        if self.l2:
            l2_ttl = ttl or self.l2_ttl
            l2_success = await self.l2.set(key, value, l2_ttl)
            success = success and l2_success
        
        return success
    
    async def delete(self, key: str) -> bool:
        """Delete from both cache tiers"""
        success = True
        
        l1_success = await self.l1.delete(key)
        success = success and l1_success
        
        if self.l2:
            l2_success = await self.l2.delete(key)
            success = success and l2_success
        
        return success
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in either tier"""
        if await self.l1.exists(key):
            return True
        
        if self.l2 and await self.l2.exists(key):
            return True
        
        return False
    
    async def clear(self) -> bool:
        """Clear both cache tiers"""
        success = True
        
        l1_success = await self.l1.clear()
        success = success and l1_success
        
        if self.l2:
            l2_success = await self.l2.clear()
            success = success and l2_success
        
        return success
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {
            "multi_tier": self.stats.copy(),
            "l1": self.l1.get_stats() if hasattr(self.l1, 'get_stats') else {},
            "l2": await self.l2.get_stats() if self.l2 else {}
        }
        
        # Calculate overall hit rate
        total_requests = sum(self.stats.values())
        if total_requests > 0:
            hit_rate = (self.stats["l1_hits"] + self.stats["l2_hits"]) / total_requests
            stats["overall_hit_rate"] = hit_rate
        
        return stats

class CacheManager:
    """Main cache manager for Gemini GitHub App"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.cache = MultiTierCache(redis_url=redis_url)
        self.tag_index = {}  # For cache invalidation by tags
    
    # Analysis result caching
    async def get_scaling_analysis(self, repo: str, commit_sha: str, files: List[str]) -> Optional[Dict[str, Any]]:
        """Get cached scaling analysis"""
        key = self.cache._make_cache_key("scaling", repo, commit_sha, hash(tuple(sorted(files))))
        return await self.cache.get(key)
    
    async def set_scaling_analysis(self, repo: str, commit_sha: str, files: List[str], 
                                  result: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache scaling analysis result"""
        key = self.cache._make_cache_key("scaling", repo, commit_sha, hash(tuple(sorted(files))))
        return await self.cache.set(key, result, ttl)
    
    async def get_duplicate_analysis(self, repo: str, similarity_threshold: float) -> Optional[Dict[str, Any]]:
        """Get cached duplicate analysis"""
        key = self.cache._make_cache_key("duplicates", repo, similarity_threshold)
        return await self.cache.get(key)
    
    async def set_duplicate_analysis(self, repo: str, similarity_threshold: float, 
                                   result: Dict[str, Any], ttl: int = 1800) -> bool:
        """Cache duplicate analysis result"""
        key = self.cache._make_cache_key("duplicates", repo, similarity_threshold)
        return await self.cache.set(key, result, ttl)
    
    async def get_code_review(self, repo: str, pr_number: int, commit_sha: str) -> Optional[Dict[str, Any]]:
        """Get cached code review"""
        key = self.cache._make_cache_key("review", repo, pr_number, commit_sha)
        return await self.cache.get(key)
    
    async def set_code_review(self, repo: str, pr_number: int, commit_sha: str, 
                             result: Dict[str, Any], ttl: int = 7200) -> bool:
        """Cache code review result"""
        key = self.cache._make_cache_key("review", repo, pr_number, commit_sha)
        return await self.cache.set(key, result, ttl)
    
    # File content caching
    async def get_file_content(self, repo: str, commit_sha: str, file_path: str) -> Optional[str]:
        """Get cached file content"""
        key = self.cache._make_cache_key("file", repo, commit_sha, file_path)
        return await self.cache.get(key)
    
    async def set_file_content(self, repo: str, commit_sha: str, file_path: str, 
                              content: str, ttl: int = 1800) -> bool:
        """Cache file content"""
        key = self.cache._make_cache_key("file", repo, commit_sha, file_path)
        return await self.cache.set(key, content, ttl)
    
    # GitHub API response caching
    async def get_pr_files(self, repo: str, pr_number: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached PR files"""
        key = self.cache._make_cache_key("pr_files", repo, pr_number)
        return await self.cache.get(key)
    
    async def set_pr_files(self, repo: str, pr_number: int, files: List[Dict[str, Any]], 
                          ttl: int = 600) -> bool:
        """Cache PR files"""
        key = self.cache._make_cache_key("pr_files", repo, pr_number)
        return await self.cache.set(key, files, ttl)
    
    # Agent state caching
    async def get_agent_state(self, agent_type: str, context: str) -> Optional[Dict[str, Any]]:
        """Get cached agent state"""
        key = self.cache._make_cache_key("agent_state", agent_type, context)
        return await self.cache.get(key)
    
    async def set_agent_state(self, agent_type: str, context: str, state: Dict[str, Any], 
                             ttl: int = 1800) -> bool:
        """Cache agent state"""
        key = self.cache._make_cache_key("agent_state", agent_type, context)
        return await self.cache.set(key, state, ttl)
    
    # Cache invalidation
    async def invalidate_repo_cache(self, repo: str) -> bool:
        """Invalidate all cache entries for a repository"""
        # This would require implementing pattern-based deletion
        # For now, we'll implement a simple approach
        patterns = [
            f"scaling:{repo}:*",
            f"duplicates:{repo}:*",
            f"review:{repo}:*",
            f"file:{repo}:*",
            f"pr_files:{repo}:*"
        ]
        
        success = True
        if self.cache.l2 and hasattr(self.cache.l2, 'client'):
            try:
                client = await self.cache.l2._get_client()
                for pattern in patterns:
                    keys = await client.keys(f"{self.cache.l2.key_prefix}{pattern}")
                    if keys:
                        await client.delete(*keys)
            except Exception as e:
                logger.error(f"Cache invalidation error: {e}")
                success = False
        
        return success
    
    async def invalidate_pr_cache(self, repo: str, pr_number: int) -> bool:
        """Invalidate cache entries for a specific PR"""
        keys_to_delete = [
            self.cache._make_cache_key("pr_files", repo, pr_number)
        ]
        
        success = True
        for key in keys_to_delete:
            delete_success = await self.cache.delete(key)
            success = success and delete_success
        
        return success
    
    # Cache warming
    async def warm_cache_for_pr(self, repo: str, pr_number: int, files: List[str], 
                               warm_functions: List[Callable] = None):
        """Pre-warm cache for PR analysis"""
        if not warm_functions:
            return
        
        logger.info(f"Warming cache for {repo}#{pr_number}")
        
        # Run cache warming functions concurrently
        tasks = []
        for func in warm_functions:
            if asyncio.iscoroutinefunction(func):
                tasks.append(func(repo, pr_number, files))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Cache warming completed for {repo}#{pr_number}")
    
    # Statistics and monitoring
    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health metrics"""
        stats = await self.cache.get_stats()
        
        health = {
            "healthy": True,
            "stats": stats,
            "recommendations": []
        }
        
        # Analyze health
        if stats.get("overall_hit_rate", 0) < 0.5:
            health["healthy"] = False
            health["recommendations"].append("Hit rate below 50% - consider cache tuning")
        
        l1_stats = stats.get("l1", {})
        if l1_stats.get("entries", 0) > l1_stats.get("max_size", 1000) * 0.9:
            health["recommendations"].append("L1 cache near capacity - consider increasing size")
        
        return health

# Global cache manager instance
_cache_manager = None

def get_cache_manager(redis_url: Optional[str] = None) -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(redis_url)
    return _cache_manager

def configure_cache(redis_url: Optional[str] = None) -> CacheManager:
    """Configure and return cache manager"""
    global _cache_manager
    _cache_manager = CacheManager(redis_url)
    return _cache_manager

# Testing and utilities
async def test_cache_performance():
    """Test cache performance"""
    cache = get_cache_manager()
    
    # Test data
    test_data = {"large_analysis": "x" * 10000, "timestamp": datetime.utcnow().isoformat()}
    
    # Timing tests
    import time
    
    # Set test
    start = time.time()
    await cache.set_scaling_analysis("test/repo", "abc123", ["file1.py"], test_data)
    set_time = time.time() - start
    
    # Get test (should hit cache)
    start = time.time()
    result = await cache.get_scaling_analysis("test/repo", "abc123", ["file1.py"])
    get_time = time.time() - start
    
    # Stats
    stats = await cache.get_cache_health()
    
    print(f"Cache Performance Test:")
    print(f"  Set time: {set_time*1000:.2f}ms")
    print(f"  Get time: {get_time*1000:.2f}ms")
    print(f"  Data retrieved: {result is not None}")
    print(f"  Cache health: {stats}")

if __name__ == "__main__":
    asyncio.run(test_cache_performance())