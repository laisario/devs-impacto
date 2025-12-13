"""
Producers module service.
Business logic for producer profile operations.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.producers.schemas import (
    ProducerProfileCreate,
    ProducerProfileInDB,
)
from app.shared.utils import to_object_id, utc_now


class ProducerService:
    """Service for producer profile operations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.collection = db.producer_profiles

    async def upsert_profile(
        self,
        user_id: str,
        data: ProducerProfileCreate,
    ) -> ProducerProfileInDB:
        """
        Create or update producer profile for user.

        Each user can have only one producer profile.
        Uses upsert to simplify the flow.

        Args:
            user_id: User's MongoDB ObjectId as string
            data: Producer profile data

        Returns:
            Created or updated producer profile
        """
        now = utc_now()
        user_oid = to_object_id(user_id)

        # Prepare document for upsert
        doc = data.model_dump(exclude_none=True)
        doc["user_id"] = user_oid
        doc["updated_at"] = now

        result = await self.collection.find_one_and_update(
            {"user_id": user_oid},
            {
                "$set": doc,
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
            return_document=True,
        )

        return ProducerProfileInDB(**result)

    async def get_profile_by_user(self, user_id: str) -> ProducerProfileInDB | None:
        """
        Get producer profile for a user.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            Producer profile if exists, None otherwise
        """
        try:
            user_oid = to_object_id(user_id)
        except ValueError:
            return None

        doc = await self.collection.find_one({"user_id": user_oid})
        if not doc:
            return None

        return ProducerProfileInDB(**doc)

    async def get_profile_by_id(self, profile_id: str) -> ProducerProfileInDB | None:
        """
        Get producer profile by its ID.

        Args:
            profile_id: Profile's MongoDB ObjectId as string

        Returns:
            Producer profile if exists, None otherwise
        """
        try:
            oid = to_object_id(profile_id)
        except ValueError:
            return None

        doc = await self.collection.find_one({"_id": oid})
        if not doc:
            return None

        return ProducerProfileInDB(**doc)
