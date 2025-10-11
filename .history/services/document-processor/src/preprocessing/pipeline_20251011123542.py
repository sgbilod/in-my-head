"""
Unified preprocessing pipeline combining all preprocessing components.

Usage:
    from preprocessing import PreprocessingPipeline
    
    pipeline = PreprocessingPipeline()
    chunks = await pipeline.process("Your document text here")
"""

from typing import List, Optional, Dict
from .text_cleaner import TextCleaner
from .text_normalizer import TextNormalizer
from .chunker import TextChunker, TextChunk
from .deduplicator import Deduplicator


class PreprocessingPipeline:
    """
    Complete text preprocessing pipeline.
    
    Stages:
    1. Clean: Remove noise, HTML, normalize whitespace
    2. Normalize: Unicode normalization, case handling
    3. Chunk: Split into optimal chunks for embeddings
    4. Deduplicate: Remove duplicate chunks
    """
    
    def __init__(
        self,
        # Cleaning options
        remove_urls: bool = False,
        remove_emails: bool = False,
        remove_phone_numbers: bool = False,
        # Normalization options
        lowercase: bool = False,
        remove_accents: bool = False,
        # Chunking options
        chunk_size: int = 512,
        overlap_size: int = 50,
        # Deduplication options
        deduplicate: bool = True,
        similarity_threshold: float = 0.95,
    ):
        """
        Initialize preprocessing pipeline.
        
        Args:
            remove_urls: Remove URLs during cleaning
            remove_emails: Remove email addresses during cleaning
            remove_phone_numbers: Remove phone numbers during cleaning
            lowercase: Convert text to lowercase
            remove_accents: Remove accent marks
            chunk_size: Target tokens per chunk
            overlap_size: Overlap tokens between chunks
            deduplicate: Whether to remove duplicate chunks
            similarity_threshold: Similarity threshold for deduplication
        """
        # Initialize components
        self.cleaner = TextCleaner(
            remove_urls=remove_urls,
            remove_emails=remove_emails,
            remove_phone_numbers=remove_phone_numbers,
        )
        
        self.normalizer = TextNormalizer(
            lowercase=lowercase,
            remove_accents=remove_accents,
        )
        
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            overlap_size=overlap_size,
        )
        
        self.deduplicator = Deduplicator(
            similarity_threshold=similarity_threshold,
        ) if deduplicate else None
    
    def process(
        self,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> List[TextChunk]:
        """
        Process text through complete pipeline.
        
        Args:
            text: Raw text to process
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of processed TextChunk objects
        """
        if not text or not text.strip():
            return []
        
        # Stage 1: Clean
        cleaned_text = self.cleaner.clean(text)
        if not cleaned_text:
            return []
        
        # Stage 2: Normalize
        normalized_text = self.normalizer.normalize(cleaned_text)
        if not normalized_text:
            return []
        
        # Stage 3: Chunk
        chunks = self.chunker.chunk_text(normalized_text, metadata)
        if not chunks:
            return []
        
        # Stage 4: Deduplicate (optional)
        if self.deduplicator:
            chunk_texts = [chunk.text for chunk in chunks]
            unique_texts = self.deduplicator.deduplicate(chunk_texts)
            
            # Filter to unique chunks
            unique_set = set(unique_texts)
            chunks = [
                chunk for chunk in chunks
                if chunk.text in unique_set
            ]
            
            # Reindex chunks
            for i, chunk in enumerate(chunks):
                chunk.chunk_index = i
        
        return chunks
    
    def process_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict]] = None,
    ) -> List[List[TextChunk]]:
        """
        Process multiple texts efficiently.
        
        Args:
            texts: List of raw texts to process
            metadata_list: Optional list of metadata dicts
            
        Returns:
            List of chunk lists (one per input text)
        """
        if metadata_list is None:
            metadata_list = [None] * len(texts)
        
        return [
            self.process(text, metadata)
            for text, metadata in zip(texts, metadata_list)
        ]


def process_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
    clean: bool = True,
    normalize: bool = True,
) -> List[TextChunk]:
    """
    Convenience function for quick text processing.
    
    Args:
        text: Text to process
        chunk_size: Target tokens per chunk
        overlap: Overlap tokens between chunks
        clean: Whether to clean text
        normalize: Whether to normalize text
        
    Returns:
        List of TextChunk objects
    """
    if not clean and not normalize:
        # Skip preprocessing, just chunk
        chunker = TextChunker(chunk_size=chunk_size, overlap_size=overlap)
        return chunker.chunk_text(text)
    
    # Full pipeline
    pipeline = PreprocessingPipeline(
        chunk_size=chunk_size,
        overlap_size=overlap,
    )
    return pipeline.process(text)
