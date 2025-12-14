"""
Producers module service.
Business logic for producer profile operations.
"""

import logging

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
        self.logger = logging.getLogger(__name__)

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
            self.logger.error(
                f"Invalid user_id format: {user_id}",
                exc_info=True,
                extra={"user_id": user_id, "operation": "get_profile_by_user"}
            )
            return None

        try:
            doc = await self.collection.find_one({"user_id": user_oid})
            if not doc:
                return None

            # Validate that the document has required fields before creating the model
            # DAP/CAF is optional (can be added later)
            required_fields = {"producer_type", "name", "address", "city", "state"}
            missing_fields = required_fields - set(doc.keys())
            
            # Try to infer producer_type from producer_mode if missing
            if "producer_type" not in doc and "producer_mode" in doc:
                producer_mode = doc.get("producer_mode")
                if isinstance(producer_mode, bool):
                    # If producer_mode is boolean, map to individual (False) or informal (True)
                    doc["producer_type"] = "informal" if producer_mode else "individual"
                elif isinstance(producer_mode, str):
                    # Map string values
                    producer_mode_map = {
                        "sozinho": "individual",
                        "grupo": "informal",
                    }
                    doc["producer_type"] = producer_mode_map.get(producer_mode.lower(), "individual")
                else:
                    # Default to individual
                    doc["producer_type"] = "individual"
                self.logger.debug(
                    f"Inferred producer_type from producer_mode: {doc['producer_type']}",
                    extra={"user_id": user_id, "producer_mode": producer_mode, "operation": "get_profile_by_user"}
                )
            
            if missing_fields:
                # Profile is missing some required fields - but still return it if producer_type exists
                # This allows onboarding-created profiles to be returned even if incomplete
                if "producer_type" not in doc:
                    # Critical field missing - can't create valid profile
                    self.logger.debug(
                        f"Profile exists but is missing critical field producer_type",
                        extra={"user_id": user_id, "operation": "get_profile_by_user"}
                    )
                    return None
                
                # Fill in missing fields with defaults to allow profile creation
                if "name" not in doc:
                    doc["name"] = "Nome não informado"
                if "address" not in doc:
                    doc["address"] = "Endereço não informado"
                if "city" not in doc:
                    doc["city"] = "Cidade não informada"
                if "state" not in doc:
                    doc["state"] = "XX"
                
                self.logger.debug(
                    f"Profile missing some fields, using defaults: {missing_fields}",
                    extra={"user_id": user_id, "missing_fields": list(missing_fields), "operation": "get_profile_by_user"}
                )
            
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
                self.logger.error(
                    f"Failed to create ProducerProfileInDB from document for user {user_id}: {e}",
                    exc_info=True,
                    extra={
                        "user_id": user_id,
                        "document_keys": list(doc.keys()),
                        "operation": "get_profile_by_user"
                    }
                )
                # If validation fails, return None instead of raising
                # This allows the frontend to handle validation and show appropriate errors
                return None
        except Exception as e:
            self.logger.error(
                f"Error in get_profile_by_user for user {user_id}: {e}",
                exc_info=True,
                extra={"user_id": user_id, "operation": "get_profile_by_user"}
            )
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
