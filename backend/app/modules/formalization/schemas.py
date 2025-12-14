"""
Formalization module schemas.
Pydantic models for formalization status and tasks.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.shared.utils import PyObjectId


class EligibilityLevel(str, Enum):
    """Eligibility level for public programs."""

    ELIGIBLE = "eligible"
    PARTIALLY_ELIGIBLE = "partially_eligible"
    NOT_ELIGIBLE = "not_eligible"


class TaskPriority(str, Enum):
    """Priority level for formalization tasks."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskCategory(str, Enum):
    """Category of formalization task."""

    DOCUMENT = "document"
    REGISTRATION = "registration"
    PREPARATION = "preparation"


class FormalizationStatusResponse(BaseModel):
    """Schema for formalization status response."""

    is_eligible: bool = Field(..., description="Se está apto para vender em programas públicos")
    eligibility_level: EligibilityLevel = Field(..., description="Nível de elegibilidade")
    score: int = Field(..., ge=0, le=100, description="Pontuação de 0 a 100")
    requirements_met: list[str] = Field(
        ..., description="Lista de requisitos atendidos"
    )
    requirements_missing: list[str] = Field(
        ..., description="Lista de requisitos faltantes"
    )
    recommendations: list[str] = Field(
        ..., description="Recomendações para melhorar elegibilidade"
    )
    diagnosed_at: datetime = Field(..., description="Data do diagnóstico")


class FormalizationTaskResponse(BaseModel):
    """Schema for formalization task response."""

    id: PyObjectId = Field(..., alias="_id")
    user_id: PyObjectId
    task_id: str = Field(..., description="ID único da tarefa")
    title: str = Field(..., description="Título da tarefa")
    description: str = Field(..., description="Descrição detalhada")
    category: TaskCategory
    priority: TaskPriority
    completed: bool = Field(default=False, description="Se a tarefa foi concluída")
    completed_at: datetime | None = Field(None, description="Data de conclusão")
    created_at: datetime
    requirement_id: str | None = Field(
        None, description="ID do requirement de onboarding associado a esta tarefa"
    )
    need_upload: bool = Field(
        default=False, description="Se esta tarefa requer upload de documento (PDF ou imagem)"
    )

    model_config = {"populate_by_name": True}


class FormalizationTaskInDB(BaseModel):
    """Formalization task as stored in MongoDB."""

    id: PyObjectId | None = Field(None, alias="_id")
    user_id: PyObjectId
    task_id: str
    title: str
    description: str
    category: TaskCategory
    priority: TaskPriority
    completed: bool = False
    completed_at: datetime | None = None
    created_at: datetime
    requirement_id: str | None = Field(
        None, description="ID do requirement de onboarding associado a esta tarefa"
    )
    need_upload: bool = Field(
        default=False, description="Se esta tarefa requer upload de documento (PDF ou imagem)"
    )

    model_config = {"populate_by_name": True}


class FormalizationStatusInDB(BaseModel):
    """Formalization status as stored in MongoDB (cache)."""

    id: PyObjectId | None = Field(None, alias="_id")
    user_id: PyObjectId
    is_eligible: bool
    eligibility_level: EligibilityLevel
    score: int
    requirements_met: list[str]
    requirements_missing: list[str]
    recommendations: list[str]
    diagnosed_at: datetime

    model_config = {"populate_by_name": True}
