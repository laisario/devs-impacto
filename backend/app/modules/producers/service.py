"""
Producers module service.
Business logic for producer profile operations.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.producers.schemas import (
    ProducerProfileCreate,
    ProducerProfileInDB,
    ProducerType,
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
        except ValueError as e:
            import traceback
            print(f"Error converting user_id to ObjectId: {e}")
            print(traceback.format_exc())
            return None

        try:
            doc = await self.collection.find_one({"user_id": user_oid})
            if not doc:
                return None

            # Validate that the document has required fields before creating the model
            # DAP/CAF is optional (can be added later)
            required_fields = {"producer_type", "name", "address", "city", "state"}
            missing_fields = required_fields - set(doc.keys())
            if missing_fields:
                # This is a minimal profile created by onboarding, not a complete profile
                # Return None so the user can create a proper profile
                print(f"Profile exists but is missing required fields: {missing_fields}")
                return None
            
            # Ensure dap_caf_number exists (can be None)
            if "dap_caf_number" not in doc:
                doc["dap_caf_number"] = None
            
            # Ensure CPF exists (comes from auth, not onboarding)
            # We'll get it from the user document if needed
            producer_type = doc.get("producer_type")
            if "cpf" not in doc and producer_type in ["individual", "informal"]:
                # Try to get CPF from user document
                try:
                    from app.modules.auth.service import AuthService
                    auth_service = AuthService(self.db)
                    user_doc = await auth_service.collection.find_one({"_id": user_oid})
                    if user_doc and user_doc.get("cpf"):
                        doc["cpf"] = user_doc["cpf"]
                except Exception:
                    pass
            
            try:
                return ProducerProfileInDB(**doc)
            except Exception as e:
                import traceback
                print(f"Error creating ProducerProfileInDB from document: {e}")
                print(f"Document keys: {list(doc.keys())}")
                print(f"Document: {doc}")
                print(traceback.format_exc())
                # If validation fails, return None instead of raising
                # This allows the frontend to handle validation and show appropriate errors
                return None
        except Exception as e:
            import traceback
            print(f"Error in get_profile_by_user: {e}")
            print(traceback.format_exc())
            raise

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
