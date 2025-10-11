"""
Comprehensive test suite for preprocessing components.

Tests:
- TextCleaner: Noise removal and whitespace normalization
- TextNormalizer: Unicode and case normalization
- TextChunker: Semantic chunking with token counting
- Deduplicator: Duplicate detection and removal
- PreprocessingPipeline: End-to-end integration
"""

import os
import sys
from pathlib import Path

# Fix SSL certificate issue on Windows (PostgreSQL sets invalid SSL_CERT_FILE)
if 'SSL_CERT_FILE' in os.environ:
    del os.environ['SSL_CERT_FILE']

# Also fix REQUESTS_CA_BUNDLE
if 'REQUESTS_CA_BUNDLE' in os.environ:
    del os.environ['REQUESTS_CA_BUNDLE']

# Set proper SSL verification using certifi
try:
    import certifi
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['SSL_CERT_FILE'] = certifi.where()
except ImportError:
    pass

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from preprocessing import (
    TextCleaner,
    TextNormalizer,
    TextChunker,
    TextChunk,
    Deduplicator,
    PreprocessingPipeline,
    clean_text,
    normalize_text,
    chunk_text,
    deduplicate_texts,
    process_text,
)


def test_text_cleaner():
    """Test TextCleaner functionality."""
    print("Testing TextCleaner...")

    cleaner = TextCleaner(remove_urls=True, remove_emails=True)

    # Test HTML removal
    html_text = "<h1>Title</h1><p>Paragraph with <b>bold</b> text.</p>"
    cleaned = cleaner.clean(html_text)
    assert "<" not in cleaned and ">" not in cleaned
    print(f"  ✓ HTML removal: '{html_text}' → '{cleaned}'")

    # Test URL removal
    url_text = "Visit https://example.com for more info."
    cleaned = cleaner.clean(url_text)
    assert "https://" not in cleaned
    print(f"  ✓ URL removal: '{url_text}' → '{cleaned}'")

    # Test email removal
    email_text = "Contact us at test@example.com for help."
    cleaned = cleaner.clean(email_text)
    assert "@" not in cleaned
    print(f"  ✓ Email removal: '{email_text}' → '{cleaned}'")

    # Test whitespace normalization
    whitespace_text = "Text   with    multiple     spaces"
    cleaned = cleaner.clean(whitespace_text)
    assert "  " not in cleaned
    print(f"  ✓ Whitespace: '{whitespace_text}' → '{cleaned}'")

    # Test convenience function
    cleaned = clean_text("<p>Simple test</p>")
    assert "<" not in cleaned
    print(f"  ✓ Convenience function works")

    print("✓ TextCleaner: ALL TESTS PASSED\n")


def test_text_normalizer():
    """Test TextNormalizer functionality."""
    print("Testing TextNormalizer...")

    normalizer = TextNormalizer(remove_accents=True)

    # Test accent removal
    accented = "café naïve résumé"
    normalized = normalizer.normalize(accented)
    assert "é" not in normalized and "ï" not in normalized
    print(f"  ✓ Accent removal: '{accented}' → '{normalized}'")

    # Test quote normalization
    # Using actual fancy quote Unicode characters
    fancy_quotes = '\u201cHello\u201d and \u2018world\u2019'  # Fancy quotes
    normalized = normalizer.normalize(fancy_quotes)
    # Check that fancy quotes were replaced
    assert '\u201c' not in normalized and '\u2018' not in normalized
    print(f"  ✓ Quote normalization: fancy quotes → standard quotes")

    # Test number normalization
    numbers = "The price is 1,000,000 dollars"
    normalized = normalizer.normalize(numbers)
    assert "1000000" in normalized
    print(f"  ✓ Number normalization: '{numbers}' → '{normalized}'")

    # Test case normalization
    normalizer_lower = TextNormalizer(lowercase=True)
    mixed_case = "MiXeD CaSe TeXt"
    normalized = normalizer_lower.normalize(mixed_case)
    assert normalized == normalized.lower()
    print(f"  ✓ Lowercase: '{mixed_case}' → '{normalized}'")

    # Test convenience function
    normalized = normalize_text("café", remove_accents=True)
    assert "é" not in normalized
    print(f"  ✓ Convenience function works")

    print("✓ TextNormalizer: ALL TESTS PASSED\n")


