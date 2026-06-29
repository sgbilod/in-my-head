"""
LLM integration for RAG query endpoint.

Supports multiple LLM providers:
- Ollama (local, default)
- Claude (Anthropic)
- Gemini (Google)
"""

import asyncio
import logging
from typing import Optional, AsyncIterator, Dict, Any
from dataclasses import dataclass

import httpx
import anthropic
from google import generativeai as genai

from src.services.rag_service import RAGContext

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM response with metadata."""
    answer: str
    model: str
    tokens_used: int
    finish_reason: str


class LLMService:
    """
    Service for LLM inference with multiple providers.
    
    Features:
    - Multiple LLM providers (local Ollama, Claude, Gemini)
    - Streaming support
    - Token counting
    - Error handling with fallbacks
    """
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        ollama_url: Optional[str] = None,
        ollama_model: Optional[str] = None
    ):
        """Initialize LLM service (local-first; no OpenAI per values rule)."""

        self.anthropic_client = None
        self.genai_model = None
        self.ollama_url = ollama_url or "http://localhost:11434"
        self.ollama_model = ollama_model or "llama3"
        self.ollama_available = False

        # Ollama (local-first, always try)
        try:
            resp = httpx.get(f"{self.ollama_url}/api/tags", timeout=3.0)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                self.ollama_available = True
                logger.info(f"Ollama connected: {', '.join(models)}")
        except Exception:
            logger.warning("Ollama not available at %s", self.ollama_url)

        if anthropic_api_key:
            self.anthropic_client = anthropic.AsyncAnthropic(
                api_key=anthropic_api_key
            )
            logger.info("Anthropic client initialized")

        if google_api_key:
            genai.configure(api_key=google_api_key)
            self.genai_model = genai.GenerativeModel('gemini-pro')
            logger.info("Google Generative AI initialized")
    
    def build_prompt(
        self,
        query: str,
        context: RAGContext
    ) -> str:
        """
        Build prompt for LLM with context and citations.
        
        Args:
            query: User's question
            context: Retrieved context with citations
            
        Returns:
            Formatted prompt
        """
        
        prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided context.

IMPORTANT INSTRUCTIONS:
1. Use ONLY information from the context provided
2. If the context doesn't contain relevant information, say so
3. Cite sources using [Doc N] notation (e.g., [Doc 1])
4. Be concise but comprehensive
5. If you're uncertain, express that uncertainty

CONTEXT:
{context.context_text}

SOURCES:
"""
        
        for i, citation in enumerate(context.citations, 1):
            prompt += f"\n[Doc {i}] {citation.document_title}"
            prompt += f"\n  Excerpt: {citation.excerpt}\n"
        
        prompt += f"\n\nQUESTION: {query}\n\nANSWER:"
        
        return prompt
    
    async def generate_ollama(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """Generate response using local Ollama."""

        if not self.ollama_available:
            raise ValueError("Ollama is not available")

        model = model or self.ollama_model
        logger.info(f"Generating with Ollama: {model}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()

        answer = data.get("response", "")
        tokens_used = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

        logger.info(f"  Ollama response: {len(answer)} chars, {tokens_used} tokens")

        return LLMResponse(
            answer=answer,
            model=model,
            tokens_used=tokens_used,
            finish_reason="stop" if data.get("done") else "length",
        )

    async def generate_claude(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Generate response using Claude.
        
        Args:
            prompt: Full prompt with context
            model: Claude model name
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            LLM response
        """
        
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        logger.info(f"Generating with Claude: {model}")
        
        message = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        answer = message.content[0].text
        tokens_used = message.usage.input_tokens + message.usage.output_tokens
        
        logger.info(f"  Response: {len(answer)} chars, {tokens_used} tokens")
        
        return LLMResponse(
            answer=answer,
            model=model,
            tokens_used=tokens_used,
            finish_reason=message.stop_reason
        )
    
    async def generate_gemini(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Generate response using Gemini.
        
        Args:
            prompt: Full prompt with context
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            LLM response
        """
        
        if not self.genai_model:
            raise ValueError("Google API key not configured")
        
        logger.info("Generating with Gemini")
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        response = await self.genai_model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        
        answer = response.text
        
        logger.info(f"  Response: {len(answer)} chars")
        
        return LLMResponse(
            answer=answer,
            model="gemini-pro",
            tokens_used=0,  # Gemini doesn't return token count easily
            finish_reason="stop"
        )
    
    async def generate(
        self,
        query: str,
        context: RAGContext,
        model: str = "claude-sonnet-4",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Generate response with automatic provider selection.
        
        Args:
            query: User's question
            context: Retrieved context
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            LLM response
        """
        
        prompt = self.build_prompt(query, context)

        # Route to appropriate provider
        if "ollama" in model.lower() or model in ("llama3", "llama3.1", "qwen3", "gemma4"):
            return await self.generate_ollama(prompt, model, temperature, max_tokens)
        elif "claude" in model.lower():
            return await self.generate_claude(prompt, model, temperature, max_tokens)
        elif "gemini" in model.lower():
            return await self.generate_gemini(prompt, temperature, max_tokens)
        else:
            # Default chain: local Ollama -> Gemini (fallback) -> Claude
            if self.ollama_available:
                logger.info(f"Defaulting to Ollama ({self.ollama_model})")
                return await self.generate_ollama(prompt, None, temperature, max_tokens)
            elif self.genai_model:
                logger.info("Ollama unavailable, falling back to Gemini")
                return await self.generate_gemini(prompt, temperature, max_tokens)
            elif self.anthropic_client:
                logger.info("Ollama/Gemini unavailable, falling back to Claude")
                return await self.generate_claude(
                    prompt, "claude-sonnet-4-20250514", temperature, max_tokens
                )
            else:
                raise ValueError("No LLM provider available (Ollama down, no API keys)")
    
    async def generate_stream(
        self,
        query: str,
        context: RAGContext,
        model: str = "claude-sonnet-4",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncIterator[str]:
        """
        Generate response with streaming.
        
        Args:
            query: User's question
            context: Retrieved context
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Yields:
            Answer chunks
        """
        
        prompt = self.build_prompt(query, context)

        use_ollama = (
            "ollama" in model.lower()
            or model in ("llama3", "llama3.1", "qwen3", "gemma4")
            or (self.ollama_available and "claude" not in model.lower())
        )

        if use_ollama and self.ollama_available:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model if model not in ("claude-sonnet-4",) else self.ollama_model,
                        "prompt": prompt,
                        "stream": True,
                        "options": {"temperature": temperature, "num_predict": max_tokens},
                    },
                ) as resp:
                    import json as _json
                    async for line in resp.aiter_lines():
                        if line:
                            chunk = _json.loads(line)
                            if chunk.get("response"):
                                yield chunk["response"]

        elif "claude" in model.lower() and self.anthropic_client:
            # Stream from Claude
            async with self.anthropic_client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        else:
            # Fallback: non-streaming
            response = await self.generate(
                query,
                context,
                model,
                temperature,
                max_tokens
            )
            yield response.answer


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service(
    anthropic_api_key: Optional[str] = None,
    google_api_key: Optional[str] = None,
    ollama_url: Optional[str] = None,
    ollama_model: Optional[str] = None
) -> LLMService:
    """Get singleton LLM service (local-first; no OpenAI per values rule)."""
    global _llm_service

    if _llm_service is None:
        import os
        _llm_service = LLMService(
            anthropic_api_key=anthropic_api_key,
            google_api_key=google_api_key,
            ollama_url=ollama_url or os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            ollama_model=ollama_model or os.getenv("OLLAMA_MODEL", "llama3"),
        )

    return _llm_service
