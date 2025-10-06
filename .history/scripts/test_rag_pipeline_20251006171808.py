"""
Test the complete RAG pipeline end-to-end.

Tests:
1. Qdrant collection exists
2. Embeddings stored correctly
3. Vector search works
4. Keyword search works
5. Hybrid search works
6. Re-ranking works
7. Context assembly works
8. Citation extraction works
"""

import asyncio
import logging
from datetime import datetime

import sys
import os
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "services", "ai-engine")
)

from src.services.rag_service import get_rag_service
from src.services.qdrant_service import get_qdrant_service

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


TEST_QUERIES = [
    "What is machine learning?",
    "How does AI work?",
    "Explain neural networks",
    "What are transformers in NLP?",
    "Tell me about deep learning"
]


async def test_qdrant_collection():
    """Test Qdrant collection exists and has data."""
    
    print("\n" + "=" * 70)
    print("TEST 1: Qdrant Collection")
    print("=" * 70 + "\n")
    
    try:
        qdrant = get_qdrant_service()
        collection_info = qdrant.client.get_collection("chunk_embeddings")
        
        print(f"✅ Collection exists: chunk_embeddings")
        print(f"  Vectors: {collection_info.points_count}")
        print(
            f"  Dimension: {collection_info.config.params.vectors.size}"
        )
        print(
            f"  Distance: {collection_info.config.params.vectors.distance}"
        )
        
        if collection_info.points_count == 0:
            print("\n⚠️  Warning: No vectors in collection!")
            print("  Run: python scripts/generate_embeddings.py")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_vector_search():
    """Test vector similarity search."""
    
    print("\n" + "=" * 70)
    print("TEST 2: Vector Search")
    print("=" * 70 + "\n")
    
    try:
        rag = get_rag_service()
        
        query = TEST_QUERIES[0]
        print(f"Query: '{query}'")
        
        results = await rag.vector_search(query, limit=5)
        
        print(f"\n✅ Retrieved {len(results)} results")
        
        for i, result in enumerate(results[:3], 1):
            print(f"\n  Result {i}:")
            print(f"    Score: {result.score:.4f}")
            print(f"    Content: {result.content[:100]}...")
            print(f"    Document: {result.metadata.get('document_title', 'N/A')}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_keyword_search():
    """Test keyword search."""
    
    print("\n" + "=" * 70)
    print("TEST 3: Keyword Search")
    print("=" * 70 + "\n")
    
    try:
        rag = get_rag_service()
        
        query = TEST_QUERIES[0]
        print(f"Query: '{query}'")
        
        # First get some chunks via vector search
        vector_results = await rag.vector_search(query, limit=20)
        
        # Then apply keyword search
        keyword_results = rag.keyword_search(
            query,
            vector_results,
            top_k=5
        )
        
        print(f"\n✅ Keyword search returned {len(keyword_results)} results")
        
        for i, result in enumerate(keyword_results[:3], 1):
            print(f"\n  Result {i}:")
            print(f"    Score: {result.score:.4f}")
            print(f"    Content: {result.content[:100]}...")
        
        return len(keyword_results) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hybrid_search():
    """Test hybrid search."""
    
    print("\n" + "=" * 70)
    print("TEST 4: Hybrid Search")
    print("=" * 70 + "\n")
    
    try:
        rag = get_rag_service()
        
        query = TEST_QUERIES[0]
        print(f"Query: '{query}'")
        print(
            f"Weights: {rag.vector_weight:.1f} vector, "
            f"{rag.keyword_weight:.1f} keyword"
        )
        
        # Get vector results
        vector_results = await rag.vector_search(query, limit=20)
        
        # Get keyword results
        keyword_results = rag.keyword_search(query, vector_results, top_k=10)
        
        # Combine
        hybrid_results = rag.hybrid_search(vector_results, keyword_results)
        
        print(f"\n✅ Hybrid search returned {len(hybrid_results)} results")
        
        for i, result in enumerate(hybrid_results[:3], 1):
            print(f"\n  Result {i}:")
            print(f"    Score: {result.score:.4f}")
            print(f"    Content: {result.content[:100]}...")
        
        return len(hybrid_results) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_reranking():
    """Test cross-encoder re-ranking."""
    
    print("\n" + "=" * 70)
    print("TEST 5: Re-ranking")
    print("=" * 70 + "\n")
    
    try:
        rag = get_rag_service()
        
        query = TEST_QUERIES[0]
        print(f"Query: '{query}'")
        
        # Get hybrid results
        vector_results = await rag.vector_search(query, limit=20)
        keyword_results = rag.keyword_search(query, vector_results, top_k=10)
        hybrid_results = rag.hybrid_search(vector_results, keyword_results)
        
        # Re-rank
        reranked_results = rag.rerank_results(
            query,
            hybrid_results[:10],
            top_k=5
        )
        
        print(f"\n✅ Re-ranked {len(reranked_results)} results")
        
        for i, result in enumerate(reranked_results[:3], 1):
            print(f"\n  Result {i}:")
            print(f"    Score: {result.score:.4f}")
            print(f"    Content: {result.content[:100]}...")
        
        return len(reranked_results) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_context_assembly():
    """Test context assembly with citations."""
    
    print("\n" + "=" * 70)
    print("TEST 6: Context Assembly")
    print("=" * 70 + "\n")
    
    try:
        rag = get_rag_service()
        
        query = TEST_QUERIES[0]
        print(f"Query: '{query}'")
        
        # Get re-ranked results
        vector_results = await rag.vector_search(query, limit=20)
        keyword_results = rag.keyword_search(query, vector_results, top_k=10)
        hybrid_results = rag.hybrid_search(vector_results, keyword_results)
        reranked_results = rag.rerank_results(
            query,
            hybrid_results[:10],
            top_k=5
        )
        
        # Assemble context
        context = rag.assemble_context(query, reranked_results)
        
        print(f"\n✅ Context assembled")
        print(f"  Total tokens: {context.total_tokens}")
        print(f"  Chunks: {len(context.chunks)}")
        print(f"  Citations: {len(context.citations)}")
        print(f"  Strategy: {context.strategy}")
        
        print(f"\n📄 Context preview:")
        print(f"  {context.context_text[:200]}...")
        
        print(f"\n📚 Citations:")
        for i, citation in enumerate(context.citations[:3], 1):
            print(f"\n  Citation {i}:")
            print(f"    Document: {citation.document_title}")
            print(f"    Relevance: {citation.relevance_score:.4f}")
            print(f"    Excerpt: {citation.excerpt[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_pipeline():
    """Test complete RAG pipeline."""
    
    print("\n" + "=" * 70)
    print("TEST 7: Full RAG Pipeline")
    print("=" * 70 + "\n")
    
    try:
        rag = get_rag_service()
        
        for i, query in enumerate(TEST_QUERIES[:3], 1):
            print(f"\n--- Query {i} ---")
            print(f"Query: '{query}'")
            
            start_time = datetime.now()
            
            context = await rag.retrieve(
                query=query,
                top_k=5,
                use_reranking=True
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            print(f"  ✅ Retrieved in {elapsed*1000:.0f}ms")
            print(f"  Tokens: {context.total_tokens}")
            print(f"  Chunks: {len(context.chunks)}")
            print(f"  Citations: {len(context.citations)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all RAG pipeline tests."""
    
    print("\n" + "=" * 70)
    print("RAG PIPELINE TEST SUITE")
    print("=" * 70)
    
    start_time = datetime.now()
    
    tests = [
        ("Qdrant Collection", test_qdrant_collection),
        ("Vector Search", test_vector_search),
        ("Keyword Search", test_keyword_search),
        ("Hybrid Search", test_hybrid_search),
        ("Re-ranking", test_reranking),
        ("Context Assembly", test_context_assembly),
        ("Full Pipeline", test_full_pipeline),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            logger.error(f"Test '{test_name}' failed: {e}")
            results[test_name] = False
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70 + "\n")
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    print(f"⏱️  Total time: {elapsed:.1f}s")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ RAG pipeline is fully operational!")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("   Please check errors above")
    
    print("=" * 70 + "\n")


def main():
    """Entry point."""
    asyncio.run(run_all_tests())


if __name__ == "__main__":
    main()
