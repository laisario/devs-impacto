"""
Security utilities for JWT authentication.
Implements simple JWT-based auth for the PNAE API.
"""

from datetime import UTC, datetime, timedelta

import jwt
from pydantic import BaseModel, ValidationError

from app.core.config import settings


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # user_id
    exp: datetime
    iat: datetime


def create_access_token(user_id: str) -> str:
    """
    Create a JWT access token for the given user.

    Args:
        user_id: The user's MongoDB ObjectId as string

    Returns:
        Encoded JWT token
    """
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)

    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload | None:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT token to decode

    Returns:
        TokenPayload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except ValidationError:
        return None


def verify_otp(provided_otp: str, stored_otp: str | None) -> bool:
    """
    Verify OTP code.
    In mock mode, accepts the fixed OTP code.

    Args:
        provided_otp: OTP provided by user
        stored_otp: OTP stored in database

    Returns:
        True if OTP is valid
    """
    # Mock mode: accept fixed OTP
    if provided_otp == settings.otp_code_mock:
        return True

    # Normal mode: compare with stored OTP
    if stored_otp and provided_otp == stored_otp:
        return True

    return False

