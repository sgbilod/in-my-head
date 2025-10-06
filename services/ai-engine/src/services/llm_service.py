"""
LLM integration for RAG query endpoint.

Supports multiple LLM providers:
- Claude (Anthropic)
- GPT (OpenAI)
- Gemini (Google)
"""

import asyncio
import logging
from typing import Optional, AsyncIterator, Dict, Any
from dataclasses import dataclass

import anthropic
import openai
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
    - Multiple LLM providers (Claude, GPT, Gemini)
    - Streaming support
    - Token counting
    - Error handling with fallbacks
    """
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None
    ):
        """Initialize LLM service."""
        
        self.anthropic_client = None
        self.openai_client = None
        self.genai_model = None
        
        # Initialize clients based on available API keys
        if anthropic_api_key:
            self.anthropic_client = anthropic.AsyncAnthropic(
                api_key=anthropic_api_key
            )
            logger.info("✅ Anthropic client initialized")
        
        if openai_api_key:
            self.openai_client = openai.AsyncOpenAI(
                api_key=openai_api_key
            )
            logger.info("✅ OpenAI client initialized")
        
        if google_api_key:
            genai.configure(api_key=google_api_key)
            self.genai_model = genai.GenerativeModel('gemini-pro')
            logger.info("✅ Google Generative AI initialized")
    
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
    
    async def generate_gpt(
        self,
        prompt: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Generate response using GPT.
        
        Args:
            prompt: Full prompt with context
            model: GPT model name
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            LLM response
        """
        
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        logger.info(f"Generating with GPT: {model}")
        
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        logger.info(f"  Response: {len(answer)} chars, {tokens_used} tokens")
        
        return LLMResponse(
            answer=answer,
            model=model,
            tokens_used=tokens_used,
            finish_reason=response.choices[0].finish_reason
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
        if "claude" in model.lower():
            return await self.generate_claude(
                prompt,
                model,
                temperature,
                max_tokens
            )
        elif "gpt" in model.lower() or "openai" in model.lower():
            return await self.generate_gpt(
                prompt,
                model,
                temperature,
                max_tokens
            )
        elif "gemini" in model.lower():
            return await self.generate_gemini(
                prompt,
                temperature,
                max_tokens
            )
        else:
            # Default to Claude
            logger.warning(
                f"Unknown model '{model}', defaulting to Claude"
            )
            return await self.generate_claude(
                prompt,
                "claude-sonnet-4-20250514",
                temperature,
                max_tokens
            )
    
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
        
        if "claude" in model.lower() and self.anthropic_client:
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
        
        elif "gpt" in model.lower() and self.openai_client:
            # Stream from GPT
            stream = await self.openai_client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
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
    openai_api_key: Optional[str] = None,
    google_api_key: Optional[str] = None
) -> LLMService:
    """Get singleton LLM service."""
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService(
            anthropic_api_key=anthropic_api_key,
            openai_api_key=openai_api_key,
            google_api_key=google_api_key
        )
    
    return _llm_service
