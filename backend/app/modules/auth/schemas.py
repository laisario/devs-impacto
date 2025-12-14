"""
Auth module schemas.
Pydantic models for authentication requests and responses.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.shared.utils import PyObjectId


# Request schemas
class AuthStartRequest(BaseModel):
    """Request to start authentication (send OTP)."""

    phone_e164: str = Field(
        ...,
        description="Phone number in E.164 format (e.g., +5511999999999)",
        pattern=r"^\+[1-9]\d{1,14}$",
        examples=["+5511999999999"],
    )


class AuthVerifyRequest(BaseModel):
    """Request to verify OTP and get token."""

    phone_e164: str = Field(
        ...,
        description="Phone number in E.164 format",
        pattern=r"^\+[1-9]\d{1,14}$",
    )
    otp: str = Field(
        ...,
        description="6-digit OTP code",
        min_length=6,
        max_length=6,
    )


# Response schemas
class AuthStartResponse(BaseModel):
    """Response after starting authentication."""

    ok: bool = True
    message: str = "OTP sent successfully"


class TokenResponse(BaseModel):
    """Response with JWT token."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User information response."""

    id: PyObjectId = Field(..., alias="_id")
    phone_e164: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


# Internal database model
class UserInDB(BaseModel):
    """User document as stored in MongoDB."""

    id: PyObjectId | None = Field(None, alias="_id")
    phone_e164: str
    otp_code: str | None = None
    otp_expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}

