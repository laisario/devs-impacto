"""
Calls module router.
Endpoints for calls for proposals (Chamadas Públicas) management.
"""

from fastapi import APIRouter, Depends, Query, status

from app.core.db import get_database
from app.core.errors import NotFoundError
from app.modules.auth.dependencies import CurrentUser
from app.modules.calls.schemas import (
    CallForProposalCreate,
    CallForProposalResponse,
)
from app.modules.calls.service import CallsService
from app.shared.pagination import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/calls", tags=["calls"])


async def get_calls_service() -> CallsService:
    """Get CallsService instance."""
    db = get_database()
    return CallsService(db)


@router.post(
    "",
    response_model=CallForProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create call for proposals",
    description="Create a new call for proposals (Chamada Pública).",
)
async def create_call(
    data: CallForProposalCreate,
    current_user: CurrentUser,  # noqa: ARG001 - Required for auth
    service: CallsService = Depends(get_calls_service),
) -> CallForProposalResponse:
    """
    Create a new call for proposals.

    In production, this would be restricted to admin users.
    For MVP, any authenticated user can create calls.
    """
    call = await service.create_call(data)
    return CallForProposalResponse(**call.model_dump(by_alias=True))


@router.get(
    "",
    response_model=PaginatedResponse[CallForProposalResponse],
    status_code=status.HTTP_200_OK,
    summary="List calls for proposals",
    description="List all calls for proposals with pagination.",
)
async def list_calls(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    call_status: str | None = Query(None, alias="status", description="Filter by status"),
    service: CallsService = Depends(get_calls_service),
) -> PaginatedResponse[CallForProposalResponse]:
    """
    List calls for proposals.

    Supports pagination and optional status filter.
    Returns most recent calls first.
    """
    pagination = PaginationParams(skip=skip, limit=limit)
    calls, total = await service.list_calls(pagination, status=call_status)

    items = [CallForProposalResponse(**c.model_dump(by_alias=True)) for c in calls]

    return PaginatedResponse.create(items=items, total=total, pagination=pagination)


@router.get(
    "/{call_id}",
    response_model=CallForProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Get call for proposals",
    description="Get details of a specific call for proposals.",
)
async def get_call(
    call_id: str,
    service: CallsService = Depends(get_calls_service),
) -> CallForProposalResponse:
    """
    Get a specific call for proposals by ID.

    This endpoint is public (no auth required) to allow producers
    to browse available calls.
    """
    call = await service.get_call_by_id(call_id)
    if not call:
        raise NotFoundError("Call for proposals", call_id)

    return CallForProposalResponse(**call.model_dump(by_alias=True))

