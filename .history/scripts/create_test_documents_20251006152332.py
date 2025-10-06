"""
Create test documents in database for embedding generation.
"""

import asyncio
import asyncpg
import uuid as uuid_pkg
from datetime import datetime


TEST_DOCUMENTS = [
    {
        "title": "Introduction to Machine Learning",
        "content": """
Machine learning is a subset of artificial intelligence that enables 
computers to learn from data without being explicitly programmed. It 
involves algorithms that can identify patterns in data and make 
predictions or decisions based on those patterns.

There are three main types of machine learning: supervised learning, 
unsupervised learning, and reinforcement learning. Supervised learning 
uses labeled data to train models, while unsupervised learning finds 
patterns in unlabeled data. Reinforcement learning involves agents 
learning through trial and error.

Deep learning is a specialized form of machine learning that uses 
neural networks with multiple layers. These deep neural networks can 
learn complex representations of data and have achieved remarkable 
results in image recognition, natural language processing, and game 
playing.
        """.strip()
    },
    {
        "title": "Natural Language Processing Fundamentals",
        "content": """
Natural Language Processing (NLP) is a field of artificial intelligence 
that focuses on enabling computers to understand, interpret, and 
generate human language. NLP combines computational linguistics with 
machine learning and deep learning techniques.

Key NLP tasks include tokenization, part-of-speech tagging, named 
entity recognition, sentiment analysis, machine translation, and text 
summarization. Modern NLP systems use transformer models like BERT, 
GPT, and T5 to achieve state-of-the-art performance.

Transformers revolutionized NLP by introducing the attention mechanism, 
which allows models to weigh the importance of different words when 
processing text. This architecture has enabled models to capture 
long-range dependencies and context much better than previous approaches.
        """.strip()
    },
    {
        "title": "Vector Databases and Semantic Search",
        "content": """
Vector databases are specialized databases designed to store and search 
high-dimensional vector embeddings efficiently. They enable semantic 
search, which finds results based on meaning rather than exact keyword 
matches.

Popular vector databases include Qdrant, Pinecone, Weaviate, and Milvus. 
These systems use approximate nearest neighbor (ANN) algorithms like 
HNSW, IVF, or LSH to perform fast similarity searches even with millions 
of vectors.

Embeddings are dense vector representations of data created by machine 
learning models. Text embeddings capture semantic meaning, allowing 
similar concepts to have similar vector representations. This enables 
powerful retrieval augmented generation (RAG) systems that can find 
relevant context for language models.
        """.strip()
    },
]


async def create_test_documents():
    """Create test documents in database."""
    
    print("\n" + "=" * 70)
    print("CREATE TEST DOCUMENTS")
    print("=" * 70 + "\n")
    
    db_url = (
        "postgresql://inmyhead:inmyhead_dev_pass@"
        "localhost:5434/inmyhead_dev"
    )
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Get or create default user
        user_id = await conn.fetchval("""
            SELECT id FROM users LIMIT 1
        """)
        
        if not user_id:
            user_id = await conn.fetchval("""
                INSERT INTO users (id, username, email, created_at)
                VALUES ($1, 'test_user', 'test@example.com', NOW())
                RETURNING id
            """, uuid_pkg.uuid4())
            print(f"✅ Created test user: {user_id}")
        
        # Create documents
        created = 0
        
        for doc in TEST_DOCUMENTS:
            doc_id = uuid_pkg.uuid4()
            
            await conn.execute("""
                INSERT INTO documents (
                    id,
                    user_id,
                    filename,
                    original_filename,
                    file_path,
                    file_size_bytes,
                    mime_type,
                    file_hash,
                    title,
                    extracted_text,
                    text_content_length,
                    word_count,
                    status,
                    created_at,
                    updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, NOW(), NOW()
                )
                ON CONFLICT (id) DO NOTHING
            """,
                doc_id,
                user_id,
                f"{doc['title'].lower().replace(' ', '_')}.txt",
                f"{doc['title']}.txt",
                f"test/{doc_id}.txt",
                len(doc['content']),
                "text/plain",
                f"hash_{doc_id}",
                doc['title'],
                doc['content'],
                len(doc['content']),
                len(doc['content'].split()),
                "completed"
            )
            
            created += 1
            print(f"✅ Created: {doc['title']}")
            print(f"   Length: {len(doc['content'])} chars")
            print(f"   Words: {len(doc['content'].split())}")
        
        print(f"\n✅ Created {created} test documents")
        
    finally:
        await conn.close()
    
    print("=" * 70 + "\n")


def main():
    """Entry point."""
    asyncio.run(create_test_documents())


if __name__ == "__main__":
    main()
