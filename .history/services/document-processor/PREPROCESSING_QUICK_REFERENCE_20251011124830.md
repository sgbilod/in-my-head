# PREPROCESSING PIPELINE - QUICK REFERENCE

**Version:** 1.0.0  
**Status:** Production Ready ✅

---

## 🚀 QUICK START

```python
# Import the pipeline
from preprocessing import PreprocessingPipeline

# Create pipeline with default settings
pipeline = PreprocessingPipeline()

# Process a document
raw_text = "Your document text here..."
chunks = pipeline.process(raw_text)

# Access results
for chunk in chunks:
    print(f"Chunk {chunk.chunk_index}:")
    print(f"  Tokens: {chunk.token_count}")
    print(f"  Text: {chunk.text[:100]}...")
```

---

## 📦 AVAILABLE COMPONENTS

### 1. TextCleaner

**Purpose:** Remove noise and normalize whitespace

```python
from preprocessing import TextCleaner

cleaner = TextCleaner(
    remove_urls=True,          # Replace URLs with [URL]
    remove_emails=True,        # Replace emails with [EMAIL]
    remove_phone_numbers=True, # Replace phones with [PHONE]
    min_line_length=3         # Minimum line length to keep
)

clean_text = cleaner.clean(raw_text)
```

**What it does:**
- ✅ Removes HTML tags and entities
- ✅ Filters URLs, emails, phone numbers (optional)
- ✅ Normalizes whitespace (spaces, tabs, newlines)
- ✅ Removes headers/footers (page numbers, dates)
- ✅ Cleans control characters

---

### 2. TextNormalizer

**Purpose:** Unicode and case normalization

```python
from preprocessing import TextNormalizer

normalizer = TextNormalizer(
    unicode_form="NFKC",      # Unicode normalization form
    lowercase=False,          # Convert to lowercase
    remove_accents=True,      # café → cafe
    normalize_numbers=True,   # 1,000 → 1000
    normalize_quotes=True     # " " → " "
)

normalized_text = normalizer.normalize(text)
```

**What it does:**
- ✅ Unicode normalization (NFKC/NFC/NFD/NFKD)
- ✅ Removes accents and diacritics
- ✅ Normalizes fancy quotes to standard quotes
- ✅ Normalizes number formats (removes commas)
- ✅ Normalizes punctuation (dashes, ellipsis)

---

### 3. TextChunker

**Purpose:** Intelligent semantic chunking

```python
from preprocessing import TextChunker

chunker = TextChunker(
    chunk_size=512,          # Target tokens per chunk
    overlap_size=50,         # Overlap tokens for context
    model="cl100k_base",     # Tokenizer model (GPT-4)
    min_chunk_size=100,      # Minimum tokens per chunk
    respect_paragraphs=True  # Keep paragraphs together
)

chunks = chunker.chunk_text(text, metadata={'source': 'doc.pdf'})
```

**What it does:**
- ✅ Semantic chunking (preserves sentences)
- ✅ Token-based sizing (accurate counting)
- ✅ Configurable overlap between chunks
- ✅ Special handling for code blocks and tables
- ✅ Comprehensive chunk metadata

**Chunk Object:**
```python
chunk.text                    # Chunk text
chunk.token_count            # Number of tokens
chunk.chunk_index            # Index in document
chunk.start_pos              # Start position in original
chunk.end_pos                # End position in original
chunk.overlap_with_previous  # Overlap with previous chunk
chunk.metadata               # Custom metadata dict
```

---

### 4. Deduplicator

**Purpose:** Remove duplicate content

```python
from preprocessing import Deduplicator

deduplicator = Deduplicator(
    similarity_threshold=0.95,  # 95% similarity = duplicate
    min_length=50,              # Minimum text length to check
    case_sensitive=False        # Ignore case differences
)

# Find duplicates
duplicates = deduplicator.find_duplicates(texts)

# Remove duplicates
unique_texts = deduplicator.deduplicate(texts, keep='first')
```

