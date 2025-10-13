"""
AI Service
Handles embedding generation and semantic search with multi-provider support
"""

from typing import List, Optional
import os
import logging

# Try importing sentence-transformers for local embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    logging.warning(
        "⚠️  sentence-transformers not available. "
        "Install with: pip install sentence-transformers torch"
    )

import numpy as np

# Try importing AI provider clients
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.info("Anthropic client not available. Install with: pip install anthropic")

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    logging.info("Google AI client not available. Install with: pip install google-generativeai")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.info("OpenAI client not available. Install with: pip install openai")


class AIService:
    """
    Service for AI operations with multi-provider support

    Supports:
    - Local embeddings (sentence-transformers) - PRIVACY FIRST
    - Claude API (Anthropic) - Best for reasoning
    - Gemini Pro (Google) - Fast and cost-effective
    - OpenAI API - Fallback option
    """

    def __init__(
        self,
        embedding_provider: str = "local",
        embedding_model: str = "all-MiniLM-L6-v2",
        llm_provider: str = "claude"
    ):
        """
        Initialize AI service with specified providers

        Args:
            embedding_provider: "local", "openai", "cohere"
            embedding_model: Model name for embeddings
            llm_provider: "claude", "gemini", "openai"
        """
        self.embedding_provider = embedding_provider
        self.llm_provider = llm_provider

        # Initialize embedding model
        self._init_embeddings(embedding_provider, embedding_model)

        # Initialize LLM client
        self._init_llm(llm_provider)

        print(f"✅ AI Service initialized!")
        print(f"   📊 Embeddings: {embedding_provider} (dim: {self.embedding_dim})")
        print(f"   🤖 LLM: {llm_provider}")

    def _init_embeddings(self, provider: str, model_name: str):
        """Initialize embedding provider"""
        if provider == "local":
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                print("⚠️  sentence-transformers not available, falling back to OpenAI")
                self._init_embeddings("openai", model_name)
                return

            print(f"🔒 Loading LOCAL embedding model: {model_name}")
            print("   (This provides 100% privacy - no external API calls)")
            self.embedding_model = SentenceTransformer(model_name)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            self.openai_client = None

        elif provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI client not installed. pip install openai")

            print("🌐 Using OpenAI embeddings API")
            self.embedding_model = None
            self.embedding_dim = 1536  # text-embedding-3-small
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self.openai_client = OpenAI(api_key=api_key)

        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

    def _init_llm(self, provider: str):
        """Initialize LLM client"""
        self.llm_client = None

        if provider == "claude":
            if not ANTHROPIC_AVAILABLE:
                print("⚠️  Anthropic client not available, falling back to Gemini")
                self._init_llm("gemini")
                return

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("⚠️  ANTHROPIC_API_KEY not set, falling back to Gemini")
                self._init_llm("gemini")
                return

            self.llm_client = Anthropic(api_key=api_key)
            self.llm_model = "claude-sonnet-4-20250514"

        elif provider == "gemini":
            if not GOOGLE_AI_AVAILABLE:
                print("⚠️  Google AI client not available, falling back to OpenAI")
                self._init_llm("openai")
                return

            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("⚠️  GOOGLE_API_KEY not set, falling back to OpenAI")
                self._init_llm("openai")
                return

            genai.configure(api_key=api_key)
            self.llm_client = genai.GenerativeModel("gemini-2.0-flash-exp")
            self.llm_model = "gemini-2.0-flash-exp"

        elif provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("No LLM provider available")

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️  No LLM provider configured - LLM features disabled")
                return

            if not self.openai_client:
                self.openai_client = OpenAI(api_key=api_key)
            self.llm_model = "gpt-4o"


    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.embedding_dim

        if self.embedding_provider == "local":
            # Use local model (100% private)
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        elif self.embedding_provider == "openai":
            # Use OpenAI API
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"❌ OpenAI embedding failed: {e}")
                raise


    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embeddings
        """
        if not texts:
            return []

        if self.embedding_provider == "local":
            # Use local model (100% private)
            embeddings = self.embedding_model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=True
            )
            return embeddings.tolist()
        elif self.embedding_provider == "openai":
            # Use OpenAI API (supports batching)
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=texts
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                print(f"❌ OpenAI batch embedding failed: {e}")
                raise

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using configured LLM

        Args:
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)

        Returns:
            Generated text
        """
        if not self.llm_client:
            return "LLM not configured - text generation unavailable"

        try:
            if self.llm_provider == "claude":
                # Use Claude API
                response = self.llm_client.messages.create(
                    model=self.llm_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text

            elif self.llm_provider == "gemini":
                # Use Gemini API
                response = self.llm_client.generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": max_tokens,
                        "temperature": temperature,
                    }
                )
                return response.text

            elif self.llm_provider == "openai":
                # Use OpenAI API
                response = self.openai_client.chat.completions.create(
                    model=self.llm_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content

        except Exception as e:
            print(f"❌ LLM generation failed with {self.llm_provider}: {e}")
            raise

    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score between 0 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Normalize to 0-1 range
        return float((similarity + 1) / 2)


# Global instance (singleton pattern)
_ai_service_instance: Optional[AIService] = None


def get_ai_service(
    embedding_provider: str = "local",
    embedding_model: str = "all-MiniLM-L6-v2",
    llm_provider: str = "claude"
) -> AIService:
    """
    Get or create AI service instance

    Args:
        embedding_provider: "local" (privacy-first), "openai", "cohere"
        embedding_model: Model name for local embeddings
        llm_provider: "claude" (best), "gemini" (fast), "openai" (fallback)

    Returns:
        AIService instance
    """
    global _ai_service_instance

    if _ai_service_instance is None:
        # Read from environment variables if set
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", embedding_provider)
        embedding_model = os.getenv("EMBEDDING_MODEL", embedding_model)
        llm_provider = os.getenv("LLM_PROVIDER", llm_provider)

        _ai_service_instance = AIService(
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            llm_provider=llm_provider
        )

    return _ai_service_instance
