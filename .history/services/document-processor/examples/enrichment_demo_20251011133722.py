"""
Complete enrichment pipeline integration example.

This example demonstrates the full document enrichment pipeline:
1. Document parsing → Text extraction
2. Text preprocessing → Cleaning & chunking
3. Metadata extraction → Claude AI
4. Embedding generation → OpenAI
5. Vector storage → Qdrant with rich metadata

Prerequisites:
- ANTHROPIC_API_KEY environment variable set
- OPENAI_API_KEY environment variable set
- Redis service running on localhost:6379
- Qdrant service running on localhost:6333
"""

import os
import sys
import asyncio
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# pylint: disable=wrong-import-position
from metadata import (
    MetadataExtractor,
    MetadataEnricher,
    MetadataField,
)
from embeddings import EmbeddingGenerator
from vector_storage import VectorStore, CollectionManager, CollectionConfig

# pylint: enable=wrong-import-position


# ============================================================================
# DEMO 1: Basic Enrichment Pipeline
# ============================================================================


async def demo_basic_enrichment():
    """Demonstrate basic document enrichment pipeline."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Document Enrichment Pipeline")
    print("=" * 70)

    sample_doc = """
    The Future of Quantum Computing
    
    By Dr. Alice Johnson, IBM Research
    Published: October 11, 2025
    
    Quantum computing represents a paradigm shift in computational
    capability. Companies like IBM, Google, and Microsoft are racing
    to achieve quantum supremacy. Recent breakthroughs at MIT and
    Stanford University have brought us closer to practical quantum
    computers that can solve problems intractable for classical systems.
    
    Applications span cryptography, drug discovery, materials science,
    and artificial intelligence. The integration of quantum algorithms
    with machine learning opens new frontiers in optimization and
    pattern recognition.
    """

    print("\n1. Initializing components...")

    # Initialize metadata extractor
    metadata_extractor = MetadataExtractor(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        redis_host="localhost",
    )
    print("   ✓ MetadataExtractor initialized")

    # Initialize embedding generator
    embedding_generator = EmbeddingGenerator(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="text-embedding-3-large",
    )
    print("   ✓ EmbeddingGenerator initialized")

    # Initialize vector store
    collection_manager = CollectionManager(host="localhost", port=6333)
    await collection_manager.create_collection(
        name="demo_collection",
        config=CollectionConfig(
            vector_size=3072, distance_metric="cosine"
        ),
    )
    vector_store = VectorStore(
        collection_name="demo_collection", host="localhost", port=6333
    )
    print("   ✓ VectorStore initialized")

    # Initialize enricher
    enricher = MetadataEnricher(
        metadata_extractor=metadata_extractor,
        embedding_generator=embedding_generator,
        vector_store=vector_store,
    )
    print("   ✓ MetadataEnricher initialized")

    print("\n2. Enriching document...")
    enriched_doc = await enricher.enrich_document(
        text=sample_doc,
        doc_id="quantum_computing_2025",
        source="demo_article.txt",
    )
    print("   ✓ Document enriched")

    print("\n3. Enriched Document Details:")
    print(f"   ID: {enriched_doc.id}")
    print(f"   Vector ID: {enriched_doc.vector_id}")
    print(f"   Embedding dimensions: {len(enriched_doc.embedding)}D")
    print(f"   Confidence: {enriched_doc.confidence:.2f}")

    print("\n4. Extracted Metadata:")
    print(f"   Title: {enriched_doc.metadata.title}")
    print(f"   Language: {enriched_doc.metadata.language}")

    print(f"\n   Authors ({len(enriched_doc.metadata.authors)}):")
    for author in enriched_doc.metadata.authors:
        print(f"     - {author.name} ({author.role})")

    print(f"\n   Topics ({len(enriched_doc.metadata.topics)}):")
    for topic in enriched_doc.metadata.topics[:3]:
        print(f"     - {topic.name} (relevance: {topic.relevance:.2f})")

    print(f"\n   Entities ({len(enriched_doc.metadata.entities)}):")
    for entity in enriched_doc.metadata.entities[:5]:
        print(f"     - {entity.name} ({entity.type.value})")

    print(f"\n   Categories:")
    for category in enriched_doc.metadata.categories:
        print(
            f"     - {category.name.value}"
            + (f" / {category.subcategory}" if category.subcategory else "")
        )

    print(f"\n   Summary: {enriched_doc.metadata.summary}")

    print("\n5. Statistics:")
    stats = enricher.get_stats()
    print(f"   - Total processed: {stats['total_processed']}")
    print(f"   - Success rate: {stats['success_rate']:.1%}")
    print(f"   - Avg processing time: {stats['avg_processing_time']:.2f}s")

    # Cleanup
    await enricher.close()
    await collection_manager.delete_collection("demo_collection")
    print("\n✓ Demo complete")


# ============================================================================
# DEMO 2: Batch Enrichment
# ============================================================================


async def demo_batch_enrichment():
    """Demonstrate batch document enrichment."""
    print("\n" + "=" * 70)
    print("DEMO 2: Batch Document Enrichment")
    print("=" * 70)

    documents = [
        {
            "text": """
            Machine Learning in Finance
            Financial institutions are using ML for fraud detection,
            risk assessment, and algorithmic trading. Companies like
            JPMorgan and Goldman Sachs have invested heavily in AI.
            """,
            "id": "ml_finance",
            "source": "finance_article.pdf",
        },
        {
            "text": """
            Climate Change and Renewable Energy
            Solar and wind power are becoming increasingly cost-effective.
            Countries worldwide are committing to net-zero emissions by 2050.
            Tesla, NextEra Energy, and Ørsted are leading the transition.
            """,
            "id": "climate_energy",
            "source": "climate_report.pdf",
        },
        {
            "text": """
            Advances in Gene Editing
            CRISPR technology is revolutionizing genetic medicine.
            Researchers at Harvard and MIT are developing treatments for
            genetic diseases. Companies like Editas Medicine and CRISPR
            Therapeutics are bringing these therapies to market.
            """,
            "id": "gene_editing",
            "source": "biotech_news.pdf",
        },
    ]

    print(f"\n1. Initializing enricher for {len(documents)} documents...")

    # Initialize components
    metadata_extractor = MetadataExtractor(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    embedding_generator = EmbeddingGenerator(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    collection_manager = CollectionManager(host="localhost", port=6333)
    await collection_manager.create_collection(
        name="batch_demo",
        config=CollectionConfig(vector_size=3072, distance_metric="cosine"),
    )
    vector_store = VectorStore(
        collection_name="batch_demo", host="localhost", port=6333
    )

    enricher = MetadataEnricher(
        metadata_extractor=metadata_extractor,
        embedding_generator=embedding_generator,
        vector_store=vector_store,
    )
    print("   ✓ Components initialized")

    print(f"\n2. Processing {len(documents)} documents in batch...")
    start_time = datetime.utcnow()

    enriched_docs = await enricher.enrich_batch(documents)

    processing_time = (datetime.utcnow() - start_time).total_seconds()
    print(
        f"   ✓ Processed {len(enriched_docs)} documents "
        f"in {processing_time:.2f}s"
    )

    print("\n3. Enriched Documents:")
    for i, doc in enumerate(enriched_docs, 1):
        print(f"\n   Document {i}: {doc.id}")
        print(f"     Title: {doc.metadata.title}")
        print(
            f"     Topics: "
            f"{', '.join([t.name for t in doc.metadata.topics[:2]])}"
        )
        print(
            f"     Categories: "
            f"{', '.join([c.name.value for c in doc.metadata.categories])}"
        )

    print("\n4. Final Statistics:")
    stats = enricher.get_stats()
    print(f"   - Total processed: {stats['total_processed']}")
    print(f"   - Successful: {stats['successful']}")
    print(f"   - Success rate: {stats['success_rate']:.1%}")
    print(
        f"   - Avg time per doc: {stats['avg_processing_time']:.2f}s"
    )

    # Cleanup
    await enricher.close()
    await collection_manager.delete_collection("batch_demo")
    print("\n✓ Demo complete")


# ============================================================================
# DEMO 3: Metadata-Based Search
# ============================================================================


async def demo_metadata_search():
    """Demonstrate searching by metadata filters."""
    print("\n" + "=" * 70)
    print("DEMO 3: Metadata-Based Search")
    print("=" * 70)

    # First, create and enrich some documents
    documents = [
        {
            "text": """
            AI in Healthcare: A Revolution
            By Dr. Sarah Martinez, Stanford Medical School
            
            Machine learning is transforming diagnostics, enabling early
            detection of diseases like cancer and Alzheimer's. Companies
            like DeepMind and PathAI are at the forefront.
            """,
            "id": "ai_healthcare",
        },
        {
            "text": """
            Blockchain for Supply Chain
            By Prof. James Lee, MIT Business School
            
            Blockchain technology provides transparency and traceability
            in global supply chains. Walmart and Maersk have implemented
            blockchain solutions for tracking products.
            """,
            "id": "blockchain_supply",
        },
        {
            "text": """
            The Future of Healthcare AI
            By Dr. Emily Chen, Johns Hopkins
            
            Artificial intelligence is revolutionizing patient care through
            predictive analytics and personalized medicine. The integration
            of AI with electronic health records enables better outcomes.
            """,
            "id": "future_healthcare_ai",
        },
    ]

    print("\n1. Setting up enricher and indexing documents...")

    # Initialize components
    metadata_extractor = MetadataExtractor(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    embedding_generator = EmbeddingGenerator(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    collection_manager = CollectionManager(host="localhost", port=6333)
    await collection_manager.create_collection(
        name="search_demo",
        config=CollectionConfig(vector_size=3072, distance_metric="cosine"),
    )
    vector_store = VectorStore(
        collection_name="search_demo", host="localhost", port=6333
    )

    enricher = MetadataEnricher(
        metadata_extractor=metadata_extractor,
        embedding_generator=embedding_generator,
        vector_store=vector_store,
    )

    # Enrich and index documents
    await enricher.enrich_batch(documents)
    print(f"   ✓ Indexed {len(documents)} documents")

    print("\n2. Search Example 1: By topic and category")
    print("   Query: Documents about 'healthcare' AND 'artificial intelligence'")

    results = await enricher.search_by_metadata(
        query_text="healthcare artificial intelligence",
        categories=["health", "technology"],
        limit=5,
    )

    print(f"   Found {len(results)} results")
    # Note: Results would be displayed if the full integration was running

    print("\n3. Search Example 2: By author")
    print("   Query: Documents by authors with 'Dr.' title")

    results = await enricher.search_by_metadata(
        authors=["Dr. Sarah Martinez", "Dr. Emily Chen"], limit=5
    )

    print(f"   Found {len(results)} results")

    print("\n4. Search Example 3: Combined filters")
    print(
        "   Query: Healthcare + AI with specific topics"
    )

    results = await enricher.search_by_metadata(
        query_text="machine learning healthcare",
        topics=["Artificial Intelligence", "Healthcare"],
        language="en",
        limit=3,
    )

    print(f"   Found {len(results)} results")

    # Cleanup
    await enricher.close()
    await collection_manager.delete_collection("search_demo")
    print("\n✓ Demo complete")


# ============================================================================
# DEMO 4: Document Updates
# ============================================================================


async def demo_document_updates():
    """Demonstrate updating and deleting documents."""
    print("\n" + "=" * 70)
    print("DEMO 4: Document Updates and Deletion")
    print("=" * 70)

    # Initialize components
    metadata_extractor = MetadataExtractor(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    embedding_generator = EmbeddingGenerator(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    collection_manager = CollectionManager(host="localhost", port=6333)
    await collection_manager.create_collection(
        name="update_demo",
        config=CollectionConfig(vector_size=3072, distance_metric="cosine"),
    )
    vector_store = VectorStore(
        collection_name="update_demo", host="localhost", port=6333
    )

    enricher = MetadataEnricher(
        metadata_extractor=metadata_extractor,
        embedding_generator=embedding_generator,
        vector_store=vector_store,
    )

    print("\n1. Creating initial document...")
    doc = await enricher.enrich_document(
        text="Sample document for update demo", doc_id="update_test"
    )
    print(f"   ✓ Created document: {doc.id}")

    print("\n2. Updating document metadata...")
    updates = {
        "summary": "Updated summary with new information",
        "keywords": ["updated", "metadata", "test"],
    }
    success = await enricher.update_document_metadata("update_test", updates)
    print(f"   ✓ Update {'successful' if success else 'failed'}")

    print("\n3. Deleting document...")
    success = await enricher.delete_document("update_test")
    print(f"   ✓ Deletion {'successful' if success else 'failed'}")

    # Cleanup
    await enricher.close()
    await collection_manager.delete_collection("update_demo")
    print("\n✓ Demo complete")


# ============================================================================
# MAIN
# ============================================================================


async def main():
    """Run all enrichment demos."""
    print("\n" + "=" * 70)
    print("METADATA ENRICHMENT PIPELINE DEMO")
    print("=" * 70)

    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ Error: OPENAI_API_KEY environment variable not set")
        return

    try:
        # Run demos
        await demo_basic_enrichment()
        await demo_batch_enrichment()
        await demo_metadata_search()
        await demo_document_updates()

        print("\n" + "=" * 70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY! ✨")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
