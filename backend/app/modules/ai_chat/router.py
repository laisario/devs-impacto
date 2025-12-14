"""
AI Chat router.
Endpoints for AI-powered chat conversations.
"""

from fastapi import APIRouter, Depends, status

from app.core.db import get_database
from uuid import uuid4

from app.modules.ai_chat.schemas import ChatMessageCreate, ChatMessageResponse
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
