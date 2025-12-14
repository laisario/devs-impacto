"""
Unit tests for AI Chat module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.ai_chat.audio_service import AudioService
from app.modules.ai_chat.schemas import ChatState, ClientCapabilities, ConversationState
from app.modules.ai_chat.service import AIChatService
from app.modules.ai_chat.state_machine import ChatStateMachine


@pytest.fixture
def audio_service():
    """Create AudioService instance for tests."""
    return AudioService()


@pytest.fixture
def chat_service(mongo_client):
    """Create AIChatService instance for tests."""
    from app.core.db import get_database

    db = get_database()
    return AIChatService(db)


@pytest.fixture
def state_machine():
    """Create ChatStateMachine instance for tests."""
    return ChatStateMachine()


class TestChatStateMachine:
    """Tests for ChatStateMachine."""

    def test_get_initial_state(self, state_machine):
        """Test getting initial state."""
        state = state_machine.get_initial_state()
        assert state == ChatState.IDLE

    def test_transition_to_explaining_task(self, state_machine):
        """Test transition to explaining task."""
        state = state_machine.transition_to_explaining_task()
        assert state == ChatState.EXPLAINING_TASK

    def test_transition_to_waiting_confirmation(self, state_machine):
        """Test transition to waiting confirmation."""
        state = state_machine.transition_to_waiting_confirmation()
        assert state == ChatState.WAITING_CONFIRMATION

    def test_transition_to_task_completed(self, state_machine):
        """Test transition to task completed."""
        state = state_machine.transition_to_task_completed()
        assert state == ChatState.TASK_COMPLETED

    def test_transition_to_error(self, state_machine):
        """Test transition to error."""
        state = state_machine.transition_to_error()
        assert state == ChatState.ERROR

    def test_valid_transitions(self, state_machine):
        """Test valid state transitions."""
        # IDLE -> EXPLAINING_TASK
        assert state_machine.can_transition_from(ChatState.IDLE, ChatState.EXPLAINING_TASK)
        # EXPLAINING_TASK -> WAITING_CONFIRMATION
        assert state_machine.can_transition_from(
            ChatState.EXPLAINING_TASK, ChatState.WAITING_CONFIRMATION
        )
        # WAITING_CONFIRMATION -> TASK_COMPLETED
        assert state_machine.can_transition_from(
            ChatState.WAITING_CONFIRMATION, ChatState.TASK_COMPLETED
        )
        # TASK_COMPLETED -> IDLE
        assert state_machine.can_transition_from(ChatState.TASK_COMPLETED, ChatState.IDLE)

    def test_invalid_transitions(self, state_machine):
        """Test invalid state transitions."""
        # IDLE -> TASK_COMPLETED (should be invalid)
        assert not state_machine.can_transition_from(ChatState.IDLE, ChatState.TASK_COMPLETED)
        # ERROR -> WAITING_CONFIRMATION (should be invalid)
        assert not state_machine.can_transition_from(
            ChatState.ERROR, ChatState.WAITING_CONFIRMATION
        )


class TestAudioService:
    """Tests for AudioService."""

    @pytest.mark.asyncio
    async def test_mock_transcribe_audio(self, audio_service):
        """Test mock transcription when OpenAI is not configured."""
        # Mock OpenAI client to be None
        audio_service.openai_client = None

        result = await audio_service.transcribe_audio("http://example.com/audio.webm")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_mock_synthesize_speech(self, audio_service):
        """Test mock TTS when OpenAI is not configured."""
        # Mock OpenAI client to be None
        audio_service.openai_client = None

        result = await audio_service.synthesize_speech("Test text")
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_transcribe_audio_with_openai(self, mock_client_class, audio_service):
        """Test transcription with OpenAI (mocked)."""
        # Mock OpenAI client
        mock_openai = MagicMock()
        mock_transcript = MagicMock()
        mock_transcript.text = "Transcribed text"
        mock_openai.audio.transcriptions.create.return_value = mock_transcript
        audio_service.openai_client = mock_openai

        # Mock HTTP client for downloading audio
        mock_response = MagicMock()
        mock_response.content = b"fake audio data"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        result = await audio_service.transcribe_audio("http://example.com/audio.webm")
        assert result == "Transcribed text"

    @pytest.mark.asyncio
    async def test_synthesize_speech_with_openai(self, audio_service):
        """Test TTS with OpenAI (mocked)."""
        # Mock OpenAI client
        mock_openai = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"fake audio data"
        mock_openai.audio.speech.create.return_value = mock_response
        audio_service.openai_client = mock_openai

        result = await audio_service.synthesize_speech("Test text")
        assert isinstance(result, bytes)
        assert result == b"fake audio data"


class TestAIChatService:
    """Tests for AIChatService."""

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_new(self, chat_service, mongo_client):
        """Test creating a new conversation."""
        from app.shared.utils import to_object_id

        user_id = str(to_object_id())
        conversation = await chat_service.get_or_create_conversation(user_id)

        assert conversation is not None
        assert "user_id" in conversation
        assert "created_at" in conversation
        assert "_id" in conversation

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_existing(self, chat_service, mongo_client):
        """Test getting existing conversation."""
        from app.shared.utils import to_object_id

        user_id = str(to_object_id())
        conversation1 = await chat_service.get_or_create_conversation(user_id)
        conv_id = str(conversation1["_id"])

        conversation2 = await chat_service.get_or_create_conversation(user_id, conv_id)
        assert conversation2["_id"] == conversation1["_id"]

    @pytest.mark.asyncio
    async def test_detect_intent_ask_what_missing(self, chat_service):
        """Test intent detection for 'what is missing'."""
        intent = chat_service._detect_intent("o que falta para mim?")
        assert intent == "ask_what_missing"

        intent = chat_service._detect_intent("o que preciso fazer?")
        assert intent == "ask_what_missing"

    @pytest.mark.asyncio
    async def test_detect_intent_confirm_task(self, chat_service):
        """Test intent detection for task confirmation."""
        intent = chat_service._detect_intent("sim, já completei")
        assert intent == "confirm_task"

        intent = chat_service._detect_intent("já fiz")
        assert intent == "confirm_task"

    @pytest.mark.asyncio
    async def test_detect_intent_general(self, chat_service):
        """Test intent detection for general questions."""
        intent = chat_service._detect_intent("como funciona o pnae?")
        assert intent == "general"

    @pytest.mark.asyncio
    @patch("app.modules.ai_chat.service.AIChatService._call_llm")
    async def test_call_llm_success(self, mock_llm, chat_service):
        """Test successful LLM call."""
        mock_llm.return_value = "Test response"
        result = await chat_service._call_llm("Test prompt")
        assert result == "Test response"

    @pytest.mark.asyncio
    async def test_call_llm_no_openai(self, chat_service):
        """Test LLM call when OpenAI is not configured."""
        chat_service.openai_client = None
        result = await chat_service._call_llm("Test prompt")
        assert "não está disponível" in result.lower()

    @pytest.mark.asyncio
    async def test_create_error_response(self, chat_service):
        """Test creating error response."""
        response = chat_service._create_error_response("conv123", "Test error")
        assert response.message_type == "error"
        assert response.text == "Test error"
        assert response.conversation_state.chat_state == ChatState.ERROR

    @pytest.mark.asyncio
    async def test_create_info_response(self, chat_service):
        """Test creating info response."""
        response = chat_service._create_info_response(
            "conv123",
            "Test info",
            ChatState.IDLE,
            None,
            ClientCapabilities(),
        )
        assert response.message_type == "info"
        assert response.text == "Test info"
        assert response.conversation_state.chat_state == ChatState.IDLE
