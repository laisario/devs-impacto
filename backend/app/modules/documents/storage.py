"""
Storage provider interface and implementations.

Supports mock storage for development, S3/R2, and Google Cloud Storage for production.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta

from app.core.config import settings

try:
    from google.cloud import storage
    from google.cloud.exceptions import GoogleCloudError

    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    storage = None  # type: ignore
    GoogleCloudError = Exception  # type: ignore

try:
    import boto3
    from botocore.exceptions import ClientError

    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    boto3 = None  # type: ignore
    ClientError = Exception  # type: ignore


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


class GCSStorageProvider(StorageProvider):
    """
    Google Cloud Storage provider for production.

    Uses GCS presigned URLs for secure file uploads.
    """

    def __init__(self, bucket_name: str):
        """
        Initialize GCS storage provider.

        Args:
            bucket_name: Name of the GCS bucket to use

        Raises:
            ValueError: If GCS is not available or bucket_name is not provided
        """
        if not GCS_AVAILABLE:
            raise ValueError(
                "google-cloud-storage is not installed. "
                "Install it with: pip install google-cloud-storage"
            )
        if not bucket_name:
            raise ValueError("GCS bucket name is required")

        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def generate_presigned_upload(
        self,
        filename: str,
        content_type: str,
        user_id: str,
    ) -> PresignedUpload:
        """
        Generate presigned URL for file upload to GCS.

        Args:
            filename: Original filename
            content_type: MIME type
            user_id: User's ID for organizing files

        Returns:
            PresignedUpload with presigned URL, public URL, and file key
        """
        # Generate unique file key
        file_id = uuid.uuid4().hex[:12]
        safe_filename = filename.replace(" ", "_").lower()
        file_key = f"{user_id}/{file_id}_{safe_filename}"

        blob = self.bucket.blob(file_key)

        # Generate presigned URL for upload (valid for 1 hour)
        # Note: The client uploading the file should set x-goog-acl: public-read header
        # to make the file publicly accessible after upload
        upload_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="PUT",
            content_type=content_type,
        )

        # Generate public URL for file access
        # Note: Files uploaded via presigned URL will be publicly accessible
        # if the bucket has uniform bucket-level access enabled, or if the
        # client sets the x-goog-acl header during upload
        file_url = f"https://storage.googleapis.com/{self.bucket_name}/{file_key}"

        return PresignedUpload(
            upload_url=upload_url,
            file_url=file_url,
            file_key=file_key,
        )

    def get_file_url(self, file_key: str) -> str:
        """
        Get public URL for a file in GCS.

        Args:
            file_key: File's unique key

        Returns:
            Public URL to access the file
        """
        return f"https://storage.googleapis.com/{self.bucket_name}/{file_key}"


class S3StorageProvider(StorageProvider):
    """
    S3-compatible storage provider (AWS S3, Cloudflare R2, etc.).

    Uses boto3 to generate presigned URLs for secure file uploads.
    """

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str | None = None,
        region_name: str = "auto",
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_url: str | None = None,
    ):
        """
        Initialize S3 storage provider.

        Args:
            bucket_name: Name of the S3/R2 bucket
            endpoint_url: Custom endpoint URL (for R2, use your R2 endpoint)
            region_name: AWS region or "auto" for R2
            access_key_id: AWS/R2 access key ID
            secret_access_key: AWS/R2 secret access key
            public_url: Public URL pattern for accessing files
                       (e.g., "https://bucket.account.r2.cloudflarestorage.com")

        Raises:
            ValueError: If boto3 is not available or required params missing
        """
        if not S3_AVAILABLE:
            raise ValueError(
                "boto3 is not installed. "
                "Install it with: pip install boto3"
            )
        if not bucket_name:
            raise ValueError("S3 bucket name is required")

        self.bucket_name = bucket_name
        self.public_url = public_url

        # Configure boto3 client
        client_config = {
            "service_name": "s3",
        }

        if endpoint_url:
            client_config["endpoint_url"] = endpoint_url

        if region_name:
            client_config["region_name"] = region_name

        if access_key_id and secret_access_key:
            client_config["aws_access_key_id"] = access_key_id
            client_config["aws_secret_access_key"] = secret_access_key

        self.client = boto3.client(**client_config)

    def generate_presigned_upload(
        self,
        filename: str,
        content_type: str,
        user_id: str,
    ) -> PresignedUpload:
        """
        Generate presigned URL for file upload to S3/R2.

        Args:
            filename: Original filename
            content_type: MIME type
            user_id: User's ID for organizing files

        Returns:
            PresignedUpload with presigned URL, public URL, and file key
        """
        # Generate unique file key
        file_id = uuid.uuid4().hex[:12]
        safe_filename = filename.replace(" ", "_").lower()
        file_key = f"{user_id}/{file_id}_{safe_filename}"

        # Generate presigned URL for upload (valid for 1 hour)
        upload_url = self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": file_key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,  # 1 hour
        )

        # Generate public URL for file access
        if self.public_url:
            # Use custom public URL pattern
            file_url = f"{self.public_url.rstrip('/')}/{file_key}"
        else:
            # Fallback: generate presigned URL for reading (valid for 1 hour)
            # Note: For production, you should configure S3_PUBLIC_URL
            file_url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_key},
                ExpiresIn=3600,
            )

        return PresignedUpload(
            upload_url=upload_url,
            file_url=file_url,
            file_key=file_key,
        )

    def get_file_url(self, file_key: str) -> str:
        """
        Get public URL for a file in S3/R2.

        Args:
            file_key: File's unique key

        Returns:
            Public URL to access the file
        """
        if self.public_url:
            return f"{self.public_url.rstrip('/')}/{file_key}"
        # Fallback: generate a presigned URL for reading (valid for 1 hour)
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": file_key},
            ExpiresIn=3600,
        )


def get_storage_provider() -> StorageProvider:
    """
    Get configured storage provider.

    Returns:
        StorageProvider instance based on settings.storage_provider:
        - "mock": MockStorageProvider (for development)
        - "s3": S3StorageProvider (requires S3_BUCKET_NAME, works with Cloudflare R2)
        - "gcs": GCSStorageProvider (requires GCS_BUCKET_NAME)
        - Default: MockStorageProvider
    """
    if settings.storage_provider == "s3":
        if not settings.s3_bucket_name:
            raise ValueError(
                "S3 bucket name is required when using S3 storage provider. "
                "Set S3_BUCKET_NAME environment variable."
            )
        return S3StorageProvider(
            bucket_name=settings.s3_bucket_name,
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region_name,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
            public_url=settings.s3_public_url,
        )

    if settings.storage_provider == "gcs":
        if not settings.gcs_bucket_name:
            raise ValueError(
                "GCS bucket name is required when using GCS storage provider. "
                "Set GCS_BUCKET_NAME environment variable."
            )
        return GCSStorageProvider(bucket_name=settings.gcs_bucket_name)

    if settings.storage_provider == "mock":
        return MockStorageProvider()

    # Default to mock if provider is not recognized
    return MockStorageProvider()

