"""
Auth module dependencies.
FastAPI dependencies for authentication.
"""

from typing import Annotated

from fastapi import Depends, Header

from app.core.db import get_database
from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token
from app.modules.auth.schemas import UserInDB
from app.modules.auth.service import AuthService


async def get_auth_service() -> AuthService:
    """Get AuthService instance with database connection."""
    db = get_database()
    return AuthService(db)


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserInDB:
    """
    Get the current authenticated user from JWT token.

    Args:
        authorization: Authorization header with Bearer token
        auth_service: AuthService instance

    Returns:
        Current authenticated user

    Raises:
        UnauthorizedError: If token is missing, invalid, or user not found
    """
    if not authorization:
        raise UnauthorizedError("Missing authorization header")

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid authorization header format")

    token = parts[1]

    # Decode and validate token
    token_payload = decode_access_token(token)
    if not token_payload:
        raise UnauthorizedError("Invalid or expired token")

    # Get user from database
    user = await auth_service.get_user_by_id(token_payload.sub)
    if not user:
        raise UnauthorizedError("User not found")

    return user


# Type alias for dependency injection
CurrentUser = Annotated[UserInDB, Depends(get_current_user)]

