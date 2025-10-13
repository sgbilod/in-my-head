"""
AI Configuration for In My Head
Supports multiple AI providers with fallback chains
"""

import os
from enum import Enum
from typing import Optional, Dict, Any


class EmbeddingProvider(str, Enum):
    """Embedding model providers"""
    LOCAL = "local"  # sentence-transformers (privacy-first)
    OPENAI = "openai"  # OpenAI API
    COHERE = "cohere"  # Cohere API
    HUGGINGFACE = "huggingface"  # HuggingFace Inference API


class LLMProvider(str, Enum):
    """Large Language Model providers"""
    CLAUDE = "claude"  # Anthropic Claude (best for reasoning)
    GEMINI = "gemini"  # Google Gemini Pro (fast, cost-effective)
    OPENAI = "openai"  # OpenAI GPT-4
    LOCAL = "local"  # Local LLM (ollama, llama.cpp)


class AIConfig:
    """Central AI configuration"""

    # ==================== EMBEDDING CONFIGURATION ====================

    # Primary embedding provider (local for privacy)
    EMBEDDING_PROVIDER: EmbeddingProvider = EmbeddingProvider.LOCAL

    # Local embedding model (lightweight and fast)
    # Options:
    # - "all-MiniLM-L6-v2" (384 dim, 80MB, fastest)
    # - "all-mpnet-base-v2" (768 dim, 420MB, better quality)
    # - "multi-qa-mpnet-base-dot-v1" (768 dim, optimized for Q&A)
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # OpenAI embedding model (fallback if local not available)
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"  # 1536 dim

    # ==================== LLM CONFIGURATION ====================

    # Primary LLM provider
    LLM_PROVIDER: LLMProvider = LLMProvider.CLAUDE

    # Fallback chain (if primary fails)
    LLM_FALLBACK_CHAIN: list[LLMProvider] = [
        LLMProvider.CLAUDE,
        LLMProvider.GEMINI,
        LLMProvider.OPENAI,
    ]

    # Claude configuration
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"  # Latest Sonnet
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.7

    # Gemini configuration
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"  # Fast and cost-effective
    GEMINI_MAX_TOKENS: int = 8192
    GEMINI_TEMPERATURE: float = 0.7

    # OpenAI configuration
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.7

    # ==================== API KEYS ====================

    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Get API key for provider from environment"""
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "google": "GOOGLE_API_KEY",
            "cohere": "COHERE_API_KEY",
            "huggingface": "HUGGINGFACE_API_KEY",
        }

        env_var = key_map.get(provider.lower())
        if env_var:
            return os.getenv(env_var)
        return None

    # ==================== PERFORMANCE TUNING ====================

    # Batch processing
    EMBEDDING_BATCH_SIZE: int = 32
    LLM_BATCH_SIZE: int = 5

    # Caching
    ENABLE_EMBEDDING_CACHE: bool = True
    ENABLE_LLM_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour

    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: float = 1.0

    # Timeouts
    EMBEDDING_TIMEOUT_SECONDS: int = 30
    LLM_TIMEOUT_SECONDS: int = 60

    # ==================== QUALITY SETTINGS ====================

    # Chunk size for document processing
    CHUNK_SIZE: int = 512  # tokens
    CHUNK_OVERLAP: int = 50  # tokens

    # Retrieval settings
    DEFAULT_TOP_K: int = 5
    MIN_SIMILARITY_THRESHOLD: float = 0.7

    # ==================== PRIVACY SETTINGS ====================

    # Always use local models (never call external APIs)
    PRIVACY_MODE: bool = True

    # Log all API calls for auditing
    LOG_API_CALLS: bool = True

    # Sanitize sensitive data before sending to APIs
    SANITIZE_PII: bool = True

    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        status = {
            "valid": True,
            "warnings": [],
            "errors": [],
        }

        # Check if sentence-transformers is available
        try:
            import sentence_transformers
            status["local_embeddings_available"] = True
        except ImportError:
            status["local_embeddings_available"] = False
            if cls.EMBEDDING_PROVIDER == EmbeddingProvider.LOCAL:
                status["warnings"].append(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )

        # Check API keys
        if cls.LLM_PROVIDER == LLMProvider.CLAUDE:
            if not cls.get_api_key("claude"):
                status["errors"].append("ANTHROPIC_API_KEY not set")
                status["valid"] = False

        if cls.LLM_PROVIDER == LLMProvider.GEMINI:
            if not cls.get_api_key("gemini"):
                status["errors"].append("GOOGLE_API_KEY not set")
                status["valid"] = False

        # Check privacy mode
        if cls.PRIVACY_MODE and cls.EMBEDDING_PROVIDER != EmbeddingProvider.LOCAL:
            status["warnings"].append(
                "PRIVACY_MODE enabled but not using local embeddings"
            )

        return status

    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("\n" + "="*70)
        print("AI CONFIGURATION".center(70))
        print("="*70)

        print(f"\n🔹 Embedding Provider: {cls.EMBEDDING_PROVIDER.value}")
        if cls.EMBEDDING_PROVIDER == EmbeddingProvider.LOCAL:
            print(f"   Model: {cls.LOCAL_EMBEDDING_MODEL}")

        print(f"\n🔹 LLM Provider: {cls.LLM_PROVIDER.value}")
        if cls.LLM_PROVIDER == LLMProvider.CLAUDE:
            print(f"   Model: {cls.CLAUDE_MODEL}")
            print(f"   API Key: {'✅ Set' if cls.get_api_key('claude') else '❌ Missing'}")
        elif cls.LLM_PROVIDER == LLMProvider.GEMINI:
            print(f"   Model: {cls.GEMINI_MODEL}")
            print(f"   API Key: {'✅ Set' if cls.get_api_key('gemini') else '❌ Missing'}")

        print(f"\n🔹 Privacy Mode: {'🔒 Enabled' if cls.PRIVACY_MODE else '🌐 Disabled'}")
        print(f"🔹 API Call Logging: {'✅ Enabled' if cls.LOG_API_CALLS else '❌ Disabled'}")

        print(f"\n🔹 Fallback Chain:")
        for i, provider in enumerate(cls.LLM_FALLBACK_CHAIN, 1):
            print(f"   {i}. {provider.value}")

        print("\n" + "="*70 + "\n")

        # Validation status
        status = cls.validate()
        if status["errors"]:
            print("❌ Configuration Errors:")
            for error in status["errors"]:
                print(f"   - {error}")

        if status["warnings"]:
            print("\n⚠️  Configuration Warnings:")
            for warning in status["warnings"]:
                print(f"   - {warning}")

        if status["valid"] and not status["warnings"]:
            print("✅ Configuration is valid!\n")


# Initialize configuration
config = AIConfig()
