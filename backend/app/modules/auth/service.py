"""
Auth module service.
Business logic for authentication operations.
"""

import re

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.errors import UnauthorizedError
from app.core.security import create_access_token
from app.modules.auth.schemas import UserInDB
from app.shared.utils import to_object_id, utc_now


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.collection = db.users

    def _clean_cpf(self, cpf: str) -> str:
        """Remove formatting from CPF, keeping only digits."""
        return re.sub(r"[^\d]", "", cpf)

    def _validate_cpf_format(self, cpf: str) -> bool:
        """Validate CPF format (11 digits)."""
        # cpf should already be cleaned, but clean again to be safe
        cleaned = self._clean_cpf(cpf)
        return len(cleaned) == 11 and cleaned.isdigit()

    def _validate_cpf_digits(self, cpf: str) -> bool:
        """
        Validate CPF using check digit algorithm.

        Args:
            cpf: CPF to validate (cleaned, 11 digits)

        Returns:
            True if CPF check digits are valid, False otherwise
        """
        # Check for known invalid patterns
        if len(set(cpf)) == 1:  # All digits are the same (e.g., 11111111111)
            return False

        # Calculate first check digit
        sum_first = sum(int(cpf[i]) * (10 - i) for i in range(9))
        remainder_first = sum_first % 11
        first_digit = 0 if remainder_first < 2 else 11 - remainder_first

        if int(cpf[9]) != first_digit:
            return False

        # Calculate second check digit
        sum_second = sum(int(cpf[i]) * (11 - i) for i in range(10))
        remainder_second = sum_second % 11
        second_digit = 0 if remainder_second < 2 else 11 - remainder_second

        return int(cpf[10]) == second_digit

    async def login(self, cpf: str) -> str:
        """
        Login with CPF. Validates CPF via public API and links to existing user.

        Args:
            cpf: User CPF (with or without formatting)

        Returns:
            JWT access token

        Raises:
            UnauthorizedError: If CPF format is invalid or validation fails
        """
        # Clean and validate format
        cleaned_cpf = self._clean_cpf(cpf)
        if not self._validate_cpf_format(cleaned_cpf):
            raise UnauthorizedError("CPF inválido. Por favor, insira um CPF válido.")

        # Validate CPF check digits
        if not self._validate_cpf_digits(cleaned_cpf):
            raise UnauthorizedError("CPF inválido. Por favor, insira um CPF válido.")

        now = utc_now()

        # Upsert user (create if doesn't exist, link to existing if exists)
        await self.collection.update_one(
            {"cpf": cleaned_cpf},
            {
                "$set": {
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "cpf": cleaned_cpf,
                    "created_at": now,
                },
            },
            upsert=True,
        )

        # Get user document
        user_doc = await self.collection.find_one({"cpf": cleaned_cpf})
        if not user_doc:
            raise RuntimeError("Failed to create or find user")

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

