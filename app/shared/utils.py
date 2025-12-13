"""
Shared utilities for the PNAE API.
"""

from datetime import UTC, datetime
from typing import Annotated, Any

from bson import ObjectId
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema


class _ObjectIdPydanticAnnotation:
    """
    Custom Pydantic annotation for MongoDB ObjectId.

    Implements proper schema generation for Pydantic v2.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Generate Pydantic core schema for ObjectId."""

        def validate_object_id(value: Any) -> ObjectId:
            if isinstance(value, ObjectId):
                return value
            if isinstance(value, str) and ObjectId.is_valid(value):
                return ObjectId(value)
            raise ValueError(f"Invalid ObjectId: {value}")

        return core_schema.no_info_plain_validator_function(
            validate_object_id,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        """Generate JSON schema for OpenAPI documentation."""
        return {"type": "string", "description": "MongoDB ObjectId"}


# Pydantic type for MongoDB ObjectId
PyObjectId = Annotated[ObjectId, _ObjectIdPydanticAnnotation]


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


def validate_object_id(value: Any) -> ObjectId:
    """
    Validate and convert a value to ObjectId.

    Args:
        value: String or ObjectId to validate

    Returns:
        Valid ObjectId

    Raises:
        ValueError: If value is not a valid ObjectId
    """
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    raise ValueError(f"Invalid ObjectId: {value}")


def to_object_id(value: str | ObjectId) -> ObjectId:
    """
    Convert string to ObjectId.

    Args:
        value: String or ObjectId

    Returns:
        ObjectId instance

    Raises:
        ValueError: If value is not a valid ObjectId string
    """
    if isinstance(value, ObjectId):
        return value
    if not ObjectId.is_valid(value):
        raise ValueError(f"Invalid ObjectId string: {value}")
    return ObjectId(value)

