"""
Integration tests for producer profile creation and updates.
"""

import pytest
from httpx import AsyncClient

from tests.integration.fixtures import (
    sample_formal_profile,
    sample_individual_profile,
    sample_informal_profile,
)
from tests.integration.helpers import create_producer_profile, create_user_and_get_token


@pytest.mark.asyncio
async def test_create_individual_profile_flow(client: AsyncClient) -> None:
    """Test complete flow: auth → create individual profile → get profile."""
    phone = "+5511444444444"  # Different phone to avoid conflicts
    headers = await create_user_and_get_token(client, phone)

    # Create profile
    profile = await create_producer_profile(client, headers, sample_individual_profile())

    # Verify profile data
    assert profile["producer_type"] == "individual"
    assert profile["name"] == sample_individual_profile()["name"]
    assert profile["cpf"] == sample_individual_profile()["cpf"]
    # CNPJ should be None or not present for individual profiles
    assert profile.get("cnpj") is None or "cnpj" not in profile
    assert profile.get("members") is None or "members" not in profile

    # Get profile
    get_response = await client.get("/producer-profile", headers=headers)
    assert get_response.status_code == 200
    retrieved_profile = get_response.json()
    assert retrieved_profile["_id"] == profile["_id"]
    assert retrieved_profile["name"] == profile["name"]


@pytest.mark.asyncio
async def test_create_formal_profile_flow(client: AsyncClient) -> None:
    """Test complete flow: auth → create formal profile → get profile."""
    phone = "+5511222222222"  # Different phone to avoid conflicts
    headers = await create_user_and_get_token(client, phone)

    # Create formal profile
    profile = await create_producer_profile(client, headers, sample_formal_profile())

    # Verify profile data
    assert profile["producer_type"] == "formal"
    assert profile["cnpj"] == sample_formal_profile()["cnpj"]
    # CPF should be None or not present for formal profiles
    assert profile.get("cpf") is None or "cpf" not in profile
    assert profile.get("members") is None or "members" not in profile

    # Get profile
    get_response = await client.get("/producer-profile", headers=headers)
    assert get_response.status_code == 200
    retrieved_profile = get_response.json()
    assert retrieved_profile["cnpj"] == profile["cnpj"]


@pytest.mark.asyncio
async def test_create_informal_profile_flow(client: AsyncClient) -> None:
    """Test complete flow: auth → create informal profile → get profile."""
    phone = "+5511333333333"  # Different phone to avoid conflicts
    headers = await create_user_and_get_token(client, phone)

    # Create informal profile
    profile = await create_producer_profile(client, headers, sample_informal_profile())

    # Verify profile data
    assert profile["producer_type"] == "informal"
    assert profile["cpf"] == sample_informal_profile()["cpf"]
    assert profile["members"] is not None
    assert len(profile["members"]) == 2
    # CNPJ should be None or not present for informal profiles
    assert profile.get("cnpj") is None or "cnpj" not in profile

    # Get profile
    get_response = await client.get("/producer-profile", headers=headers)
    assert get_response.status_code == 200
    retrieved_profile = get_response.json()
    assert len(retrieved_profile["members"]) == 2


@pytest.mark.asyncio
async def test_update_profile_flow(client: AsyncClient) -> None:
    """Test updating an existing profile."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Create initial profile
    initial_profile = await create_producer_profile(
        client, headers, sample_individual_profile()
    )
    assert initial_profile["city"] == "Exemplo"

    # Update profile
    updated_data = sample_individual_profile()
    updated_data["city"] = "Nova Cidade"
    updated_data["name"] = "Nome Atualizado"

    update_response = await client.put(
        "/producer-profile", json=updated_data, headers=headers
    )
    assert update_response.status_code == 200
    updated_profile = update_response.json()

    # Verify update
    assert updated_profile["_id"] == initial_profile["_id"]
    assert updated_profile["city"] == "Nova Cidade"
    assert updated_profile["name"] == "Nome Atualizado"


@pytest.mark.asyncio
async def test_profile_requires_auth(client: AsyncClient) -> None:
    """Test that profile endpoints require authentication."""
    # Try to get profile without auth
    response = await client.get("/producer-profile")
    assert response.status_code == 401

    # Try to create profile without auth
    response = await client.put(
        "/producer-profile", json=sample_individual_profile()
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_profile_validation_errors(client: AsyncClient) -> None:
    """Test profile validation errors."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Try to create formal profile without CNPJ
    invalid_data = sample_formal_profile()
    del invalid_data["cnpj"]

    response = await client.put("/producer-profile", json=invalid_data, headers=headers)
    assert response.status_code == 422

    # Try to create informal profile without members
    invalid_data = sample_informal_profile()
    del invalid_data["members"]

    response = await client.put("/producer-profile", json=invalid_data, headers=headers)
    assert response.status_code == 422
