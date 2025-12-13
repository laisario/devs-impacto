"""
Tests for producers module.
"""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_producer_profile_individual(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """PUT /producer-profile should create profile for individual producer."""
    profile_data = {
        "producer_type": "individual",
        "name": "Maria Santos",
        "address": "Fazenda Santa Maria, km 5",
        "city": "Campinas",
        "state": "SP",
        "dap_caf_number": "DAP987654321",
        "cpf": "98765432100",
    }

    response = await client.put(
        "/producer-profile",
        json=profile_data,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Maria Santos"
    assert data["producer_type"] == "individual"
    assert data["cpf"] == "98765432100"
    assert "_id" in data


@pytest.mark.asyncio
async def test_create_producer_profile_formal(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """PUT /producer-profile should create profile for formal producer (cooperativa)."""
    profile_data = {
        "producer_type": "formal",
        "name": "Cooperativa Agricultores Unidos",
        "address": "Rua Principal, 100",
        "city": "Ribeirão Preto",
        "state": "SP",
        "dap_caf_number": "DAP111222333",
        "cnpj": "12345678000195",
    }

    response = await client.put(
        "/producer-profile",
        json=profile_data,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["producer_type"] == "formal"
    assert data["cnpj"] == "12345678000195"


@pytest.mark.asyncio
async def test_create_producer_profile_informal(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """PUT /producer-profile should create profile for informal group."""
    profile_data = {
        "producer_type": "informal",
        "name": "Grupo Familiar Boa Esperança",
        "address": "Comunidade Rural, s/n",
        "city": "Piracicaba",
        "state": "SP",
        "dap_caf_number": "DAP444555666",
        "cpf": "11122233344",  # Representative's CPF
        "members": [
            {"name": "José Silva", "cpf": "11122233344", "dap_caf_number": "DAP001"},
            {"name": "Ana Silva", "cpf": "22233344455", "dap_caf_number": "DAP002"},
        ],
    }

    response = await client.put(
        "/producer-profile",
        json=profile_data,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["producer_type"] == "informal"
    assert len(data["members"]) == 2


@pytest.mark.asyncio
async def test_create_producer_profile_validation_error_formal_without_cnpj(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """PUT /producer-profile formal without CNPJ should return 422."""
    profile_data = {
        "producer_type": "formal",
        "name": "Cooperativa Sem CNPJ",
        "address": "Rua X, 1",
        "city": "Cidade",
        "state": "SP",
        "dap_caf_number": "DAP123",
        # Missing cnpj
    }

    response = await client.put(
        "/producer-profile",
        json=profile_data,
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_producer_profile_validation_error_individual_without_cpf(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """PUT /producer-profile individual without CPF should return 422."""
    profile_data = {
        "producer_type": "individual",
        "name": "Produtor Sem CPF",
        "address": "Rua Y, 2",
        "city": "Cidade",
        "state": "SP",
        "dap_caf_number": "DAP456",
        # Missing cpf
    }

    response = await client.put(
        "/producer-profile",
        json=profile_data,
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_producer_profile(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_producer_profile: dict[str, Any],
) -> None:
    """GET /producer-profile should return the user's profile."""
    response = await client.get("/producer-profile", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_producer_profile["name"]


@pytest.mark.asyncio
async def test_get_producer_profile_not_found(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /producer-profile without profile should return 404."""
    # Note: This test assumes no profile was created yet in this test
    # We need a fresh auth token for a user without profile
    phone = "+5511666666666"

    await client.post("/auth/start", json={"phone_e164": phone})
    response = await client.post(
        "/auth/verify",
        json={"phone_e164": phone, "otp": "123456"},
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/producer-profile", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_producer_profile(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_producer_profile: dict[str, Any],
) -> None:
    """PUT /producer-profile should update existing profile."""
    # Update the profile
    updated_data = {
        "producer_type": "individual",
        "name": "João da Silva Atualizado",
        "address": "Novo Endereço, 123",
        "city": "Nova Cidade",
        "state": "MG",
        "dap_caf_number": "DAP123456789",
        "cpf": "12345678901",
    }

    response = await client.put(
        "/producer-profile",
        json=updated_data,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "João da Silva Atualizado"
    assert data["city"] == "Nova Cidade"
    # Same _id (upsert)
    assert data["_id"] == sample_producer_profile["_id"]


@pytest.mark.asyncio
async def test_get_producer_profile_by_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_producer_profile: dict[str, Any],
) -> None:
    """GET /producer-profile/{id} should return the profile."""
    profile_id = sample_producer_profile["_id"]

    response = await client.get(f"/producer-profile/{profile_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == profile_id
    assert data["name"] == sample_producer_profile["name"]


@pytest.mark.asyncio
async def test_get_producer_profile_by_id_not_found(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /producer-profile/{id} with invalid ID should return 404."""
    fake_id = "507f1f77bcf86cd799439011"

    response = await client.get(f"/producer-profile/{fake_id}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_producer_profile_by_id_without_auth(client: AsyncClient) -> None:
    """GET /producer-profile/{id} without auth should return 401."""
    fake_id = "507f1f77bcf86cd799439011"

    response = await client.get(f"/producer-profile/{fake_id}")

    assert response.status_code == 401

