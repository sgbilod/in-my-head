"""
Metadata extraction integration demo.

This example demonstrates how to use the metadata extraction system
to extract rich metadata from documents using Claude AI.

Prerequisites:
- ANTHROPIC_API_KEY environment variable set
- Redis service running on localhost:6379
"""

import os
import sys
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# pylint: disable=wrong-import-position
from metadata import (
    MetadataExtractor,
    MetadataField,
)
# pylint: enable=wrong-import-position


# ============================================================================
# DEMO 1: Basic Metadata Extraction
# ============================================================================


async def demo_basic_extraction():
    """Demonstrate basic metadata extraction."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Metadata Extraction")
    print("=" * 70)

    sample_text = """
    The Future of Renewable Energy

    By Dr. Sarah Johnson and Prof. Michael Chen
    Published: October 11, 2025

    Solar and wind energy have become increasingly viable alternatives to
    fossil fuels. Companies like Tesla, NextEra Energy, and Vestas are
    leading the charge in renewable energy technology development.

    According to research from Stanford University and MIT, renewable
    energy could provide up to 80% of global electricity by 2050.
    The technology has applications in power generation, transportation,
    and industrial manufacturing.

    This represents a significant step forward in addressing climate change
    and ensuring sustainable energy for future generations.
    """

    print("\n1. Initializing MetadataExtractor...")
    extractor = MetadataExtractor(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        redis_host="localhost",
        redis_port=6379,
    )
    print("✓ Extractor initialized")

    print("\n2. Extracting metadata from text...")
    metadata = await extractor.extract(sample_text)
    print("✓ Metadata extracted")

    print("\n3. Results:")
    print(f"\n   Title: {metadata.title}")
    print(f"   Language: {metadata.language}")
    print(f"   Summary: {metadata.summary}")

    print(f"\n   Authors ({len(metadata.authors)}):")
    for author in metadata.authors:
        print(f"     - {author.name} ({author.role})")

    print(f"\n   Topics ({len(metadata.topics)}):")
    for topic in metadata.topics[:3]:  # Top 3
        print(f"     - {topic.name} (relevance: {topic.relevance:.2f})")

    print(f"\n   Entities ({len(metadata.entities)}):")
    for entity in metadata.entities[:5]:  # Top 5
        print(f"     - {entity.name} ({entity.type.value})")

    print(f"\n   Keywords: {', '.join(metadata.keywords[:5])}")

    if metadata.sentiment:
        print(
            f"\n   Sentiment: {metadata.sentiment.label} "
            f"(score: {metadata.sentiment.score:.2f})"
        )

    # Get statistics
    stats = await extractor.get_stats()
    print("\n4. Statistics:")
    print(f"   - Total extracted: {stats['total_extracted']}")
    print(f"   - Cache hits: {stats['cache_hits']}")
    print(f"   - Cache misses: {stats['cache_misses']}")

    await extractor.close()
    print("\n✓ Demo complete")


# ============================================================================
# DEMO 2: Specific Field Extraction
# ============================================================================


async def demo_specific_fields():
    """Demonstrate extraction of specific metadata fields."""
    print("\n" + "=" * 70)
    print("DEMO 2: Specific Field Extraction")
    print("=" * 70)

    sample_text = """
    Quantum Computing Breakthrough at IBM Research

    IBM announced today a major advancement in quantum computing,
    demonstrating a 127-qubit quantum processor. This achievement
    brings us closer to practical quantum advantage.

    The research, led by Dr. Jay Gambetta and his team at IBM's
    Thomas J. Watson Research Center in Yorktown Heights, New York,
    represents years of collaborative effort with partners including
    MIT and the University of Tokyo.
    """

    print("\n1. Extracting only AUTHORS and ENTITIES...")
    extractor = MetadataExtractor(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Extract specific fields
    fields = {MetadataField.AUTHORS, MetadataField.ENTITIES}
    metadata = await extractor.extract(sample_text, fields=fields)

    print("\n2. Results:")
    print(f"\n   Authors: {[a.name for a in metadata.authors]}")
    print(f"\n   Entities:")
    for entity in metadata.entities:
        print(f"     - {entity.name} ({entity.type.value})")

    await extractor.close()
    print("\n✓ Demo complete")


# ============================================================================
# DEMO 3: Batch Processing
# ============================================================================


async def demo_batch_processing():
    """Demonstrate batch metadata extraction."""
    print("\n" + "=" * 70)
    print("DEMO 3: Batch Metadata Extraction")
    print("=" * 70)

    texts = [
        """
        The Role of AI in Healthcare
        Machine learning models are transforming medical diagnosis.
        Companies like DeepMind and IBM Watson Health are pioneering
        AI applications in healthcare.
        """,
        """
        Climate Change and Global Policy
        The United Nations Climate Summit addressed critical environmental
        issues. Leaders from around the world gathered to discuss carbon
        emissions and renewable energy policies.
        """,
        """
        Advances in Space Exploration
        NASA's Artemis program aims to return humans to the Moon by 2025.
        This mission will pave the way for future Mars exploration and
        establish a sustainable lunar presence.
        """,
    ]

    print(f"\n1. Processing {len(texts)} documents...")
    extractor = MetadataExtractor(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    results = await extractor.extract_batch(texts)
    print(f"✓ Processed {len(results)} documents")

    print("\n2. Results:")
    for i, metadata in enumerate(results, 1):
        print(f"\n   Document {i}:")
        print(f"     Title: {metadata.title}")
        print(
            f"     Topics: "
            f"{', '.join([t.name for t in metadata.topics[:2]])}"
        )
        print(
            f"     Categories: "
            f"{', '.join([c.name.value for c in metadata.categories[:2]])}"
        )

    # Get statistics
    stats = await extractor.get_stats()
    print(f"\n3. Final Statistics:")
    print(f"   - Total processed: {stats['total_extracted']}")
    print(f"   - Cache hit rate: {stats['cache_hit_rate']:.1%}")

    await extractor.close()
    print("\n✓ Demo complete")


# ============================================================================
# DEMO 4: Caching Performance
# ============================================================================


async def demo_caching():
    """Demonstrate caching performance benefits."""
    print("\n" + "=" * 70)
    print("DEMO 4: Caching Performance")
    print("=" * 70)

    sample_text = """
    The Evolution of Programming Languages
    From assembly to high-level languages, programming has evolved
    dramatically. Python, JavaScript, and Rust are shaping modern
    software development.
    """

    extractor = MetadataExtractor(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # First extraction (cache miss)
    print("\n1. First extraction (cache miss)...")
    import time

    start = time.time()
    metadata1 = await extractor.extract(sample_text)
    time1 = time.time() - start
    print(f"✓ Completed in {time1:.2f}s")

    # Second extraction (cache hit)
    print("\n2. Second extraction (cache hit)...")
    start = time.time()
    metadata2 = await extractor.extract(sample_text)
    time2 = time.time() - start
    print(f"✓ Completed in {time2:.2f}s")

    print(f"\n3. Performance Improvement:")
    print(f"   - First extraction: {time1:.2f}s")
    print(f"   - Second extraction: {time2:.2f}s")
    print(f"   - Speedup: {time1 / max(time2, 0.001):.1f}x faster")

    stats = await extractor.get_stats()
    print(f"\n4. Cache Statistics:")
    print(f"   - Cache hits: {stats['cache_hits']}")
    print(f"   - Cache misses: {stats['cache_misses']}")
    print(f"   - Hit rate: {stats['cache_hit_rate']:.1%}")

    await extractor.close()
    print("\n✓ Demo complete")


# ============================================================================
# MAIN
# ============================================================================


async def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("METADATA EXTRACTION DEMO")
    print("=" * 70)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it and try again.")
        return

    try:
        # Run demos
        await demo_basic_extraction()
        await demo_specific_fields()
        await demo_batch_processing()
        await demo_caching()

        print("\n" + "=" * 70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY! ✨")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
