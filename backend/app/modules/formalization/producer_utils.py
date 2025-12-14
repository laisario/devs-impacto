"""Utility functions for producer type checking."""

INDIVIDUAL_PRODUCER_TYPES = {"individual", "produtor individual"}
FORMAL_PRODUCER_TYPES = {"formal (cnpj)", "formal", "grupo formal (cnpj)"}
INFORMAL_PRODUCER_TYPES = {"informal", "grupo informal"}


def normalize_producer_type(producer_type: str | None) -> str:
    """Normalize producer type string to lowercase."""
    if not producer_type:
        return ""
    return producer_type.lower().strip()


def is_individual_producer(producer_type: str | None) -> bool:
    """Check if producer type is individual."""
    normalized = normalize_producer_type(producer_type)
    return normalized in INDIVIDUAL_PRODUCER_TYPES


def is_formal_producer(producer_type: str | None) -> bool:
    """Check if producer type is formal (has CNPJ)."""
    normalized = normalize_producer_type(producer_type)
    return normalized in FORMAL_PRODUCER_TYPES


def is_informal_producer(producer_type: str | None) -> bool:
    """Check if producer type is informal group."""
    normalized = normalize_producer_type(producer_type)
    return normalized in INFORMAL_PRODUCER_TYPES
