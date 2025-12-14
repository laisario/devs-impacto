"""
Integration tests for complete authentication flow.
"""

import pytest
from httpx import AsyncClient

from tests.integration.helpers import create_user_and_get_token


@pytest.mark.asyncio
async def test_complete_auth_flow(client: AsyncClient) -> None:
    """Test complete authentication flow: start → verify → get user."""
    phone = "+5511999999999"

    # Step 1: Start authentication
    start_response = await client.post("/auth/start", json={"phone_e164": phone})
    assert start_response.status_code == 200
    assert start_response.json()["ok"] is True

    # Step 2: Verify OTP
    verify_response = await client.post(
        "/auth/verify",
        json={"phone_e164": phone, "otp": "123456"},
    )
    assert verify_response.status_code == 200
    token_data = verify_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # Step 3: Get current user
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["phone_e164"] == phone
    assert "_id" in user_data


@pytest.mark.asyncio
async def test_auth_flow_with_wrong_otp(client: AsyncClient) -> None:
    """Test authentication flow with wrong OTP."""
    phone = "+5511888888888"

    # Start auth
    await client.post("/auth/start", json={"phone_e164": phone})

    # Try wrong OTP
    verify_response = await client.post(
        "/auth/verify",
        json={"phone_e164": phone, "otp": "000000"},
    )
    assert verify_response.status_code == 401

    # Verify we can't access protected endpoints
    me_response = await client.get("/auth/me")
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_auth_token_persistence(client: AsyncClient) -> None:
    """Test that auth token works across multiple requests."""
    phone = "+5511777777777"
    headers = await create_user_and_get_token(client, phone)

    # Make multiple authenticated requests
    for _ in range(3):
        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["phone_e164"] == phone


@pytest.mark.asyncio
async def test_multiple_users_auth(client: AsyncClient) -> None:
    """Test authentication for multiple different users."""
    phone1 = "+5511111111111"
    phone2 = "+5511222222222"

    # Create two users
    headers1 = await create_user_and_get_token(client, phone1)
    headers2 = await create_user_and_get_token(client, phone2)

    # Verify each user gets their own data
    user1_response = await client.get("/auth/me", headers=headers1)
    user2_response = await client.get("/auth/me", headers=headers2)

    assert user1_response.status_code == 200
    assert user2_response.status_code == 200

    user1_data = user1_response.json()
    user2_data = user2_response.json()

    assert user1_data["phone_e164"] == phone1
    assert user2_data["phone_e164"] == phone2
    assert user1_data["_id"] != user2_data["_id"]
