"""
Embedding generation service for document chunks.

Generates embeddings using sentence-transformers and stores in Qdrant.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid as uuid_pkg

from sentence_transformers import SentenceTransformer
import asyncpg
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)


@dataclass
class ChunkEmbedding:
    """Chunk with embedding."""
    chunk_id: str
    document_id: str
    content: str
    embedding: List[float]
    chunk_index: int
    metadata: Dict[str, Any]


class EmbeddingService:
    """
    Service for generating and storing chunk embeddings.
    
    Features:
    - Batch embedding generation
    - Qdrant storage
    - PostgreSQL sync
    - Progress tracking
    - Error handling
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        qdrant_url: str = "http://localhost:6333",
        db_url: str = None,
        batch_size: int = 32
    ):
        """Initialize embedding service."""
        
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        self.qdrant = QdrantClient(url=qdrant_url)
        self.db_url = db_url or (
            "postgresql://inmyhead:inmyhead_dev_pass@"
            "localhost:5434/inmyhead_dev"
        )
        self.batch_size = batch_size
        
        logger.info(
            f"EmbeddingService initialized: {model_name}, "
            f"dim={self.embedding_dim}"
        )
    
    async def ensure_collection(
        self,
        collection_name: str = "chunk_embeddings"
    ) -> None:
        """
        Ensure Qdrant collection exists.
        
        Args:
            collection_name: Name of collection
        """
        
        collections = self.qdrant.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        
        if not exists:
            logger.info(
                f"Creating collection: {collection_name} "
                f"(dim={self.embedding_dim})"
            )
            
            self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"✅ Collection created: {collection_name}")
        else:
            logger.info(f"Collection exists: {collection_name}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for batch of texts.
        
        Args:
            texts: List of texts
            
        Returns:
            List of embedding vectors
        """
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        return [emb.tolist() for emb in embeddings]
    
    async def store_embeddings(
        self,
        chunks: List[ChunkEmbedding],
        collection_name: str = "chunk_embeddings"
    ) -> int:
        """
        Store chunk embeddings in Qdrant.
        
        Args:
            chunks: List of chunks with embeddings
            collection_name: Qdrant collection
            
        Returns:
            Number of chunks stored
        """
        
        if not chunks:
            return 0
        
        # Create points for Qdrant
        points = [
            PointStruct(
                id=chunk.chunk_id,
                vector=chunk.embedding,
                payload={
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata
                }
            )
            for chunk in chunks
        ]
        
        # Upload to Qdrant
        self.qdrant.upsert(
            collection_name=collection_name,
            points=points
        )
        
        logger.info(f"Stored {len(chunks)} embeddings in Qdrant")
        
        return len(chunks)
    
    async def update_chunk_records(
        self,
        chunks: List[ChunkEmbedding]
    ) -> int:
        """
        Update PostgreSQL chunk records with embedding info.
        
        Args:
            chunks: List of chunks with embeddings
            
        Returns:
            Number of records updated
        """
        
        if not chunks:
            return 0
        
        conn = await asyncpg.connect(self.db_url)
        
        try:
            # Update each chunk
            for chunk in chunks:
                await conn.execute(
                    """
                    UPDATE document_chunks
                    SET embedding_id = $1,
                        embedding_model = $2,
                        has_embedding = TRUE,
                        updated_at = NOW()
                    WHERE id = $3
                    """,
                    uuid_pkg.UUID(chunk.chunk_id),
                    self.model_name,
                    uuid_pkg.UUID(chunk.chunk_id)
                )
            
            logger.info(f"Updated {len(chunks)} chunk records in PostgreSQL")
            return len(chunks)
            
        finally:
            await conn.close()
    
    async def process_chunks(
        self,
        chunks: List[Dict[str, Any]],
        collection_name: str = "chunk_embeddings"
    ) -> int:
        """
        Process chunks: generate embeddings and store.
        
        Args:
            chunks: List of chunk dictionaries
            collection_name: Qdrant collection
            
        Returns:
            Number of chunks processed
        """
        
        if not chunks:
            return 0
        
        logger.info(f"Processing {len(chunks)} chunks...")
        
        # Generate embeddings in batches
        chunk_embeddings = []
        
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            texts = [c["content"] for c in batch]
            
            embeddings = self.generate_embeddings_batch(texts)
            
            for chunk, embedding in zip(batch, embeddings):
                chunk_embeddings.append(ChunkEmbedding(
                    chunk_id=str(chunk["id"]),
                    document_id=str(chunk["document_id"]),
                    content=chunk["content"],
                    embedding=embedding,
                    chunk_index=chunk["chunk_index"],
                    metadata={
                        "document_title": chunk.get("document_title", ""),
                        "char_count": chunk.get("char_count", 0),
                        "word_count": chunk.get("word_count", 0),
                        "sentence_count": chunk.get("sentence_count", 0),
                        "chunking_strategy": chunk.get(
                            "chunking_strategy",
                            "unknown"
                        )
                    }
                ))
            
            logger.info(
                f"  Generated embeddings: "
                f"{i + len(batch)}/{len(chunks)}"
            )
        
        # Store in Qdrant
        stored = await self.store_embeddings(
            chunk_embeddings,
            collection_name
        )
        
        # Update PostgreSQL
        updated = await self.update_chunk_records(chunk_embeddings)
        
        logger.info(
            f"✅ Processed {len(chunks)} chunks "
            f"({stored} stored, {updated} updated)"
        )
        
        return len(chunks)


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service."""
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    
    return _embedding_service
