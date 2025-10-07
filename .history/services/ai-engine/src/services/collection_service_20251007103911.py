"""
Collection Service

Manages document collections for organizational purposes.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import asyncpg

logger = logging.getLogger(__name__)


class CollectionService:
    """Service for managing document collections."""

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize CollectionService.

        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool

    async def create_collection(
        self, user_id: UUID, name: str, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new collection.

        Args:
            user_id: User ID who owns the collection
            name: Collection name (must be unique per user)
            description: Optional description

        Returns:
            Created collection data

        Raises:
            ValueError: If collection name already exists for user
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Check if collection name exists for this user
                existing = await conn.fetchrow(
                    """
                    SELECT id FROM collections 
                    WHERE user_id = $1 AND name = $2
                    """,
                    user_id,
                    name,
                )

                if existing:
                    raise ValueError(f"Collection '{name}' already exists")

                # Create collection
                row = await conn.fetchrow(
                    """
                    INSERT INTO collections (user_id, name, description)
                    VALUES ($1, $2, $3)
                    RETURNING id, user_id, name, description, document_count, 
                              created_at, updated_at
                    """,
                    user_id,
                    name,
                    description,
                )

                logger.info(f"Created collection: {row['id']} for user {user_id}")
                return dict(row)

        except asyncpg.UniqueViolationError:
            raise ValueError(f"Collection '{name}' already exists")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    async def get_collection(
        self, collection_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get collection by ID.

        Args:
            collection_id: Collection ID
            user_id: Optional user ID for authorization check

        Returns:
            Collection data or None if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT id, user_id, name, description, document_count,
                           created_at, updated_at
                    FROM collections
                    WHERE id = $1
                """
                params = [collection_id]

                if user_id:
                    query += " AND user_id = $2"
                    params.append(user_id)

                row = await conn.fetchrow(query, *params)
                return dict(row) if row else None

        except Exception as e:
            logger.error(f"Error fetching collection {collection_id}: {e}")
            raise

    async def list_collections(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> List[Dict[str, Any]]:
        """
        List collections for a user.

        Args:
            user_id: User ID
            limit: Maximum number of results
            offset: Offset for pagination
            sort_by: Field to sort by (name, created_at, document_count)
            sort_order: Sort order (asc, desc)

        Returns:
            List of collections
        """
        try:
            # Validate sort parameters
            valid_sort_fields = ["name", "created_at", "updated_at", "document_count"]
            if sort_by not in valid_sort_fields:
                sort_by = "created_at"

            if sort_order.lower() not in ["asc", "desc"]:
                sort_order = "desc"

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT id, user_id, name, description, document_count,
                           created_at, updated_at
                    FROM collections
                    WHERE user_id = $1
                    ORDER BY {sort_by} {sort_order}
                    LIMIT $2 OFFSET $3
                    """,
                    user_id,
                    limit,
                    offset,
                )

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error listing collections for user {user_id}: {e}")
            raise

    async def update_collection(
        self,
        collection_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update collection details.

        Args:
            collection_id: Collection ID
            user_id: User ID (for authorization)
            name: New name (optional)
            description: New description (optional)

        Returns:
            Updated collection data or None if not found

        Raises:
            ValueError: If new name conflicts with existing collection
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Build dynamic update query
                updates = []
                params = [collection_id, user_id]
                param_count = 2

                if name is not None:
                    param_count += 1
                    updates.append(f"name = ${param_count}")
                    params.append(name)

                if description is not None:
                    param_count += 1
                    updates.append(f"description = ${param_count}")
                    params.append(description)

                if not updates:
                    # Nothing to update
                    return await self.get_collection(collection_id, user_id)

                query = f"""
                    UPDATE collections
                    SET {', '.join(updates)}
                    WHERE id = $1 AND user_id = $2
                    RETURNING id, user_id, name, description, document_count,
                              created_at, updated_at
                """

                row = await conn.fetchrow(query, *params)
                if row:
                    logger.info(f"Updated collection: {collection_id}")
                    return dict(row)
                return None

        except asyncpg.UniqueViolationError:
            raise ValueError(f"Collection '{name}' already exists")
        except Exception as e:
            logger.error(f"Error updating collection {collection_id}: {e}")
            raise

    async def delete_collection(
        self, collection_id: UUID, user_id: UUID
    ) -> bool:
        """
        Delete a collection.

        Note: Documents in the collection will have collection_id set to NULL.

        Args:
            collection_id: Collection ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM collections
                    WHERE id = $1 AND user_id = $2
                    """,
                    collection_id,
                    user_id,
                )

                deleted = result.split()[-1] == "1"
                if deleted:
                    logger.info(f"Deleted collection: {collection_id}")
                return deleted

        except Exception as e:
            logger.error(f"Error deleting collection {collection_id}: {e}")
            raise

    async def add_document_to_collection(
        self, collection_id: UUID, document_id: UUID, user_id: UUID
    ) -> bool:
        """
        Add a document to a collection.

        Args:
            collection_id: Collection ID
            document_id: Document ID
            user_id: User ID (for authorization)

        Returns:
            True if added, False if not found

        Raises:
            ValueError: If collection or document not found or not owned by user
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Verify collection exists and is owned by user
                collection = await conn.fetchrow(
                    "SELECT id FROM collections WHERE id = $1 AND user_id = $2",
                    collection_id,
                    user_id,
                )
                if not collection:
                    raise ValueError("Collection not found")

                # Update document
                result = await conn.execute(
                    """
                    UPDATE documents
                    SET collection_id = $1
                    WHERE id = $2 AND user_id = $3
                    """,
                    collection_id,
                    document_id,
                    user_id,
                )

                updated = result.split()[-1] == "1"
                if updated:
                    logger.info(
                        f"Added document {document_id} to collection {collection_id}"
                    )
                else:
                    raise ValueError("Document not found")

                return updated

        except Exception as e:
            logger.error(
                f"Error adding document {document_id} to collection {collection_id}: {e}"
            )
            raise

    async def remove_document_from_collection(
        self, document_id: UUID, user_id: UUID
    ) -> bool:
        """
        Remove a document from its collection.

        Args:
            document_id: Document ID
            user_id: User ID (for authorization)

        Returns:
            True if removed, False if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE documents
                    SET collection_id = NULL
                    WHERE id = $1 AND user_id = $2
                    """,
                    document_id,
                    user_id,
                )

                updated = result.split()[-1] == "1"
                if updated:
                    logger.info(f"Removed document {document_id} from collection")
                return updated

        except Exception as e:
            logger.error(
                f"Error removing document {document_id} from collection: {e}"
            )
            raise

    async def get_collection_documents(
        self, collection_id: UUID, user_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all documents in a collection.

        Args:
            collection_id: Collection ID
            user_id: User ID (for authorization)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of documents
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT d.id, d.user_id, d.file_name, d.file_type, d.file_size,
                           d.status, d.chunk_count, d.collection_id, d.metadata,
                           d.created_at, d.updated_at
                    FROM documents d
                    JOIN collections c ON d.collection_id = c.id
                    WHERE d.collection_id = $1 AND c.user_id = $2
                    ORDER BY d.created_at DESC
                    LIMIT $3 OFFSET $4
                    """,
                    collection_id,
                    user_id,
                    limit,
                    offset,
                )

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(
                f"Error fetching documents for collection {collection_id}: {e}"
            )
            raise
