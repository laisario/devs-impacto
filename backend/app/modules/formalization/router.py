"""
Formalization module router.
Endpoints for formalization status and tasks.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.db import get_database
from app.modules.auth.dependencies import CurrentUser
from app.modules.formalization.schemas import (
    FormalizationStatusResponse,
    FormalizationTaskResponse,
    FormalizationTaskUserResponse,
    TaskCompletionUpdate,
    TaskStatusUpdate,
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
    response_model=list[FormalizationTaskUserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get formalization tasks",
    description="Get list of formalization tasks for the current user (novo sistema baseado em CSV).",
)
async def get_formalization_tasks(
    current_user: CurrentUser,
    service: FormalizationService = Depends(get_formalization_service),
) -> list[FormalizationTaskUserResponse]:
    """
    Get formalization tasks for the current user.

    Tasks are calculated based on producer profile and rules.
    Returns tasks with catalog data (title, description, why, etc.).
    """
    user_id = str(current_user.id)
    tasks = await service.get_tasks(user_id)
    return tasks


@router.post(
    "/tasks/regenerate",
    status_code=status.HTTP_200_OK,
    summary="Regenerate formalization tasks",
    description="Recalculate and synchronize formalization tasks based on current producer profile.",
)
async def regenerate_formalization_tasks(
    current_user: CurrentUser,
    service: FormalizationService = Depends(get_formalization_service),
) -> dict[str, str]:
    """
    Regenerate formalization tasks for the current user.

    Recalculates which tasks are required based on the producer profile
    and synchronizes the user's task list.
    """
    user_id = str(current_user.id)
    await service.regenerate_tasks(user_id)
    return {"message": "Tasks regenerated successfully"}


@router.patch(
    "/tasks/{task_code}",
    response_model=FormalizationTaskUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task status",
    description="Update task status (pending, done, or skipped).",
)
async def update_task_status(
    task_code: str,
    update: TaskStatusUpdate,
    current_user: CurrentUser,
    service: FormalizationService = Depends(get_formalization_service),
) -> FormalizationTaskUserResponse:
    """
    Update task status.

    Args:
        task_code: Task code (e.g., "HAS_CPF", "HAS_BANK_ACCOUNT")
        update: Status update (pending, done, or skipped)
        current_user: Current authenticated user

    Returns:
        Updated task with catalog data

    Raises:
        HTTPException: If task not found or status is invalid
    """
    user_id = str(current_user.id)
    try:
        updated_task = await service.update_task_status(user_id, task_code, update.status)
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with code '{task_code}' not found for user",
            )

        # Buscar dados do catálogo para resposta completa
        catalog_task = await service.repo.get_task_catalog(task_code)
        if not catalog_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task code '{task_code}' not found in catalog",
            )

        return FormalizationTaskUserResponse(
            id=updated_task.id,
            user_id=updated_task.user_id,
            task_code=updated_task.task_code,
            title=catalog_task.title,
            description=catalog_task.description,
            why=catalog_task.why,
            status=updated_task.status,
            blocking=updated_task.blocking,
            estimated_time_days=catalog_task.estimated_time_days,
            requirement_id=updated_task.requirement_id,
            created_at=updated_task.created_at,
            updated_at=updated_task.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/tasks/{task_id}/complete",
    response_model=FormalizationTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task completion status",
    description="Mark a task as completed or uncompleted.",
)
async def update_task_completion(
    task_id: str,
    update: TaskCompletionUpdate,
    current_user: CurrentUser,
    service: FormalizationService = Depends(get_formalization_service),
) -> FormalizationTaskResponse:
    """
    Update task completion status.

    Args:
        task_id: The task_id (not MongoDB _id) of the task to update
        update: Completion status update
        current_user: Current authenticated user
        service: FormalizationService instance

    Returns:
        Updated task

    Raises:
        HTTPException: If task not found
    """
    user_id = str(current_user.id)
    try:
        updated_task = await service.update_task_completion(
            user_id, task_id, update.completed
        )
        return FormalizationTaskResponse(**updated_task.model_dump(by_alias=True))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
