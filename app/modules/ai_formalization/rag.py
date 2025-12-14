"""
RAG (Retrieval-Augmented Generation) service.
Handles document chunks, embeddings, and similarity search.
"""

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.config import settings
from app.shared.utils import utc_now


class RAGChunk(BaseModel):
    """Model for a RAG document chunk."""

    id: Any | None = Field(None, alias="_id")
    content: str = Field(..., description="Text content of the chunk")
    topic: str = Field(..., description="Topic/category of the chunk")
    applies_to: list[str] = Field(
        ..., description="List of requirement IDs this chunk applies to"
    )
    source: str = Field(..., description="Source document/file name")
    page: int | None = Field(None, description="Page number in source document")
    embedding: list[float] | None = Field(None, description="Embedding vector")
    created_at: datetime = Field(default_factory=utc_now)

    model_config = {"populate_by_name": True}


class RAGService:
    """Service for RAG operations (chunk storage and retrieval)."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.collection = db.rag_chunks

    async def add_chunks(self, chunks: list[RAGChunk]) -> None:
        """
        Add chunks to the RAG store.

        Args:
            chunks: List of RAG chunks to add
        """
        if not chunks:
            return

        documents = []
        for chunk in chunks:
            doc = chunk.model_dump(exclude={"id"}, exclude_none=True)
            documents.append(doc)

        if documents:
            await self.collection.insert_many(documents)

    async def search_relevant_chunks(
        self, requirement_id: str, limit: int = 5
    ) -> list[RAGChunk]:
        """
        Search for relevant chunks by requirement ID.

        Args:
            requirement_id: The requirement ID to search for
            limit: Maximum number of chunks to return (default: 5)

        Returns:
            List of relevant RAG chunks
        """
        # Filter chunks where applies_to array contains the requirement_id
        # MongoDB automatically matches array fields with direct value
        query = {"applies_to": requirement_id}

        cursor = self.collection.find(query).limit(limit)
        chunks = []
        async for doc in cursor:
            chunks.append(RAGChunk(**doc))

        return chunks

    async def search_by_topic(self, topic: str, limit: int = 5) -> list[RAGChunk]:
        """
        Search for chunks by topic.

        Args:
            topic: The topic to search for
            limit: Maximum number of chunks to return

        Returns:
            List of chunks with the specified topic
        """
        query = {"topic": topic}
        cursor = self.collection.find(query).limit(limit)
        chunks = []
        async for doc in cursor:
            chunks.append(RAGChunk(**doc))

        return chunks

    async def get_all_chunks(self) -> list[RAGChunk]:
        """
        Get all chunks (for debugging/admin purposes).

        Returns:
            List of all chunks
        """
        cursor = self.collection.find()
        chunks = []
        async for doc in cursor:
            chunks.append(RAGChunk(**doc))

        return chunks


async def generate_embedding(text: str) -> list[float]:
    """
    Generate embedding for text using OpenAI.

    Args:
        text: Text to generate embedding for

    Returns:
        Embedding vector as list of floats
    """
    try:
        from openai import AsyncOpenAI
    except ImportError:
        # If OpenAI not available, return empty embedding
        return []

    api_key = getattr(settings, "openai_api_key", None)
    if not api_key:
        return []

    model = getattr(settings, "rag_embedding_model", "text-embedding-3-small")

    client = AsyncOpenAI(api_key=api_key)
    response = await client.embeddings.create(
        model=model,
        input=text,
    )

    return response.data[0].embedding
