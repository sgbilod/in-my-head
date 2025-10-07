"""
Tests for LLM service.

Covers:
- Multi-provider support (Claude, GPT, Gemini)
- Response generation
- Streaming functionality
- Error handling and fallbacks
- Context integration
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

from src.services.llm_service import (
    LLMService,
    LLMResponse,
    get_llm_service
)
from src.services.rag_service import RAGContext, SearchResult, Citation


# ==================== Fixtures ====================

@pytest.fixture
def sample_rag_context():
    """Sample RAG context for testing."""
    return RAGContext(
        query="What is machine learning?",
        context_text="Machine learning is a subset of AI...",
        chunks=[
            SearchResult(
                chunk_id=str(uuid4()),
                document_id=str(uuid4()),
                content="Machine learning is a subset of AI...",
                score=0.95,
                chunk_index=0,
                metadata={}
            )
        ],
        citations=[
            Citation(
                document_id=str(uuid4()),
                document_title="ML Basics",
                chunk_id=str(uuid4()),
                chunk_index=0,
                relevance_score=0.95,
                excerpt="Machine learning is a subset of AI..."
            )
        ],
        total_tokens=100,
        strategy="hybrid_rerank"
    )


@pytest.fixture
def llm_service():
    """LLM service with mock clients."""
    service = LLMService(
        anthropic_api_key="test-anthropic-key",
        openai_api_key="test-openai-key",
        google_api_key="test-google-key"
    )
    return service


# ==================== Prompt Building Tests ====================

class TestPromptBuilding:
    """Test prompt construction."""
    
    def test_build_prompt_includes_query(self, llm_service, sample_rag_context):
        """Test that prompt includes the user query."""
        prompt = llm_service.build_prompt(
            query="What is ML?",
            context=sample_rag_context
        )
        
        assert "What is ML?" in prompt
        assert "QUESTION:" in prompt
    
    def test_build_prompt_includes_context(self, llm_service, sample_rag_context):
        """Test that prompt includes retrieved context."""
        prompt = llm_service.build_prompt(
            query="What is ML?",
            context=sample_rag_context
        )
        
        assert sample_rag_context.context_text in prompt
        assert "CONTEXT:" in prompt
    
    def test_build_prompt_includes_citations(self, llm_service, sample_rag_context):
        """Test that prompt includes source citations."""
        prompt = llm_service.build_prompt(
            query="What is ML?",
            context=sample_rag_context
        )
        
        assert "SOURCES:" in prompt
        assert "[Doc 1]" in prompt
        assert sample_rag_context.citations[0].document_title in prompt
    
    def test_build_prompt_includes_instructions(
        self, llm_service, sample_rag_context
    ):
        """Test that prompt includes important instructions."""
        prompt = llm_service.build_prompt(
            query="What is ML?",
            context=sample_rag_context
        )
        
        assert "IMPORTANT INSTRUCTIONS:" in prompt
        assert "Use ONLY information from the context" in prompt
        assert "Cite sources" in prompt


# ==================== Claude Integration Tests ====================

class TestClaudeIntegration:
    """Test Claude/Anthropic integration."""
    
    @pytest.mark.asyncio
    async def test_generate_claude_success(self, sample_rag_context):
        """Test successful Claude response generation."""
        # Mock Anthropic client
        mock_message = Mock()
        mock_message.content = [Mock(text="Machine learning is AI.")]
        mock_message.usage = Mock(input_tokens=100, output_tokens=50)
        mock_message.stop_reason = "end_turn"
        
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        
        service = LLMService(anthropic_api_key="test-key")
        service.anthropic_client = mock_client
        
        # Generate response
        prompt = service.build_prompt("What is ML?", sample_rag_context)
        response = await service.generate_claude(prompt)
        
        # Verify response
        assert isinstance(response, LLMResponse)
        assert response.answer == "Machine learning is AI."
        assert response.model == "claude-sonnet-4-20250514"
        assert response.tokens_used == 150
        assert response.finish_reason == "end_turn"
        
        # Verify API call
        mock_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_claude_no_api_key(self):
        """Test Claude generation without API key."""
        service = LLMService()
        
        with pytest.raises(ValueError, match="Anthropic API key not configured"):
            await service.generate_claude("test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_claude_custom_params(self, sample_rag_context):
        """Test Claude with custom parameters."""
        mock_message = Mock()
        mock_message.content = [Mock(text="Response")]
        mock_message.usage = Mock(input_tokens=50, output_tokens=25)
        mock_message.stop_reason = "end_turn"
        
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        
        service = LLMService(anthropic_api_key="test-key")
        service.anthropic_client = mock_client
        
        prompt = service.build_prompt("Test", sample_rag_context)
        await service.generate_claude(
            prompt,
            model="claude-3-opus-20240229",
            temperature=0.5,
            max_tokens=2000
        )
        
        # Verify parameters passed to API
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs['model'] == "claude-3-opus-20240229"
        assert call_kwargs['temperature'] == 0.5
        assert call_kwargs['max_tokens'] == 2000


# ==================== GPT Integration Tests ====================

class TestGPTIntegration:
    """Test GPT/OpenAI integration."""
    
    @pytest.mark.asyncio
    async def test_generate_gpt_success(self, sample_rag_context):
        """Test successful GPT response generation."""
        # Mock OpenAI response
        mock_choice = Mock()
        mock_choice.message.content = "Machine learning is AI."
        mock_choice.finish_reason = "stop"
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage.total_tokens = 150
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        
        service = LLMService(openai_api_key="test-key")
        service.openai_client = mock_client
        
        # Generate response
        prompt = service.build_prompt("What is ML?", sample_rag_context)
        response = await service.generate_gpt(prompt)
        
        # Verify response
        assert isinstance(response, LLMResponse)
        assert response.answer == "Machine learning is AI."
        assert response.model == "gpt-4-turbo-preview"
        assert response.tokens_used == 150
        assert response.finish_reason == "stop"
    
    @pytest.mark.asyncio
    async def test_generate_gpt_no_api_key(self):
        """Test GPT generation without API key."""
        service = LLMService()
        
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            await service.generate_gpt("test prompt")


# ==================== Gemini Integration Tests ====================

class TestGeminiIntegration:
    """Test Gemini/Google integration."""
    
    @pytest.mark.asyncio
    async def test_generate_gemini_success(self, sample_rag_context):
        """Test successful Gemini response generation."""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = "Machine learning is AI."
        
        service = LLMService(google_api_key="test-key")
        service.genai_model = Mock()
        service.genai_model.generate_content_async = AsyncMock(
            return_value=mock_response
        )
        
        # Generate response
        prompt = service.build_prompt("What is ML?", sample_rag_context)
        response = await service.generate_gemini(prompt)
        
        # Verify response
        assert isinstance(response, LLMResponse)
        assert response.answer == "Machine learning is AI."
        assert response.model == "gemini-pro"
    
    @pytest.mark.asyncio
    async def test_generate_gemini_no_api_key(self):
        """Test Gemini generation without API key."""
        service = LLMService()
        
        with pytest.raises(ValueError, match="Google API key not configured"):
            await service.generate_gemini("test prompt")


# ==================== Unified Generation Tests ====================

class TestUnifiedGeneration:
    """Test unified generate() method with routing."""
    
    @pytest.mark.asyncio
    async def test_generate_routes_to_claude(self, sample_rag_context):
        """Test that 'claude' model routes to Claude."""
        service = LLMService(anthropic_api_key="test-key")
        service.generate_claude = AsyncMock(
            return_value=LLMResponse(
                answer="Test",
                model="claude-sonnet-4",
                tokens_used=100,
                finish_reason="end_turn"
            )
        )
        
        await service.generate(
            query="Test",
            context=sample_rag_context,
            model="claude-sonnet-4"
        )
        
        service.generate_claude.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_routes_to_gpt(self, sample_rag_context):
        """Test that 'gpt' model routes to GPT."""
        service = LLMService(openai_api_key="test-key")
        service.generate_gpt = AsyncMock(
            return_value=LLMResponse(
                answer="Test",
                model="gpt-4",
                tokens_used=100,
                finish_reason="stop"
            )
        )
        
        await service.generate(
            query="Test",
            context=sample_rag_context,
            model="gpt-4-turbo"
        )
        
        service.generate_gpt.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_routes_to_gemini(self, sample_rag_context):
        """Test that 'gemini' model routes to Gemini."""
        service = LLMService(google_api_key="test-key")
        service.generate_gemini = AsyncMock(
            return_value=LLMResponse(
                answer="Test",
                model="gemini-pro",
                tokens_used=100,
                finish_reason="stop"
            )
        )
        
        await service.generate(
            query="Test",
            context=sample_rag_context,
            model="gemini-pro"
        )
        
        service.generate_gemini.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_defaults_to_claude(self, sample_rag_context):
        """Test that unknown model defaults to Claude."""
        service = LLMService(anthropic_api_key="test-key")
        service.generate_claude = AsyncMock(
            return_value=LLMResponse(
                answer="Test",
                model="claude-sonnet-4",
                tokens_used=100,
                finish_reason="end_turn"
            )
        )
        
        await service.generate(
            query="Test",
            context=sample_rag_context,
            model="unknown-model"
        )
        
        service.generate_claude.assert_called_once()


# ==================== Streaming Tests ====================

class TestStreaming:
    """Test streaming functionality."""
    
    @pytest.mark.asyncio
    async def test_stream_claude(self, sample_rag_context):
        """Test Claude streaming."""
        # Mock streaming response
        async def mock_text_stream():
            for chunk in ["Machine ", "learning ", "is ", "AI."]:
                yield chunk
        
        mock_stream = AsyncMock()
        mock_stream.text_stream = mock_text_stream()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock()
        
        mock_client = Mock()
        mock_client.messages.stream = Mock(return_value=mock_stream)
        
        service = LLMService(anthropic_api_key="test-key")
        service.anthropic_client = mock_client
        
        # Collect streamed chunks
        chunks = []
        async for chunk in service.generate_stream(
            query="Test",
            context=sample_rag_context,
            model="claude-sonnet-4"
        ):
            chunks.append(chunk)
        
        # Verify streaming
        assert chunks == ["Machine ", "learning ", "is ", "AI."]
    
    @pytest.mark.asyncio
    async def test_stream_gpt(self, sample_rag_context):
        """Test GPT streaming."""
        # Mock streaming response
        async def mock_stream():
            for text in ["Machine ", "learning ", "is ", "AI."]:
                mock_chunk = Mock()
                mock_chunk.choices = [Mock()]
                mock_chunk.choices[0].delta.content = text
                yield mock_chunk
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )
        
        service = LLMService(openai_api_key="test-key")
        service.openai_client = mock_client
        
        # Collect streamed chunks
        chunks = []
        async for chunk in service.generate_stream(
            query="Test",
            context=sample_rag_context,
            model="gpt-4"
        ):
            chunks.append(chunk)
        
        # Verify streaming
        assert chunks == ["Machine ", "learning ", "is ", "AI."]
    
    @pytest.mark.asyncio
    async def test_stream_fallback_non_streaming(self, sample_rag_context):
        """Test fallback to non-streaming for unsupported providers."""
        service = LLMService(google_api_key="test-key")
        service.generate = AsyncMock(
            return_value=LLMResponse(
                answer="Complete response",
                model="gemini-pro",
                tokens_used=100,
                finish_reason="stop"
            )
        )
        
        # Collect streamed chunks
        chunks = []
        async for chunk in service.generate_stream(
            query="Test",
            context=sample_rag_context,
            model="gemini-pro"
        ):
            chunks.append(chunk)
        
        # Should receive full response at once
        assert chunks == ["Complete response"]


# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_no_api_keys_provided(self):
        """Test service initialization without any API keys."""
        service = LLMService()
        
        # Should initialize but have no clients
        assert service.anthropic_client is None
        assert service.openai_client is None
        assert service.genai_model is None
    
    @pytest.mark.asyncio
    async def test_generate_with_no_clients(self, sample_rag_context):
        """Test generation fails gracefully with no API keys."""
        service = LLMService()
        
        # Should raise ValueError for all providers
        with pytest.raises(ValueError):
            await service.generate(
                query="Test",
                context=sample_rag_context,
                model="claude-sonnet-4"
            )
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, sample_rag_context):
        """Test handling of API errors."""
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        service = LLMService(anthropic_api_key="test-key")
        service.anthropic_client = mock_client
        
        # Should propagate exception
        with pytest.raises(Exception, match="API Error"):
            prompt = service.build_prompt("Test", sample_rag_context)
            await service.generate_claude(prompt)


# ==================== Singleton Tests ====================

class TestSingleton:
    """Test singleton pattern."""
    
    def test_get_llm_service_singleton(self):
        """Test that get_llm_service returns singleton."""
        service1 = get_llm_service()
        service2 = get_llm_service()
        
        assert service1 is service2
    
    def test_get_llm_service_with_keys(self):
        """Test singleton with API keys."""
        service = get_llm_service(
            anthropic_api_key="test-key-1",
            openai_api_key="test-key-2"
        )
        
        # Should initialize with keys (only on first call)
        assert service is not None
