"""
Storage provider interface and mock implementation.

In production, this would integrate with S3, GCS, or similar.
For MVP, uses mock URLs that simulate presigned URL flow.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class PresignedUpload:
    """Presigned upload information."""

    upload_url: str
    file_url: str
    file_key: str


class StorageProvider(ABC):
    """Abstract storage provider interface."""

    @abstractmethod
    def generate_presigned_upload(
        self,
        filename: str,
        content_type: str,
        user_id: str,
    ) -> PresignedUpload:
        """
        Generate presigned URL for file upload.

        Args:
            filename: Original filename
            content_type: MIME type
            user_id: User's ID for organizing files

        Returns:
            PresignedUpload with URLs and key
        """
        pass

    @abstractmethod
    def get_file_url(self, file_key: str) -> str:
        """
        Get public URL for a file.

        Args:
            file_key: File's unique key

        Returns:
            Public URL to access the file
        """
        pass


class MockStorageProvider(StorageProvider):
    """
    Mock storage provider for development.

    Simulates presigned URL flow without actual file storage.
    In production, replace with S3StorageProvider or similar.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.mock_storage_base_url

    def generate_presigned_upload(
        self,
        filename: str,
        content_type: str,  # noqa: ARG002 - Used in real implementation
        user_id: str,
    ) -> PresignedUpload:
        """
        Generate mock presigned upload URLs.

        Creates unique file key and simulated URLs.
        """
        # Generate unique file key
        file_id = uuid.uuid4().hex[:12]
        safe_filename = filename.replace(" ", "_").lower()
        file_key = f"{user_id}/{file_id}_{safe_filename}"

        # Mock URLs - in production these would be actual S3/GCS presigned URLs
        upload_url = f"{self.base_url}/upload/{file_key}"
        file_url = f"{self.base_url}/files/{file_key}"

        return PresignedUpload(
            upload_url=upload_url,
            file_url=file_url,
            file_key=file_key,
        )

    def get_file_url(self, file_key: str) -> str:
        """Get mock file URL."""
        return f"{self.base_url}/files/{file_key}"


def get_storage_provider() -> StorageProvider:
    """
    Get configured storage provider.

    Returns MockStorageProvider for development.
    In production, would return S3/GCS provider based on config.
    """
    if settings.storage_provider == "mock":
        return MockStorageProvider()

    # Future: Add S3, GCS providers
    # if settings.storage_provider == "s3":
    #     return S3StorageProvider(...)

    return MockStorageProvider()