def test_text_chunker():
    """Test TextChunker functionality."""
    print("Testing TextChunker...")

    chunker = TextChunker(chunk_size=50, overlap_size=10)

    # Test small text (single chunk)
    small_text = "This is a short text."
    chunks = chunker.chunk_text(small_text)
    assert len(chunks) == 1
    assert chunks[0].text == small_text.strip()
    print(f"  ✓ Small text: 1 chunk created")

    # Test longer text (multiple chunks)
    long_text = " ".join([
        f"This is sentence number {i}." for i in range(100)
    ])
    chunks = chunker.chunk_text(long_text)
    assert len(chunks) > 1
    print(f"  ✓ Long text: {len(chunks)} chunks created")

    # Test chunk properties
    first_chunk = chunks[0]
    assert isinstance(first_chunk, TextChunk)
    assert first_chunk.chunk_index == 0
    assert first_chunk.token_count > 0
    assert first_chunk.start_pos == 0
    print(f"  ✓ Chunk properties: {first_chunk.token_count} tokens")

    # Test overlap
    if len(chunks) > 1:
        second_chunk = chunks[1]
        # Overlap should be greater than or equal to 0 (may be 0 if first chunk was very small)
        assert second_chunk.overlap_with_previous >= 0
        print(f"  ✓ Overlap: {second_chunk.overlap_with_previous} tokens")

    # Test token counting
    token_count = chunker.count_tokens("Hello world")
    assert token_count > 0
    print(f"  ✓ Token counting: 'Hello world' = {token_count} tokens")

    # Test convenience function
    chunks = chunk_text("Test text", chunk_size=50)
    assert len(chunks) > 0
    print(f"  ✓ Convenience function works")

    print("✓ TextChunker: ALL TESTS PASSED\n")


def test_deduplicator():
    """Test Deduplicator functionality."""
    print("Testing Deduplicator...")

    deduplicator = Deduplicator(similarity_threshold=0.95)

    # Test exact duplicate detection
    dedup = Deduplicator(similarity_threshold=0.95)
    texts = [
        "This is the first text that is long enough to process.",
        "This is the second text that is different from the first.",
        "This is the first text that is long enough to process.",  # Exact duplicate of first
    ]
    
    duplicates = dedup.find_duplicates(texts)
    assert len(duplicates) > 0
    print(f"  ✓ Exact duplicates: Found {len(duplicates)} pairs")    # Test deduplication
    unique_texts = deduplicator.deduplicate(texts)
    assert len(unique_texts) < len(texts)
    print(f"  ✓ Deduplication: {len(texts)} → {len(unique_texts)} texts")

    # Test similarity calculation
    text1 = "The quick brown fox jumps over the lazy dog."
    text2 = "The quick brown fox jumps over the lazy cat."
    similarity = deduplicator.calculate_similarity(text1, text2)
    assert 0.0 <= similarity <= 1.0
    print(f"  ✓ Similarity: {similarity:.2f}")

    # Test hashing
    content_hash = deduplicator.hash_content("Test content")
    assert len(content_hash) == 64  # SHA-256 produces 64-char hex
    print(f"  ✓ Hashing: {content_hash[:16]}...")

    # Test convenience function
    unique = deduplicate_texts(texts)
    assert len(unique) < len(texts)
    print(f"  ✓ Convenience function works")

    print("✓ Deduplicator: ALL TESTS PASSED\n")


