"""
MongoDB async database connection using Motor.
Provides database access for the PNAE API.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

# Global client instance
_client: AsyncIOMotorClient | None = None  # type: ignore[type-arg]


async def connect_db() -> None:
    """Initialize MongoDB connection."""
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_uri)


async def close_db() -> None:
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        _client = None


def get_database() -> AsyncIOMotorDatabase:  # type: ignore[type-arg]
    """
    Get the database instance.

    Returns:
        AsyncIOMotorDatabase instance

    Raises:
        RuntimeError: If database is not connected
    """
    if _client is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _client[settings.database_name]


def get_client() -> AsyncIOMotorClient:  # type: ignore[type-arg]
    """
    Get the MongoDB client instance.

    Returns:
        AsyncIOMotorClient instance

    Raises:
        RuntimeError: If database is not connected
    """
    if _client is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _client

