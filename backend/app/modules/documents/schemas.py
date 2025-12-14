"""
Documents module schemas.
Pydantic models for document upload and management.

PNAE Reference:
- Envelope 01 contém documentos de habilitação do fornecedor
- Documentos variam conforme tipo de fornecedor (formal/informal/individual)
- Todos precisam de DAP/CAF (Declaração de Aptidão ao Pronaf)
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.shared.utils import PyObjectId


class DocumentType(str, Enum):
    """
    Types of documents for Envelope 01 (habilitação).

    Required documents vary by producer type:
    - All: DAP/CAF
    - Formal: CNPJ, estatuto, ata
    - Informal: CPFs dos membros
    - Individual: CPF, comprovante de residência
    """

    DAP_CAF = "dap_caf"  # Declaração de Aptidão ao Pronaf
    CPF = "cpf"
    CNPJ = "cnpj"
    PROOF_ADDRESS = "proof_address"  # Comprovante de endereço
    BANK_STATEMENT = "bank_statement"  # Dados bancários
    STATUTE = "statute"  # Estatuto social (cooperativas)
    MINUTES = "minutes"  # Ata de assembleia
    OTHER = "other"


# Request schemas
class PresignRequest(BaseModel):
    """Request for presigned upload URL."""

    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original filename",
    )
    content_type: str = Field(
        default="application/octet-stream",
        max_length=100,
        description="MIME type of the file",
    )


class PresignResponse(BaseModel):
    """Response with presigned URL for upload."""

    upload_url: str = Field(..., description="URL to upload the file")
    file_url: str = Field(..., description="URL where file will be accessible after upload")
    file_key: str = Field(..., description="Unique key to reference the file")


class DocumentCreate(BaseModel):
    """Request to create document metadata after upload."""

    doc_type: DocumentType = Field(..., description="Type of document")
    file_url: str = Field(..., description="URL where file was uploaded")
    file_key: str = Field(..., description="Unique key from presign response")
    original_filename: str = Field(..., min_length=1, max_length=255)


class DocumentResponse(BaseModel):
    """Document response."""

    id: PyObjectId = Field(..., alias="_id")
    user_id: PyObjectId
    doc_type: DocumentType
    file_url: str
    file_key: str
    original_filename: str
    uploaded_at: datetime
    ai_notes: str | None = Field(None, description="Notas geradas pela IA após validação")
    ai_validated: bool = Field(default=False, description="Se o documento foi validado pela IA")
    ai_confidence: str | None = Field(None, description="Nível de confiança da validação (high/medium/low)")

    model_config = {"populate_by_name": True}


class DocumentInDB(BaseModel):
    """Document as stored in MongoDB."""

    id: PyObjectId | None = Field(None, alias="_id")
    user_id: PyObjectId
    doc_type: DocumentType
    file_url: str
    file_key: str
    original_filename: str
    uploaded_at: datetime
    ai_notes: str | None = None
    ai_validated: bool = False
    ai_confidence: str | None = None

    model_config = {"populate_by_name": True}


# DocumentListResponse is now replaced by PaginatedResponse[DocumentResponse]
# from app.shared.pagination import PaginatedResponse

