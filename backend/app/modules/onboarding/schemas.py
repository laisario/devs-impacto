"""
Onboarding module schemas.
Pydantic models for onboarding questions and answers.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.shared.utils import PyObjectId


class OnboardingStatus(str, Enum):
    """Status of onboarding process."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class QuestionType(str, Enum):
    """Type of onboarding question."""

    BOOLEAN = "boolean"  # Yes/No questions
    CHOICE = "choice"  # Multiple choice
    TEXT = "text"  # Free text input


class OnboardingAnswerCreate(BaseModel):
    """Schema for submitting an onboarding answer."""

    question_id: str = Field(..., min_length=1, max_length=50, description="ID da pergunta")
    answer: Any = Field(..., description="Resposta (pode ser bool, str, ou número)")


class OnboardingAnswerResponse(BaseModel):
    """Schema for onboarding answer response."""

    id: PyObjectId = Field(..., alias="_id")
    user_id: PyObjectId
    question_id: str
    answer: Any
    answered_at: datetime

    model_config = {"populate_by_name": True}


class OnboardingAnswerInDB(BaseModel):
    """Onboarding answer as stored in MongoDB."""

    id: PyObjectId | None = Field(None, alias="_id")
    user_id: PyObjectId
    question_id: str
    answer: Any
    answered_at: datetime

    model_config = {"populate_by_name": True}


class OnboardingQuestion(BaseModel):
    """Model for an onboarding question."""

    question_id: str = Field(..., description="ID único da pergunta")
    question_text: str = Field(..., min_length=5, max_length=500, description="Texto da pergunta")
    question_type: QuestionType = Field(..., description="Tipo da pergunta")
    options: list[str] | None = Field(
        None, description="Opções para perguntas do tipo choice"
    )
    order: int = Field(..., ge=0, description="Ordem de exibição da pergunta")
    required: bool = Field(default=True, description="Se a pergunta é obrigatória")
    requirement_id: str | None = Field(
        None,
        description="ID do requisito de formalização associado. Se presente, esta pergunta gera um requirement de formalização.",
    )


class OnboardingStatusResponse(BaseModel):
    """Schema for onboarding status response."""

    status: OnboardingStatus
    progress_percentage: float = Field(
        ..., ge=0, le=100, description="Percentual de conclusão (0-100)"
    )
    total_questions: int = Field(..., ge=0, description="Total de perguntas")
    answered_questions: int = Field(..., ge=0, description="Perguntas respondidas")
    next_question: OnboardingQuestion | None = Field(
        None, description="Próxima pergunta a ser respondida (se houver)"
    )
    completed_at: datetime | None = Field(None, description="Data de conclusão do onboarding")


class ProducerOnboardingSummary(BaseModel):
    """Summary of producer's onboarding and formalization data."""

    user_id: PyObjectId
    onboarding_status: OnboardingStatus | None = None
    onboarding_completed_at: datetime | None = None
    onboarding_progress: float = Field(0.0, ge=0, le=100, description="Progresso do onboarding (%)")
    formalization_eligible: bool | None = None
    formalization_score: int | None = Field(None, ge=0, le=100, description="Pontuação de elegibilidade")
    has_profile: bool = False
    total_answers: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0

    model_config = {"populate_by_name": True}
