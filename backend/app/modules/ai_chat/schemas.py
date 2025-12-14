"""
AI Chat module schemas.
Pydantic models for chat conversations and messages.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.shared.utils import PyObjectId


# Legacy schemas (mantidos para compatibilidade)
class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message (legacy)."""

    message: str = Field(..., min_length=1, max_length=2000, description="Mensagem do usuário")
    conversation_id: str | None = Field(
        None, description="ID da conversa (opcional, cria nova se não fornecido)"
    )


class ChatMessageResponse(BaseModel):
    """Schema for chat message response (legacy)."""

    id: str = Field(..., description="ID da mensagem")
    role: str = Field(..., description="Role da mensagem (user ou assistant)")
    content: str = Field(..., description="Conteúdo da mensagem")
    created_at: datetime = Field(..., description="Data de criação")
    conversation_id: str = Field(..., description="ID da conversa")

    model_config = {"populate_by_name": True}


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: str = Field(..., description="ID da conversa")
    user_id: PyObjectId = Field(..., description="ID do usuário")
    messages: list[ChatMessageResponse] = Field(..., description="Lista de mensagens")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data de atualização")

    model_config = {"populate_by_name": True}


# New schemas for state-driven chatbot
class ChatState(str, Enum):
    """Chatbot state machine states."""

    IDLE = "idle"
    EXPLAINING_TASK = "explaining_task"
    WAITING_CONFIRMATION = "waiting_confirmation"
    TASK_COMPLETED = "task_completed"
    ERROR = "error"


class ClientCapabilities(BaseModel):
    """Client capabilities for audio support."""

    can_play_audio: bool = Field(default=True, description="Client can play audio")
    prefers_audio: bool = Field(default=False, description="Client prefers audio responses")


class SuggestedAction(BaseModel):
    """Suggested action for the frontend to execute."""

    type: Literal["mark_task_done", "go_to_screen", "open_guide"] = Field(
        ..., description="Type of action"
    )
    task_code: str | None = Field(None, description="Task code (for mark_task_done)")
    screen: str | None = Field(None, description="Screen name (for go_to_screen)")
    requirement_id: str | None = Field(None, description="Requirement ID (for open_guide)")


class ConversationState(BaseModel):
    """Current conversation state."""

    current_goal: str | None = Field(None, description="Current goal (e.g., 'formalization')")
    current_task_code: str | None = Field(None, description="Current task code being discussed")
    chat_state: ChatState = Field(default=ChatState.IDLE, description="Current chat state")


class ChatMessageRequest(BaseModel):
    """New unified chat message request schema."""

    conversation_id: str | None = Field(
        None, description="ID da conversa (opcional, cria nova se não fornecido)"
    )
    input_type: Literal["text", "audio"] = Field(default="text", description="Input type")
    text: str | None = Field(None, description="Text message (required if input_type is text)")
    audio_url: str | None = Field(None, description="Audio URL (required if input_type is audio)")
    locale: str = Field(default="pt-BR", description="Locale")
    client_capabilities: ClientCapabilities = Field(
        default_factory=ClientCapabilities, description="Client capabilities"
    )

    @model_validator(mode="after")
    def validate_input(self) -> "ChatMessageRequest":
        """Validate that either text or audio_url is provided based on input_type."""
        if self.input_type == "text" and not self.text:
            raise ValueError("text is required when input_type is 'text'")
        if self.input_type == "audio" and not self.audio_url:
            raise ValueError("audio_url is required when input_type is 'audio'")
        return self


class ChatMessageResponseNew(BaseModel):
    """New unified chat message response schema."""

    conversation_id: str = Field(..., description="ID da conversa")
    message_id: str = Field(..., description="ID da mensagem")
    message_type: Literal["info", "question", "action", "error"] = Field(
        ..., description="Type of message"
    )
    text: str = Field(..., description="Message text")
    audio_url: str | None = Field(None, description="Audio URL (if available)")
    suggested_actions: list[SuggestedAction] = Field(
        default_factory=list, description="Suggested actions for frontend"
    )
    conversation_state: ConversationState = Field(..., description="Current conversation state")

    model_config = {"populate_by_name": True}

