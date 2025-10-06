"""
Simplified embedding generation with progress output.

This script:
1. Loads sentence-transformers model (with progress)
2. Chunks documents using ChunkerService
3. Generates embeddings in batches
4. Stores in Qdrant
5. Updates PostgreSQL

Optimized for transparency and debugging.
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ai-engine"))

print("=" * 70)
print("EMBEDDING GENERATION - SIMPLIFIED VERSION")
print("=" * 70)

# Step 1: Test sentence-transformers
print("\n[1/6] Testing sentence-transformers...")
try:
    from sentence_transformers import SentenceTransformer
    print("     ✅ Imported successfully")
except ImportError as e:
    print(f"     ❌ Import failed: {e}")
    print("\nInstalling sentence-transformers...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sentence-transformers"])
    from sentence_transformers import SentenceTransformer
    print("     ✅ Installed and imported")

# Step 2: Load model
print("\n[2/6] Loading embedding model (all-MiniLM-L6-v2)...")
print("     (This may take 1-2 minutes on first run - downloading ~90MB)")
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("     ✅ Model loaded successfully")
    
    # Quick test
    test_embedding = model.encode("test")
    print(f"     ✅ Test embedding: {len(test_embedding)} dimensions")
except Exception as e:
    print(f"     ❌ Model loading failed: {e}")
    sys.exit(1)

# Step 3: Connect to database
print("\n[3/6] Connecting to PostgreSQL...")
async def main():
    db_url = "postgresql://inmyhead:inmyhead_dev_pass@localhost:5434/inmyhead_dev"
    
    try:
        conn = await asyncpg.connect(db_url)
        print("     ✅ Connected to database")
    except Exception as e:
        print(f"     ❌ Connection failed: {e}")
        return
    
    try:
        # Step 4: Fetch documents
        print("\n[4/6] Fetching documents with text...")
        docs = await conn.fetch("""
            SELECT id, title, extracted_text
            FROM documents
            WHERE extracted_text IS NOT NULL
            AND LENGTH(extracted_text) > 10
            ORDER BY created_at DESC
        """)
        
        print(f"     ✅ Found {len(docs)} documents")
        for doc in docs:
            text_len = len(doc['extracted_text'])
            print(f"        - {doc['title']}: {text_len} chars")
        
        if len(docs) == 0:
            print("\n     ⚠️  No documents to process!")
            return
        
        # Step 5: Chunk documents
        print("\n[5/6] Chunking documents...")
        from src.services.chunker_service import get_chunker_service
        
        chunker = get_chunker_service()
        all_chunks = []
        
        for i, doc in enumerate(docs, 1):
            print(f"     [{i}/{len(docs)}] Chunking: {doc['title']}")
            
            result = chunker.chunk_document(
                text=doc['extracted_text'],
                strategy="sentence",
                chunk_size=500,
                chunk_overlap=50
            )
            
            print(f"         → {len(result['chunks'])} chunks")
            
            # Store chunks in database
            for j, chunk in enumerate(result['chunks']):
                chunk_id = await conn.fetchval("""
                    INSERT INTO document_chunks (
                        document_id, content, chunk_index,
                        start_position, end_position,
                        char_count, word_count, sentence_count,
                        chunking_strategy
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (document_id, chunk_index)
                    DO UPDATE SET content = EXCLUDED.content
                    RETURNING id
                """,
                    doc['id'],
                    chunk['content'],
                    j,
                    chunk['positions']['start_char'],
                    chunk['positions']['end_char'],
                    chunk['statistics']['char_count'],
                    chunk['statistics']['word_count'],
                    chunk['statistics']['sentence_count'],
                    'sentence'
                )
                
                all_chunks.append({
                    'chunk_id': chunk_id,
                    'document_id': doc['id'],
                    'content': chunk['content'],
                    'chunk_index': j,
                    'document_title': doc['title']
                })
        
        print(f"     ✅ Total chunks created: {len(all_chunks)}")
        
        # Step 6: Generate embeddings
        print("\n[6/6] Generating embeddings...")
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
        
        # Connect to Qdrant
        qdrant = QdrantClient(url="http://localhost:6333")
        print("     ✅ Connected to Qdrant")
        
        # Create collection
        collection_name = "chunk_embeddings"
        try:
            qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"     ✅ Created collection: {collection_name}")
        except Exception:
            print(f"     ℹ️  Collection already exists: {collection_name}")
        
        # Generate and upload embeddings in batches
        batch_size = 32
        num_batches = (len(all_chunks) + batch_size - 1) // batch_size
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(all_chunks))
            batch = all_chunks[start_idx:end_idx]
            
            print(f"     [{batch_idx + 1}/{num_batches}] Batch {start_idx + 1}-{end_idx}...")
            
            # Extract content
            texts = [chunk['content'] for chunk in batch]
            
            # Generate embeddings
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
            
            print(f"         ✅ {len(batch)} embeddings stored")
        
        # Final stats
        collection_info = qdrant.get_collection(collection_name)
        chunk_count = await conn.fetchval(
            "SELECT COUNT(*) FROM document_chunks WHERE has_embedding = TRUE"
        )
        
        print(f"\n{'=' * 70}")
        print("EMBEDDING GENERATION COMPLETE!")
        print(f"{'=' * 70}")
        print(f"✅ Documents processed: {len(docs)}")
        print(f"✅ Chunks created: {len(all_chunks)}")
        print(f"✅ Embeddings in Qdrant: {collection_info.points_count}")
        print(f"✅ PostgreSQL records updated: {chunk_count}")
        print(f"\nReady for RAG testing! Run: python scripts/test_rag_pipeline.py")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
