"""
Documents module service.
Business logic for document upload and management.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.documents.schemas import (
    DocumentCreate,
    DocumentInDB,
    PresignRequest,
)
from app.modules.documents.storage import PresignedUpload, get_storage_provider
from app.shared.pagination import PaginationParams
from app.shared.utils import to_object_id, utc_now


class DocumentsService:
    """Service for document operations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.collection = db.documents
        self.storage = get_storage_provider()

    def generate_presigned_upload(
        self,
        user_id: str,
        request: PresignRequest,
    ) -> PresignedUpload:
        """
        Generate presigned URL for file upload.

        Args:
            user_id: User's MongoDB ObjectId as string
            request: Presign request with filename and content type

        Returns:
            Presigned upload information
        """
        return self.storage.generate_presigned_upload(
            filename=request.filename,
            content_type=request.content_type,
            user_id=user_id,
        )

    async def create_document(
        self,
        user_id: str,
        data: DocumentCreate,
    ) -> DocumentInDB:
        """
        Create document metadata after upload.

        Args:
            user_id: User's MongoDB ObjectId as string
            data: Document metadata

        Returns:
            Created document
        """
        now = utc_now()
        user_oid = to_object_id(user_id)

        doc = {
            "user_id": user_oid,
            "doc_type": data.doc_type.value,
            "file_url": data.file_url,
            "file_key": data.file_key,
            "original_filename": data.original_filename,
            "uploaded_at": now,
        }

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        return DocumentInDB(**doc)

    async def list_user_documents(
        self,
        user_id: str,
        pagination: PaginationParams | None = None,
    ) -> tuple[list[DocumentInDB], int]:
        """
        List all documents for a user.

        Args:
            user_id: User's MongoDB ObjectId as string
            pagination: Optional pagination parameters

        Returns:
            Tuple of (documents list, total count)
        """
        try:
            user_oid = to_object_id(user_id)
        except ValueError:
            return [], 0

        query = {"user_id": user_oid}

        total = await self.collection.count_documents(query)

        cursor = self.collection.find(query).sort("uploaded_at", -1)

        if pagination:
            cursor = cursor.skip(pagination.skip).limit(pagination.limit)

        documents = []
        async for doc in cursor:
            documents.append(DocumentInDB(**doc))

        return documents, total

    async def get_document_by_id(
        self,
        doc_id: str,
        user_id: str,
    ) -> DocumentInDB | None:
        """
        Get a document by ID, ensuring it belongs to the user.

        Args:
            doc_id: Document's MongoDB ObjectId as string
            user_id: User's MongoDB ObjectId as string

        Returns:
            Document if found and belongs to user, None otherwise
        """
        try:
            doc_oid = to_object_id(doc_id)
            user_oid = to_object_id(user_id)
        except ValueError:
            return None

        doc = await self.collection.find_one(
            {
                "_id": doc_oid,
                "user_id": user_oid,
            }
        )

        if not doc:
            return None

        return DocumentInDB(**doc)

