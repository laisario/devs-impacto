"""
Producers module router.
Endpoints for producer profile management.
"""

import asyncio

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


async def generate_guides_async(user_id: str) -> None:
    """Background task to generate guides for user."""
    try:
        # Lazy imports to avoid circular dependency
        from app.modules.ai_formalization.llm_client import create_llm_client
        from app.modules.ai_formalization.rag import RAGService
        from app.modules.ai_formalization.service import AIFormalizationService
        from app.modules.onboarding.service import OnboardingService
        
        db = get_database()
        rag_service = RAGService(db)
        llm_client = create_llm_client()
        onboarding_service = OnboardingService(db)
        producer_service = ProducerService(db)
        
        ai_service = AIFormalizationService(
            db=db,
            rag_service=rag_service,
            llm_client=llm_client,
            onboarding_service=onboarding_service,
            producer_service=producer_service,
        )
        
        await ai_service.generate_guides_for_user(user_id)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error generating guides in background: {e}")


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
    
    Automatically generates AI guides for all tasks when profile is complete.
    """
    user_id = str(current_user.id)
    profile = await service.upsert_profile(user_id, data)
    
    # Check if profile is complete and generate guides in background
    try:
        # Check if profile has minimum required fields
        required_fields = ["producer_type", "name", "address", "city", "state"]
        is_complete = all(
            getattr(profile, field, None) for field in required_fields
        )
        
        if is_complete:
            # Generate guides in background (non-blocking)
            # Use create_task to run async function in background
            asyncio.create_task(generate_guides_async(user_id))
    except Exception as e:
        # Don't fail the request if guide generation fails
        print(f"Error setting up guide generation: {e}")
    
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
    try:
        user_id = str(current_user.id)
        profile = await service.get_profile_by_user(user_id)

        if not profile:
            raise NotFoundError("Producer profile")

        return ProducerProfileResponse(**profile.model_dump(by_alias=True))
    except Exception as e:
        import traceback
        print(f"Error in get_producer_profile endpoint: {e}")
        print(traceback.format_exc())
        raise


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
