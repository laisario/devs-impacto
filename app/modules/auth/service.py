"""
Auth module service.
Business logic for authentication operations.
"""

from datetime import timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.security import create_access_token, verify_otp
from app.modules.auth.schemas import UserInDB
from app.shared.utils import to_object_id, utc_now


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.collection = db.users

    async def start_auth(self, phone_e164: str) -> bool:
        """
        Start authentication by creating/updating user with OTP.

        In mock mode, uses fixed OTP code.
        In production, would send SMS via external service.

        Args:
            phone_e164: Phone number in E.164 format

        Returns:
            True if OTP was "sent" successfully
        """
        now = utc_now()
        otp_expires = now + timedelta(minutes=settings.otp_expire_minutes)

        # Upsert user with new OTP
        await self.collection.update_one(
            {"phone_e164": phone_e164},
            {
                "$set": {
                    "otp_code": settings.otp_code_mock,
                    "otp_expires_at": otp_expires,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "phone_e164": phone_e164,
                    "created_at": now,
                },
            },
            upsert=True,
        )

        # In production: send OTP via SMS provider
        # For now, mock always succeeds
        return True

    async def verify_auth(self, phone_e164: str, otp: str) -> str | None:
        """
        Verify OTP and return JWT token.

        Args:
            phone_e164: Phone number in E.164 format
            otp: OTP code provided by user

        Returns:
            JWT access token if valid, None otherwise
        """
        user_doc = await self.collection.find_one({"phone_e164": phone_e164})
        if not user_doc:
            return None

        stored_otp = user_doc.get("otp_code")
        if not verify_otp(otp, stored_otp):
            return None

        # Clear OTP after successful verification
        await self.collection.update_one(
            {"_id": user_doc["_id"]},
            {
                "$set": {
                    "otp_code": None,
                    "otp_expires_at": None,
                    "updated_at": utc_now(),
                }
            },
        )

        # Generate JWT token
        user_id = str(user_doc["_id"])
        return create_access_token(user_id)

    async def get_user_by_id(self, user_id: str) -> UserInDB | None:
        """
        Get user by ID.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            UserInDB if found, None otherwise
        """
        try:
            oid = to_object_id(user_id)
        except ValueError:
            return None

        user_doc = await self.collection.find_one({"_id": oid})
        if not user_doc:
            return None

        return UserInDB(**user_doc)

