"""
Sales Project module schemas.
Pydantic models for sales project generation and management.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.shared.utils import PyObjectId


class SalesProjectDraftRequest(BaseModel):
    """Request for generating a sales project draft with AI."""

    edital_id: str | None = Field(
        None, description="ID do edital específico (opcional)"
    )
    custom_requirements: dict[str, Any] | None = Field(
        None, description="Requisitos específicos do edital (opcional)"
    )


class ProductItem(BaseModel):
    """Product item in sales project."""

    name: str = Field(..., description="Nome do produto")
    unit: str = Field(..., description="Unidade (kg, litro, unidade)")
    quantity: float = Field(..., ge=0, description="Quantidade")
    unit_price: float = Field(..., ge=0, description="Preço unitário")
    total_price: float = Field(..., ge=0, description="Preço total")
    delivery_frequency: str = Field(
        ..., description="Frequência de entrega (semanal, quinzenal, mensal)"
    )


class DeliverySchedule(BaseModel):
    """Delivery schedule for sales project."""

    # Monthly delivery data
    february: dict[str, Any] | None = None
    march: dict[str, Any] | None = None
    april: dict[str, Any] | None = None
    may: dict[str, Any] | None = None
    june: dict[str, Any] | None = None
    july: dict[str, Any] | None = None
    august: dict[str, Any] | None = None
    september: dict[str, Any] | None = None
    october: dict[str, Any] | None = None
    november: dict[str, Any] | None = None


class SalesProjectCreate(BaseModel):
    """Create a sales project (after AI generation or manual creation)."""

    edital_id: str | None = None
    products: list[ProductItem]
    delivery_schedule: dict[str, Any]  # DeliverySchedule as dict
    total_value: float = Field(..., ge=0)
    notes: str | None = None


class SalesProjectResponse(BaseModel):
    """Sales project response."""

    id: str = Field(..., alias="_id")
    user_id: PyObjectId
    edital_id: str | None = None
    products: list[dict[str, Any]] = Field(..., description="Lista de produtos")
    delivery_schedule: dict[str, Any] = Field(..., description="Cronograma de entrega")
    total_value: float = Field(..., ge=0, description="Valor total do projeto")
    ai_generated: bool = Field(default=False, description="Se foi gerado por IA")
    notes: str | None = Field(None, description="Observações")
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class SalesProjectInDB(BaseModel):
    """Sales project as stored in MongoDB."""

    id: PyObjectId | None = Field(None, alias="_id")
    user_id: PyObjectId
    edital_id: str | None = None
    products: list[dict[str, Any]]
    delivery_schedule: dict[str, Any]
    total_value: float
    ai_generated: bool = False
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}
