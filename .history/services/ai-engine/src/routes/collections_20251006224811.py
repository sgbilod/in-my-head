"""
Collections API Routes

Endpoints for managing document collections.
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..services.collection_service import CollectionService
from ..dependencies import get_collection_service, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/collections", tags=["collections"])


# Request/Response Models
class CreateCollectionRequest(BaseModel):
    """Request model for creating a collection."""

    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    description: Optional[str] = Field(None, description="Optional description")


class UpdateCollectionRequest(BaseModel):
    """Request model for updating a collection."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class AddDocumentRequest(BaseModel):
    """Request model for adding a document to collection."""

    document_id: UUID


class CollectionResponse(BaseModel):
    """Response model for collection data."""

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    document_count: int
    created_at: str
    updated_at: str


# Endpoints
@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    request: CreateCollectionRequest,
    service: CollectionService = Depends(get_collection_service),
    user_id: UUID = Depends(get_current_user),
):
    """
    Create a new collection.

    - **name**: Collection name (must be unique per user)
    - **description**: Optional description
    """
    try:
        collection = await service.create_collection(
            user_id=user_id, name=request.name, description=request.description
        )
        return collection
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create collection",
        )


@router.get("", response_model=list[CollectionResponse])
async def list_collections(
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    service: CollectionService = Depends(get_collection_service),
    user_id: UUID = Depends(get_current_user),
):
    """
    List all collections for the current user.

    - **limit**: Maximum number of results (default: 100)
    - **offset**: Offset for pagination (default: 0)
    - **sort_by**: Field to sort by (name, created_at, document_count)
    - **sort_order**: Sort order (asc, desc)
    """
    try:
        collections = await service.list_collections(
            user_id=user_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return collections
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list collections",
        )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: UUID,
    service: CollectionService = Depends(get_collection_service),
    user_id: UUID = Depends(get_current_user),
):
    """Get collection by ID."""
    try:
        collection = await service.get_collection(collection_id, user_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
            )
        return collection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch collection",
        )


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: UUID,
    request: UpdateCollectionRequest,
    service: CollectionService = Depends(get_collection_service),
    user_id: UUID = Depends(get_current_user),
):
    """
    Update collection details.

    - **name**: New name (optional)
    - **description**: New description (optional)
    """
    try:
        collection = await service.update_collection(
            collection_id=collection_id,
            user_id=user_id,
            name=request.name,
            description=request.description,
        )
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
            )
        return collection
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update collection",
        )


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: UUID,
    service: CollectionService = Depends(get_collection_service),
    user_id: UUID = Depends(get_current_user),
):
    """
    Delete a collection.

    Note: Documents in the collection will remain but will no longer be associated with the collection.
    """
    try:
        deleted = await service.delete_collection(collection_id, user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete collection",
        )


@router.post("/{collection_id}/documents", status_code=status.HTTP_200_OK)
async def add_document_to_collection(
    collection_id: UUID,
    request: AddDocumentRequest,
    service: CollectionService = Depends(get_collection_service),
    user_id: UUID = Depends(get_current_user),
):
    """
    Add a document to a collection.

    - **document_id**: Document ID to add
    """
    try:
        await service.add_document_to_collection(
            collection_id=collection_id,
            document_id=request.document_id,
            user_id=user_id,
        )
        return {"message": "Document added to collection"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding document to collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add document to collection",
        )


@router.delete(
    "/{collection_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_document_from_collection(
    collection_id: UUID,
    document_id: UUID,
    service: CollectionService = Depends(get_collection_service),
    user_id: UUID = Depends(get_current_user),
):
    """Remove a document from a collection."""
    try:
        removed = await service.remove_document_from_collection(document_id, user_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing document from collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove document from collection",
        )


@router.get("/{collection_id}/documents")
async def get_collection_documents(
    collection_id: UUID,
    limit: int = 100,
    offset: int = 0,
    service: CollectionService = Depends(get_collection_service),
    user_id: UUID = Depends(get_current_user),
):
    """
    Get all documents in a collection.

    - **limit**: Maximum number of results (default: 100)
    - **offset**: Offset for pagination (default: 0)
    """
    try:
        documents = await service.get_collection_documents(
            collection_id=collection_id, user_id=user_id, limit=limit, offset=offset
        )
        return {"documents": documents, "total": len(documents)}
    except Exception as e:
        logger.error(f"Error fetching collection documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch collection documents",
        )
