"""
Tests for conversation service.

Covers:
- Conversation CRUD operations
- Message management
- RAG integration
- Citation tracking
- Multi-turn conversations
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID
import asyncpg

from src.services.conversation_service import (
    ConversationService,
    get_conversation_service
)


# ==================== Fixtures ====================

@pytest.fixture
async def db_pool():
    """Create test database connection pool."""
    pool = await asyncpg.create_pool(
        "postgresql://inmyhead:inmyhead_dev_pass@"
        "localhost:5434/inmyhead_dev",
        min_size=1,
        max_size=2
    )
    yield pool
    await pool.close()


@pytest.fixture
async def conversation_service(db_pool):
    """Conversation service with test database."""
    service = ConversationService(
        "postgresql://inmyhead:inmyhead_dev_pass@"
        "localhost:5434/inmyhead_dev"
    )
    await service.initialize()
    yield service
    await service.close()


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return uuid4()


@pytest.fixture
async def test_conversation(conversation_service, test_user_id):
    """Create a test conversation."""
    conversation = await conversation_service.create_conversation(
        user_id=test_user_id,
        title="Test Conversation"
    )
    return conversation


# ==================== Conversation CRUD Tests ====================

class TestConversationCRUD:
    """Test conversation creation, reading, updating, deletion."""
    
    @pytest.mark.asyncio
    async def test_create_conversation(
        self, conversation_service, test_user_id
    ):
        """Test creating a new conversation."""
        conversation = await conversation_service.create_conversation(
            user_id=test_user_id,
            title="Machine Learning Q&A"
        )
        
        # Verify conversation created
        assert conversation['id'] is not None
        assert conversation['user_id'] == test_user_id
        assert conversation['title'] == "Machine Learning Q&A"
        assert conversation['created_at'] is not None
        assert conversation['updated_at'] is not None
    
    @pytest.mark.asyncio
    async def test_get_conversation(
        self, conversation_service, test_user_id, test_conversation
    ):
        """Test retrieving a conversation."""
        conversation = await conversation_service.get_conversation(
            conversation_id=test_conversation['id'],
            user_id=test_user_id
        )
        
        # Verify conversation retrieved
        assert conversation is not None
        assert conversation['id'] == test_conversation['id']
        assert conversation['title'] == test_conversation['title']
    
    @pytest.mark.asyncio
    async def test_get_conversation_wrong_user(
        self, conversation_service, test_conversation
    ):
        """Test that users can't access other users' conversations."""
        wrong_user_id = uuid4()
        
        conversation = await conversation_service.get_conversation(
            conversation_id=test_conversation['id'],
            user_id=wrong_user_id
        )
        
        # Should not find conversation
        assert conversation is None
    
    @pytest.mark.asyncio
    async def test_list_conversations(
        self, conversation_service, test_user_id
    ):
        """Test listing user's conversations."""
        # Create multiple conversations
        conv1 = await conversation_service.create_conversation(
            user_id=test_user_id,
            title="Conversation 1"
        )
        conv2 = await conversation_service.create_conversation(
            user_id=test_user_id,
            title="Conversation 2"
        )
        
        # List conversations
        conversations = await conversation_service.list_conversations(
            user_id=test_user_id,
            limit=10
        )
        
        # Verify both conversations listed
        assert len(conversations) >= 2
        conversation_ids = [c['id'] for c in conversations]
        assert conv1['id'] in conversation_ids
        assert conv2['id'] in conversation_ids
    
    @pytest.mark.asyncio
    async def test_list_conversations_pagination(
        self, conversation_service, test_user_id
    ):
        """Test conversation pagination."""
        # Create several conversations
        for i in range(5):
            await conversation_service.create_conversation(
                user_id=test_user_id,
                title=f"Conversation {i}"
            )
        
        # Test pagination
        page1 = await conversation_service.list_conversations(
            user_id=test_user_id,
            limit=2,
            offset=0
        )
        page2 = await conversation_service.list_conversations(
            user_id=test_user_id,
            limit=2,
            offset=2
        )
        
        # Verify different conversations
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]['id'] != page2[0]['id']
    
    @pytest.mark.asyncio
    async def test_delete_conversation(
        self, conversation_service, test_user_id, test_conversation
    ):
        """Test deleting a conversation."""
        # Delete conversation
        deleted = await conversation_service.delete_conversation(
            conversation_id=test_conversation['id'],
            user_id=test_user_id
        )
        
        assert deleted is True
        
        # Verify conversation deleted
        conversation = await conversation_service.get_conversation(
            conversation_id=test_conversation['id'],
            user_id=test_user_id
        )
        assert conversation is None
    
    @pytest.mark.asyncio
    async def test_delete_conversation_wrong_user(
        self, conversation_service, test_conversation
    ):
        """Test that users can't delete other users' conversations."""
        wrong_user_id = uuid4()
        
        deleted = await conversation_service.delete_conversation(
            conversation_id=test_conversation['id'],
            user_id=wrong_user_id
        )
        
        # Should not delete
        assert deleted is False


