"""
Redis-based caching for embeddings.

Features:
- Content-based cache keys (SHA-256 hashing)
- TTL management (configurable expiration)
- Batch get/set operations
- Cache statistics tracking
- Automatic serialization/deserialization
"""

import json
import hashlib
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import redis.asyncio as redis

from .embedding_generator import Embedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Redis-based cache for embeddings.

    Features:
    - SHA-256 hashing for cache keys
    - Configurable TTL (default: 7 days)
    - Batch operations for efficiency
    - Cache statistics tracking
    - Automatic cleanup of expired entries
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl: int = 604800,  # 7 days in seconds
        prefix: str = "emb:",
        db: int = 0,
    ):
        """
        Initialize embedding cache.

        Args:
            redis_url: Redis connection URL
            ttl: Time-to-live in seconds (default: 7 days)
            prefix: Key prefix for namespacing
            db: Redis database number
        """
        self.redis_url = redis_url
        self.ttl = ttl
        self.prefix = prefix
        self.db = db

        # Initialize Redis client
        self.redis_client: Optional[redis.Redis] = None

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
        }

        logger.info(
            f"Initialized EmbeddingCache with ttl={ttl}s, prefix={prefix}"
        )

    async def connect(self):
        """Connect to Redis."""
        if self.redis_client is None:
            try:
                self.redis_client = await redis.from_url(
                    self.redis_url,
                    db=self.db,
                    encoding="utf-8",
                    decode_responses=False,
                )
                await self.redis_client.ping()
                logger.info("Connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Disconnected from Redis")

    def _generate_cache_key(self, text: str, model: str) -> str:
        """
        Generate cache key from text and model.

        Args:
            text: Text content
            model: Model name

        Returns:
            Cache key (SHA-256 hash)
        """
        content = f"{text}:{model}"
        hash_hex = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return f"{self.prefix}{hash_hex}"

    def _serialize_embedding(self, embedding: Embedding) -> bytes:
        """
        Serialize embedding to bytes.

        Args:
            embedding: Embedding object

        Returns:
            Serialized bytes
        """
        data = embedding.to_dict()
        return json.dumps(data).encode("utf-8")

    def _deserialize_embedding(self, data: bytes) -> Embedding:
        """
        Deserialize embedding from bytes.

        Args:
            data: Serialized bytes

        Returns:
            Embedding object
        """
        obj = json.loads(data.decode("utf-8"))
        return Embedding.from_dict(obj)

    async def get(
        self,
        text: str,
        model: str,
    ) -> Optional[Embedding]:
        """
        Get embedding from cache.

        Args:
            text: Text content
            model: Model name

        Returns:
            Embedding if found, None otherwise
        """
        if self.redis_client is None:
            await self.connect()

        cache_key = self._generate_cache_key(text, model)

        try:
            data = await self.redis_client.get(cache_key)

            if data:
                embedding = self._deserialize_embedding(data)
                self.stats["hits"] += 1
                logger.debug(f"Cache hit: {cache_key}")
                return embedding
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache miss: {cache_key}")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats["errors"] += 1
            return None

    async def set(
        self,
        embedding: Embedding,
    ) -> bool:
        """
        Set embedding in cache.

        Args:
            embedding: Embedding to cache

        Returns:
            True if successful, False otherwise
        """
        if self.redis_client is None:
            await self.connect()

        cache_key = self._generate_cache_key(
            embedding.text, embedding.model
        )

        try:
            data = self._serialize_embedding(embedding)
            await self.redis_client.setex(
                cache_key,
                self.ttl,
                data,
            )
            self.stats["sets"] += 1
            logger.debug(f"Cache set: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.stats["errors"] += 1
            return False

    async def get_batch(
        self,
        texts: List[str],
        model: str,
    ) -> Dict[str, Embedding]:
        """
        Get multiple embeddings from cache efficiently.

        Args:
            texts: List of texts
            model: Model name

        Returns:
            Dictionary mapping text to embedding (only cached items)
        """
        if self.redis_client is None:
            await self.connect()

        # Generate cache keys
        cache_keys = [
            self._generate_cache_key(text, model) for text in texts
        ]

        try:
            # Batch get
            pipeline = self.redis_client.pipeline()
            for key in cache_keys:
                pipeline.get(key)
            results = await pipeline.execute()

            # Parse results
            embeddings = {}
            for text, data in zip(texts, results):
                if data:
                    embedding = self._deserialize_embedding(data)
                    embeddings[text] = embedding
                    self.stats["hits"] += 1
                else:
                    self.stats["misses"] += 1

            logger.debug(
                f"Cache batch get: {len(embeddings)}/{len(texts)} hits"
            )
            return embeddings

        except Exception as e:
            logger.error(f"Cache batch get error: {e}")
            self.stats["errors"] += 1
            return {}

    async def set_batch(
        self,
        embeddings: List[Embedding],
    ) -> int:
        """
        Set multiple embeddings in cache efficiently.

        Args:
            embeddings: List of embeddings to cache

        Returns:
            Number of successfully cached embeddings
        """
        if self.redis_client is None:
            await self.connect()

        try:
            # Batch set
            pipeline = self.redis_client.pipeline()
            for embedding in embeddings:
                cache_key = self._generate_cache_key(
                    embedding.text, embedding.model
                )
                data = self._serialize_embedding(embedding)
                pipeline.setex(cache_key, self.ttl, data)

            await pipeline.execute()

            self.stats["sets"] += len(embeddings)
            logger.debug(f"Cache batch set: {len(embeddings)} embeddings")
            return len(embeddings)

        except Exception as e:
            logger.error(f"Cache batch set error: {e}")
            self.stats["errors"] += 1
            return 0

    async def delete(self, text: str, model: str) -> bool:
        """
        Delete embedding from cache.

        Args:
            text: Text content
            model: Model name

        Returns:
            True if deleted, False otherwise
        """
        if self.redis_client is None:
            await self.connect()

        cache_key = self._generate_cache_key(text, model)

        try:
            result = await self.redis_client.delete(cache_key)
            logger.debug(f"Cache delete: {cache_key}")
            return result > 0

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.stats["errors"] += 1
            return False

    async def clear(self) -> int:
        """
        Clear all cached embeddings.

        Returns:
            Number of keys deleted
        """
        if self.redis_client is None:
            await self.connect()

        try:
            # Find all keys with prefix
            pattern = f"{self.prefix}*"
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor, match=pattern, count=100
                )
                if keys:
                    deleted += await self.redis_client.delete(*keys)

                if cursor == 0:
                    break

            logger.info(f"Cache cleared: {deleted} keys deleted")
            return deleted

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self.stats["errors"] += 1
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            self.stats["hits"] / total_requests
            if total_requests > 0
            else 0.0
        )

        # Get Redis info
        info = {}
        if self.redis_client:
            try:
                # Count cached embeddings
                pattern = f"{self.prefix}*"
                cursor = 0
                key_count = 0

                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor, match=pattern, count=100
                    )
                    key_count += len(keys)
                    if cursor == 0:
                        break

                info["cached_embeddings"] = key_count

            except Exception as e:
                logger.error(f"Failed to get Redis info: {e}")

        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl,
            **info,
        }

    async def reset_stats(self):
        """Reset cache statistics."""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
        }
        logger.info("Cache statistics reset")

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()
