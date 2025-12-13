"""
Calls module schemas.
Pydantic models for calls for proposals (Chamadas Públicas).

PNAE Reference:
- Chamada Pública é o instrumento para aquisição de gêneros alimentícios
  da agricultura familiar (Art. 24 - dispensa de licitação)
- Entidade Executora: Prefeitura, Secretaria de Educação, etc.
- Produtos listados com preços máximos definidos no edital
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.shared.utils import PyObjectId


class CallStatus(str, Enum):
    """Status of a call for proposals."""

    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"


class CallProduct(BaseModel):
    """
    Product available in the call for proposals.

    Represents items that producers can offer in their Projeto de Venda.
    """

    name: str = Field(..., min_length=2, max_length=200, description="Nome do produto")
    unit: str = Field(
        ...,
        max_length=20,
        description="Unidade de medida (kg, unidade, litro, etc.)",
    )
    quantity: float = Field(..., gt=0, description="Quantidade solicitada")
    unit_price: float = Field(
        ...,
        gt=0,
        description="Preço unitário máximo definido no edital (R$)",
    )


class CallForProposalBase(BaseModel):
    """Base fields for call for proposals."""

    number: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Número da chamada pública (ex: CP 001/2025)",
    )
    entity_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Nome da entidade executora (Prefeitura, Secretaria, etc.)",
    )
    entity_cnpj: str = Field(
        ...,
        pattern=r"^\d{14}$",
        description="CNPJ da entidade executora (14 dígitos)",
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Descrição/objeto da chamada pública",
    )
    products: list[CallProduct] = Field(
        ...,
        min_length=1,
        description="Lista de produtos disponíveis para oferta",
    )
    delivery_schedule: str = Field(
        ...,
        max_length=500,
        description="Cronograma de entrega previsto",
    )
    submission_deadline: datetime = Field(
        ...,
        description="Prazo para submissão de propostas",
    )


class CallForProposalCreate(CallForProposalBase):
    """Schema for creating a call for proposals."""

    status: CallStatus = Field(
        default=CallStatus.DRAFT,
        description="Status inicial da chamada",
    )


class CallForProposalResponse(CallForProposalBase):
    """Schema for call for proposals response."""

    id: PyObjectId = Field(..., alias="_id")
    status: CallStatus
    created_at: datetime

    model_config = {"populate_by_name": True}


class CallForProposalInDB(CallForProposalBase):
    """Call for proposals as stored in MongoDB."""

    id: PyObjectId | None = Field(None, alias="_id")
    status: CallStatus
    created_at: datetime

    model_config = {"populate_by_name": True}


# CallListResponse is now replaced by PaginatedResponse[CallForProposalResponse]
# from app.shared.pagination import PaginatedResponse