# ==================== Message Management Tests ====================

class TestMessageManagement:
    """Test message creation and retrieval."""
    
    @pytest.mark.asyncio
    async def test_add_user_message(
        self, conversation_service, test_conversation
    ):
        """Test adding a user message."""
        message = await conversation_service.add_user_message(
            conversation_id=test_conversation['id'],
            content="What is machine learning?"
        )
        
        # Verify message created
        assert message['id'] is not None
        assert message['conversation_id'] == test_conversation['id']
        assert message['role'] == 'user'
        assert message['content'] == "What is machine learning?"
        assert message['created_at'] is not None
    
    @pytest.mark.asyncio
    async def test_add_assistant_message_without_rag(
        self, conversation_service, test_conversation
    ):
        """Test adding assistant message without RAG."""
        message = await conversation_service.add_assistant_message(
            conversation_id=test_conversation['id'],
            content="Test content",
            query="Test query",
            use_rag=False
        )
        
        # Verify message created
        assert message['id'] is not None
        assert message['role'] == 'assistant'
        assert message['rag_context'] is None
        assert message['citations'] is None
    
    @pytest.mark.asyncio
    @patch('src.services.conversation_service.get_rag_service')
    @patch('src.services.conversation_service.get_llm_service')
    async def test_add_assistant_message_with_rag(
        self,
        mock_get_llm,
        mock_get_rag,
        conversation_service,
        test_conversation
    ):
        """Test adding assistant message with RAG integration."""
        # Mock RAG service
        mock_rag = Mock()
        mock_context = Mock()
        mock_context.chunks = [
            Mock(
                chunk_id=str(uuid4()),
                document_id=str(uuid4()),
                content="ML is AI",
                score=0.95
            )
        ]
        mock_context.context_text = "Machine learning is AI..."
        mock_context.total_tokens = 100
        
        mock_citation = Mock()
        mock_citation.document_id = str(uuid4())
        mock_citation.document_title = "ML Basics"
        mock_citation.chunk_id = str(uuid4())
        mock_citation.relevance_score = 0.95
        mock_citation.excerpt = "ML is AI"
        
        mock_rag.retrieve = AsyncMock(return_value=mock_context)
        mock_rag.extract_citations = Mock(return_value=[mock_citation])
        mock_get_rag.return_value = mock_rag
        
        # Mock LLM service
        mock_llm = Mock()
        mock_llm_response = Mock()
        mock_llm_response.answer = "Machine learning is a subset of AI..."
        mock_llm_response.tokens_used = 150
        mock_llm.generate = AsyncMock(return_value=mock_llm_response)
        mock_get_llm.return_value = mock_llm
        
        # Add assistant message
        message = await conversation_service.add_assistant_message(
            conversation_id=test_conversation['id'],
            content="What is machine learning?",
            query="What is machine learning?",
            use_rag=True
        )
        
        # Verify message created with RAG context
        assert message['role'] == 'assistant'
        assert message['content'] == "Machine learning is a subset of AI..."
        assert message['rag_context'] is not None
        assert message['citations'] is not None
        assert message['tokens_used'] == 150
        
        # Verify RAG service called
        mock_rag.retrieve.assert_called_once()
        mock_llm.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_messages(
        self, conversation_service, test_conversation
    ):
        """Test retrieving conversation messages."""
        # Add messages
        msg1 = await conversation_service.add_user_message(
            conversation_id=test_conversation['id'],
            content="Question 1"
        )
        msg2 = await conversation_service.add_user_message(
            conversation_id=test_conversation['id'],
            content="Question 2"
        )
        
        # Get messages
        messages = await conversation_service.get_messages(
            conversation_id=test_conversation['id']
        )
        
        # Verify messages retrieved in order
        assert len(messages) >= 2
        message_ids = [m['id'] for m in messages]
        assert msg1['id'] in message_ids
        assert msg2['id'] in message_ids
        
        # Verify chronological order
        msg1_idx = next(
            i for i, m in enumerate(messages) if m['id'] == msg1['id']
        )
        msg2_idx = next(
            i for i, m in enumerate(messages) if m['id'] == msg2['id']
        )
        assert msg1_idx < msg2_idx
    
    @pytest.mark.asyncio
    async def test_get_messages_pagination(
        self, conversation_service, test_conversation
    ):
        """Test message pagination."""
        # Add multiple messages
        for i in range(5):
            await conversation_service.add_user_message(
                conversation_id=test_conversation['id'],
                content=f"Message {i}"
            )
        
        # Test pagination
        page1 = await conversation_service.get_messages(
            conversation_id=test_conversation['id'],
            limit=2,
            offset=0
        )
        page2 = await conversation_service.get_messages(
            conversation_id=test_conversation['id'],
            limit=2,
            offset=2
        )
        
        # Verify different messages
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]['id'] != page2[0]['id']


