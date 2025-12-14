"""
AI Chat module schemas.
Pydantic models for chat conversations and messages.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.shared.utils import PyObjectId


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""

    message: str = Field(..., min_length=1, max_length=2000, description="Mensagem do usuário")
    conversation_id: str | None = Field(
        None, description="ID da conversa (opcional, cria nova se não fornecido)"
    )


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""

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

