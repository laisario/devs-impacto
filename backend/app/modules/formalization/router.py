"""
Formalization module router.
Endpoints for formalization status and tasks.
"""

from fastapi import APIRouter, Depends, status

from app.core.db import get_database
from app.modules.auth.dependencies import CurrentUser
from app.modules.formalization.schemas import (
    FormalizationStatusResponse,
    FormalizationTaskResponse,
)
from app.modules.formalization.service import FormalizationService

router = APIRouter(prefix="/formalization", tags=["formalization"])


async def get_formalization_service() -> FormalizationService:
    """Get FormalizationService instance."""
    db = get_database()
    return FormalizationService(db)


@router.get(
    "/status",
    response_model=FormalizationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get formalization status",
    description="Get eligibility diagnosis for selling to public programs (PNAE, etc.).",
)
async def get_formalization_status(
    current_user: CurrentUser,
    service: FormalizationService = Depends(get_formalization_service),
) -> FormalizationStatusResponse:
    """
    Get formalization status and eligibility diagnosis.

    The diagnosis is calculated based on onboarding answers.
    Returns eligibility level, score, requirements met/missing, and recommendations.
    """
    user_id = str(current_user.id)
    return await service.get_or_calculate_status(user_id)


@router.get(
    "/tasks",
    response_model=list[FormalizationTaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get formalization tasks",
    description="Get list of formalization tasks based on current eligibility diagnosis.",
)
async def get_formalization_tasks(
    current_user: CurrentUser,
    service: FormalizationService = Depends(get_formalization_service),
) -> list[FormalizationTaskResponse]:
    """
    Get formalization tasks for the current user.

    Tasks are automatically generated based on the eligibility diagnosis.
    Tasks are prioritized and categorized.
    """
    user_id = str(current_user.id)
    tasks = await service.get_tasks(user_id)
    return [FormalizationTaskResponse(**task.model_dump(by_alias=True)) for task in tasks]
