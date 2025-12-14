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
        self, query_text: str, limit: int = 15
    ) -> list[RAGChunk]:
        """
        Search for relevant chunks by requirement ID or text query.

        Enhanced search that:
        - Returns more chunks (default 15 instead of 5)
        - Prioritizes chunks with exact requirement_id match
        - Includes related chunks by topic
        - Supports text search for location-specific queries

        Args:
            query_text: The requirement ID or text to search for
            limit: Maximum number of chunks to return (default: 15)

        Returns:
            List of relevant RAG chunks
        """
        # First, try to find chunks by requirement_id (exact match)
        query = {"applies_to": query_text}

        cursor = self.collection.find(query).limit(limit).sort("created_at", -1)
        chunks = []
        async for doc in cursor:
            chunks.append(RAGChunk(**doc))
        
        # If we have fewer chunks than limit, try text search
        if len(chunks) < limit:
            # Try text search in content (case-insensitive)
            text_query = {
                "$or": [
                    {"content": {"$regex": query_text, "$options": "i"}},
                    {"topic": {"$regex": query_text, "$options": "i"}},
                ],
                "applies_to": {"$ne": query_text}  # Exclude already found chunks
            }
            text_cursor = self.collection.find(text_query).limit(limit - len(chunks))
            async for doc in text_cursor:
                chunks.append(RAGChunk(**doc))
        
        # If we still have fewer chunks, try to get related chunks by topic
        if len(chunks) < limit:
            # Get topics from found chunks
            topics = {chunk.topic for chunk in chunks if chunk.topic}
            
            # Search for chunks with related topics
            if topics:
                related_query = {
                    "topic": {"$in": list(topics)},
                    "applies_to": {"$ne": query_text}  # Exclude already found chunks
                }
                related_cursor = self.collection.find(related_query).limit(limit - len(chunks))
                async for doc in related_cursor:
                    chunks.append(RAGChunk(**doc))
        
        return chunks[:limit]

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