# ==================== Multi-Turn Conversation Tests ====================

class TestMultiTurnConversations:
    """Test multi-turn conversation flows."""
    
    @pytest.mark.asyncio
    @patch('src.services.conversation_service.get_rag_service')
    @patch('src.services.conversation_service.get_llm_service')
    async def test_multi_turn_conversation_flow(
        self,
        mock_get_llm,
        mock_get_rag,
        conversation_service,
        test_user_id
    ):
        """Test a complete multi-turn conversation."""
        # Create conversation
        conversation = await conversation_service.create_conversation(
            user_id=test_user_id,
            title="ML Discussion"
        )
        
        # Mock services
        mock_rag = Mock()
        mock_rag.retrieve = AsyncMock(return_value=Mock(
            chunks=[],
            context_text="Context",
            total_tokens=50
        ))
        mock_rag.extract_citations = Mock(return_value=[])
        mock_get_rag.return_value = mock_rag
        
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(return_value=Mock(
            answer="Response",
            tokens_used=100
        ))
        mock_get_llm.return_value = mock_llm
        
        # Turn 1: User asks question
        user_msg1 = await conversation_service.add_user_message(
            conversation_id=conversation['id'],
            content="What is supervised learning?"
        )
        
        # Turn 1: Assistant responds
        assistant_msg1 = await conversation_service.add_assistant_message(
            conversation_id=conversation['id'],
            content="What is supervised learning?",
            query="What is supervised learning?",
            use_rag=True
        )
        
        # Turn 2: User asks follow-up
        user_msg2 = await conversation_service.add_user_message(
            conversation_id=conversation['id'],
            content="Can you give me an example?"
        )
        
        # Turn 2: Assistant responds
        assistant_msg2 = await conversation_service.add_assistant_message(
            conversation_id=conversation['id'],
            content="Can you give me an example?",
            query="Can you give me an example?",
            use_rag=True
        )
        
        # Verify conversation history
        messages = await conversation_service.get_messages(
            conversation_id=conversation['id']
        )
        
        assert len(messages) >= 4
        assert messages[0]['id'] == user_msg1['id']
        assert messages[1]['id'] == assistant_msg1['id']
        assert messages[2]['id'] == user_msg2['id']
        assert messages[3]['id'] == assistant_msg2['id']
    
    @pytest.mark.asyncio
    async def test_conversation_timestamp_updates(
        self, conversation_service, test_conversation
    ):
        """Test that conversation timestamp updates on new messages."""
        import asyncio
        
        original_updated_at = test_conversation['updated_at']
        
        # Wait a moment to ensure timestamp difference
        await asyncio.sleep(0.1)
        
        # Add message
        await conversation_service.add_user_message(
            conversation_id=test_conversation['id'],
            content="New message"
        )
        
        # Get updated conversation
        conversation = await conversation_service.get_conversation(
            conversation_id=test_conversation['id'],
            user_id=test_conversation['user_id']
        )
        
        # Verify timestamp updated
        assert conversation['updated_at'] > original_updated_at


