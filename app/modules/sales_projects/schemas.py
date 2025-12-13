"""
Sales Projects module schemas.
Pydantic models for Projeto de Venda (Envelope 02).

PNAE Reference:
- Projeto de Venda é o documento que o fornecedor submete em resposta à Chamada Pública
- Contém: identificação da proposta, do fornecedor, da entidade executora
- Relação de produtos com quantidade, preço e cronograma de entrega
- Deve seguir formato padronizado para facilitar análise
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field

from app.shared.utils import PyObjectId


class ProjectStatus(str, Enum):
    """Status of a sales project."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


class ProjectItem(BaseModel):
    """
    Item in the sales project.

    Represents a product the producer is offering to supply.
    """

    product_name: str = Field(..., min_length=2, max_length=200)
    unit: str = Field(..., max_length=20, description="Unidade (kg, unidade, litro)")
    quantity: float = Field(..., gt=0, description="Quantidade ofertada")
    unit_price: float = Field(..., gt=0, description="Preço unitário (R$)")
    delivery_schedule: str = Field(
        ...,
        max_length=200,
        description="Cronograma de entrega (ex: Março/2025, Abril/2025)",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> float:
        """Calculate total value for this item."""
        return round(self.quantity * self.unit_price, 2)


class SalesProjectCreate(BaseModel):
    """Schema for creating a sales project."""

    call_id: str = Field(..., description="ID da chamada pública vinculada")
    items: list[ProjectItem] = Field(
        ...,
        min_length=1,
        description="Lista de itens/produtos ofertados",
    )


class SalesProjectResponse(BaseModel):
    """Schema for sales project response."""

    id: PyObjectId = Field(..., alias="_id")
    user_id: PyObjectId
    call_id: PyObjectId
    producer_profile_id: PyObjectId
    items: list[ProjectItem]
    total_value: float
    status: ProjectStatus
    generated_pdf_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class SalesProjectInDB(BaseModel):
    """Sales project as stored in MongoDB."""

    id: PyObjectId | None = Field(None, alias="_id")
    user_id: PyObjectId
    call_id: PyObjectId
    producer_profile_id: PyObjectId
    items: list[ProjectItem]
    total_value: float
    status: ProjectStatus
    generated_pdf_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class GeneratePdfResponse(BaseModel):
    """Response after generating PDF."""

    pdf_url: str = Field(..., description="URL do PDF gerado")
    message: str = "PDF gerado com sucesso"


# Extended response with related data for PDF generation
class SalesProjectWithDetails(BaseModel):
    """Sales project with expanded call and producer data."""

    project: SalesProjectInDB
    call_number: str
    call_entity_name: str
    call_entity_cnpj: str
    producer_name: str
    producer_type: str
    producer_document: str  # CNPJ or CPF
    producer_dap_caf: str
    producer_address: str
    producer_city: str
    producer_state: str

