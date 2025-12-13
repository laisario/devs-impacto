"""
Tests for sales projects module.
"""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_sales_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_call: dict[str, Any],
    sample_producer_profile: dict[str, Any],
) -> None:
    """POST /sales-projects should create a new sales project."""
    project_data = {
        "call_id": sample_call["_id"],
        "items": [
            {
                "product_name": "Alface",
                "unit": "kg",
                "quantity": 50,
                "unit_price": 5.00,
                "delivery_schedule": "Março/2025, Abril/2025",
            },
            {
                "product_name": "Tomate",
                "unit": "kg",
                "quantity": 100,
                "unit_price": 7.50,
                "delivery_schedule": "Março/2025",
            },
        ],
    }

    response = await client.post(
        "/sales-projects",
        json=project_data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["call_id"] == sample_call["_id"]
    assert len(data["items"]) == 2
    assert data["status"] == "draft"
    # Check total calculation: (50 * 5.00) + (100 * 7.50) = 250 + 750 = 1000
    assert data["total_value"] == 1000.0
    assert "_id" in data


@pytest.mark.asyncio
async def test_create_sales_project_without_profile(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_call: dict[str, Any],
) -> None:
    """POST /sales-projects without producer profile should return 422."""
    # Create a new user without profile
    phone = "+5511555555555"
    await client.post("/auth/start", json={"phone_e164": phone})
    response = await client.post(
        "/auth/verify",
        json={"phone_e164": phone, "otp": "123456"},
    )
    token = response.json()["access_token"]
    new_auth_headers = {"Authorization": f"Bearer {token}"}

    project_data = {
        "call_id": sample_call["_id"],
        "items": [
            {
                "product_name": "Banana",
                "unit": "kg",
                "quantity": 10,
                "unit_price": 3.00,
                "delivery_schedule": "Janeiro/2025",
            },
        ],
    }

    response = await client.post(
        "/sales-projects",
        json=project_data,
        headers=new_auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_sales_project_invalid_call(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_producer_profile: dict[str, Any],
) -> None:
    """POST /sales-projects with invalid call_id should return 404."""
    fake_call_id = "507f1f77bcf86cd799439011"

    project_data = {
        "call_id": fake_call_id,
        "items": [
            {
                "product_name": "Produto",
                "unit": "kg",
                "quantity": 10,
                "unit_price": 5.00,
                "delivery_schedule": "Janeiro/2025",
            },
        ],
    }

    response = await client.post(
        "/sales-projects",
        json=project_data,
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_sales_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_call: dict[str, Any],
    sample_producer_profile: dict[str, Any],
) -> None:
    """GET /sales-projects/{id} should return the project."""
    # Create project
    project_data = {
        "call_id": sample_call["_id"],
        "items": [
            {
                "product_name": "Cenoura",
                "unit": "kg",
                "quantity": 30,
                "unit_price": 4.00,
                "delivery_schedule": "Fevereiro/2025",
            },
        ],
    }

    create_response = await client.post(
        "/sales-projects",
        json=project_data,
        headers=auth_headers,
    )
    project_id = create_response.json()["_id"]

    # Get project
    response = await client.get(f"/sales-projects/{project_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == project_id
    assert data["items"][0]["product_name"] == "Cenoura"


@pytest.mark.asyncio
async def test_generate_pdf(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_call: dict[str, Any],
    sample_producer_profile: dict[str, Any],
) -> None:
    """POST /sales-projects/{id}/generate-pdf should generate PDF."""
    # Create project
    project_data = {
        "call_id": sample_call["_id"],
        "items": [
            {
                "product_name": "Alface Crespa",
                "unit": "unidade",
                "quantity": 100,
                "unit_price": 2.50,
                "delivery_schedule": "Março/2025, Abril/2025, Maio/2025",
            },
            {
                "product_name": "Couve Manteiga",
                "unit": "maço",
                "quantity": 50,
                "unit_price": 3.00,
                "delivery_schedule": "Março/2025",
            },
        ],
    }

    create_response = await client.post(
        "/sales-projects",
        json=project_data,
        headers=auth_headers,
    )
    project_id = create_response.json()["_id"]

    # Generate PDF
    response = await client.post(
        f"/sales-projects/{project_id}/generate-pdf",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "pdf_url" in data
    assert "projeto_venda" in data["pdf_url"]
    assert data["pdf_url"].endswith(".pdf")


@pytest.mark.asyncio
async def test_generate_pdf_updates_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_call: dict[str, Any],
    sample_producer_profile: dict[str, Any],
) -> None:
    """POST /sales-projects/{id}/generate-pdf should update project with PDF URL."""
    # Create project
    project_data = {
        "call_id": sample_call["_id"],
        "items": [
            {
                "product_name": "Batata",
                "unit": "kg",
                "quantity": 200,
                "unit_price": 5.00,
                "delivery_schedule": "Junho/2025",
            },
        ],
    }

    create_response = await client.post(
        "/sales-projects",
        json=project_data,
        headers=auth_headers,
    )
    project_id = create_response.json()["_id"]

    # Generate PDF
    pdf_response = await client.post(
        f"/sales-projects/{project_id}/generate-pdf",
        headers=auth_headers,
    )
    pdf_url = pdf_response.json()["pdf_url"]

    # Get project and verify PDF URL is saved
    get_response = await client.get(f"/sales-projects/{project_id}", headers=auth_headers)
    project = get_response.json()

    assert project["generated_pdf_url"] == pdf_url

