"""
AI Formalization router.
Endpoints for AI-powered formalization guide generation.
"""

from fastapi import APIRouter, Depends, status

from app.core.db import get_database
from app.modules.ai_formalization.llm_client import create_llm_client
from app.modules.ai_formalization.rag import RAGService
from app.modules.ai_formalization.schemas import (
    FormalizationGuideResponse,
    GuideGenerationRequest,
)
from app.modules.ai_formalization.service import AIFormalizationService
from app.modules.auth.dependencies import CurrentUser
from app.modules.onboarding.service import OnboardingService
from app.modules.producers.service import ProducerService

router = APIRouter(prefix="/ai/formalization", tags=["ai-formalization"])


async def get_ai_formalization_service() -> AIFormalizationService:
    """Get AIFormalizationService instance with all dependencies."""
    db = get_database()
    rag_service = RAGService(db)
    llm_client = create_llm_client()
    onboarding_service = OnboardingService(db)
    producer_service = ProducerService(db)

    return AIFormalizationService(
        db=db,
        rag_service=rag_service,
        llm_client=llm_client,
        onboarding_service=onboarding_service,
        producer_service=producer_service,
    )


@router.post(
    "/guide",
    response_model=FormalizationGuideResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate formalization guide",
    description="Generate a personalized step-by-step guide to fulfill a formalization requirement using AI and RAG.",
)
async def generate_guide(
    request: GuideGenerationRequest,
    current_user: CurrentUser,
    service: AIFormalizationService = Depends(get_ai_formalization_service),
) -> FormalizationGuideResponse:
    """
    Generate a personalized formalization guide.

    Uses RAG to retrieve relevant information from official documents
    and AI to generate a step-by-step guide adapted to the producer's profile.

    Args:
        request: Guide generation request with requirement_id
        current_user: Current authenticated user
        service: AIFormalizationService instance

    Returns:
        FormalizationGuideResponse with personalized steps

    Raises:
        404: If requirement_id doesn't exist
        500: If guide generation fails
    """
    user_id = str(current_user.id)
    guide = await service.generate_guide(user_id, request.requirement_id)
    return guide