**What it does:**
- ✅ Exact duplicate detection (SHA-256 hashing)
- ✅ Fuzzy duplicate detection (similarity scoring)
- ✅ Configurable similarity threshold
- ✅ Choose which duplicate to keep (first/last)

---

### 5. PreprocessingPipeline

**Purpose:** Unified end-to-end pipeline

```python
from preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline(
    # Cleaning options
    remove_urls=False,
    remove_emails=False,
    remove_phone_numbers=False,
    
    # Normalization options
    lowercase=False,
    remove_accents=False,
    
    # Chunking options
    chunk_size=512,
    overlap_size=50,
    
    # Deduplication options
    deduplicate=True,
    similarity_threshold=0.95
)

# Single document
chunks = pipeline.process(text, metadata={'doc_id': '123'})

# Multiple documents
batch_results = pipeline.process_batch(
    texts=[text1, text2, text3],
    metadata_list=[meta1, meta2, meta3]
)
```

**Pipeline Stages:**
1. **Clean** → Remove noise, HTML, normalize whitespace
2. **Normalize** → Unicode normalization, case handling
3. **Chunk** → Split into optimal chunks for embeddings
4. **Deduplicate** → Remove duplicate chunks (optional)

---

## ⚡ CONVENIENCE FUNCTIONS

### Quick Cleaning

```python
from preprocessing import clean_text

clean = clean_text(
    text,
    remove_urls=True,
    remove_emails=True
)
```

### Quick Normalization

```python
from preprocessing import normalize_text

normalized = normalize_text(
    text,
    lowercase=True,
    remove_accents=True
)
```

### Quick Chunking

```python
from preprocessing import chunk_text

chunks = chunk_text(
    text,
    chunk_size=512,
    overlap=50
)
```

### Quick Deduplication

```python
from preprocessing import deduplicate_texts

unique = deduplicate_texts(
    texts,
    similarity_threshold=0.95,
    keep='first'
)
```

### Quick Full Processing

```python
from preprocessing import process_text

chunks = process_text(
    text,
    chunk_size=512,
    overlap=50,
    clean=True,
    normalize=True
)
```

---

## 🎯 COMMON USE CASES

### Use Case 1: Process Web-Scraped Content

**Problem:** HTML artifacts, URLs, excessive whitespace

```python
from preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline(
    remove_urls=True,
    remove_emails=True,
    chunk_size=512,
    deduplicate=True
)

chunks = pipeline.process(scraped_html)
```

---

### Use Case 2: Process Academic Papers

**Problem:** Special characters, citations, formatting

```python
from preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline(
    remove_accents=False,  # Keep proper names
    normalize_quotes=True,
    chunk_size=512,
    respect_paragraphs=True
)

chunks = pipeline.process(pdf_text)
```

---

### Use Case 3: Process User-Generated Content

**Problem:** Privacy concerns, varied formatting

```python
from preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline(
    remove_urls=True,
    remove_emails=True,
    remove_phone_numbers=True,
    lowercase=True,
    chunk_size=256,  # Smaller chunks
    deduplicate=True
)

chunks = pipeline.process(user_content)
```

---

### Use Case 4: Process Code Documentation

**Problem:** Code snippets, special formatting

```python
from preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline(
    remove_urls=False,  # Keep code links
    normalize_quotes=False,  # Preserve code quotes
    chunk_size=512,
    respect_paragraphs=True  # Keep code blocks together
)

chunks = pipeline.process(documentation)
```

---

## 🔧 ADVANCED USAGE

### Custom Preprocessing Logic

```python
from preprocessing import (
    TextCleaner,
    TextNormalizer,
    TextChunker
)

# Custom pipeline
cleaner = TextCleaner(remove_urls=True)
normalizer = TextNormalizer(remove_accents=True)
chunker = TextChunker(chunk_size=512)

# Process step-by-step
cleaned = cleaner.clean(raw_text)
normalized = normalizer.normalize(cleaned)
chunks = chunker.chunk_text(normalized)

# Add custom processing between steps
# ...
```

