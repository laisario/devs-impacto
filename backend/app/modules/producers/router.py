"""
Producers module router.
Endpoints for producer profile management.
"""

from fastapi import APIRouter, Depends, status

from app.core.db import get_database
from app.core.errors import NotFoundError
from app.modules.auth.dependencies import CurrentUser
from app.modules.producers.schemas import (
    ProducerProfileCreate,
    ProducerProfileResponse,
)
from app.modules.producers.service import ProducerService

router = APIRouter(prefix="/producer-profile", tags=["producers"])


async def get_producer_service() -> ProducerService:
    """Get ProducerService instance."""
    db = get_database()
    return ProducerService(db)


@router.put(
    "",
    response_model=ProducerProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update producer profile",
    description="Create or update the producer profile for the current user.",
)
async def upsert_producer_profile(
    data: ProducerProfileCreate,
    current_user: CurrentUser,
    service: ProducerService = Depends(get_producer_service),
) -> ProducerProfileResponse:
    """
    Create or update producer profile.

    Validates required fields based on producer_type:
    - formal: requires cnpj, dap_caf_number
    - informal: requires cpf (representative), members[], dap_caf_number
    - individual: requires cpf, dap_caf_number

    All types require DAP/CAF (Declaração de Aptidão ao Pronaf).
    """
    user_id = str(current_user.id)
    profile = await service.upsert_profile(user_id, data)
    return ProducerProfileResponse(**profile.model_dump(by_alias=True))


@router.get(
    "",
    response_model=ProducerProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get producer profile",
    description="Get the producer profile for the current user.",
)
async def get_producer_profile(
    current_user: CurrentUser,
    service: ProducerService = Depends(get_producer_service),
) -> ProducerProfileResponse:
    """
    Get current user's producer profile.

    Returns 404 if profile doesn't exist.
    """
    user_id = str(current_user.id)
    profile = await service.get_profile_by_user(user_id)

    if not profile:
        raise NotFoundError("Producer profile")

    return ProducerProfileResponse(**profile.model_dump(by_alias=True))


@router.get(
    "/{profile_id}",
    response_model=ProducerProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get producer profile by ID",
    description="Get a specific producer profile by its ID.",
)
async def get_producer_profile_by_id(
    profile_id: str,
    current_user: CurrentUser,  # noqa: ARG001 - Required for auth
    service: ProducerService = Depends(get_producer_service),
) -> ProducerProfileResponse:
    """
    Get a producer profile by ID.

    This endpoint is useful for viewing other producers' public profiles.
    Requires authentication.
    """
    profile = await service.get_profile_by_id(profile_id)

    if not profile:
        raise NotFoundError("Producer profile", profile_id)

    return ProducerProfileResponse(**profile.model_dump(by_alias=True))
