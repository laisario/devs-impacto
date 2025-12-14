"""
Pytest configuration and fixtures for PNAE Backend tests.
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.main import app

# Use a separate test database
TEST_DATABASE_NAME = f"{settings.database_name}_test"


@pytest.fixture
async def mongo_client() -> AsyncGenerator[AsyncIOMotorClient[Any], None]:
    """Create MongoDB client for tests."""
    client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(settings.mongodb_uri)
    yield client
    client.close()


@pytest.fixture(autouse=True)
async def setup_test_db(
    mongo_client: AsyncIOMotorClient[Any],
) -> AsyncGenerator[None, None]:
    """
    Set up test database before each test.

    - Drops and recreates test database
    - Patches get_database to use test database
    """
    import app.core.db as db_module

    # Set up the client
    db_module._client = mongo_client

    # Drop test database before each test
    await mongo_client.drop_database(TEST_DATABASE_NAME)

    # Patch get_database to return test database
    original_get_database = db_module.get_database

    def get_test_database() -> Any:
        if db_module._client is None:
            raise RuntimeError("Database not connected")
        return db_module._client[TEST_DATABASE_NAME]

    db_module.get_database = get_test_database

    yield

    # Restore original function
    db_module.get_database = original_get_database

    # Clean up test database
    await mongo_client.drop_database(TEST_DATABASE_NAME)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """
    Get authentication headers for a test user.

    Creates a user and returns Authorization header with JWT token.
    """
    phone = "+5511999999999"

    # Start auth
    await client.post("/auth/start", json={"phone_e164": phone})

    # Verify with mock OTP
    response = await client.post(
        "/auth/verify",
        json={"phone_e164": phone, "otp": "123456"},
    )
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def sample_producer_profile(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> dict[str, Any]:
    """Create a sample producer profile."""
    profile_data = {
        "producer_type": "individual",
        "name": "João da Silva",
        "address": "Sítio Boa Vista, s/n",
        "city": "Exemplo",
        "state": "SP",
        "dap_caf_number": "DAP123456789",
        "cpf": "12345678901",
    }

    response = await client.put("/producer-profile", json=profile_data, headers=auth_headers)
    return response.json()

