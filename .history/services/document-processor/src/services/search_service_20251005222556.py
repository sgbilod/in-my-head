"""
Search Service
Handles semantic search and document similarity
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import json

from src.models.database import Document
from src.services.ai_service import get_ai_service


class SearchService:
    """Service for search operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = get_ai_service()
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.5,
        user_id: Optional[UUID] = None
    ) -> List[dict]:
        """
        Perform semantic search using embeddings
        
        Args:
            query: Search query text
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold
            user_id: User ID
        
        Returns:
            List of documents with similarity scores
        """
        # Generate query embedding
        query_embedding = self.ai_service.generate_embedding(query)
        
        # Get all documents (filter by user in production)
        documents = self.db.query(Document).all()
        
        results = []
        for doc in documents:
            if not doc.embedding:
                continue
            
            # Parse embedding from JSON string
            try:
                doc_embedding = json.loads(doc.embedding)
            except:
                continue
            
            # Calculate similarity
            similarity = self.ai_service.calculate_similarity(
                query_embedding,
                doc_embedding
            )
            
            if similarity >= min_similarity:
                results.append({
                    "document_id": str(doc.id),
                    "title": doc.title,
                    "similarity": similarity,
                    "excerpt": self._get_excerpt(doc.extracted_text, 200)
                })
        
        # Sort by similarity and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    async def find_similar(
        self,
        document_id: UUID,
        limit: int = 10,
        min_similarity: float = 0.5,
        user_id: Optional[UUID] = None
    ) -> List[dict]:
        """
        Find documents similar to a given document
        
        Args:
            document_id: ID of the reference document
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            user_id: User ID
        
        Returns:
            List of similar documents
        """
        # Get reference document
        ref_doc = self.db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not ref_doc or not ref_doc.embedding:
            return []
        
        # Parse reference embedding
        try:
            ref_embedding = json.loads(ref_doc.embedding)
        except:
            return []
        
        # Get all other documents
        documents = self.db.query(Document).filter(
            Document.id != document_id
        ).all()
        
        results = []
        for doc in documents:
            if not doc.embedding:
                continue
            
            try:
                doc_embedding = json.loads(doc.embedding)
            except:
                continue
            
            similarity = self.ai_service.calculate_similarity(
                ref_embedding,
                doc_embedding
            )
            
            if similarity >= min_similarity:
                results.append({
                    "document_id": str(doc.id),
                    "title": doc.title,
                    "similarity": similarity,
                    "excerpt": self._get_excerpt(doc.extracted_text, 200)
                })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    async def generate_missing_embeddings(self) -> int:
        """
        Generate embeddings for documents that don't have them
        
        Returns:
            Number of documents processed
        """
        # Get documents without embeddings
        documents = self.db.query(Document).filter(
            Document.embedding == None,
            Document.extracted_text != None
        ).all()
        
        count = 0
        for doc in documents:
            if doc.extracted_text:
                # Generate embedding
                embedding = self.ai_service.generate_embedding(
                    doc.extracted_text[:5000]  # Limit text length
                )
                
                # Store as JSON string
                doc.embedding = json.dumps(embedding)
                count += 1
        
        if count > 0:
            self.db.commit()
        
        return count
    
    def _get_excerpt(self, text: Optional[str], length: int) -> str:
        """Get excerpt from text"""
        if not text:
            return ""
        
        if len(text) <= length:
            return text
        
        return text[:length] + "..."
