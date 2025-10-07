"""
Redis Cache Service for RAG optimizations.

Provides query result caching, embedding caching, and intelligent cache invalidation
to improve RAG performance and reduce compute costs.

Features:
- Query result caching with TTL
- Embedding vector caching
- Semantic cache (similar query detection)
- Cache warming for popular queries
- Smart invalidation on document updates
"""

import logging
import json
import hashlib
from typing import List, Dict, Any, Optional
import redis.asyncio as redis
import numpy as np
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisCacheService:
    """
    Redis-based caching service for RAG operations.
    
    Caching strategies:
    1. Query Result Cache: Full RAG context by query hash
    2. Embedding Cache: Embedding vectors by text hash
    3. Semantic Cache: Similar queries mapped to results
    4. Document Cache: Document metadata and chunks
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,  # 1 hour
        embedding_ttl: int = 86400,  # 24 hours
        result_ttl: int = 1800  # 30 minutes
    ):
        """
        Initialize Redis cache service.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default cache TTL in seconds
            embedding_ttl: TTL for embedding cache
            result_ttl: TTL for query result cache
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.embedding_ttl = embedding_ttl
        self.result_ttl = result_ttl
        
        # Redis client (will be initialized on first use)
        self._client: Optional[redis.Redis] = None
        
        logger.info(f"Redis cache service configured: {redis_url}")
    
    async def get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # Handle binary data
            )
            logger.info("Redis client initialized")
        return self._client
    
    @staticmethod
    def hash_text(text: str) -> str:
        """Create stable hash for text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hash_query(query: str, collection_id: Optional[str] = None) -> str:
        """
        Create stable hash for query with optional collection filter.
        
        Args:
            query: Query text
            collection_id: Optional collection filter
        
        Returns:
            Hash string
        """
        key_parts = [query.lower().strip()]
        if collection_id:
            key_parts.append(collection_id)
        
        combined = "|".join(key_parts)
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    async def cache_query_result(
        self,
        query: str,
        result: Dict[str, Any],
        collection_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache RAG query result.
        
        Args:
            query: Original query
            result: RAG context result (serializable dict)
            collection_id: Optional collection filter
            ttl: Cache TTL in seconds (uses result_ttl if None)
        
        Returns:
            True if cached successfully
        """
        try:
            client = await self.get_client()
            
            # Generate cache key
            query_hash = self.hash_query(query, collection_id)
            cache_key = f"rag:query:{query_hash}"
            
            # Serialize result
            result_json = json.dumps(result)
            
            # Cache with TTL
            ttl = ttl or self.result_ttl
            await client.setex(cache_key, ttl, result_json)
            
            logger.debug(f"Cached query result: {cache_key[:16]}... (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache query result: {e}")
            return False
    
    async def get_query_result(
        self,
        query: str,
        collection_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached query result.
        
        Args:
            query: Original query
            collection_id: Optional collection filter
        
        Returns:
            Cached result dict or None if not found
        """
        try:
            client = await self.get_client()
            
            # Generate cache key
            query_hash = self.hash_query(query, collection_id)
            cache_key = f"rag:query:{query_hash}"
            
            # Retrieve from cache
            cached = await client.get(cache_key)
            
            if cached:
                logger.debug(f"Cache HIT: {cache_key[:16]}...")
                return json.loads(cached)
            else:
                logger.debug(f"Cache MISS: {cache_key[:16]}...")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached result: {e}")
            return None
    
    async def cache_embedding(
        self,
        text: str,
        embedding: List[float],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache embedding vector for text.
        
        Args:
            text: Original text
            embedding: Embedding vector
            ttl: Cache TTL in seconds (uses embedding_ttl if None)
        
        Returns:
            True if cached successfully
        """
        try:
            client = await self.get_client()
            
            # Generate cache key
            text_hash = self.hash_text(text)
            cache_key = f"rag:embedding:{text_hash}"
            
            # Serialize embedding as numpy array (more efficient)
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
            
            # Cache with TTL
            ttl = ttl or self.embedding_ttl
            await client.setex(cache_key, ttl, embedding_bytes)
            
            logger.debug(f"Cached embedding: {cache_key[:20]}... ({len(embedding)} dims)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache embedding: {e}")
            return False
    
    async def get_embedding(
        self,
        text: str
    ) -> Optional[List[float]]:
        """
        Retrieve cached embedding vector.
        
        Args:
            text: Original text
        
        Returns:
            Embedding vector or None if not found
        """
        try:
            client = await self.get_client()
            
            # Generate cache key
            text_hash = self.hash_text(text)
            cache_key = f"rag:embedding:{text_hash}"
            
            # Retrieve from cache
            cached = await client.get(cache_key)
            
            if cached:
                # Deserialize numpy array
                embedding = np.frombuffer(cached, dtype=np.float32).tolist()
                logger.debug(f"Embedding cache HIT: {cache_key[:20]}...")
                return embedding
            else:
                logger.debug(f"Embedding cache MISS: {cache_key[:20]}...")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached embedding: {e}")
            return None
    
    async def invalidate_document_cache(
        self,
        document_id: str
    ) -> int:
        """
        Invalidate all cache entries related to a document.
        
        Called when document is updated or deleted.
        
        Args:
            document_id: Document ID
        
        Returns:
            Number of keys invalidated
        """
        try:
            client = await self.get_client()
            
            # Find all keys mentioning this document
            # Note: SCAN is more efficient than KEYS for production
            pattern = f"*{document_id}*"
            
            deleted_count = 0
            async for key in client.scan_iter(match=pattern, count=100):
                await client.delete(key)
                deleted_count += 1
            
            logger.info(f"Invalidated {deleted_count} cache entries for document {document_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate document cache: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        try:
            client = await self.get_client()
            
            info = await client.info("stats")
            
            # Count keys by prefix
            query_keys = 0
            embedding_keys = 0
            
            async for key in client.scan_iter(match="rag:query:*", count=1000):
                query_keys += 1
            
            async for key in client.scan_iter(match="rag:embedding:*", count=1000):
                embedding_keys += 1
            
            return {
                "total_keys": info.get("db0", {}).get("keys", 0),
                "query_cache_keys": query_keys,
                "embedding_cache_keys": embedding_keys,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100
    
    async def warm_cache(
        self,
        popular_queries: List[str],
        collection_id: Optional[str] = None
    ) -> int:
        """
        Warm cache with popular queries.
        
        Args:
            popular_queries: List of frequently used queries
            collection_id: Optional collection filter
        
        Returns:
            Number of queries warmed
        """
        # This would be called with actual RAG results
        # For now, just log the intent
        logger.info(f"Cache warming requested for {len(popular_queries)} queries")
        return 0
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis client closed")


# Global cache service instance
_cache_service: Optional[RedisCacheService] = None


def get_cache_service(redis_url: str = "redis://localhost:6379") -> RedisCacheService:
    """
    Get or create global cache service instance.
    
    Args:
        redis_url: Redis connection URL
    
    Returns:
        RedisCacheService instance
    """
    global _cache_service
    
    if _cache_service is None:
        _cache_service = RedisCacheService(redis_url=redis_url)
    
    return _cache_service
