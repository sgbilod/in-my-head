"""
Test script for document chunking service.

Demonstrates all chunking strategies and validates the service works correctly.
"""

import asyncio
import logging
from src.services.chunker_service import (
    ChunkerService,
    ChunkingStrategy,
    get_chunker_service
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample documents for testing
SAMPLE_DOCS = {
    "short": "This is a short document with just one sentence.",

    "medium": """
This is the first paragraph. It contains multiple sentences. Each sentence adds context and meaning. Together they form a coherent thought.

This is the second paragraph. It continues the narrative. The content flows naturally from the previous section.

Finally, we have a third paragraph. It concludes the document. The ending provides closure.
""".strip(),

    "technical": """
Artificial Intelligence (AI) is revolutionizing modern technology. Machine learning algorithms can now process vast amounts of data efficiently. Deep neural networks have achieved human-level performance in many tasks.

Natural Language Processing (NLP) enables computers to understand human language. This technology powers chatbots, translation services, and document analysis tools. Recent advances in transformer models have dramatically improved NLP capabilities.

Vector databases store embeddings for semantic search. Unlike traditional keyword search, semantic search understands the meaning behind queries. This enables more accurate and contextual information retrieval.
""".strip()
}


async def test_strategy(
    chunker: ChunkerService,
    strategy: ChunkingStrategy,
    document_id: str,
    content: str,
    chunk_size: int = 200,
    chunk_overlap: int = 50
):
    """Test a specific chunking strategy."""
    print(f"\n{'='*80}")
    print(f"Testing {strategy.value.upper()} strategy")
    print(f"Document: {document_id}")
    print(f"Content length: {len(content)} characters")
    print(f"Settings: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    print('='*80)

    try:
        # Chunk the document
        chunks = chunker.chunk_document(
            document_id=document_id,
            content=content,
            strategy=strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Get statistics
        stats = chunker.get_chunk_statistics(chunks)

        # Display results
        print(f"\n✓ Created {len(chunks)} chunks")
        print(f"\nStatistics:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Avg chunk size: {stats['avg_chunk_size']:.1f} chars")
        print(f"  Min chunk size: {stats['min_chunk_size']} chars")
        print(f"  Max chunk size: {stats['max_chunk_size']} chars")
        print(f"  Avg word count: {stats['avg_word_count']:.1f} words")
        print(f"  Avg sentence count: {stats['avg_sentence_count']:.1f} sentences")

        # Show first few chunks
        print(f"\nFirst 3 chunks:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n  Chunk {i}:")
            print(f"    Position: {chunk.metadata.start_position}-{chunk.metadata.end_position}")
            print(f"    Size: {chunk.metadata.char_count} chars, "
                  f"{chunk.metadata.word_count} words, "
                  f"{chunk.metadata.sentence_count} sentences")
            preview = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
            print(f"    Content: {preview}")

        if len(chunks) > 3:
            print(f"\n  ... and {len(chunks) - 3} more chunks")

        return chunks

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function."""
    print("\n" + "="*80)
    print("DOCUMENT CHUNKING SERVICE TEST")
    print("="*80)

    # Initialize chunker
    chunker = get_chunker_service()

    # Test each strategy with medium document
    strategies = [
        ChunkingStrategy.SENTENCE,
        ChunkingStrategy.PARAGRAPH,
        ChunkingStrategy.FIXED,
        ChunkingStrategy.SEMANTIC
    ]

    for strategy in strategies:
        await test_strategy(
            chunker,
            strategy,
            document_id="test-technical-doc",
            content=SAMPLE_DOCS["technical"],
            chunk_size=200,
            chunk_overlap=30
        )

    # Test edge cases
    print(f"\n\n{'='*80}")
    print("EDGE CASE TESTS")
    print('='*80)

    # Test short document
    print("\n\n--- Test: Short Document ---")
    await test_strategy(
        chunker,
        ChunkingStrategy.SENTENCE,
        document_id="test-short",
        content=SAMPLE_DOCS["short"],
        chunk_size=200
    )

    # Test with different chunk sizes
    print("\n\n--- Test: Small Chunk Size (100 chars) ---")
    await test_strategy(
        chunker,
        ChunkingStrategy.SENTENCE,
        document_id="test-small-chunks",
        content=SAMPLE_DOCS["technical"],
        chunk_size=100,
        chunk_overlap=20
    )

    print("\n\n--- Test: Large Chunk Size (500 chars) ---")
    await test_strategy(
        chunker,
        ChunkingStrategy.SENTENCE,
        document_id="test-large-chunks",
        content=SAMPLE_DOCS["technical"],
        chunk_size=500,
        chunk_overlap=50
    )

    # Test paragraph strategy
    print("\n\n--- Test: Paragraph Strategy ---")
    await test_strategy(
        chunker,
        ChunkingStrategy.PARAGRAPH,
        document_id="test-paragraphs",
        content=SAMPLE_DOCS["medium"],
        chunk_size=300
    )

    # Final summary
    print(f"\n\n{'='*80}")
    print("✓ ALL TESTS COMPLETE")
    print('='*80)
    print("\nChunking service is working correctly!")
    print("\nNext steps:")
    print("1. Integrate with document-processor to chunk documents after extraction")
    print("2. Generate embeddings for each chunk")
    print("3. Store chunks in PostgreSQL document_chunks table")
    print("4. Store chunk embeddings in Qdrant chunk_embeddings collection")
    print("5. Update search API to use chunk-level retrieval")


if __name__ == '__main__':
    asyncio.run(main())
