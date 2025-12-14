"""
Auth module router.
Endpoints for authentication: login and get current user.
"""

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import CurrentUser, get_auth_service
from app.modules.auth.schemas import (
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
    description="Login with CPF. Validates CPF via public API and links to existing user.",
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Login with CPF.

    - Validates CPF via public API
    - Creates or links to existing user
    - Returns JWT access token
    """
    token = await auth_service.login(request.cpf)
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
        cpf=current_user.cpf,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )

