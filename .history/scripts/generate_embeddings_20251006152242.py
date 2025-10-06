"""
Generate embeddings for all existing documents.

Complete workflow:
1. Fetch documents from PostgreSQL
2. Chunk each document
3. Generate embeddings for chunks
4. Store chunks in PostgreSQL
5. Store embeddings in Qdrant
6. Test retrieval
"""

import asyncio
import asyncpg
import logging
from datetime import datetime
from typing import List, Dict, Any
import uuid as uuid_pkg

import sys
import os
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "services", "ai-engine")
)

from src.services.chunker_service import (
    get_chunker_service,
    ChunkingStrategy
)
from src.services.embedding_service import get_embedding_service
from src.services.qdrant_service import get_qdrant_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


DB_URL = (
    "postgresql://inmyhead:inmyhead_dev_pass@"
    "localhost:5434/inmyhead_dev"
)


async def fetch_documents() -> List[Dict[str, Any]]:
    """Fetch all documents from database."""
    
    conn = await asyncpg.connect(DB_URL)
    
    try:
        docs = await conn.fetch("""
            SELECT 
                id, 
                title, 
                extracted_text,
                text_content_length,
                word_count,
                mime_type
            FROM documents
            WHERE extracted_text IS NOT NULL
            AND text_content_length > 0
            ORDER BY created_at DESC
        """)
        
        logger.info(f"Fetched {len(docs)} documents")
        return [dict(doc) for doc in docs]
        
    finally:
        await conn.close()


async def chunk_document(
    document: Dict[str, Any],
    strategy: ChunkingStrategy = ChunkingStrategy.SENTENCE
) -> List[Dict[str, Any]]:
    """
    Chunk a document.
    
    Args:
        document: Document dict
        strategy: Chunking strategy
        
    Returns:
        List of chunk dicts
    """
    
    chunker = get_chunker_service()
    
    document_id = str(document["id"])
    content = document["extracted_text"]
    
    if not content or len(content.strip()) < 50:
        logger.warning(f"Document {document_id} too short, skipping")
        return []
    
    chunks = chunker.chunk_document(
        document_id=document_id,
        content=content,
        strategy=strategy,
        chunk_size=500,
        chunk_overlap=50
    )
    
    logger.info(
        f"  Chunked '{document['title'][:40]}': "
        f"{len(chunks)} chunks"
    )
    
    return chunks


async def store_chunks(
    chunks: List[Any]
) -> List[Dict[str, Any]]:
    """
    Store chunks in PostgreSQL.
    
    Args:
        chunks: List of DocumentChunk objects
        
    Returns:
        List of chunk dicts with IDs
    """
    
    if not chunks:
        return []
    
    conn = await asyncpg.connect(DB_URL)
    
    try:
        stored_chunks = []
        
        for chunk in chunks:
            metadata = chunk.metadata
            
            chunk_id = await conn.fetchval(
                """
                INSERT INTO document_chunks (
                    id,
                    document_id,
                    content,
                    chunk_index,
                    start_position,
                    end_position,
                    char_count,
                    word_count,
                    sentence_count,
                    chunking_strategy,
                    chunk_metadata,
                    has_embedding,
                    created_at,
                    updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    NOW(), NOW()
                )
                ON CONFLICT (id) DO UPDATE
                SET content = EXCLUDED.content,
                    updated_at = NOW()
                RETURNING id
                """,
                uuid_pkg.UUID(metadata.chunk_id),
                uuid_pkg.UUID(metadata.document_id),
                chunk.content,
                metadata.chunk_index,
                metadata.start_position,
                metadata.end_position,
                metadata.char_count,
                metadata.word_count,
                metadata.sentence_count,
                "sentence",  # Default strategy
                {},  # Empty metadata for now
                False  # Will be updated when embedding generated
            )
            
            stored_chunks.append({
                "id": chunk_id,
                "document_id": metadata.document_id,
                "content": chunk.content,
                "chunk_index": metadata.chunk_index,
                "char_count": metadata.char_count,
                "word_count": metadata.word_count,
                "sentence_count": metadata.sentence_count,
                "chunking_strategy": "sentence"
            })
        
        logger.info(f"  Stored {len(stored_chunks)} chunks in PostgreSQL")
        return stored_chunks
        
    finally:
        await conn.close()


async def process_document(
    document: Dict[str, Any]
) -> int:
    """
    Process single document: chunk, store, embed.
    
    Args:
        document: Document dict
        
    Returns:
        Number of chunks processed
    """
    
    try:
        # Chunk document
        chunks = await chunk_document(document)
        
        if not chunks:
            return 0
        
        # Store chunks
        stored_chunks = await store_chunks(chunks)
        
        if not stored_chunks:
            return 0
        
        # Add document title to chunks
        for chunk in stored_chunks:
            chunk["document_title"] = document["title"]
        
        # Generate and store embeddings
        embedding_service = get_embedding_service()
        processed = await embedding_service.process_chunks(stored_chunks)
        
        return processed
        
    except Exception as e:
        logger.error(
            f"Error processing document {document['id']}: {e}",
            exc_info=True
        )
        return 0


async def generate_all_embeddings():
    """Main function to generate embeddings for all documents."""
    
    print("\n" + "=" * 70)
    print("GENERATE EMBEDDINGS FOR ALL DOCUMENTS")
    print("=" * 70 + "\n")
    
    start_time = datetime.now()
    
    # Initialize services
    logger.info("Initializing services...")
    embedding_service = get_embedding_service()
    qdrant_service = get_qdrant_service()
    
    # Ensure Qdrant collection exists
    logger.info("Setting up Qdrant collection...")
    await embedding_service.ensure_collection("chunk_embeddings")
    
    # Fetch documents
    logger.info("Fetching documents from database...")
    documents = await fetch_documents()
    
    if not documents:
        print("\n⚠️  No documents found in database!")
        print("\nTo add documents:")
        print("  1. Upload files via document-processor")
        print("  2. Ensure extracted_text is populated")
        print("  3. Run this script again\n")
        return
    
    print(f"\n📄 Found {len(documents)} documents to process\n")
    
    # Process each document
    total_chunks = 0
    
    for i, document in enumerate(documents, 1):
        print(f"\n[{i}/{len(documents)}] Processing: {document['title']}")
        print(f"  Length: {document['text_content_length']} chars")
        
        chunks_processed = await process_document(document)
        total_chunks += chunks_processed
        
        print(f"  ✅ Processed {chunks_processed} chunks")
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 70)
    print("✅ EMBEDDING GENERATION COMPLETE")
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"  Documents processed: {len(documents)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Avg chunks/doc: {total_chunks / len(documents):.1f}")
    print(f"  Processing time: {elapsed:.1f}s")
    print(f"  Speed: {total_chunks / elapsed:.1f} chunks/sec")
    
    # Get Qdrant stats
    try:
        collection_info = qdrant_service.client.get_collection(
            "chunk_embeddings"
        )
        print(
            f"\n🔍 Qdrant collection stats:"
        )
        print(f"  Vectors: {collection_info.points_count}")
        print(
            f"  Dimension: "
            f"{collection_info.config.params.vectors.size}"
        )
    except Exception as e:
        logger.error(f"Could not get Qdrant stats: {e}")
    
    print("\n✅ Ready for RAG retrieval!")
    print("=" * 70 + "\n")


def main():
    """Entry point."""
    asyncio.run(generate_all_embeddings())


if __name__ == "__main__":
    main()
