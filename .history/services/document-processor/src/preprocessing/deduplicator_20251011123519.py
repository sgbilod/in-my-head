"""
Content deduplicator for identifying and removing duplicate content.

Features:
- Exact duplicate detection using SHA-256 hashing
- Near-duplicate detection using fuzzy matching
- Configurable similarity thresholds
- Efficient batch processing
"""

import hashlib
from difflib import SequenceMatcher
from typing import List, Set, Tuple, Dict


class Deduplicator:
    """
    Detects and removes duplicate content from text.
    
    Uses:
    - SHA-256 hashing for exact duplicates
    - SequenceMatcher for fuzzy duplicates
    - Configurable similarity thresholds
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.95,
        min_length: int = 50,
        case_sensitive: bool = False,
    ):
        """
        Initialize deduplicator.
        
        Args:
            similarity_threshold: Minimum similarity (0-1) to consider duplicate
            min_length: Minimum text length to check (ignore very short texts)
            case_sensitive: Whether to consider case in comparisons
        """
        self.similarity_threshold = similarity_threshold
        self.min_length = min_length
        self.case_sensitive = case_sensitive
        
        # Track seen content
        self.seen_hashes: Set[str] = set()
        self.seen_texts: List[str] = []
    
    def hash_content(self, text: str) -> str:
        """
        Generate SHA-256 hash of text content.
        
        Args:
            text: Text to hash
            
        Returns:
            Hexadecimal hash string
        """
        if not self.case_sensitive:
            text = text.lower()
        
        # Normalize whitespace for hashing
        text = " ".join(text.split())
        
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    def is_duplicate(self, text: str) -> bool:
        """
        Check if text is a duplicate of previously seen content.
        
        Args:
            text: Text to check
            
        Returns:
            True if duplicate, False otherwise
        """
        if not text or len(text) < self.min_length:
            return False
        
        # Check exact duplicate
        content_hash = self.hash_content(text)
        if content_hash in self.seen_hashes:
            return True
        
        # Check fuzzy duplicates
        for seen_text in self.seen_texts:
            similarity = self.calculate_similarity(text, seen_text)
            if similarity >= self.similarity_threshold:
                return True
        
        # Not a duplicate - remember this text
        self.seen_hashes.add(content_hash)
        self.seen_texts.append(text)
        
        return False
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two texts.
        
        Uses Python's SequenceMatcher for fuzzy string matching.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity ratio between 0 and 1
        """
        if not self.case_sensitive:
            text1 = text1.lower()
            text2 = text2.lower()
        
        # Normalize whitespace
        text1 = " ".join(text1.split())
        text2 = " ".join(text2.split())
        
        # Calculate similarity
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def find_duplicates(
        self,
        texts: List[str],
    ) -> List[Tuple[int, int, float]]:
        """
        Find all duplicate pairs in a list of texts.
        
        Args:
            texts: List of texts to compare
            
        Returns:
            List of (index1, index2, similarity) tuples for duplicates
        """
        duplicates = []
        
        # Build hash map
        hash_to_indices: Dict[str, List[int]] = {}
        for i, text in enumerate(texts):
            if len(text) < self.min_length:
                continue
            
            content_hash = self.hash_content(text)
            if content_hash not in hash_to_indices:
                hash_to_indices[content_hash] = []
            hash_to_indices[content_hash].append(i)
        
        # Find exact duplicates
        for indices in hash_to_indices.values():
            if len(indices) > 1:
                # Mark all but first as duplicates
                for i in range(1, len(indices)):
                    duplicates.append((indices[0], indices[i], 1.0))
        
        # Find fuzzy duplicates (more expensive)
        checked_pairs = set()
        for i, text1 in enumerate(texts):
            if len(text1) < self.min_length:
                continue
            
            for j, text2 in enumerate(texts[i + 1:], start=i + 1):
                if len(text2) < self.min_length:
                    continue
                
                # Skip if already marked as exact duplicate
                if (i, j) in checked_pairs or (j, i) in checked_pairs:
                    continue
                
                similarity = self.calculate_similarity(text1, text2)
                if similarity >= self.similarity_threshold:
                    duplicates.append((i, j, similarity))
                    checked_pairs.add((i, j))
        
        return duplicates
    
    def deduplicate(
        self,
        texts: List[str],
        keep: str = "first",
    ) -> List[str]:
        """
        Remove duplicates from list of texts.
        
        Args:
            texts: List of texts to deduplicate
            keep: Which duplicate to keep ('first' or 'last')
            
        Returns:
            List of unique texts
        """
        if keep not in ("first", "last"):
            raise ValueError("keep must be 'first' or 'last'")
        
        # Find duplicates
        duplicate_pairs = self.find_duplicates(texts)
        
        # Build set of indices to remove
        indices_to_remove = set()
        for idx1, idx2, _ in duplicate_pairs:
            if keep == "first":
                indices_to_remove.add(idx2)
            else:
                indices_to_remove.add(idx1)
        
        # Return texts that aren't marked for removal
        return [
            text
            for i, text in enumerate(texts)
            if i not in indices_to_remove
        ]
    
    def reset(self):
        """Clear all stored hashes and texts."""
        self.seen_hashes.clear()
        self.seen_texts.clear()


def deduplicate_texts(
    texts: List[str],
    similarity_threshold: float = 0.95,
    keep: str = "first",
) -> List[str]:
    """
    Convenience function for quick deduplication.
    
    Args:
        texts: List of texts to deduplicate
        similarity_threshold: Minimum similarity to consider duplicate
        keep: Which duplicate to keep ('first' or 'last')
        
    Returns:
        List of unique texts
    """
    deduplicator = Deduplicator(similarity_threshold=similarity_threshold)
    return deduplicator.deduplicate(texts, keep=keep)
