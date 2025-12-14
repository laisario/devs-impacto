"""
Auth module schemas.
Pydantic models for authentication requests and responses.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.shared.utils import PyObjectId


# Request schemas
class LoginRequest(BaseModel):
    """Request to login with CPF."""

    cpf: str


# Response schemas


class TokenResponse(BaseModel):
    """Response with JWT token."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User information response."""

    id: PyObjectId = Field(..., alias="_id")
    cpf: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


# Internal database model
class UserInDB(BaseModel):
    """User document as stored in MongoDB."""

    id: PyObjectId | None = Field(None, alias="_id")
    cpf: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}

