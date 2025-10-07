"""
Force download sentence-transformers model and generate embeddings.

This script:
1. Forces model download with progress
2. Tests embedding generation
3. Creates embeddings for documents if successful
"""

print("=" * 70)
print("FORCE MODEL DOWNLOAD & EMBEDDING GENERATION")
print("=" * 70)

# Step 1: Install/upgrade sentence-transformers
print("\n[1/5] Ensuring sentence-transformers installed...")
import subprocess
import sys

try:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--upgrade", "sentence-transformers", "-q"
    ])
    print("     ✅ sentence-transformers ready")
except Exception as e:
    print(f"     ❌ Installation failed: {e}")
    sys.exit(1)

# Step 2: Force download model with progress
print("\n[2/5] Downloading model (this may take 2-3 minutes)...")
print("     Model: all-MiniLM-L6-v2 (~90MB)")

try:
    from sentence_transformers import SentenceTransformer
    print("     Importing model (downloading if needed)...")
    
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    print("     ✅ Model loaded successfully")
except Exception as e:
    print(f"     ❌ Model loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test embedding
print("\n[3/5] Testing embedding generation...")
try:
    test_text = "This is a test sentence for embedding."
    embedding = model.encode(test_text)
    print(f"     ✅ Generated embedding: {len(embedding)} dimensions")
    print(f"     Sample values: {embedding[:3]}")
except Exception as e:
    print(f"     ❌ Embedding failed: {e}")
    sys.exit(1)

# Step 4: Generate embeddings for documents
print("\n[4/5] Generating embeddings for documents...")

import asyncio
import asyncpg
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ai-engine"))

from src.services.chunker_service import get_chunker_service, ChunkingStrategy
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


async def generate():
    """Generate embeddings."""
    # Connect to database
    conn = await asyncpg.connect(
        "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    )
    
    try:
        # Fetch documents
        docs = await conn.fetch("""
            SELECT id, title, extracted_text
            FROM documents
            WHERE extracted_text IS NOT NULL
            AND LENGTH(extracted_text) > 10
            ORDER BY created_at DESC
        """)
        
        print(f"     Found {len(docs)} documents")
        
        if len(docs) == 0:
            print("     ⚠️  No documents to process")
            return False
        
        # Initialize chunker and Qdrant
        chunker = get_chunker_service()
        qdrant = QdrantClient(url="http://localhost:6333")
        
        # Create collection
        collection_name = "chunk_embeddings"
        try:
            qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"     ✅ Created Qdrant collection: {collection_name}")
        except Exception:
            print(f"     ℹ️  Collection exists: {collection_name}")
        
        # Process documents
        all_chunks = []
        for i, doc in enumerate(docs, 1):
            print(f"     [{i}/{len(docs)}] {doc['title']}")
            
            # Chunk document
            result = chunker.chunk_document(
                document_id=str(doc['id']),
                content=doc['extracted_text'],
                strategy=ChunkingStrategy.SENTENCE,
                chunk_size=500,
                chunk_overlap=50
            )
            
            print(f"         → {len(result)} chunks")
            
            # Store chunks in database and collect for embedding
            for chunk in result:
                # Chunk already has its ID from chunker service
                all_chunks.append({
                    'chunk_id': chunk.id,
                    'document_id': doc['id'],
                    'content': chunk.content,
                    'chunk_index': chunk.chunk_index,
                    'document_title': doc['title']
                })
        
        print(f"\n     ✅ Total chunks: {len(all_chunks)}")
        
        # Generate embeddings in batches
        print("\n[5/5] Generating and storing embeddings...")
        batch_size = 32
        num_batches = (len(all_chunks) + batch_size - 1) // batch_size
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(all_chunks))
            batch = all_chunks[start_idx:end_idx]
            
            print(f"     Batch {batch_idx + 1}/{num_batches}: chunks {start_idx + 1}-{end_idx}")
            
            # Generate embeddings
            texts = [chunk['content'] for chunk in batch]
            embeddings = model.encode(texts, show_progress_bar=False)
            
            # Upload to Qdrant
            points = [
                PointStruct(
                    id=str(chunk['chunk_id']),
                    vector=embedding.tolist(),
                    payload={
                        'document_id': str(chunk['document_id']),
                        'document_title': chunk['document_title'],
                        'content': chunk['content'],
                        'chunk_index': chunk['chunk_index']
                    }
                )
                for chunk, embedding in zip(batch, embeddings)
            ]
            
            qdrant.upsert(collection_name=collection_name, points=points)
            
            # Update PostgreSQL
            for chunk in batch:
                await conn.execute("""
                    UPDATE document_chunks
                    SET embedding_id = id,
                        embedding_model = $1,
                        has_embedding = TRUE
                    WHERE id = $2
                """, 'all-MiniLM-L6-v2', chunk['chunk_id'])
            
            print(f"         ✅ Stored {len(batch)} embeddings")
        
        # Final stats
        collection_info = qdrant.get_collection(collection_name)
        chunk_count = await conn.fetchval(
            "SELECT COUNT(*) FROM document_chunks WHERE has_embedding = TRUE"
        )
        
        print(f"\n{'=' * 70}")
        print("✅ EMBEDDING GENERATION COMPLETE!")
        print(f"{'=' * 70}")
        print(f"Documents: {len(docs)}")
        print(f"Chunks: {len(all_chunks)}")
        print(f"Qdrant vectors: {collection_info.points_count}")
        print(f"PostgreSQL updated: {chunk_count}")
        print(f"\n✨ Ready for RAG testing!")
        
        return True
        
    finally:
        await conn.close()


# Run generation
success = asyncio.run(generate())

if success:
    print("\n🎯 Next step: python scripts/test_rag_pipeline.py")
else:
    print("\n⚠️  No documents found or error occurred")
