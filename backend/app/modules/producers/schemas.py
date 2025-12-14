"""
Producers module schemas.
Pydantic models for producer profile with validation by producer type.

PNAE Reference:
- Fornecedores podem ser: Formal (Cooperativa/Associação), Informal (Grupo), ou Individual
- Cada tipo requer documentação específica para Envelope 01 (habilitação)
- DAP/CAF é obrigatório para todos os tipos de fornecedores da agricultura familiar
"""

from datetime import datetime
from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.modules.onboarding.schemas import OnboardingStatus
from app.shared.utils import PyObjectId


class ProducerType(str, Enum):
    """
    Type of producer/supplier for PNAE.

    - FORMAL: Cooperativa ou Associação (possui CNPJ)
    - INFORMAL: Grupo informal de agricultores (lista de CPFs)
    - INDIVIDUAL: Agricultor familiar individual
    """

    FORMAL = "formal"
    INFORMAL = "informal"
    INDIVIDUAL = "individual"


class Member(BaseModel):
    """Member of an informal group."""

    name: str = Field(..., min_length=1, max_length=200)
    cpf: str = Field(..., pattern=r"^\d{11}$", description="CPF sem pontuação (11 dígitos)")
    dap_caf_number: str | None = Field(
        None, max_length=50, description="Número da DAP/CAF do membro"
    )


class ProducerProfileBase(BaseModel):
    """Base fields for producer profile."""

    producer_type: ProducerType = Field(..., description="Tipo de fornecedor")
    name: str = Field(..., min_length=1, max_length=200, description="Nome/Razão social")
    address: str = Field(..., min_length=1, max_length=500, description="Endereço completo")
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2, description="UF (2 letras)")

    # DAP/CAF é obrigatório para todos - Declaração de Aptidão ao Pronaf
    # Mas pode ser None temporariamente durante onboarding
    dap_caf_number: str | None = Field(
        None,
        max_length=50,
        description="Número da DAP (Declaração de Aptidão ao Pronaf) ou CAF",
    )

    # Campos condicionais por tipo
    cnpj: str | None = Field(
        None,
        pattern=r"^\d{14}$",
        description="CNPJ sem pontuação (obrigatório para tipo formal)",
    )
    cpf: str | None = Field(
        None,
        pattern=r"^\d{11}$",
        description="CPF sem pontuação (obrigatório para individual/informal)",
    )
    members: list[Member] | None = Field(
        None, description="Membros do grupo (obrigatório para tipo informal)"
    )

    # Dados bancários para pagamento
    bank_name: str | None = Field(None, max_length=100)
    bank_agency: str | None = Field(None, max_length=20)
    bank_account: str | None = Field(None, max_length=30)

    @model_validator(mode="after")
    def validate_by_producer_type(self) -> Self:
        """
        Validate required fields based on producer type.

        - FORMAL: requires CNPJ
        - INFORMAL: requires CPF (representante) and members list
        - INDIVIDUAL: requires CPF
        
        Note: DAP/CAF is optional during onboarding, can be added later.
        """
        if self.producer_type == ProducerType.FORMAL:
            if not self.cnpj:
                raise ValueError("CNPJ é obrigatório para fornecedor formal")

        elif self.producer_type == ProducerType.INFORMAL:
            # CPF comes from login/auth, not required here
            # Members list is optional during onboarding
            pass

        elif self.producer_type == ProducerType.INDIVIDUAL:
            # CPF comes from login/auth, not required here
            pass

        # DAP/CAF is optional - can be added later
        # We don't validate it here to allow profile creation during onboarding

        return self


class ProducerProfileCreate(ProducerProfileBase):
    """Schema for creating/updating producer profile."""

    pass


class ProducerProfileResponse(ProducerProfileBase):
    """Schema for producer profile response."""

    id: PyObjectId = Field(..., alias="_id")
    user_id: PyObjectId
    created_at: datetime
    updated_at: datetime

    # Onboarding fields (optional, added by onboarding module)
    onboarding_status: OnboardingStatus | None = Field(
        None, description="Status do processo de onboarding"
    )
    onboarding_completed_at: datetime | None = Field(
        None, description="Data de conclusão do onboarding"
    )

    model_config = {"populate_by_name": True}


class ProducerProfileInDB(ProducerProfileBase):
    """Producer profile as stored in MongoDB."""

    id: PyObjectId | None = Field(None, alias="_id")
    user_id: PyObjectId
    created_at: datetime
    updated_at: datetime

    # Onboarding fields (optional, added by onboarding module)
    onboarding_status: OnboardingStatus | None = Field(
        None, description="Status do processo de onboarding"
    )
    onboarding_completed_at: datetime | None = Field(
        None, description="Data de conclusão do onboarding"
    )

    model_config = {"populate_by_name": True}

