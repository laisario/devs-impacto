"""
AI Formalization module schemas.
Pydantic models for guide generation requests and responses.
"""

from pydantic import BaseModel, Field, field_validator


class GuideGenerationRequest(BaseModel):
    """Request schema for generating a formalization guide."""

    requirement_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID do requisito de formalização (deve corresponder a um requirement_id de uma OnboardingQuestion)",
    )


class GuideStep(BaseModel):
    """Individual step in a formalization guide."""

    step: int = Field(..., ge=1, description="Número do passo (1-N)")
    title: str = Field(..., min_length=3, max_length=200, description="Título do passo")
    description: str = Field(
        ..., min_length=10, max_length=1000, description="Descrição detalhada do passo"
    )


class ConfidenceLevel(str):
    """Confidence level for the generated guide."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FormalizationGuideResponse(BaseModel):
    """Response schema for formalization guide."""

    summary: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="Resumo do que precisa ser feito",
    )
    steps: list[GuideStep] = Field(
        ..., min_length=1, max_length=8, description="Lista de passos (máximo 8)"
    )
    estimated_time_days: int = Field(
        ..., ge=1, le=365, description="Tempo estimado em dias"
    )
    where_to_go: list[str] = Field(
        ...,
        min_length=0,
        description="Lista de locais/órgãos onde o produtor deve ir",
    )
    confidence_level: str = Field(
        ...,
        description="Nível de confiança do guia (high/medium/low)",
    )

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: str) -> str:
        """Validate confidence level."""
        if v not in ["high", "medium", "low"]:
            raise ValueError("confidence_level must be 'high', 'medium', or 'low'")
        return v

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: list[GuideStep]) -> list[GuideStep]:
        """Validate that steps are numbered sequentially starting from 1."""
        if not v:
            raise ValueError("Steps list cannot be empty")
        if len(v) > 8:
            raise ValueError("Maximum 8 steps allowed")
        for i, step in enumerate(v, start=1):
            if step.step != i:
                raise ValueError(f"Steps must be numbered sequentially. Expected {i}, got {step.step}")
        return v
