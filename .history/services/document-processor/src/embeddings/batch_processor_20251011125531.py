"""
Batch embedding processor with rate limiting and caching.

Features:
- Efficient batch processing with OpenAI API
- Automatic cache integration
- Rate limit handling (3,000 RPM, 1,000,000 TPM)
- Parallel processing with asyncio
- Progress tracking
- Retry logic with exponential backoff
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import openai

from .embedding_generator import EmbeddingGenerator, Embedding
from .embedding_cache import EmbeddingCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BatchProgress:
    """Track batch processing progress."""

    total: int
    processed: int = 0
    cached: int = 0
    generated: int = 0
    failed: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        return (self.processed / self.total * 100) if self.total > 0 else 0.0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        return (
            (self.cached / self.processed * 100)
            if self.processed > 0
            else 0.0
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.processed / elapsed if elapsed > 0 else 0.0

        return {
            "total": self.total,
            "processed": self.processed,
            "cached": self.cached,
            "generated": self.generated,
            "failed": self.failed,
            "completion_percentage": self.completion_percentage,
            "cache_hit_rate": self.cache_hit_rate,
            "elapsed_seconds": elapsed,
            "processing_rate": rate,
        }


class BatchEmbeddingProcessor:
    """
    Process embeddings in batches with caching and rate limiting.

    Features:
    - Automatic cache checking before generation
    - Batch optimization for API efficiency
    - Rate limit handling (3,000 RPM, 1,000,000 TPM)
    - Parallel processing with configurable concurrency
    - Progress tracking and reporting
    - Comprehensive error handling
    """

    # OpenAI rate limits
    RATE_LIMIT_RPM = 3000  # Requests per minute
    RATE_LIMIT_TPM = 1000000  # Tokens per minute

    def __init__(
        self,
        generator: EmbeddingGenerator,
        cache: Optional[EmbeddingCache] = None,
        batch_size: int = 100,
        max_parallel: int = 5,
        use_cache: bool = True,
    ):
        """
        Initialize batch processor.

        Args:
            generator: EmbeddingGenerator instance
            cache: Optional EmbeddingCache instance
            batch_size: Maximum texts per batch request
            max_parallel: Maximum parallel batch requests
            use_cache: Whether to use caching
        """
        self.generator = generator
        self.cache = cache
        self.batch_size = batch_size
        self.max_parallel = max_parallel
        self.use_cache = use_cache and cache is not None

        # Progress tracking
        self.progress: Optional[BatchProgress] = None

        # Rate limiting
        self._request_times: List[float] = []
        self._token_counts: List[int] = []

        logger.info(
            f"Initialized BatchEmbeddingProcessor with "
            f"batch_size={batch_size}, max_parallel={max_parallel}, "
            f"use_cache={use_cache}"
        )

    async def process_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        show_progress: bool = True,
    ) -> List[Embedding]:
        """
        Process batch of texts into embeddings.

        Args:
            texts: List of texts to embed
            metadata_list: Optional metadata for each text
            show_progress: Whether to log progress

        Returns:
            List of embeddings (same order as input)
        """
        if not texts:
            return []

        if metadata_list is None:
            metadata_list = [{}] * len(texts)

        # Initialize progress tracking
        self.progress = BatchProgress(total=len(texts))

        # Step 1: Check cache (if enabled)
        embeddings_dict: Dict[str, Embedding] = {}
        texts_to_generate: List[str] = []
        texts_to_generate_metadata: List[Dict[str, Any]] = []

        if self.use_cache:
            logger.info("Checking cache for existing embeddings...")
            embeddings_dict = await self.cache.get_batch(
                texts, self.generator.model
            )

            # Track cached items
            self.progress.cached = len(embeddings_dict)
            self.progress.processed = len(embeddings_dict)

            # Find texts that need generation
            for i, text in enumerate(texts):
                if text not in embeddings_dict:
                    texts_to_generate.append(text)
                    texts_to_generate_metadata.append(metadata_list[i])

            if show_progress:
                logger.info(
                    f"Cache hits: {len(embeddings_dict)}/{len(texts)} "
                    f"({self.progress.cache_hit_rate:.1f}%)"
                )
        else:
            texts_to_generate = texts
            texts_to_generate_metadata = metadata_list

        # Step 2: Generate embeddings for uncached texts
        if texts_to_generate:
            logger.info(
                f"Generating {len(texts_to_generate)} new embeddings..."
            )

            generated_embeddings = await self._generate_with_batching(
                texts_to_generate,
                texts_to_generate_metadata,
                show_progress,
            )

            # Add to results
            for embedding in generated_embeddings:
                embeddings_dict[embedding.text] = embedding

            # Cache new embeddings
            if self.use_cache and generated_embeddings:
                logger.info("Caching new embeddings...")
                await self.cache.set_batch(generated_embeddings)

        # Step 3: Reconstruct results in original order
        results = []
        for text in texts:
            if text in embeddings_dict:
                results.append(embeddings_dict[text])
            else:
                # Failed to generate - create placeholder
                logger.warning(f"Failed to generate embedding for: {text[:50]}...")
                self.progress.failed += 1

        if show_progress:
            progress_info = self.progress.to_dict()
            logger.info(f"Batch processing complete: {progress_info}")

        return results

    async def _generate_with_batching(
        self,
        texts: List[str],
        metadata_list: List[Dict[str, Any]],
        show_progress: bool,
    ) -> List[Embedding]:
        """
        Generate embeddings with efficient batching.

        Args:
            texts: Texts to embed
            metadata_list: Metadata for each text
            show_progress: Whether to log progress

        Returns:
            List of generated embeddings
        """
        # Split into batches
        batches = self._split_batches(texts, metadata_list)

        # Process batches with parallelism
        all_embeddings = []

        # Process in chunks to limit parallelism
        for i in range(0, len(batches), self.max_parallel):
            batch_chunk = batches[i : i + self.max_parallel]

            # Process chunk in parallel
            tasks = [
                self._process_single_batch(batch_texts, batch_metadata)
                for batch_texts, batch_metadata in batch_chunk
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                    continue

                all_embeddings.extend(result)
                self.progress.generated += len(result)
                self.progress.processed += len(result)

                if show_progress and self.progress.total > 0:
                    logger.info(
                        f"Progress: {self.progress.processed}/{self.progress.total} "
                        f"({self.progress.completion_percentage:.1f}%)"
                    )

        return all_embeddings

    @retry(
        retry=retry_if_exception_type(
            (openai.error.RateLimitError, openai.error.APIError)
        ),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
    )
    async def _process_single_batch(
        self,
        texts: List[str],
        metadata_list: List[Dict[str, Any]],
    ) -> List[Embedding]:
        """
        Process single batch with rate limiting.

        Args:
            texts: Batch of texts
            metadata_list: Metadata for each text

        Returns:
            List of embeddings
        """
        # Check rate limits
        await self._check_rate_limits(len(texts))

        try:
            # Generate embeddings
            embeddings = self.generator.generate_batch(
                texts, metadata_list
            )

            # Track request
            import time

            self._request_times.append(time.time())
            self._token_counts.append(sum(len(t.split()) for t in texts))

            return embeddings

        except Exception as e:
            logger.error(f"Batch generation error: {e}")
            raise

    async def _check_rate_limits(self, batch_size: int):
        """
        Check and enforce rate limits.

        Args:
            batch_size: Size of upcoming batch
        """
        import time

        current_time = time.time()

        # Clean old entries (older than 1 minute)
        cutoff_time = current_time - 60
        self._request_times = [
            t for t in self._request_times if t > cutoff_time
        ]

        # Check RPM limit
        if len(self._request_times) >= self.RATE_LIMIT_RPM:
            sleep_time = 60 - (current_time - self._request_times[0])
            if sleep_time > 0:
                logger.warning(
                    f"Rate limit approaching, sleeping {sleep_time:.1f}s"
                )
                await asyncio.sleep(sleep_time)

        # Check TPM limit (approximate)
        recent_tokens = sum(self._token_counts[-50:])  # Last 50 requests
        if recent_tokens > self.RATE_LIMIT_TPM * 0.9:
            logger.warning("Token rate limit approaching, adding delay")
            await asyncio.sleep(2)

    def _split_batches(
        self,
        texts: List[str],
        metadata_list: List[Dict[str, Any]],
    ) -> List[tuple[List[str], List[Dict[str, Any]]]]:
        """
        Split texts into batches.

        Args:
            texts: All texts
            metadata_list: All metadata

        Returns:
            List of (texts, metadata) tuples
        """
        batches = []
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i : i + self.batch_size]
            batch_metadata = metadata_list[i : i + self.batch_size]
            batches.append((batch_texts, batch_metadata))

        return batches

    def get_progress(self) -> Optional[Dict[str, Any]]:
        """
        Get current progress information.

        Returns:
            Progress dictionary or None if not processing
        """
        if self.progress:
            return self.progress.to_dict()
        return None

    async def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get cache statistics.

        Returns:
            Cache stats dictionary or None if cache disabled
        """
        if self.cache:
            return await self.cache.get_stats()
        return None
