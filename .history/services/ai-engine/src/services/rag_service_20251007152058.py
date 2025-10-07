"""
RAG (Retrieval-Augmented Generation) Service.

Implements hybrid search, re-ranking, context assembly, and citation extraction
for intelligent question answering over document collections.

Features:
- Hybrid search: Vector similarity + keyword matching
- Re-ranking: Cross-encoder for improved relevance
- Context assembly: Smart chunk ordering and deduplication
- Citation tracking: Source attribution for answers
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np
from collections import defaultdict

from src.services.qdrant_service import get_qdrant_service

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result with score and metadata."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "score": self.score,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata
        }


@dataclass
class Citation:
    """Source citation for generated answer."""
    document_id: str
    document_title: str
    chunk_id: str
    chunk_index: int
    relevance_score: float
    excerpt: str  # Relevant excerpt from chunk
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "relevance_score": self.relevance_score,
            "excerpt": self.excerpt
        }


@dataclass
class RAGContext:
    """Assembled context for RAG generation."""
    query: str
    context_text: str
    chunks: List[SearchResult]
    citations: List[Citation]
    total_tokens: int
    strategy: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "context_text": self.context_text,
            "chunks": [c.to_dict() for c in self.chunks],
            "citations": [c.to_dict() for c in self.citations],
            "total_tokens": self.total_tokens,
            "strategy": self.strategy
        }


class RAGService:
    """
    RAG service for intelligent document retrieval and context assembly.
    
    Workflow:
    1. Hybrid search: Vector + keyword search
    2. Re-ranking: Cross-encoder for relevance
    3. Context assembly: Order and deduplicate chunks
    4. Citation extraction: Track sources
    """
    
    def __init__(
        self,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        max_context_tokens: int = 4000
    ):
        """
        Initialize RAG service.
        
        Args:
            embedding_model_name: Sentence transformer model for embeddings
            reranker_model_name: Cross-encoder model for re-ranking
            vector_weight: Weight for vector search (0-1)
            keyword_weight: Weight for keyword search (0-1)
            max_context_tokens: Maximum tokens for context window
        """
        self.embedding_model_name = embedding_model_name
        self.reranker_model_name = reranker_model_name
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.max_context_tokens = max_context_tokens
        
        # Load models
        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        logger.info(f"Loading re-ranker model: {reranker_model_name}")
        self.reranker = CrossEncoder(reranker_model_name)
        
        # Get Qdrant service
        self.qdrant = get_qdrant_service()
        
        logger.info("RAG service initialized successfully")
    
    def encode_query(self, query: str) -> List[float]:
        """
        Encode query text to embedding vector.
        
        Args:
            query: Query text
        
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.embedding_model.encode(query)
        return embedding.tolist()
    
    async def vector_search(
        self,
        query: str,
        collection_name: str = "chunk_embeddings",
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Perform vector similarity search.
        
        Args:
            query: Search query
            collection_name: Qdrant collection name
            limit: Maximum results to return
            filters: Optional Qdrant filters
        
        Returns:
            List of search results sorted by similarity
        """
        # Encode query
        query_vector = self.encode_query(query)
        
        # Search Qdrant
        results = await self.qdrant.search_similar(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            filters=filters
        )
        
        # Convert to SearchResult objects
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                chunk_id=result["id"],
                document_id=result["payload"].get("document_id", ""),
                content=result["payload"].get("content", ""),
                score=result["score"],
                chunk_index=result["payload"].get("chunk_index", 0),
                metadata=result["payload"]
            ))
        
        return search_results
    
    def keyword_search(
        self,
        query: str,
        chunks: List[SearchResult],
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Perform keyword-based search using BM25-like scoring.
        
        Args:
            query: Search query
            chunks: List of chunks to search
            top_k: Number of top results to return
        
        Returns:
            Top-k chunks by keyword relevance
        """
        query_terms = set(query.lower().split())
        
        # Score each chunk
        scored_chunks = []
        for chunk in chunks:
            content_terms = set(chunk.content.lower().split())
            
            # Calculate term frequency
            matches = query_terms & content_terms
            if not matches:
                continue
            
            # Simple BM25-inspired scoring
            tf = len(matches) / len(query_terms)
            idf = 1.0  # Simplified (would need document frequency)
            keyword_score = tf * idf
            
            chunk_copy = SearchResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                content=chunk.content,
                score=keyword_score,
                chunk_index=chunk.chunk_index,
                metadata=chunk.metadata
            )
            scored_chunks.append(chunk_copy)
        
        # Sort by score
        scored_chunks.sort(key=lambda x: x.score, reverse=True)
        
        return scored_chunks[:top_k]
    
    def hybrid_search(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Combine vector and keyword search results with weighted scoring.
        
        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
        
        Returns:
            Combined and re-scored results
        """
        # Normalize scores to 0-1 range
        def normalize_scores(results: List[SearchResult]) -> List[SearchResult]:
            if not results:
                return []
            
            scores = [r.score for r in results]
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score
            
            if score_range == 0:
                return results
            
            normalized = []
            for result in results:
                normalized_score = (result.score - min_score) / score_range
                result_copy = SearchResult(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    content=result.content,
                    score=normalized_score,
                    chunk_index=result.chunk_index,
                    metadata=result.metadata
                )
                normalized.append(result_copy)
            
            return normalized
        
        # Normalize both result sets
        norm_vector = normalize_scores(vector_results)
        norm_keyword = normalize_scores(keyword_results)
        
        # Combine scores
        combined_scores = defaultdict(float)
        all_chunks = {}
        
        # Add vector scores
        for result in norm_vector:
            combined_scores[result.chunk_id] += (
                result.score * self.vector_weight
            )
            all_chunks[result.chunk_id] = result
        
        # Add keyword scores
        for result in norm_keyword:
            combined_scores[result.chunk_id] += (
                result.score * self.keyword_weight
            )
            if result.chunk_id not in all_chunks:
                all_chunks[result.chunk_id] = result
        
        # Create final results
        final_results = []
        for chunk_id, score in combined_scores.items():
            chunk = all_chunks[chunk_id]
            final_results.append(SearchResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                content=chunk.content,
                score=score,
                chunk_index=chunk.chunk_index,
                metadata=chunk.metadata
            ))
        
        # Sort by combined score
        final_results.sort(key=lambda x: x.score, reverse=True)
        
        return final_results
    
    def rerank_results(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Re-rank results using cross-encoder for improved relevance.
        
        Args:
            query: Original query
            results: Search results to re-rank
            top_k: Number of top results to return
        
        Returns:
            Re-ranked results
        """
        if not results:
            return []
        
        # Prepare query-document pairs
        pairs = [[query, result.content] for result in results]
        
        # Get cross-encoder scores
        rerank_scores = self.reranker.predict(pairs)
        
        # Update scores
        reranked = []
        for result, score in zip(results, rerank_scores):
            reranked.append(SearchResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                content=result.content,
                score=float(score),
                chunk_index=result.chunk_index,
                metadata=result.metadata
            ))
        
        # Sort by new scores
        reranked.sort(key=lambda x: x.score, reverse=True)
        
        return reranked[:top_k]
    
    def assemble_context(
        self,
        query: str,
        chunks: List[SearchResult],
        max_tokens: Optional[int] = None
    ) -> RAGContext:
        """
        Assemble context from retrieved chunks.
        
        Args:
            query: Original query
            chunks: Retrieved and ranked chunks
            max_tokens: Override max context tokens
        
        Returns:
            Assembled RAG context with citations
        """
        max_tokens = max_tokens or self.max_context_tokens
        
        # Group chunks by document
        doc_chunks = defaultdict(list)
        for chunk in chunks:
            doc_chunks[chunk.document_id].append(chunk)
        
        # Sort chunks within each document by chunk_index
        for doc_id in doc_chunks:
            doc_chunks[doc_id].sort(key=lambda x: x.chunk_index)
        
        # Assemble context
        context_parts = []
        selected_chunks = []
        citations = []
        total_tokens = 0
        
        for doc_id, doc_chunk_list in doc_chunks.items():
            for chunk in doc_chunk_list:
                # Estimate tokens (rough: 1 token ≈ 4 chars)
                chunk_tokens = len(chunk.content) // 4
                
                if total_tokens + chunk_tokens > max_tokens:
                    break
                
                # Add chunk to context
                context_parts.append(chunk.content)
                selected_chunks.append(chunk)
                total_tokens += chunk_tokens
                
                # Create citation
                citation = Citation(
                    document_id=chunk.document_id,
                    document_title=chunk.metadata.get(
                        "document_title", "Unknown"
                    ),
                    chunk_id=chunk.chunk_id,
                    chunk_index=chunk.chunk_index,
                    relevance_score=chunk.score,
                    excerpt=chunk.content[:200] + "..."
                    if len(chunk.content) > 200 else chunk.content
                )
                citations.append(citation)
            
            if total_tokens >= max_tokens:
                break
        
        # Join context
        context_text = "\n\n---\n\n".join(context_parts)
        
        return RAGContext(
            query=query,
            context_text=context_text,
            chunks=selected_chunks,
            citations=citations,
            total_tokens=total_tokens,
            strategy="hybrid_rerank"
        )
    
    async def retrieve(
        self,
        query: str,
        collection_name: str = "chunk_embeddings",
        top_k: int = 5,
        use_reranking: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        collection_id: Optional[str] = None
    ) -> RAGContext:
        """
        Main retrieval method: hybrid search + re-ranking + context assembly.
        
        Args:
            query: User query
            collection_name: Qdrant collection to search
            top_k: Number of chunks to retrieve
            use_reranking: Whether to apply re-ranking
            filters: Optional Qdrant filters (dict)
            collection_id: Optional collection ID to filter documents
        
        Returns:
            RAG context ready for generation
        """
        logger.info(f"Retrieving context for query: {query[:100]}...")
        
        # Add collection_id to filters if provided
        if collection_id:
            if filters is None:
                filters = {}
            filters["collection_id"] = collection_id
            logger.info(f"Filtering by collection_id: {collection_id}")
        
        
        # 1. Vector search
        vector_results = await self.vector_search(
            query=query,
            collection_name=collection_name,
            limit=20,
            filters=filters
        )
        logger.info(f"Vector search: {len(vector_results)} results")
        
        # 2. Keyword search (on vector results)
        keyword_results = self.keyword_search(
            query=query,
            chunks=vector_results,
            top_k=10
        )
        logger.info(f"Keyword search: {len(keyword_results)} results")
        
        # 3. Hybrid combination
        hybrid_results = self.hybrid_search(vector_results, keyword_results)
        logger.info(f"Hybrid search: {len(hybrid_results)} results")
        
        # 4. Re-ranking (optional)
        if use_reranking:
            final_results = self.rerank_results(
                query=query,
                results=hybrid_results,
                top_k=top_k * 2  # Get more for better context
            )
            logger.info(f"Re-ranking: {len(final_results)} results")
        else:
            final_results = hybrid_results[:top_k * 2]
        
        # 5. Assemble context
        context = self.assemble_context(
            query=query,
            chunks=final_results
        )
        logger.info(
            f"Context assembled: {len(context.chunks)} chunks, "
            f"{context.total_tokens} tokens"
        )
        
        return context
    
    def extract_citations(
        self,
        context: RAGContext,
        answer: str
    ) -> List[Citation]:
        """
        Extract which citations were actually used in the generated answer.
        
        Args:
            context: RAG context with all citations
            answer: Generated answer text
        
        Returns:
            List of citations that appear relevant to the answer
        """
        # Simple heuristic: check if citation text appears in answer
        used_citations = []
        
        for citation in context.citations:
            # Check if key terms from citation appear in answer
            citation_terms = set(
                citation.excerpt.lower().split()[:20]
            )  # First 20 words
            answer_terms = set(answer.lower().split())
            
            overlap = citation_terms & answer_terms
            if len(overlap) >= 3:  # At least 3 matching terms
                used_citations.append(citation)
        
        return used_citations


# Global RAG service instance (singleton)
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get or create the global RAG service instance.
    
    Returns:
        RAGService instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
