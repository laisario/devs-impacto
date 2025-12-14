"""
Sales Project router.
Endpoints for AI-powered sales project generation.
"""

from fastapi import APIRouter, Depends, status

from app.core.db import get_database
from app.core.errors import NotFoundError
from app.modules.auth.dependencies import CurrentUser
from app.modules.sales_project.schemas import (
    SalesProjectDraftRequest,
    SalesProjectResponse,
)
from app.modules.sales_project.service import SalesProjectService

router = APIRouter(prefix="/sales-project", tags=["sales-project"])


async def get_sales_project_service() -> SalesProjectService:
    """Get SalesProjectService instance."""
    db = get_database()
    return SalesProjectService(db)


@router.post(
    "/draft",
    response_model=SalesProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate sales project draft",
    description="Generate a draft sales project for PNAE using AI based on producer profile and onboarding answers.",
)
async def generate_draft(
    request: SalesProjectDraftRequest,
    current_user: CurrentUser,
    service: SalesProjectService = Depends(get_sales_project_service),
) -> SalesProjectResponse:
    """
    Generate a sales project draft using AI.

    Uses producer profile and onboarding answers to generate a personalized
    sales project with products, quantities, prices, and delivery schedule.
    """
    user_id = str(current_user.id)
    project = await service.generate_draft_with_ai(user_id, request)
    return SalesProjectResponse(**project.model_dump(by_alias=True))


@router.get(
    "",
    response_model=list[SalesProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="List user sales projects",
    description="List all sales projects for the current user.",
)
async def list_projects(
    current_user: CurrentUser,
    service: SalesProjectService = Depends(get_sales_project_service),
) -> list[SalesProjectResponse]:
    """List all sales projects for the current user."""
    user_id = str(current_user.id)
    projects = await service.get_user_projects(user_id)
    return [SalesProjectResponse(**p.model_dump(by_alias=True)) for p in projects]


@router.get(
    "/{project_id}",
    response_model=SalesProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sales project by ID",
    description="Get a specific sales project by its ID.",
)
async def get_project(
    project_id: str,
    current_user: CurrentUser,
    service: SalesProjectService = Depends(get_sales_project_service),
) -> SalesProjectResponse:
    """Get a specific sales project by ID."""
    user_id = str(current_user.id)
    project = await service.get_project_by_id(project_id, user_id)
    if not project:
        raise NotFoundError("Sales project", project_id)
    return SalesProjectResponse(**project.model_dump(by_alias=True))

