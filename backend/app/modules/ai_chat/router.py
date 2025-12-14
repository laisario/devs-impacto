"""
AI Chat router.
Endpoints for AI-powered chat conversations.
"""

from fastapi import APIRouter, Body, Depends, status
from uuid import uuid4

from app.core.db import get_database
from app.modules.ai_chat.schemas import (
    ChatMessageCreate,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatMessageResponseNew,
)
from app.modules.ai_chat.service import AIChatService
from app.modules.auth.dependencies import CurrentUser
from app.modules.producers.service import ProducerService
from app.shared.utils import utc_now

router = APIRouter(prefix="/ai/chat", tags=["ai-chat"])


async def get_chat_service() -> AIChatService:
    """Get AIChatService instance."""
    db = get_database()
    return AIChatService(db)


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message",
    description="Send a message to the AI chat assistant and get a response.",
)
async def send_message(
    request: ChatMessageCreate,
    current_user: CurrentUser,
    service: AIChatService = Depends(get_chat_service),
) -> ChatMessageResponse:
    """
    Send a message to the AI chat assistant.

    Args:
        request: Chat message request
        current_user: Current authenticated user
        service: AIChatService instance

    Returns:
        ChatMessageResponse with assistant's response
    """
    user_id = str(current_user.id)

    # Get user profile for context (optional - can work without it)
    producer_service = ProducerService(get_database())
    profile = None
    try:
        profile = await producer_service.get_profile_by_user(user_id)
    except Exception:
        # Profile doesn't exist yet - that's OK, we'll use onboarding answers
        pass

    # Generate response
    response_content, conversation_id = await service.generate_response(
        user_message=request.message,
        user_id=user_id,
        conversation_id=request.conversation_id,
        user_profile=profile,
    )

    return ChatMessageResponse(
        id=str(uuid4()),
        role="assistant",
        content=response_content,
        created_at=utc_now(),
        conversation_id=conversation_id,
    )


@router.post(
    "/message/v2",
    response_model=ChatMessageResponseNew,
    status_code=status.HTTP_200_OK,
    summary="Send chat message (new contract)",
    description="Send a message to the specialized PNAE chatbot using the new state-driven contract.",
)
async def send_message_v2(
    request: ChatMessageRequest,
    current_user: CurrentUser,
    service: AIChatService = Depends(get_chat_service),
) -> ChatMessageResponseNew:
    """
    Send a message to the specialized PNAE chatbot.

    Supports both text and audio input. Returns structured response with
    suggested actions and conversation state.

    Args:
        request: Chat message request (new contract)
        current_user: Current authenticated user
        service: AIChatService instance

    Returns:
        ChatMessageResponseNew with structured response
    """
    user_id = str(current_user.id)

    # Get user profile for context (optional - can work without it)
    producer_service = ProducerService(get_database())
    profile = None
    try:
        profile = await producer_service.get_profile_by_user(user_id)
    except Exception:
        # Profile doesn't exist yet - that's OK, we'll use onboarding answers
        pass

    # Generate specialized response
    response = await service.generate_specialized_response(
        request=request,
        user_id=user_id,
        user_profile=profile,
    )

    return response


@router.post(
    "/audio/transcribe",
    status_code=status.HTTP_200_OK,
    summary="Transcribe audio to text",
    description="Transcribe audio file to text (ASR).",
)
async def transcribe_audio(
    current_user: CurrentUser,
    audio_url: str = Body(..., description="URL of the audio file"),
    service: AIChatService = Depends(get_chat_service),
) -> dict[str, str]:
    """
    Transcribe audio to text.

    Args:
        current_user: Current authenticated user
        audio_url: URL of the audio file
        service: AIChatService instance

    Returns:
        Dictionary with transcribed text
    """
    text = await service.audio_service.transcribe_audio(audio_url)
    return {"text": text}


@router.post(
    "/audio/speak",
    status_code=status.HTTP_200_OK,
    summary="Synthesize text to speech",
    description="Convert text to speech and return audio URL (TTS).",
)
async def synthesize_speech(
    current_user: CurrentUser,
    text: str = Body(..., description="Text to synthesize"),
    locale: str = Body("pt-BR", description="Locale for voice"),
    service: AIChatService = Depends(get_chat_service),
) -> dict[str, str | None]:
    """
    Synthesize text to speech.

    Args:
        current_user: Current authenticated user
        text: Text to synthesize
        locale: Locale for voice (default: pt-BR)
        service: AIChatService instance

    Returns:
        Dictionary with audio URL
    """
    user_id = str(current_user.id)
    audio_url = await service._generate_audio_url(text, user_id)
    return {"audio_url": audio_url}

