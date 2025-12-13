"""
Auth module router.
Endpoints for authentication: OTP start, verify, and get current user.
"""

from fastapi import APIRouter, Depends, status

from app.core.errors import UnauthorizedError
from app.modules.auth.dependencies import CurrentUser, get_auth_service
from app.modules.auth.schemas import (
    AuthStartRequest,
    AuthStartResponse,
    AuthVerifyRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/start",
    response_model=AuthStartResponse,
    status_code=status.HTTP_200_OK,
    summary="Start authentication",
    description="Send OTP to the provided phone number. In dev mode, OTP is always '123456'.",
)
async def auth_start(
    request: AuthStartRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthStartResponse:
    """
    Start authentication flow by sending OTP to phone.

    - Receives phone in E.164 format (e.g., +5511999999999)
    - Creates or updates user record
    - "Sends" OTP (mock in development)
    """
    await auth_service.start_auth(request.phone_e164)
    return AuthStartResponse()


@router.post(
    "/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP",
    description="Verify OTP code and receive JWT access token.",
)
async def auth_verify(
    request: AuthVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Verify OTP and get JWT token.

    - Validates OTP code (use '123456' in development)
    - Returns JWT access token for authenticated requests
    """
    token = await auth_service.verify_auth(request.phone_e164, request.otp)
    if not token:
        raise UnauthorizedError("Invalid phone number or OTP code")

    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """
    Get current authenticated user.

    Requires valid JWT token in Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        phone_e164=current_user.phone_e164,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )

