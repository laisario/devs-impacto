"""
Documents module router.
Endpoints for document upload and management (Envelope 01).
"""

import asyncio

from fastapi import APIRouter, Depends, Query, status

from app.core.db import get_database
from app.core.errors import NotFoundError
from app.modules.auth.dependencies import CurrentUser
from app.modules.documents.schemas import (
    DocumentCreate,
    DocumentResponse,
    DocumentType,
    PresignRequest,
    PresignResponse,
)
from app.modules.documents.service import DocumentsService
from app.shared.pagination import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/documents", tags=["documents"])


async def get_documents_service() -> DocumentsService:
    """Get DocumentsService instance."""
    db = get_database()
    return DocumentsService(db)


@router.post(
    "/presign",
    response_model=PresignResponse,
    status_code=status.HTTP_200_OK,
    summary="Get presigned upload URL",
    description="Get a presigned URL to upload a document directly to storage.",
)
async def get_presigned_url(
    request: PresignRequest,
    current_user: CurrentUser,
    service: DocumentsService = Depends(get_documents_service),
) -> PresignResponse:
    """
    Get presigned URL for document upload.

    Flow:
    1. Client requests presigned URL with filename
    2. Server returns upload_url and file_url
    3. Client uploads file directly to upload_url
    4. Client calls POST /documents with metadata and file_url
    """
    user_id = str(current_user.id)
    presigned = service.generate_presigned_upload(user_id, request)

    return PresignResponse(
        upload_url=presigned.upload_url,
        file_url=presigned.file_url,
        file_key=presigned.file_key,
    )


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create document metadata",
    description="Save document metadata after uploading to storage.",
)
async def create_document(
    data: DocumentCreate,
    current_user: CurrentUser,
    service: DocumentsService = Depends(get_documents_service),
) -> DocumentResponse:
    """
    Create document metadata after upload.

    Called after client has uploaded the file using the presigned URL.
    Stores the document reference in the database.
    Triggers AI validation in background.
    """
    user_id = str(current_user.id)
    document = await service.create_document(user_id, data)

    # Trigger AI validation in background (non-blocking)
    asyncio.create_task(
        validate_document_async(user_id, str(document.id), data.doc_type, service)
    )

    return DocumentResponse(**document.model_dump(by_alias=True))


async def validate_document_async(
    user_id: str, doc_id: str, doc_type: DocumentType, service: DocumentsService
) -> None:
    """
    Validate document with AI in background.

    Args:
        user_id: User ID
        doc_id: Document ID
        doc_type: Document type
        service: DocumentsService instance
    """
    try:
        # Get user profile for context
        from app.modules.producers.service import ProducerService

        producer_service = ProducerService(get_database())
        try:
            profile = await producer_service.get_profile_by_user(user_id)
        except Exception:
            profile = None

        # Get document
        doc = await service.get_document_by_id(doc_id, user_id)
        if not doc:
            return

        # Validate with AI
        validation = await service.validate_document_with_ai(doc.file_url, doc_type, profile)

        # Build notes
        notes = validation.get("notes", "")
        if validation.get("issues"):
            issues_text = ", ".join(validation.get("issues", []))
            if notes:
                notes += f"\n\nProblemas encontrados: {issues_text}"
            else:
                notes = f"Problemas encontrados: {issues_text}"

        # Update document with AI validation results
        await service.update_document(
            doc_id,
            {
                "ai_notes": notes,
                "ai_validated": True,
                "ai_confidence": validation.get("confidence", "low"),
            },
        )
    except Exception as e:
        # Log error but don't fail - validation is optional
        import traceback

        print(f"Error in background document validation: {e}")
        print(traceback.format_exc())


@router.get(
    "",
    response_model=PaginatedResponse[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="List user documents",
    description="List all documents uploaded by the current user.",
)
async def list_documents(
    current_user: CurrentUser,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    service: DocumentsService = Depends(get_documents_service),
) -> PaginatedResponse[DocumentResponse]:
    """
    List all documents for the current user.

    Returns documents sorted by upload date (most recent first).
    """
    user_id = str(current_user.id)
    pagination = PaginationParams(skip=skip, limit=limit)
    documents, total = await service.list_user_documents(user_id, pagination)

    items = [DocumentResponse(**d.model_dump(by_alias=True)) for d in documents]

    return PaginatedResponse.create(items=items, total=total, pagination=pagination)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document by ID",
    description="Get a specific document by its ID.",
)
async def get_document(
    document_id: str,
    current_user: CurrentUser,
    service: DocumentsService = Depends(get_documents_service),
) -> DocumentResponse:
    """
    Get a specific document by ID.

    Only returns the document if it belongs to the current user.
    """
    user_id = str(current_user.id)
    document = await service.get_document_by_id(document_id, user_id)

    if not document:
        raise NotFoundError("Document", document_id)

    return DocumentResponse(**document.model_dump(by_alias=True))

