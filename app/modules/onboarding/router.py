"""
Onboarding module router.
Endpoints for guided onboarding process.
"""

from fastapi import APIRouter, Depends, status

from app.core.db import get_database
from app.modules.auth.dependencies import CurrentUser
from app.modules.onboarding.schemas import (
    OnboardingAnswerCreate,
    OnboardingAnswerResponse,
    OnboardingStatusResponse,
    ProducerOnboardingSummary,
)
from app.modules.onboarding.service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


async def get_onboarding_service() -> OnboardingService:
    """Get OnboardingService instance."""
    db = get_database()
    return OnboardingService(db)


@router.post(
    "/answer",
    response_model=OnboardingAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit onboarding answer",
    description="Submit an answer to an onboarding question. Can be called one question at a time.",
)
async def submit_answer(
    data: OnboardingAnswerCreate,
    current_user: CurrentUser,
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingAnswerResponse:
    """
    Submit an answer to an onboarding question.

    Users can answer questions incrementally and can update previous answers.
    The system tracks progress automatically.
    """
    user_id = str(current_user.id)
    answer = await service.save_answer(user_id, data)
    return OnboardingAnswerResponse(**answer.model_dump(by_alias=True))


@router.get(
    "/status",
    response_model=OnboardingStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get onboarding status",
    description="Get current onboarding status, progress, and next question to answer.",
)
async def get_onboarding_status(
    current_user: CurrentUser,
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """
    Get onboarding status for the current user.

    Returns progress information and the next question to be answered (if any).
    """
    user_id = str(current_user.id)
    return await service.get_status(user_id)


@router.get(
    "/summary",
    response_model=ProducerOnboardingSummary,
    status_code=status.HTTP_200_OK,
    summary="Get producer onboarding summary",
    description="Get aggregated summary of producer's onboarding, formalization status, and tasks.",
)
async def get_producer_summary(
    current_user: CurrentUser,
    service: OnboardingService = Depends(get_onboarding_service),
) -> ProducerOnboardingSummary:
    """
    Get aggregated summary of producer data.

    Returns a comprehensive summary including:
    - Onboarding status and progress
    - Formalization eligibility and score
    - Profile existence
    - Task counts
    - Answer counts

    Useful for dashboards and overview screens.
    """
    user_id = str(current_user.id)
    return await service.get_producer_summary(user_id)
