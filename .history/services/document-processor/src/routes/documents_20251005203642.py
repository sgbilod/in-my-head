"""
Document Routes
API endpoints for document management
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
import os
from datetime import datetime

from src.database.connection import get_db_session
from src.services.document_service import DocumentService
from src.models.schemas import DocumentResponse, DocumentCreate, DocumentList

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    collection_id: Optional[UUID] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tag names"),
    db: Session = Depends(get_db_session)
):
    """
    Upload a document for processing
    
    Args:
        file: The document file to upload
        collection_id: Optional collection ID to organize the document
        tags: Optional comma-separated list of tags
        db: Database session
    
    Returns:
        Document metadata with processing status
    
    Example:
        Upload a PDF:
        ```
        curl -X POST "http://localhost:8001/documents/upload" \\
             -F "file=@document.pdf" \\
             -F "collection_id=1" \\
             -F "tags=important,research"
        ```
    """
    # Validate file type
    allowed_types = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'text/plain': '.txt',
        'text/markdown': '.md',
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. "
                   f"Supported types: {', '.join(allowed_types.values())}"
        )
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
    
    # Process document
    doc_service = DocumentService(db)
    try:
        document = await doc_service.process_upload(
            file=file,
            collection_id=collection_id,
            tags=tag_list
        )
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of documents to return"),
    collection_id: Optional[UUID] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """
    List documents with optional filtering
    
    Args:
        skip: Pagination offset
        limit: Maximum number of results
        collection_id: Filter by collection
        tag: Filter by tag name
        search: Search in document titles
        db: Database session
    
    Returns:
        List of documents with metadata
    """
    doc_service = DocumentService(db)
    documents, total = doc_service.list_documents(
        skip=skip,
        limit=limit,
        collection_id=collection_id,
        tag=tag,
        search=search
    )
    
    return {
        "documents": documents,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db_session)
):
    """
    Get a specific document by ID
    
    Args:
        document_id: Document ID
        db: Database session
    
    Returns:
        Document details
    """
    doc_service = DocumentService(db)
    document = doc_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db_session)
):
    """
    Delete a document
    
    Args:
        document_id: Document ID
        db: Database session
    """
    doc_service = DocumentService(db)
    success = doc_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return None


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: UUID,
    db: Session = Depends(get_db_session)
):
    """
    Get the extracted content of a document
    
    Args:
        document_id: Document ID
        db: Database session
    
    Returns:
        Document content as text
    """
    doc_service = DocumentService(db)
    content = doc_service.get_document_content(document_id)
    
    if content is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"content": content}
