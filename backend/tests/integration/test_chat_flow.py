"""
Integration tests for AI Chat flow.
"""

import pytest
from httpx import AsyncClient

from app.core.db import get_database
from app.modules.formalization.service import FormalizationService
from app.modules.onboarding.service import OnboardingService
from app.modules.producers.service import ProducerService
from app.shared.utils import to_object_id, utc_now


@pytest.fixture
async def test_user_with_profile(mongo_client):
    """Create a test user with profile and tasks."""
    from app.modules.auth.service import AuthService

    db = get_database()
    auth_service = AuthService(db)

    # Create user
    user = await auth_service.create_user(
        cpf="12345678901",
        password="test123",
        email="test@example.com",
    )
    user_id = str(user.id)

    # Create onboarding answers
    onboarding_service = OnboardingService(db)
    await onboarding_service.save_answer(
        user_id,
        {
            "question_id": "producer_type",
            "answer": "Individual",
        },
    )
    await onboarding_service.save_answer(
        user_id,
        {
            "question_id": "name",
            "answer": "João Silva",
        },
    )
    await onboarding_service.save_answer(
        user_id,
        {
            "question_id": "city",
            "answer": "Brasília",
        },
    )
    await onboarding_service.save_answer(
        user_id,
        {
            "question_id": "state",
            "answer": "DF",
        },
    )

    # Create producer profile
    producer_service = ProducerService(db)
    await producer_service.upsert_profile(
        user_id,
        {
            "producer_type": "individual",
            "name": "João Silva",
            "address": "Rua Teste, 123",
            "city": "Brasília",
            "state": "DF",
        },
    )

    # Generate formalization tasks
    formalization_service = FormalizationService(db)
    await formalization_service.regenerate_tasks(user_id)

    return user_id, user


@pytest.mark.asyncio
async def test_chat_message_text_flow(client: AsyncClient, test_user_with_profile, auth_token):
    """Test complete chat flow with text message."""
    user_id, user = test_user_with_profile

    # Send text message
    response = await client.post(
        "/ai/chat/message/v2",
        json={
            "input_type": "text",
            "text": "o que falta para mim?",
            "locale": "pt-BR",
            "client_capabilities": {
                "can_play_audio": True,
                "prefers_audio": False,
            },
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "message_id" in data
    assert "text" in data
    assert "message_type" in data
    assert "conversation_state" in data
    assert data["message_type"] in ["info", "question", "action", "error"]

    # Check conversation state
    assert "chat_state" in data["conversation_state"]
    assert "current_goal" in data["conversation_state"]
    assert "current_task_code" in data["conversation_state"]


@pytest.mark.asyncio
async def test_chat_message_identifies_task(client: AsyncClient, test_user_with_profile, auth_token):
    """Test that chat identifies pending tasks."""
    user_id, user = test_user_with_profile

    # Get tasks first
    from httpx import AsyncClient as TestClient

    tasks_response = await client.get(
        "/formalization/tasks",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    tasks = tasks_response.json()
    pending_tasks = [t for t in tasks if t["status"] == "pending"]

    if pending_tasks:
        # Ask what's missing
        response = await client.post(
            "/ai/chat/message/v2",
            json={
                "input_type": "text",
                "text": "o que falta para mim?",
                "locale": "pt-BR",
                "client_capabilities": {
                    "can_play_audio": True,
                    "prefers_audio": False,
                },
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should be explaining a task
        assert data["conversation_state"]["chat_state"] in [
            "idle",
            "explaining_task",
        ]
        # Should have suggested actions if task is identified
        if data["conversation_state"]["current_task_code"]:
            assert len(data["suggested_actions"]) > 0


@pytest.mark.asyncio
async def test_chat_suggested_action_mark_task_done(
    client: AsyncClient, test_user_with_profile, auth_token
):
    """Test that suggested action can mark task as done."""
    user_id, user = test_user_with_profile

    # Get a pending task
    tasks_response = await client.get(
        "/formalization/tasks",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    tasks = tasks_response.json()
    pending_task = next((t for t in tasks if t["status"] == "pending"), None)

    if pending_task:
        # Ask about the task
        response = await client.post(
            "/ai/chat/message/v2",
            json={
                "input_type": "text",
                "text": f"o que preciso fazer para {pending_task['title'].lower()}?",
                "locale": "pt-BR",
                "client_capabilities": {
                    "can_play_audio": True,
                    "prefers_audio": False,
                },
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check if there's a suggested action to mark task as done
        mark_done_actions = [
            a for a in data["suggested_actions"] if a["type"] == "mark_task_done"
        ]

        if mark_done_actions:
            # Execute the action
            task_code = mark_done_actions[0]["task_code"]
            update_response = await client.patch(
                f"/formalization/tasks/{task_code}",
                json={"status": "done"},
                headers={"Authorization": f"Bearer {auth_token}"},
            )

            assert update_response.status_code == 200
            updated_task = update_response.json()
            assert updated_task["status"] == "done"


@pytest.mark.asyncio
async def test_chat_audio_endpoints(client: AsyncClient, test_user_with_profile, auth_token):
    """Test audio transcription and synthesis endpoints."""
    user_id, user = test_user_with_profile

    # Test transcription endpoint (with mock audio URL)
    transcribe_response = await client.post(
        "/ai/chat/audio/transcribe",
        json={"audio_url": "http://example.com/audio.webm"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    # Should return text (even if mock)
    assert transcribe_response.status_code == 200
    data = transcribe_response.json()
    assert "text" in data
    assert isinstance(data["text"], str)

    # Test synthesis endpoint
    synthesize_response = await client.post(
        "/ai/chat/audio/speak",
        json={"text": "Teste de síntese de voz", "locale": "pt-BR"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    # Should return audio URL (or null if mock)
    assert synthesize_response.status_code == 200
    data = synthesize_response.json()
    assert "audio_url" in data


@pytest.mark.asyncio
async def test_chat_conversation_persistence(
    client: AsyncClient, test_user_with_profile, auth_token
):
    """Test that conversation state persists across messages."""
    user_id, user = test_user_with_profile

    # Send first message
    response1 = await client.post(
        "/ai/chat/message/v2",
        json={
            "input_type": "text",
            "text": "o que falta?",
            "locale": "pt-BR",
            "client_capabilities": {
                "can_play_audio": True,
                "prefers_audio": False,
            },
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response1.status_code == 200
    data1 = response1.json()
    conversation_id = data1["conversation_id"]

    # Send second message with same conversation_id
    response2 = await client.post(
        "/ai/chat/message/v2",
        json={
            "conversation_id": conversation_id,
            "input_type": "text",
            "text": "como faço isso?",
            "locale": "pt-BR",
            "client_capabilities": {
                "can_play_audio": True,
                "prefers_audio": False,
            },
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response2.status_code == 200
    data2 = response2.json()

    # Should use same conversation
    assert data2["conversation_id"] == conversation_id

    # State should be maintained or updated
    assert "conversation_state" in data2


@pytest.mark.asyncio
async def test_chat_legacy_endpoint_compatibility(
    client: AsyncClient, test_user_with_profile, auth_token
):
    """Test that legacy endpoint still works."""
    user_id, user = test_user_with_profile

    # Use legacy endpoint
    response = await client.post(
        "/ai/chat/message",
        json={
            "message": "teste",
            "conversation_id": None,
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "role" in data
    assert "content" in data
    assert "conversation_id" in data
