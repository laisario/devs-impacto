"""
Onboarding module router.
Endpoints for guided onboarding process.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.core.db import get_database
from app.modules.auth.dependencies import CurrentUser
from app.modules.onboarding.schemas import (
    OnboardingAnswerCreate,
    OnboardingAnswerResponse,
    OnboardingPreferenceResponse,
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


@router.post(
    "/seed-questions",
    status_code=status.HTTP_200_OK,
    summary="Seed onboarding questions (development only)",
    description="Seed default onboarding questions into the database. Development only.",
)
async def seed_questions(
    service: OnboardingService = Depends(get_onboarding_service),
) -> dict[str, str]:
    """
    Seed default onboarding questions.
    This is a development endpoint and should be removed or protected in production.
    """
    await service.seed_default_questions()
    return {"message": "Questions seeded successfully"}


@router.get(
    "/preference",
    response_model=OnboardingPreferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get onboarding preference",
    description="Get user's preference for audio or text communication from onboarding.",
)
async def get_onboarding_preference(
    current_user: CurrentUser,
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingPreferenceResponse:
    """
    Get user's preference for audio or text communication from onboarding.
    
    Returns the answer to the preferences_1 question (prefers_audio flag).
    If the question hasn't been answered yet, returns prefers_audio=False.
    """
    user_id = str(current_user.id)
    
    # Get answer for preferences_1 question
    answer_value = await service.get_answer_value(user_id, "preferences_1")
    
    # Convert answer to boolean
    # Answer can be "sim", "não", True, False, etc.
    prefers_audio = False
    if answer_value is not None:
        if isinstance(answer_value, str):
            prefers_audio = answer_value.lower() in ["sim", "yes", "true", "1"]
        else:
            prefers_audio = bool(answer_value)
    
    return OnboardingPreferenceResponse(
        prefers_audio=prefers_audio,
        question_id="preferences_1" if answer_value is not None else None,
    )


@router.post(
    "/update-profile-field",
    status_code=status.HTTP_200_OK,
    summary="Update profile field directly",
    description="Update a specific field in the producer profile (e.g., DAP/CAF number).",
)
async def update_profile_field(
    current_user: CurrentUser,
    field: str = Query(..., description="Field name to update"),
    value: str = Query(..., description="Field value"),
    service: OnboardingService = Depends(get_onboarding_service),
) -> dict[str, str]:
    """
    Update a specific field in the producer profile.
    Used for conditional inputs like DAP/CAF number after answering has_dap_caf.
    """
    from app.shared.utils import to_object_id, utc_now
    
    user_id = str(current_user.id)
    user_oid = to_object_id(user_id)
    now = utc_now()
    
    update_doc: dict[str, Any] = {"updated_at": now}
    
    if field == "dap_caf_number":
        update_doc["dap_caf_number"] = str(value).strip()
    else:
        from app.core.errors import ValidationError
        raise ValidationError(f"Invalid field: {field}")
    
    await service.profiles_collection.update_one(
        {"user_id": user_oid},
        {
            "$set": update_doc,
            "$setOnInsert": {
                "user_id": user_oid,
                "created_at": now,
            },
        },
        upsert=True,
    )
    
    return {"message": "Profile field updated"}
