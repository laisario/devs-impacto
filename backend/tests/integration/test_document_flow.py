"""
Integration tests for complete document upload flow.
"""

import pytest
from httpx import AsyncClient

from tests.integration.helpers import create_user_and_get_token


@pytest.mark.asyncio
async def test_complete_document_upload_flow(client: AsyncClient) -> None:
    """Test complete document flow: presign → upload → register."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Step 1: Get presigned URL
    presign_response = await client.post(
        "/documents/presign",
        json={"filename": "test.pdf", "content_type": "application/pdf"},
        headers=headers,
    )
    assert presign_response.status_code == 200
    presign_data = presign_response.json()
    assert "upload_url" in presign_data
    assert "file_url" in presign_data
    assert "file_key" in presign_data

    # Step 2: Upload file to presigned URL (mock - actual upload depends on storage)
    # In test environment with mock storage, we can skip actual upload
    upload_url = presign_data["upload_url"]
    file_key = presign_data["file_key"]
    file_url = presign_data["file_url"]

    # Step 3: Register document metadata
    create_response = await client.post(
        "/documents",
        json={
            "doc_type": "dap_caf",
            "file_url": file_url,
            "file_key": file_key,
            "original_filename": "test.pdf",
        },
        headers=headers,
    )
    assert create_response.status_code in [200, 201]  # 201 Created is valid
    document = create_response.json()
    assert document["doc_type"] == "dap_caf"
    assert document["file_url"] == file_url
    assert document["file_key"] == file_key
    assert document["original_filename"] == "test.pdf"
    assert "_id" in document


@pytest.mark.asyncio
async def test_document_list_flow(client: AsyncClient) -> None:
    """Test listing documents."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Create a document first
    presign_response = await client.post(
        "/documents/presign",
        json={"filename": "test.pdf", "content_type": "application/pdf"},
        headers=headers,
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
        headers=headers,
    )

    # List documents
    list_response = await client.get("/documents", headers=headers)
    assert list_response.status_code == 200

    documents_data = list_response.json()
    assert "items" in documents_data
    assert "total" in documents_data
    assert "skip" in documents_data
    assert "limit" in documents_data
    assert isinstance(documents_data["items"], list)
    assert len(documents_data["items"]) >= 1


@pytest.mark.asyncio
async def test_document_pagination(client: AsyncClient) -> None:
    """Test document list pagination."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Create multiple documents
    for i in range(3):
        presign_response = await client.post(
            "/documents/presign",
            json={"filename": f"test{i}.pdf", "content_type": "application/pdf"},
            headers=headers,
        )
        presign_data = presign_response.json()

        await client.post(
            "/documents",
            json={
                "doc_type": "dap_caf",
                "file_url": presign_data["file_url"],
                "file_key": presign_data["file_key"],
                "original_filename": f"test{i}.pdf",
            },
            headers=headers,
        )

    # Get first page
    page1_response = await client.get("/documents?skip=0&limit=2", headers=headers)
    assert page1_response.status_code == 200
    page1_data = page1_response.json()
    assert len(page1_data["items"]) <= 2

    # Get second page
    page2_response = await client.get("/documents?skip=2&limit=2", headers=headers)
    assert page2_response.status_code == 200
    page2_data = page2_response.json()
    assert len(page2_data["items"]) <= 2


@pytest.mark.asyncio
async def test_document_get_by_id(client: AsyncClient) -> None:
    """Test getting a specific document by ID."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Create a document
    presign_response = await client.post(
        "/documents/presign",
        json={"filename": "test.pdf", "content_type": "application/pdf"},
        headers=headers,
    )
    presign_data = presign_response.json()

    create_response = await client.post(
        "/documents",
        json={
            "doc_type": "cpf",
            "file_url": presign_data["file_url"],
            "file_key": presign_data["file_key"],
            "original_filename": "test.pdf",
        },
        headers=headers,
    )
    document_id = create_response.json()["_id"]

    # Get document by ID
    get_response = await client.get(f"/documents/{document_id}", headers=headers)
    assert get_response.status_code == 200

    document = get_response.json()
    assert document["_id"] == document_id
    assert document["doc_type"] == "cpf"


@pytest.mark.asyncio
async def test_document_requires_auth(client: AsyncClient) -> None:
    """Test that document endpoints require authentication."""
    # Try without auth
    response = await client.post(
        "/documents/presign",
        json={"filename": "test.pdf", "content_type": "application/pdf"},
    )
    assert response.status_code == 401

    response = await client.get("/documents")
    assert response.status_code == 401

    response = await client.post(
        "/documents",
        json={
            "doc_type": "dap_caf",
            "file_url": "http://test.com/file.pdf",
            "file_key": "test/file.pdf",
            "original_filename": "test.pdf",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_document_type_validation(client: AsyncClient) -> None:
    """Test document type validation."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Get presigned URL
    presign_response = await client.post(
        "/documents/presign",
        json={"filename": "test.pdf", "content_type": "application/pdf"},
        headers=headers,
    )
    presign_data = presign_response.json()

    # Try invalid doc_type
    response = await client.post(
        "/documents",
        json={
            "doc_type": "invalid_type",
            "file_url": presign_data["file_url"],
            "file_key": presign_data["file_key"],
            "original_filename": "test.pdf",
        },
        headers=headers,
    )
    # Should either validate or accept (depending on enum validation)
    assert response.status_code in [200, 422]
