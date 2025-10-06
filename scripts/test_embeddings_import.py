"""Quick test of sentence-transformers."""

print("Testing sentence-transformers import...")

try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence-transformers imported successfully")
    
    print("\nLoading model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded successfully")
    
    print("\nGenerating test embedding...")
    text = "This is a test sentence."
    embedding = model.encode(text)
    print(f"✅ Embedding generated: {len(embedding)} dimensions")
    print(f"   First few values: {embedding[:5]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
