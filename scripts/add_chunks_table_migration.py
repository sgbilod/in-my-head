"""
Database migration: Add document_chunks table.

This migration adds support for storing document chunks with embeddings
for improved RAG and semantic search capabilities.

Run with:
    python scripts/add_chunks_table_migration.py
"""

import asyncio
import logging
from sqlalchemy import (
    Column, String, Integer, BigInteger, Text, Boolean,
    DateTime, ForeignKey, Index, CheckConstraint, create_engine
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
import uuid as uuid_pkg

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

Base = declarative_base()


class DocumentChunk(Base):
    """
    Document chunks for RAG and semantic search.

    Stores chunks of documents with their embeddings for improved
    retrieval and context assembly.
    """
    __tablename__ = 'document_chunks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey('documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Position in document

    # Position tracking
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)

    # Statistics
    char_count = Column(Integer, nullable=False)
    word_count = Column(Integer, nullable=False)
    sentence_count = Column(Integer, nullable=False)

    # Chunking metadata
    chunking_strategy = Column(String(50), nullable=False)  # sentence, paragraph, fixed, semantic
    chunk_metadata = Column(JSONB, default={})  # Additional metadata (tokens, keywords, etc.)

    # Vector search
    embedding_id = Column(UUID(as_uuid=True), unique=True)  # ID in Qdrant
    embedding_model = Column(String(100))
    has_embedding = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "chunking_strategy IN ('sentence', 'paragraph', 'fixed', 'semantic')",
            name='check_chunking_strategy'
        ),
        CheckConstraint(
            "chunk_index >= 0",
            name='check_chunk_index_positive'
        ),
        CheckConstraint(
            "start_position >= 0",
            name='check_start_position_positive'
        ),
        CheckConstraint(
            "end_position > start_position",
            name='check_end_after_start'
        ),
        # Composite index for efficient chunk retrieval
        Index('idx_chunks_document_index', 'document_id', 'chunk_index'),
        # Index for finding chunks with embeddings
        Index('idx_chunks_embedding', 'document_id', 'has_embedding'),
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentChunk(id={self.id}, document_id={self.document_id}, "
            f"chunk_index={self.chunk_index})>"
        )


async def run_migration():
    """Run the migration to add document_chunks table."""
    # Get database URL from environment or use default
    import os
    from dotenv import load_dotenv

    load_dotenv()

    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev'
    )

    logger.info("=== Document Chunks Table Migration ===")
    logger.info(f"Database: {database_url.split('@')[1]}")

    try:
        # Create engine
        engine = create_engine(database_url)

        # Check if table already exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if 'document_chunks' in existing_tables:
            logger.warning("⚠ Table 'document_chunks' already exists!")

            # Ask user if they want to proceed
            response = input("Drop and recreate table? This will delete all chunk data! (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Migration cancelled.")
                return

            # Drop table
            logger.info("Dropping existing table...")
            Base.metadata.tables['document_chunks'].drop(engine)
            logger.info("✓ Table dropped")

        # Create table
        logger.info("Creating document_chunks table...")
        Base.metadata.tables['document_chunks'].create(engine)
        logger.info("✓ Table created successfully")

        # Verify table creation
        inspector = inspect(engine)
        columns = inspector.get_columns('document_chunks')
        indexes = inspector.get_indexes('document_chunks')

        logger.info(f"\n✓ Table verified: {len(columns)} columns, {len(indexes)} indexes")

        # Show table structure
        logger.info("\nTable structure:")
        logger.info("-" * 60)
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            logger.info(f"  {col['name']:<25} {str(col['type']):<20} {nullable}")

        logger.info("\nIndexes:")
        logger.info("-" * 60)
        for idx in indexes:
            cols = ', '.join(idx['column_names'])
            logger.info(f"  {idx['name']:<40} ({cols})")

        logger.info("\n" + "="*60)
        logger.info("✓ MIGRATION COMPLETE")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("1. Update document-processor to create chunks when processing documents")
        logger.info("2. Generate embeddings for chunks using ai-engine")
        logger.info("3. Store chunk embeddings in Qdrant chunk_embeddings collection")
        logger.info("4. Update search API to use chunk-level retrieval")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise


def main():
    """Main entry point."""
    asyncio.run(run_migration())


if __name__ == '__main__':
    main()
