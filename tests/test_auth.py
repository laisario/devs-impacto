"""
Tests for auth module.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_start_returns_ok(client: AsyncClient) -> None:
    """POST /auth/start should return ok: true."""
    response = await client.post(
        "/auth/start",
        json={"phone_e164": "+5511999999999"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "message" in data


@pytest.mark.asyncio
async def test_auth_start_invalid_phone(client: AsyncClient) -> None:
    """POST /auth/start with invalid phone should return 422."""
    response = await client.post(
        "/auth/start",
        json={"phone_e164": "invalid"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_auth_verify_returns_token(client: AsyncClient) -> None:
    """POST /auth/verify with correct OTP should return JWT token."""
    phone = "+5511888888888"

    # Start auth first
    await client.post("/auth/start", json={"phone_e164": phone})

    # Verify with mock OTP (123456)
    response = await client.post(
        "/auth/verify",
        json={"phone_e164": phone, "otp": "123456"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_auth_verify_wrong_otp(client: AsyncClient) -> None:
    """POST /auth/verify with wrong OTP should return 401."""
    phone = "+5511777777777"

    # Start auth first
    await client.post("/auth/start", json={"phone_e164": phone})

    # Verify with wrong OTP
    response = await client.post(
        "/auth/verify",
        json={"phone_e164": phone, "otp": "000000"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """GET /auth/me with valid token should return user data."""
    response = await client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "_id" in data
    assert data["phone_e164"] == "+5511999999999"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient) -> None:
    """GET /auth/me without token should return 401."""
    response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token(client: AsyncClient) -> None:
    """GET /auth/me with invalid token should return 401."""
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401

