"""
Pagination utilities for the PNAE API.
"""

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    skip: int = 0
    limit: int = 20

    @classmethod
    def from_query(
        cls,
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    ) -> "PaginationParams":
        """Create pagination params from query parameters."""
        return cls(skip=skip, limit=limit)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        pagination: PaginationParams,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response from items and pagination params."""
        return cls(
            items=items,
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
            has_more=pagination.skip + len(items) < total,
        )

