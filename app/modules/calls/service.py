"""
Calls module service.
Business logic for calls for proposals operations.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.calls.schemas import (
    CallForProposalCreate,
    CallForProposalInDB,
)
from app.shared.pagination import PaginationParams
from app.shared.utils import to_object_id, utc_now


class CallsService:
    """Service for calls for proposals operations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.collection = db.calls_for_proposals

    async def create_call(self, data: CallForProposalCreate) -> CallForProposalInDB:
        """
        Create a new call for proposals.

        Args:
            data: Call data

        Returns:
            Created call
        """
        now = utc_now()

        doc = data.model_dump()
        doc["created_at"] = now

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        return CallForProposalInDB(**doc)

    async def get_call_by_id(self, call_id: str) -> CallForProposalInDB | None:
        """
        Get a call by ID.

        Args:
            call_id: Call's MongoDB ObjectId as string

        Returns:
            Call if found, None otherwise
        """
        try:
            oid = to_object_id(call_id)
        except ValueError:
            return None

        doc = await self.collection.find_one({"_id": oid})
        if not doc:
            return None

        return CallForProposalInDB(**doc)

    async def list_calls(
        self,
        pagination: PaginationParams,
        status: str | None = None,
    ) -> tuple[list[CallForProposalInDB], int]:
        """
        List calls for proposals with pagination.

        Args:
            pagination: Pagination parameters
            status: Optional status filter

        Returns:
            Tuple of (calls list, total count)
        """
        query: dict[str, str] = {}
        if status:
            query["status"] = status

        # Get total count
        total = await self.collection.count_documents(query)

        # Get paginated results
        cursor = self.collection.find(query)
        cursor = cursor.sort("created_at", -1)  # Most recent first
        cursor = cursor.skip(pagination.skip).limit(pagination.limit)

        calls = []
        async for doc in cursor:
            calls.append(CallForProposalInDB(**doc))

        return calls, total

