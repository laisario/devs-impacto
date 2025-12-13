"""
Tests for calls module.
"""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_call(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """POST /calls should create a new call for proposals."""
    call_data = {
        "number": "CP 002/2025",
        "entity_name": "Secretaria Municipal de Educação",
        "entity_cnpj": "98765432000188",
        "description": "Aquisição de frutas e verduras para merenda escolar",
        "products": [
            {
                "name": "Banana",
                "unit": "kg",
                "quantity": 500,
                "unit_price": 4.00,
            },
            {
                "name": "Maçã",
                "unit": "kg",
                "quantity": 300,
                "unit_price": 6.50,
            },
        ],
        "delivery_schedule": "Entregas quinzenais",
        "submission_deadline": "2025-06-30T18:00:00",
    }

    response = await client.post("/calls", json=call_data, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["number"] == "CP 002/2025"
    assert len(data["products"]) == 2
    assert data["status"] == "draft"
    assert "_id" in data


@pytest.mark.asyncio
async def test_list_calls(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_call: dict[str, Any],
) -> None:
    """GET /calls should return paginated list of calls."""
    response = await client.get("/calls")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_list_calls_with_pagination(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /calls should support pagination parameters."""
    # Create multiple calls
    for i in range(5):
        call_data = {
            "number": f"CP 00{i}/2025",
            "entity_name": f"Entidade {i}",
            "entity_cnpj": f"1234567800019{i}",
            "description": f"Descrição {i}",
            "products": [{"name": "Produto", "unit": "kg", "quantity": 10, "unit_price": 1.0}],
            "delivery_schedule": "Semanal",
            "submission_deadline": "2025-12-31T23:59:59",
        }
        await client.post("/calls", json=call_data, headers=auth_headers)

    # Test pagination
    response = await client.get("/calls?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_get_call_by_id(
    client: AsyncClient,
    sample_call: dict[str, Any],
) -> None:
    """GET /calls/{id} should return specific call."""
    call_id = sample_call["_id"]

    response = await client.get(f"/calls/{call_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == call_id
    assert data["number"] == sample_call["number"]


@pytest.mark.asyncio
async def test_get_call_not_found(client: AsyncClient) -> None:
    """GET /calls/{id} with invalid ID should return 404."""
    fake_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format but doesn't exist

    response = await client.get(f"/calls/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_calls_filter_by_status(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /calls?status=open should filter by status."""
    # Create a call with specific status
    call_data = {
        "number": "CP OPEN/2025",
        "entity_name": "Entidade Open",
        "entity_cnpj": "11111111000111",
        "description": "Chamada aberta",
        "products": [{"name": "Produto", "unit": "kg", "quantity": 10, "unit_price": 1.0}],
        "delivery_schedule": "Semanal",
        "submission_deadline": "2025-12-31T23:59:59",
        "status": "open",
    }
    await client.post("/calls", json=call_data, headers=auth_headers)

    # Filter by status
    response = await client.get("/calls?status=open")
    assert response.status_code == 200
    data = response.json()
    # All returned items should have status "open"
    for item in data["items"]:
        assert item["status"] == "open"

