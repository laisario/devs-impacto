"""
Test fixtures and data factories for integration tests.
"""

from typing import Any

import pytest
from httpx import AsyncClient


def sample_phone() -> str:
    """Sample phone number for testing."""
    return "+5511999999999"


def sample_phone_2() -> str:
    """Second sample phone number for testing."""
    return "+5511888888888"


def sample_individual_profile() -> dict[str, Any]:
    """Sample individual producer profile data."""
    return {
        "producer_type": "individual",
        "name": "João da Silva",
        "address": "Sítio Boa Vista, s/n, Zona Rural",
        "city": "Exemplo",
        "state": "SP",
        "dap_caf_number": "DAP123456789",
        "cpf": "12345678901",
        "bank_name": "Banco do Brasil",
        "bank_agency": "1234-5",
        "bank_account": "12345-6",
    }


def sample_formal_profile() -> dict[str, Any]:
    """Sample formal (cooperative) producer profile data."""
    return {
        "producer_type": "formal",
        "name": "Cooperativa Agrícola do Vale",
        "address": "Rua das Flores, 123",
        "city": "São Paulo",
        "state": "SP",
        "dap_caf_number": "DAP-123456",
        "cnpj": "12345678000190",
        "bank_name": "Banco do Brasil",
        "bank_agency": "1234-5",
        "bank_account": "12345-6",
    }


def sample_informal_profile() -> dict[str, Any]:
    """Sample informal (group) producer profile data."""
    return {
        "producer_type": "informal",
        "name": "Grupo de Agricultores Familiares",
        "address": "Estrada Rural, Km 5",
        "city": "Campinas",
        "state": "SP",
        "dap_caf_number": "DAP-789012",
        "cpf": "12345678901",
        "members": [
            {
                "name": "João Silva",
                "cpf": "12345678901",
                "dap_caf_number": "DAP-789012",
            },
            {
                "name": "Maria Santos",
                "cpf": "98765432109",
                "dap_caf_number": "DAP-789013",
            },
        ],
        "bank_name": "Caixa Econômica",
        "bank_agency": "5678",
        "bank_account": "98765-4",
    }


@pytest.fixture
async def authenticated_client(
    client: AsyncClient, sample_phone: str
) -> tuple[AsyncClient, dict[str, str]]:
    """
    Create an authenticated client with auth headers.

    Returns:
        Tuple of (client, auth_headers)
    """
    # Start auth
    await client.post("/auth/start", json={"phone_e164": sample_phone})

    # Verify with mock OTP
    response = await client.post(
        "/auth/verify",
        json={"phone_e164": sample_phone, "otp": "123456"},
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return client, headers