---

### Batch Processing with Progress Tracking

```python
from preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline()

documents = [...]  # List of documents
all_chunks = []

for i, doc in enumerate(documents):
    print(f"Processing document {i+1}/{len(documents)}...")
    chunks = pipeline.process(doc)
    all_chunks.extend(chunks)
    print(f"  Created {len(chunks)} chunks")

print(f"Total chunks: {len(all_chunks)}")
```

---

### Metadata Preservation

```python
from preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline()

# Add metadata
metadata = {
    'source': 'document.pdf',
    'author': 'John Doe',
    'date': '2025-10-11',
    'category': 'research'
}

chunks = pipeline.process(text, metadata=metadata)

# Metadata is preserved in each chunk
for chunk in chunks:
    print(chunk.metadata)  # {'source': 'document.pdf', ...}
```

---

## 🐛 TROUBLESHOOTING

### Issue: SSL Certificate Errors

**Symptom:**
```
OSError: Could not find a suitable TLS CA certificate bundle
```

**Solution:**
```python
import os
import certifi

# Fix SSL certificates
if 'SSL_CERT_FILE' in os.environ:
    del os.environ['SSL_CERT_FILE']

os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
```

---

### Issue: Memory Usage High

**Symptom:** Processing large documents uses too much memory

**Solution:**
```python
# Process in smaller batches
batch_size = 10

for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    results = pipeline.process_batch(batch)
    # Save results immediately
    save_to_disk(results)
```

---

### Issue: Chunks Too Small/Large

**Symptom:** Generated chunks don't meet size expectations

**Solution:**
```python
# Adjust chunk size and minimum
chunker = TextChunker(
    chunk_size=512,      # Target size
    min_chunk_size=100,  # Minimum allowed
    overlap_size=50      # Overlap between chunks
)

chunks = chunker.chunk_text(text)

# Verify chunk sizes
for chunk in chunks:
    print(f"Chunk {chunk.chunk_index}: {chunk.token_count} tokens")
```

---

## 📊 PERFORMANCE TIPS

### 1. Batch Processing
```python
# SLOW: Process one at a time
for text in texts:
    result = pipeline.process(text)

# FAST: Batch processing
results = pipeline.process_batch(texts)
```

### 2. Reuse Pipeline Objects
```python
# SLOW: Create new pipeline each time
for text in texts:
    pipeline = PreprocessingPipeline()
    result = pipeline.process(text)

# FAST: Reuse pipeline
pipeline = PreprocessingPipeline()
for text in texts:
    result = pipeline.process(text)
```

### 3. Disable Unnecessary Features
```python
# Only enable what you need
pipeline = PreprocessingPipeline(
    remove_urls=False,       # Disable if not needed
    remove_emails=False,     # Disable if not needed
    deduplicate=False,       # Expensive operation
)
```

---

## 📈 EXPECTED OUTPUT

### Input Document
```text
<h1>Research Paper</h1>

This is a research paper about AI.
Visit https://example.com for more info.

Contact: research@example.com
```

### After Processing
```python
chunks = pipeline.process(input_doc)

# Result:
# Chunk 0:
#   text: "Research Paper\n\nThis is a research paper about AI.\nVisit [URL] for more info.\n\nContact: [EMAIL]"
#   token_count: 28
#   chunk_index: 0
#   metadata: {}
```

---

## 🔗 SEE ALSO

- **Phase 3 Architecture:** `docs/PHASE_3_ARCHITECTURE.md`
- **Test Report:** `docs/PHASE_3_PREPROCESSING_TEST_REPORT.md`
- **Parser Quick Reference:** `services/document-processor/PARSER_QUICK_REFERENCE.md`

---

**Last Updated:** October 11, 2025  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
