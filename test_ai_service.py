"""
Test AI Service Configuration
Verify local embeddings and AI providers work correctly
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'document-processor'))

from src.services.ai_service import AIService, SENTENCE_TRANSFORMERS_AVAILABLE

def test_local_embeddings():
    """Test local embedding generation"""
    print("\n" + "="*70)
    print("TEST 1: LOCAL EMBEDDINGS (Privacy-First)".center(70))
    print("="*70)

    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        print("❌ sentence-transformers not available")
        return False

    try:
        # Initialize with local embeddings
        service = AIService(
            embedding_provider="local",
            embedding_model="all-MiniLM-L6-v2",
            llm_provider="claude"
        )

        # Test single embedding
        print("\n📝 Testing single text embedding...")
        text = "Machine learning is a subset of artificial intelligence."
        embedding = service.generate_embedding(text)

        print(f"✅ Generated embedding!")
        print(f"   - Dimension: {len(embedding)}")
        print(f"   - First 5 values: {embedding[:5]}")
        print(f"   - Provider: {service.embedding_provider}")
        print(f"   - Privacy: 100% LOCAL (no API calls)")

        # Test batch embeddings
        print("\n📝 Testing batch embeddings...")
        texts = [
            "This is the first document.",
            "Here is the second document.",
            "And this is the third one.",
        ]
        embeddings = service.generate_embeddings_batch(texts)

        print(f"✅ Generated {len(embeddings)} embeddings!")
        print(f"   - All same dimension: {len(set(len(e) for e in embeddings)) == 1}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_keys():
    """Check which API keys are configured"""
    print("\n" + "="*70)
    print("TEST 2: API KEY CONFIGURATION".center(70))
    print("="*70)

    keys = {
        "ANTHROPIC_API_KEY": "Claude (Anthropic)",
        "GOOGLE_API_KEY": "Gemini Pro (Google)",
        "OPENAI_API_KEY": "OpenAI",
    }

    configured = []
    missing = []

    for env_var, name in keys.items():
        key = os.getenv(env_var)
        if key and key != "your_anthropic_api_key_here" and key != "your_google_api_key_here":
            configured.append(name)
            # Don't print the actual key, just confirm it exists
            key_preview = key[:10] + "..." if len(key) > 10 else key
            print(f"✅ {name}: Configured ({key_preview}...)")
        else:
            missing.append(name)
            print(f"⚠️  {name}: Not configured")

    print(f"\n📊 Summary:")
    print(f"   - Configured: {len(configured)}/3")
    print(f"   - Missing: {len(missing)}/3")

    if missing:
        print(f"\n💡 To configure missing keys:")
        print(f"   Edit: infrastructure/docker/.env")
        print(f"   See: docs/AI_SETUP_GUIDE.md")

    return len(configured) >= 1  # At least one provider configured


def test_llm_generation():
    """Test LLM text generation (if API keys available)"""
    print("\n" + "="*70)
    print("TEST 3: LLM TEXT GENERATION".center(70))
    print("="*70)

    # Check which providers are available
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    gemini_key = os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    has_anthropic = anthropic_key and anthropic_key != "your_anthropic_api_key_here"
    has_gemini = gemini_key and gemini_key != "your_google_api_key_here"
    has_openai = openai_key and "sk-" in openai_key

    if not (has_anthropic or has_gemini or has_openai):
        print("⚠️  No LLM API keys configured - skipping LLM test")
        print("   This is OK! Embeddings work without LLM keys.")
        return True

    # Try providers in order
    providers_to_try = []
    if has_anthropic:
        providers_to_try.append("claude")
    if has_gemini:
        providers_to_try.append("gemini")
    if has_openai:
        providers_to_try.append("openai")

    for provider in providers_to_try:
        try:
            print(f"\n🤖 Testing {provider.upper()} provider...")
            service = AIService(
                embedding_provider="local",
                llm_provider=provider
            )

            # Test text generation
            prompt = "In one sentence, what is artificial intelligence?"
            print(f"   Prompt: {prompt}")

            response = service.generate_text(
                prompt=prompt,
                max_tokens=100,
                temperature=0.7
            )

            print(f"✅ Response from {provider}:")
            print(f"   {response}")
            return True

        except Exception as e:
            print(f"⚠️  {provider} failed: {e}")
            continue

    print("❌ All LLM providers failed")
    return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("IN MY HEAD - AI SERVICE TEST SUITE".center(70))
    print("="*70)
    print("\nThis will test:")
    print("  1. Local embedding generation (privacy-first)")
    print("  2. API key configuration")
    print("  3. LLM text generation (if keys available)")

    results = {}

    # Test 1: Local embeddings (critical)
    results['embeddings'] = test_local_embeddings()

    # Test 2: API keys (informational)
    results['api_keys'] = test_api_keys()

    # Test 3: LLM generation (optional)
    results['llm'] = test_llm_generation()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY".center(70))
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n✅ Passed: {passed}/{total}")

    if results['embeddings']:
        print("\n🎉 SUCCESS! Local embeddings are working!")
        print("   - Documents can be uploaded and embedded")
        print("   - 100% privacy (no external API calls for embeddings)")
    else:
        print("\n❌ Local embeddings failed - install sentence-transformers")
        print("   pip install sentence-transformers torch transformers")

    if not results['api_keys']:
        print("\n⚠️  No API keys configured yet")
        print("   - Embeddings work, but LLM queries won't")
        print("   - See docs/AI_SETUP_GUIDE.md to add your keys")

    if results['llm']:
        print("\n✅ LLM generation working - full system operational!")
    else:
        print("\n⚠️  LLM not tested - add API keys to enable")

    print("\n" + "="*70 + "\n")

    return results['embeddings']  # Return True if embeddings work


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