# ==================== Citation Tracking Tests ====================

class TestCitationTracking:
    """Test citation tracking in messages."""
    
    @pytest.mark.asyncio
    @patch('src.services.conversation_service.get_rag_service')
    @patch('src.services.conversation_service.get_llm_service')
    async def test_citations_stored_with_message(
        self,
        mock_get_llm,
        mock_get_rag,
        conversation_service,
        test_conversation
    ):
        """Test that citations are properly stored with messages."""
        # Mock RAG with citations
        mock_citation = Mock()
        mock_citation.document_id = str(uuid4())
        mock_citation.document_title = "Test Doc"
        mock_citation.chunk_id = str(uuid4())
        mock_citation.relevance_score = 0.95
        mock_citation.excerpt = "Test excerpt"
        
        mock_rag = Mock()
        mock_rag.retrieve = AsyncMock(return_value=Mock(
            chunks=[],
            context_text="Context",
            total_tokens=50
        ))
        mock_rag.extract_citations = Mock(return_value=[mock_citation])
        mock_get_rag.return_value = mock_rag
        
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(return_value=Mock(
            answer="Answer with citation",
            tokens_used=100
        ))
        mock_get_llm.return_value = mock_llm
        
        # Add assistant message
        message = await conversation_service.add_assistant_message(
            conversation_id=test_conversation['id'],
            content="Question",
            query="Question",
            use_rag=True
        )
        
        # Verify citations stored
        assert message['citations'] is not None
        citations = message['citations']['citations']
        assert len(citations) == 1
        assert citations[0]['document_title'] == "Test Doc"
        assert citations[0]['relevance_score'] == 0.95


# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization."""
        service = ConversationService(
            "postgresql://inmyhead:inmyhead_dev_pass@"
            "localhost:5434/inmyhead_dev"
        )
        
        # Should initialize pool
        await service.initialize()
        assert service.pool is not None
        
        # Cleanup
        await service.close()
        assert service.pool is None
    
    @pytest.mark.asyncio
    async def test_nonexistent_conversation(
        self, conversation_service, test_user_id
    ):
        """Test operations on nonexistent conversation."""
        fake_id = uuid4()
        
        conversation = await conversation_service.get_conversation(
            conversation_id=fake_id,
            user_id=test_user_id
        )
        
        assert conversation is None


# ==================== Singleton Tests ====================

class TestSingleton:
    """Test singleton pattern."""
    
    def test_get_conversation_service_singleton(self):
        """Test that get_conversation_service returns singleton."""
        service1 = get_conversation_service()
        service2 = get_conversation_service()
        
        assert service1 is service2
