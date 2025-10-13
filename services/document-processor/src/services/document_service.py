"""
Document Service
Business logic for document processing and management
"""

from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from uuid import UUID
import os
import hashlib
from datetime import datetime
from pathlib import Path

from src.models.database import Document, Tag, Collection, User
from src.utils.file_storage import FileStorage
from src.utils.text_extractor import (
    extract_text,
    get_page_count,
    extract_metadata
)
from src.services.ai_service import get_ai_service
import uuid
import json


class DocumentService:
    """Service for managing document operations"""

    def __init__(self, db: Session):
        self.db = db
        self.file_storage = FileStorage()
        self.ai_service = get_ai_service()

    def _get_or_create_default_user(self) -> UUID:
        """Get or create a default user for testing/development"""
        default_username = "default_user"
        user = self.db.query(User).filter(
            User.username == default_username
        ).first()

        if not user:
            user = User(
                id=uuid.uuid4(),
                username=default_username,
                email="default@inmyhead.dev",
                password_hash="not_used",
                full_name="Default User",
                is_verified=True,
                is_active=True
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        return user.id

    async def process_upload(
        self,
        file: UploadFile,
        collection_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[UUID] = None  # Will come from auth later
    ) -> Document:
        """
        Process an uploaded document

        Args:
            file: Uploaded file
            collection_id: Optional collection to add document to
            tags: Optional list of tag names
            user_id: User uploading the document

        Returns:
            Created document record
        """
        # Get or create default user if none provided
        if user_id is None:
            user_id = self._get_or_create_default_user()

        # Read file content
        content = await file.read()

        # Calculate file hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()

        # Check if document already exists
        existing_doc = self.db.query(Document).filter(
            Document.file_hash == file_hash,
            Document.user_id == user_id
        ).first()

        if existing_doc:
            return existing_doc

        # Save file to storage (returns relative path)
        relative_file_path = await self.file_storage.save_file(
            content=content,
            filename=file.filename,
            content_type=file.content_type
        )

        # Get full path for text extraction
        full_file_path = self.file_storage.get_full_path(relative_file_path)

        # Determine document type from mime type
        mime_type = file.content_type or 'application/octet-stream'
        doc_type = self._get_document_type(mime_type, file.filename)

        # Extract text content
        try:
            print(f"DEBUG: Extracting text from {full_file_path}, type: {doc_type}")
            extracted_text = await extract_text(str(full_file_path), doc_type)
            print(f"DEBUG: Extraction successful, length: {len(extracted_text) if extracted_text else 0}")
            status = "completed"
            word_count = len(extracted_text.split()) if extracted_text else 0
        except Exception as e:
            print(f"Text extraction failed: {e}")
            import traceback
            traceback.print_exc()
            extracted_text = None
            status = "failed"
            word_count = 0

        # Extract page count
        page_count = get_page_count(str(full_file_path), doc_type)

        # Extract metadata
        try:
            doc_metadata = await extract_metadata(str(full_file_path), doc_type)
            print(f"DEBUG: Metadata extracted: {doc_metadata}")
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            doc_metadata = {}

        # Generate embedding for vector storage
        embedding_vector = None
        embedding_model_name = None
        if extracted_text and status == "completed":
            try:
                # Generate embedding (limit to 5000 chars for performance)
                embedding_vector = self.ai_service.generate_embedding(
                    extracted_text[:5000]
                )
                embedding_model_name = "text-embedding-ada-002"  # OpenAI model
                print(f"DEBUG: Generated embedding of dimension {len(embedding_vector)}")
            except Exception as e:
                print(f"Embedding generation failed: {e}")

        # Create document record
        document = Document(
            filename=file.filename,
            original_filename=file.filename,
            title=doc_metadata.get('title', file.filename),
            file_path=relative_file_path,
            file_size_bytes=len(content),
            mime_type=mime_type,
            file_hash=file_hash,
            extracted_text=extracted_text,
            word_count=word_count,
            page_count=page_count,
            embedding_model=embedding_model_name,
            status=status,
            collection_id=collection_id,
            user_id=user_id,
            indexed_at=datetime.utcnow() if status == "completed" else None
        )

        self.db.add(document)
        self.db.flush()  # Get document ID without committing

        # Store embedding in Qdrant vector database
        if embedding_vector and document.id:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import PointStruct
                import os

                # Connect to Qdrant
                qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
                qdrant_client = QdrantClient(url=qdrant_url)

                # Store in document_embeddings collection
                point = PointStruct(
                    id=str(document.id),
                    vector=embedding_vector,
                    payload={
                        "document_id": str(document.id),
                        "title": document.title,
                        "filename": document.filename,
                        "mime_type": document.mime_type,
                        "extracted_text_preview": extracted_text[:500] if extracted_text else "",
                        "user_id": str(user_id),
                        "created_at": document.created_at.isoformat() if document.created_at else None
                    }
                )

                qdrant_client.upsert(
                    collection_name="document_embeddings",
                    points=[point]
                )

                # Update document with embedding_id
                document.embedding_id = document.id
                print(f"DEBUG: Stored embedding in Qdrant for document {document.id}")

            except Exception as e:
                print(f"Warning: Failed to store embedding in Qdrant: {e}")
                # Don't fail the upload if Qdrant storage fails

        # Add tags using the association table relationship
        if tags:
            for tag_name in tags:
                tag = self._get_or_create_tag(tag_name, user_id)
                document.tags.append(tag)

        self.db.commit()
        self.db.refresh(document)

        return document

    def list_documents(
        self,
        skip: int = 0,
        limit: int = 50,
        collection_id: Optional[UUID] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> Tuple[List[Document], int]:
        """
        List documents with optional filtering

        Args:
            skip: Pagination offset
            limit: Maximum results
            collection_id: Filter by collection
            tag: Filter by tag name
            search: Search in titles
            user_id: User ID

        Returns:
            Tuple of (documents list, total count)
        """
        # Get or create default user if none provided
        if user_id is None:
            user_id = self._get_or_create_default_user()

        query = self.db.query(Document).filter(Document.user_id == user_id)

        # Apply filters
        if collection_id:
            query = query.filter(Document.collection_id == collection_id)

        if tag:
            # Use the tags relationship
            query = query.join(Document.tags).filter(Tag.name == tag)

        if search:
            query = query.filter(Document.title.ilike(f"%{search}%"))

        # Get total count
        total = query.count()

        # Apply pagination
        documents = (
            query.order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return documents, total

    def get_document(
        self, document_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[Document]:
        """Get a document by ID"""
        query = self.db.query(Document).filter(Document.id == document_id)
        if user_id:
            query = query.filter(Document.user_id == user_id)
        return query.first()

    def delete_document(
        self, document_id: UUID, user_id: Optional[UUID] = None
    ) -> bool:
        """
        Delete a document

        Args:
            document_id: Document ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        document = self.get_document(document_id, user_id)
        if not document:
            return False

        # Delete file from storage
        try:
            self.file_storage.delete_file(document.file_path)
        except Exception as e:
            print(f"Failed to delete file: {e}")

        # Delete document record (cascades to tags)
        self.db.delete(document)
        self.db.commit()

        return True

    def get_document_content(
        self, document_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[str]:
        """Get the extracted content of a document"""
        document = self.get_document(document_id, user_id)
        return document.extracted_text if document else None

    def _get_or_create_tag(
        self, tag_name: str, user_id: Optional[UUID]
    ) -> Tag:
        """Get existing tag or create new one"""
        tag = self.db.query(Tag).filter(
            Tag.name == tag_name,
            Tag.user_id == user_id
        ).first()

        if not tag:
            tag = Tag(name=tag_name, user_id=user_id)
            self.db.add(tag)
            self.db.flush()

        return tag

    def _get_document_type(self, mime_type: str, filename: str) -> str:
        """Determine document type from mime type and filename"""
        mime_to_type = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'text/plain': 'txt',
            'text/markdown': 'md',
        }

        doc_type = mime_to_type.get(mime_type)
        if doc_type:
            return doc_type

        # Fallback to file extension
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext if ext else 'other'
