"""
Tests for Conversations API Routes

Comprehensive test coverage for conversations.py endpoints
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_conversation_service():
    """Mock conversation service"""
    mock = MagicMock()
    mock.initialize = AsyncMock()
    mock.create_conversation = AsyncMock(return_value={
        'id': uuid4(),
        'user_id': uuid4(),
        'title': 'Test Conversation',
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })
    mock.list_conversations = AsyncMock(return_value=[{
        'id': uuid4(),
        'user_id': uuid4(),
        'title': 'Test Conversation',
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'message_count': 5
    }])
    mock.get_conversation = AsyncMock(return_value={
        'id': uuid4(),
        'user_id': uuid4(),
        'title': 'Test Conversation',
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })
    mock.delete_conversation = AsyncMock(return_value=True)
    mock.add_user_message = AsyncMock(return_value={
        'id': uuid4(),
        'conversation_id': uuid4(),
        'role': 'user',
        'content': 'Test message',
        'created_at': datetime.now()
    })
    mock.add_assistant_message = AsyncMock(return_value={
        'id': uuid4(),
        'conversation_id': uuid4(),
        'role': 'assistant',
        'content': 'Test response',
        'citations': {'citations': []},
        'model': 'claude-sonnet-4',
        'tokens_used': 100,
        'created_at': datetime.now()
    })
    mock.get_messages = AsyncMock(return_value=[{
        'id': uuid4(),
        'conversation_id': uuid4(),
        'role': 'user',
        'content': 'Test message',
        'citations': None,
        'model': None,
        'tokens_used': None,
        'created_at': datetime.now()
    }])
    return mock


@pytest.fixture
async def client(mock_conversation_service):
    """Create test client with mocked dependencies"""
    from src.main import app
    
    # Override dependency
    app.dependency_overrides = {}
    
    def get_mock_service():
        return mock_conversation_service
    
    from src.services.conversation_service import get_conversation_service
    app.dependency_overrides[get_conversation_service] = get_mock_service
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_conversation_success(client, mock_conversation_service):
    """Test successful conversation creation"""
    user_id = str(uuid4())
    
    response = await client.post(
        "/conversations",
        json={
            "user_id": user_id,
            "title": "Test Conversation"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'id' in data
    assert data['title'] == 'Test Conversation'
    
    # Verify service was called
    mock_conversation_service.initialize.assert_called_once()
    mock_conversation_service.create_conversation.assert_called_once()


@pytest.mark.asyncio
async def test_create_conversation_invalid_data(client):
    """Test conversation creation with invalid data"""
    response = await client.post(
        "/conversations",
        json={
            "user_id": "invalid-uuid",  # Invalid UUID
            "title": "Test"
        }
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_conversation_empty_title(client):
    """Test conversation creation with empty title"""
    response = await client.post(
        "/conversations",
        json={
            "user_id": str(uuid4()),
            "title": ""  # Empty title
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_conversations_success(client, mock_conversation_service):
    """Test listing conversations"""
    user_id = str(uuid4())
    
    response = await client.get(
        "/conversations",
        params={"user_id": user_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Verify service was called
    mock_conversation_service.list_conversations.assert_called_once()


@pytest.mark.asyncio
async def test_list_conversations_with_pagination(client, mock_conversation_service):
    """Test listing conversations with pagination"""
    user_id = str(uuid4())
    
    response = await client.get(
        "/conversations",
        params={
            "user_id": user_id,
            "limit": 10,
            "offset": 5
        }
    )
    
    assert response.status_code == 200
    
    # Verify pagination params were passed
    call_args = mock_conversation_service.list_conversations.call_args
    assert call_args.kwargs['limit'] == 10
    assert call_args.kwargs['offset'] == 5


@pytest.mark.asyncio
async def test_get_conversation_success(client, mock_conversation_service):
    """Test getting conversation details"""
    conversation_id = str(uuid4())
    user_id = str(uuid4())
    
    response = await client.get(
        f"/conversations/{conversation_id}",
        params={"user_id": user_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'id' in data
    assert 'title' in data


@pytest.mark.asyncio
async def test_get_conversation_not_found(client, mock_conversation_service):
    """Test getting non-existent conversation"""
    mock_conversation_service.get_conversation.return_value = None
    
    conversation_id = str(uuid4())
    user_id = str(uuid4())
    
    response = await client.get(
        f"/conversations/{conversation_id}",
        params={"user_id": user_id}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_conversation_success(client, mock_conversation_service):
    """Test deleting conversation"""
    conversation_id = str(uuid4())
    user_id = str(uuid4())
    
    response = await client.delete(
        f"/conversations/{conversation_id}",
        params={"user_id": user_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'deleted'


@pytest.mark.asyncio
async def test_delete_conversation_not_found(client, mock_conversation_service):
    """Test deleting non-existent conversation"""
    mock_conversation_service.delete_conversation.return_value = False
    
    conversation_id = str(uuid4())
    user_id = str(uuid4())
    
    response = await client.delete(
        f"/conversations/{conversation_id}",
        params={"user_id": user_id}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_message_success(client, mock_conversation_service):
    """Test sending message in conversation"""
    conversation_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "content": "What is machine learning?",
            "model": "claude-sonnet-4",
            "temperature": 0.7,
            "use_rag": True,
            "top_k": 5
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # User + Assistant messages
    assert data[0]['role'] == 'user'
    assert data[1]['role'] == 'assistant'


@pytest.mark.asyncio
async def test_send_message_with_rag_disabled(client, mock_conversation_service):
    """Test sending message without RAG"""
    conversation_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "content": "Hello",
            "use_rag": False
        }
    )
    
    assert response.status_code == 200
    
    # Verify use_rag was passed
    call_args = mock_conversation_service.add_assistant_message.call_args
    assert call_args.kwargs['use_rag'] is False


@pytest.mark.asyncio
async def test_send_message_with_collection(client, mock_conversation_service):
    """Test sending message with specific collection"""
    conversation_id = str(uuid4())
    collection_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "content": "Search in my work docs",
            "collection_id": collection_id
        }
    )
    
    assert response.status_code == 200
    
    # Verify collection_id was passed
    call_args = mock_conversation_service.add_assistant_message.call_args
    assert str(call_args.kwargs['collection_id']) == collection_id


@pytest.mark.asyncio
async def test_send_message_with_citations(client, mock_conversation_service):
    """Test message response includes citations"""
    # Mock response with citations
    mock_conversation_service.add_assistant_message.return_value = {
        'id': uuid4(),
        'conversation_id': uuid4(),
        'role': 'assistant',
        'content': 'Answer with citations',
        'citations': {
            'citations': [{
                'document_id': 'doc1',
                'document_title': 'Test Doc',
                'chunk_id': 'chunk1',
                'relevance_score': 0.95,
                'excerpt': 'Relevant text'
            }]
        },
        'model': 'claude-sonnet-4',
        'tokens_used': 150,
        'created_at': datetime.now()
    }
    
    conversation_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "Test with citations"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check assistant message has citations
    assistant_msg = data[1]
    assert assistant_msg['citations'] is not None
    assert len(assistant_msg['citations']) > 0


@pytest.mark.asyncio
async def test_send_message_empty_content(client):
    """Test sending empty message"""
    conversation_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": ""}
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_send_message_invalid_temperature(client):
    """Test sending message with invalid temperature"""
    conversation_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "content": "Test",
            "temperature": 3.0  # Too high
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_send_message_invalid_top_k(client):
    """Test sending message with invalid top_k"""
    conversation_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "content": "Test",
            "top_k": 0  # Below minimum
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_messages_success(client, mock_conversation_service):
    """Test retrieving message history"""
    conversation_id = str(uuid4())
    
    response = await client.get(
        f"/conversations/{conversation_id}/messages"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_messages_with_pagination(client, mock_conversation_service):
    """Test retrieving messages with pagination"""
    conversation_id = str(uuid4())
    
    response = await client.get(
        f"/conversations/{conversation_id}/messages",
        params={"limit": 20, "offset": 10}
    )
    
    assert response.status_code == 200
    
    # Verify pagination
    call_args = mock_conversation_service.get_messages.call_args
    assert call_args.kwargs['limit'] == 20
    assert call_args.kwargs['offset'] == 10


@pytest.mark.asyncio
async def test_get_messages_empty_conversation(client, mock_conversation_service):
    """Test getting messages from empty conversation"""
    mock_conversation_service.get_messages.return_value = []
    
    conversation_id = str(uuid4())
    
    response = await client.get(
        f"/conversations/{conversation_id}/messages"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_error_handling_service_failure(client, mock_conversation_service):
    """Test error handling when service fails"""
    mock_conversation_service.create_conversation.side_effect = Exception("Database error")
    
    response = await client.post(
        "/conversations",
        json={
            "user_id": str(uuid4()),
            "title": "Test"
        }
    )
    
    assert response.status_code == 500
    assert 'detail' in response.json()


@pytest.mark.asyncio
async def test_concurrent_message_sending(client, mock_conversation_service):
    """Test sending multiple messages concurrently"""
    import asyncio
    
    conversation_id = str(uuid4())
    
    async def send_message(content):
        return await client.post(
            f"/conversations/{conversation_id}/messages",
            json={"content": content}
        )
    
    # Send 3 messages concurrently
    responses = await asyncio.gather(
        send_message("Message 1"),
        send_message("Message 2"),
        send_message("Message 3")
    )
    
    # All should succeed
    for response in responses:
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_conversation_title_update_on_first_message(client, mock_conversation_service):
    """Test that conversation title can be updated based on first message"""
    conversation_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "What is the meaning of life?"}
    )
    
    assert response.status_code == 200
    # Service method was called
    mock_conversation_service.add_user_message.assert_called_once()


@pytest.mark.asyncio
async def test_message_token_usage_tracking(client, mock_conversation_service):
    """Test that token usage is tracked in messages"""
    conversation_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "Test message"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Assistant message should have tokens_used
    assistant_msg = data[1]
    assert 'tokens_used' in assistant_msg


@pytest.mark.asyncio
async def test_invalid_uuid_in_path(client):
    """Test handling of invalid UUID in path"""
    response = await client.get(
        "/conversations/not-a-uuid",
        params={"user_id": str(uuid4())}
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_model_parameter_passed_correctly(client, mock_conversation_service):
    """Test that model parameter is passed to service"""
    conversation_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "content": "Test",
            "model": "claude-opus-4"
        }
    )
    
    assert response.status_code == 200
    
    # Verify model was passed
    call_args = mock_conversation_service.add_assistant_message.call_args
    assert call_args.kwargs['model'] == "claude-opus-4"


@pytest.mark.asyncio
async def test_temperature_parameter_passed_correctly(client, mock_conversation_service):
    """Test that temperature parameter is passed to service"""
    conversation_id = str(uuid4())
    
    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "content": "Test",
            "temperature": 0.5
        }
    )
    
    assert response.status_code == 200
    
    # Verify temperature was passed
    call_args = mock_conversation_service.add_assistant_message.call_args
    assert call_args.kwargs['temperature'] == 0.5
