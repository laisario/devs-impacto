"""
Tests for documents module.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_presigned_url(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """POST /documents/presign should return presigned URL."""
    response = await client.post(
        "/documents/presign",
        json={"filename": "dap.pdf", "content_type": "application/pdf"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "upload_url" in data
    assert "file_url" in data
    assert "file_key" in data
    assert "dap.pdf" in data["file_key"]


@pytest.mark.asyncio
async def test_create_document(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """POST /documents should create document metadata."""
    # First get presigned URL
    presign_response = await client.post(
        "/documents/presign",
        json={"filename": "cpf.pdf"},
        headers=auth_headers,
    )
    presign_data = presign_response.json()

    # Create document
    doc_data = {
        "doc_type": "cpf",
        "file_url": presign_data["file_url"],
        "file_key": presign_data["file_key"],
        "original_filename": "cpf.pdf",
    }

    response = await client.post("/documents", json=doc_data, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["doc_type"] == "cpf"
    assert data["original_filename"] == "cpf.pdf"
    assert "_id" in data


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """GET /documents should return user's documents."""
    # Create a document first
    presign_response = await client.post(
        "/documents/presign",
        json={"filename": "test.pdf"},
        headers=auth_headers,
    )
    presign_data = presign_response.json()

    await client.post(
        "/documents",
        json={
            "doc_type": "dap_caf",
            "file_url": presign_data["file_url"],
            "file_key": presign_data["file_key"],
            "original_filename": "test.pdf",
        },
        headers=auth_headers,
    )

    # List documents
    response = await client.get("/documents", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert "has_more" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_presign_without_auth(client: AsyncClient) -> None:
    """POST /documents/presign without auth should return 401."""
    response = await client.post(
        "/documents/presign",
        json={"filename": "test.pdf"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_document_with_different_types(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /documents should accept different document types."""
    doc_types = ["dap_caf", "cpf", "cnpj", "proof_address", "bank_statement", "other"]

    for doc_type in doc_types:
        presign_response = await client.post(
            "/documents/presign",
            json={"filename": f"{doc_type}.pdf"},
            headers=auth_headers,
        )
        presign_data = presign_response.json()

        response = await client.post(
            "/documents",
            json={
                "doc_type": doc_type,
                "file_url": presign_data["file_url"],
                "file_key": presign_data["file_key"],
                "original_filename": f"{doc_type}.pdf",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        assert response.json()["doc_type"] == doc_type


@pytest.mark.asyncio
async def test_get_document_by_id(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """GET /documents/{id} should return the document."""
    # Create a document first
    presign_response = await client.post(
        "/documents/presign",
        json={"filename": "get_test.pdf"},
        headers=auth_headers,
    )
    presign_data = presign_response.json()

    create_response = await client.post(
        "/documents",
        json={
            "doc_type": "cpf",
            "file_url": presign_data["file_url"],
            "file_key": presign_data["file_key"],
            "original_filename": "get_test.pdf",
        },
        headers=auth_headers,
    )
    document_id = create_response.json()["_id"]

    # Get document by ID
    response = await client.get(f"/documents/{document_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == document_id
    assert data["original_filename"] == "get_test.pdf"


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """GET /documents/{id} with invalid ID should return 404."""
    fake_id = "507f1f77bcf86cd799439011"

    response = await client.get(f"/documents/{fake_id}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_document_without_auth(client: AsyncClient) -> None:
    """GET /documents/{id} without auth should return 401."""
    fake_id = "507f1f77bcf86cd799439011"

    response = await client.get(f"/documents/{fake_id}")

    assert response.status_code == 401