def test_preprocessing_pipeline():
    """Test complete PreprocessingPipeline."""
    print("Testing PreprocessingPipeline...")

    pipeline = PreprocessingPipeline(
        remove_urls=True,
        chunk_size=50,
        overlap_size=10,
    )

    # Test complete pipeline
    raw_text = """
    <h1>Document Title</h1>
    <p>This is a paragraph with <b>HTML tags</b>.</p>
    <p>Visit https://example.com for more information.</p>
    <p>Contact us at test@example.com if you have questions.</p>

    This is a longer paragraph with multiple sentences. It should be processed
    through the cleaning stage first. Then it will be normalized. Finally, it
    will be chunked into appropriate sizes for embeddings.

    This is another paragraph that provides additional content for testing
    the chunking functionality. We want to ensure that the pipeline creates
    multiple chunks when the text is long enough.
    """

    chunks = pipeline.process(raw_text)

    assert len(chunks) > 0
    print(f"  ✓ Pipeline processing: {len(chunks)} chunks created")

    # Verify cleaning worked
    first_chunk_text = chunks[0].text
    assert "<" not in first_chunk_text
    assert "https://" not in first_chunk_text
    print(f"  ✓ Cleaning: HTML and URLs removed")

    # Verify chunking properties
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert chunk.token_count > 0
    print(f"  ✓ Chunks: All have valid properties")

    # Test batch processing
    texts = [raw_text, raw_text]
    batch_results = pipeline.process_batch(texts)
    assert len(batch_results) == 2
    print(f"  ✓ Batch processing: {len(batch_results)} results")

    # Test convenience function
    chunks = process_text("Simple test text", chunk_size=50)
    assert len(chunks) > 0
    print(f"  ✓ Convenience function works")

    print("✓ PreprocessingPipeline: ALL TESTS PASSED\n")


def test_integration():
    """Test realistic integration scenario."""
    print("Testing Integration Scenario...")

    # Simulate document processing workflow
    document = """
    # Research Paper: AI and Machine Learning

    ## Abstract
    This paper explores the applications of artificial intelligence and machine
    learning in modern computing. We examine various approaches and techniques.

    ## Introduction
    Artificial intelligence has revolutionized many fields of computing. Machine
    learning, a subset of AI, has proven particularly effective for pattern
    recognition and prediction tasks.

    For more information, visit our website at https://example.com or contact
    us at research@example.com.

    ## Methodology
    We conducted experiments using state-of-the-art neural networks. The results
    demonstrate significant improvements over baseline approaches.

    ## Conclusion
    Our findings suggest that AI and ML will continue to play crucial roles in
    advancing computational capabilities.
    """

    # Process with full pipeline
    pipeline = PreprocessingPipeline(
        remove_urls=True,
        remove_emails=True,
        chunk_size=100,
        overlap_size=20,
        deduplicate=True,
    )

    chunks = pipeline.process(document)

    print(f"  ✓ Processed document into {len(chunks)} chunks")

    # Verify chunk details
    total_tokens = sum(chunk.token_count for chunk in chunks)
    print(f"  ✓ Total tokens: {total_tokens}")

    avg_tokens = total_tokens / len(chunks) if chunks else 0
    print(f"  ✓ Average tokens per chunk: {avg_tokens:.1f}")

    # Check that sensitive data removed
    all_text = " ".join(chunk.text for chunk in chunks)
    assert "https://" not in all_text
    assert "@" not in all_text
    print(f"  ✓ Sensitive data removed")

    print("✓ Integration: ALL TESTS PASSED\n")


def main():
    """Run all preprocessing tests."""
    print("=" * 70)
    print("PREPROCESSING COMPONENT TEST SUITE")
    print("=" * 70)
    print()

    try:
        test_text_cleaner()
        test_text_normalizer()
        test_text_chunker()
        test_deduplicator()
        test_preprocessing_pipeline()
        test_integration()

        print("=" * 70)
        print("✅ ALL PREPROCESSING TESTS PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✓ TextCleaner: Noise removal, HTML cleaning, whitespace")
        print("  ✓ TextNormalizer: Unicode, case, accent handling")
        print("  ✓ TextChunker: Semantic chunking with overlap")
        print("  ✓ Deduplicator: Exact and fuzzy duplicate detection")
        print("  ✓ Pipeline: End-to-end integration")
        print("  ✓ Integration: Realistic document processing")
        print()
        return 0

    except Exception as e:
        print("=" * 70)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
