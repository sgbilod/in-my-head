"""
Embedding generator using OpenAI API.

Features:
- Generate embeddings for text chunks
- Support for multiple embedding models
- Metadata-aware embeddings
- Automatic retry with exponential backoff
- Comprehensive error handling
"""

import os
import hashlib
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI, RateLimitError, APIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Embedding:
    """Represents a text embedding with metadata."""

    vector: List[float]
    text: str
    model: str
    dimensions: int
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    embedding_id: Optional[str] = None

    def __post_init__(self):
        """Generate embedding ID if not provided."""
        if self.embedding_id is None:
            self.embedding_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID based on text and model."""
        content = f"{self.text}:{self.model}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert embedding to dictionary."""
        return {
            "embedding_id": self.embedding_id,
            "vector": self.vector,
            "text": self.text,
            "model": self.model,
            "dimensions": self.dimensions,
            "token_count": self.token_count,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Embedding":
        """Create embedding from dictionary."""
        data = data.copy()
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


class EmbeddingGenerator:
    """
    Generate embeddings using OpenAI API.

    Features:
    - Multiple model support (text-embedding-3-small, text-embedding-3-large)
    - Automatic retry with exponential backoff
    - Token counting and cost estimation
    - Metadata enrichment
    - Error handling and logging
    """

    # Model configurations
    MODELS = {
        "text-embedding-3-small": {
            "dimensions": 1536,
            "max_tokens": 8191,
            "cost_per_1k_tokens": 0.00002,
        },
        "text-embedding-3-large": {
            "dimensions": 3072,
            "max_tokens": 8191,
            "cost_per_1k_tokens": 0.00013,
        },
        "text-embedding-ada-002": {
            "dimensions": 1536,
            "max_tokens": 8191,
            "cost_per_1k_tokens": 0.0001,
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        dimensions: Optional[int] = None,
        max_retries: int = 3,
    ):
        """
        Initialize embedding generator.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Embedding model to use
            dimensions: Custom dimensions (for text-embedding-3-* models)
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment "
                "variable or pass api_key parameter."
            )

        if model not in self.MODELS:
            raise ValueError(
                f"Unknown model: {model}. "
                f"Available models: {list(self.MODELS.keys())}"
            )

        self.model = model
        self.model_config = self.MODELS[model]
        self.max_retries = max_retries

        # Custom dimensions (only for text-embedding-3-* models)
        if dimensions:
            if not model.startswith("text-embedding-3-"):
                logger.warning(
                    f"Custom dimensions not supported for {model}, "
                    f"ignoring dimensions parameter"
                )
                self.dimensions = self.model_config["dimensions"]
            else:
                self.dimensions = dimensions
        else:
            self.dimensions = self.model_config["dimensions"]

        # Initialize OpenAI client
        openai.api_key = self.api_key

        # Statistics
        self.stats = {
            "total_embeddings": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "failed_requests": 0,
        }

        logger.info(
            f"Initialized EmbeddingGenerator with model={self.model}, "
            f"dimensions={self.dimensions}"
        )

    @retry(
        retry=retry_if_exception_type(
            (openai.error.RateLimitError, openai.error.APIError)
        ),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
    )
    def _call_openai_api(self, texts: List[str]) -> Any:
        """
        Call OpenAI API with retry logic.

        Args:
            texts: List of texts to embed

        Returns:
            OpenAI API response
        """
        try:
            if self.dimensions != self.model_config["dimensions"]:
                # Use custom dimensions
                response = openai.Embedding.create(
                    model=self.model,
                    input=texts,
                    dimensions=self.dimensions,
                )
            else:
                response = openai.Embedding.create(
                    model=self.model,
                    input=texts,
                )
            return response
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            self.stats["failed_requests"] += 1
            raise

    def generate(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Embedding:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed
            metadata: Optional metadata to attach

        Returns:
            Embedding object
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Check token limit
        token_count = len(text.split())  # Approximate
        if token_count > self.model_config["max_tokens"]:
            raise ValueError(
                f"Text too long: {token_count} tokens "
                f"(max: {self.model_config['max_tokens']})"
            )

        try:
            # Call API
            response = self._call_openai_api([text])

            # Extract embedding
            vector = response["data"][0]["embedding"]

            # Update statistics
            self.stats["total_embeddings"] += 1
            self.stats["total_tokens"] += response["usage"]["total_tokens"]
            self.stats["total_cost"] += self._calculate_cost(
                response["usage"]["total_tokens"]
            )

            # Create embedding object
            embedding = Embedding(
                vector=vector,
                text=text,
                model=self.model,
                dimensions=self.dimensions,
                token_count=response["usage"]["total_tokens"],
                metadata=metadata or {},
            )

            logger.debug(f"Generated embedding: {embedding.embedding_id}")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def generate_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Embedding]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed
            metadata_list: Optional list of metadata dicts

        Returns:
            List of Embedding objects
        """
        if not texts:
            return []

        if metadata_list is None:
            metadata_list = [{}] * len(texts)

        if len(texts) != len(metadata_list):
            raise ValueError(
                "texts and metadata_list must have same length"
            )

        # Filter empty texts
        valid_indices = [
            i for i, text in enumerate(texts) if text and text.strip()
        ]
        valid_texts = [texts[i] for i in valid_indices]
        valid_metadata = [metadata_list[i] for i in valid_indices]

        if not valid_texts:
            logger.warning("No valid texts to embed")
            return []

        try:
            # Call API with batch
            response = self._call_openai_api(valid_texts)

            # Extract embeddings
            embeddings = []
            for i, embedding_data in enumerate(response["data"]):
                vector = embedding_data["embedding"]
                text = valid_texts[i]
                metadata = valid_metadata[i]

                embedding = Embedding(
                    vector=vector,
                    text=text,
                    model=self.model,
                    dimensions=self.dimensions,
                    token_count=len(text.split()),  # Approximate
                    metadata=metadata,
                )
                embeddings.append(embedding)

            # Update statistics
            self.stats["total_embeddings"] += len(embeddings)
            self.stats["total_tokens"] += response["usage"]["total_tokens"]
            self.stats["total_cost"] += self._calculate_cost(
                response["usage"]["total_tokens"]
            )

            logger.info(
                f"Generated {len(embeddings)} embeddings "
                f"({response['usage']['total_tokens']} tokens)"
            )

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise

    def _calculate_cost(self, tokens: int) -> float:
        """Calculate cost in USD for given token count."""
        cost_per_token = (
            self.model_config["cost_per_1k_tokens"] / 1000
        )
        return tokens * cost_per_token

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            **self.stats,
            "model": self.model,
            "dimensions": self.dimensions,
            "average_cost_per_embedding": (
                self.stats["total_cost"] / self.stats["total_embeddings"]
                if self.stats["total_embeddings"] > 0
                else 0.0
            ),
        }

    def reset_stats(self):
        """Reset usage statistics."""
        self.stats = {
            "total_embeddings": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "failed_requests": 0,
        }
        logger.info("Statistics reset")


def generate_embedding(
    text: str,
    model: str = "text-embedding-3-small",
    api_key: Optional[str] = None,
) -> List[float]:
    """
    Convenience function for quick embedding generation.

    Args:
        text: Text to embed
        model: Embedding model to use
        api_key: Optional OpenAI API key

    Returns:
        Embedding vector
    """
    generator = EmbeddingGenerator(api_key=api_key, model=model)
    embedding = generator.generate(text)
    return embedding.vector
