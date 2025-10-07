"""
Minimal embedding generation test - download model only.
"""

print("Testing sentence-transformers model download...")
print("This will download ~90MB on first run")
print("-" * 60)

try:
    print("\n1. Importing library...")
    from sentence_transformers import SentenceTransformer
    print("   ✅ Import successful")
    
    print("\n2. Loading model (downloading if needed)...")
    print("   Model: all-MiniLM-L6-v2")
    print("   This may take 2-3 minutes on first run...")
    
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    print("   ✅ Model loaded!")
    
    print("\n3. Testing embedding generation...")
    test_text = "This is a test sentence."
    embedding = model.encode(test_text)
    
    print(f"   ✅ Generated embedding:")
    print(f"      Dimensions: {len(embedding)}")
    print(f"      First 5 values: {embedding[:5]}")
    print(f"      Data type: {type(embedding)}")
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Model is working.")
    print("=" * 60)
    print("\nNext: Run full embedding generation script")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
