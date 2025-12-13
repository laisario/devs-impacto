"""
Sales Projects module router.
Endpoints for Projeto de Venda (Envelope 02) management.
"""

from fastapi import APIRouter, Depends, status

from app.core.db import get_database
from app.core.errors import NotFoundError
from app.modules.auth.dependencies import CurrentUser
from app.modules.sales_projects.schemas import (
    GeneratePdfResponse,
    SalesProjectCreate,
    SalesProjectResponse,
)
from app.modules.sales_projects.service import SalesProjectsService

router = APIRouter(prefix="/sales-projects", tags=["sales-projects"])


async def get_sales_projects_service() -> SalesProjectsService:
    """Get SalesProjectsService instance."""
    db = get_database()
    return SalesProjectsService(db)


@router.post(
    "",
    response_model=SalesProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create sales project",
    description="Create a new Projeto de Venda linked to a call and producer profile.",
)
async def create_sales_project(
    data: SalesProjectCreate,
    current_user: CurrentUser,
    service: SalesProjectsService = Depends(get_sales_projects_service),
) -> SalesProjectResponse:
    """
    Create a new sales project (Projeto de Venda).

    Requires:
    - Valid call_id (chamada pública must exist)
    - User must have a producer profile
    - At least one item in the products list

    The project is created in 'draft' status.
    """
    user_id = str(current_user.id)
    project = await service.create_project(user_id, data)
    return SalesProjectResponse(**project.model_dump(by_alias=True))


@router.get(
    "/{project_id}",
    response_model=SalesProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sales project",
    description="Get details of a specific sales project.",
)
async def get_sales_project(
    project_id: str,
    current_user: CurrentUser,
    service: SalesProjectsService = Depends(get_sales_projects_service),
) -> SalesProjectResponse:
    """
    Get a specific sales project by ID.

    Only returns projects owned by the current user.
    """
    user_id = str(current_user.id)
    project = await service.get_project_by_id(project_id, user_id)

    if not project:
        raise NotFoundError("Projeto de venda", project_id)

    return SalesProjectResponse(**project.model_dump(by_alias=True))


@router.post(
    "/{project_id}/generate-pdf",
    response_model=GeneratePdfResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate PDF",
    description="Generate the Projeto de Venda PDF document.",
)
async def generate_pdf(
    project_id: str,
    current_user: CurrentUser,
    service: SalesProjectsService = Depends(get_sales_projects_service),
) -> GeneratePdfResponse:
    """
    Generate PDF for the sales project.

    Creates a printable PDF document with:
    - Identification of the proposal (call number)
    - Identification of the executing entity
    - Identification of the supplier (producer)
    - Product list with quantities, prices, and schedule
    - Total value
    - Signature area

    The PDF URL is saved in the project record.
    """
    user_id = str(current_user.id)
    pdf_url = await service.generate_pdf(project_id, user_id)

    return GeneratePdfResponse(pdf_url=pdf_url)

