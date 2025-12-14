"""
Tests for AI Formalization module.
"""

import pytest
from httpx import AsyncClient

from app.core.db import get_database
from app.modules.ai_formalization.llm_client import MockLLMClient
from app.modules.ai_formalization.rag import RAGChunk, RAGService
from app.modules.ai_formalization.service import AIFormalizationService
from app.modules.onboarding.service import OnboardingService
from app.modules.producers.service import ProducerService
from app.shared.utils import utc_now


@pytest.fixture
async def rag_service(mongo_client):
    """Create RAG service for tests."""
    db = get_database()
    service = RAGService(db)
    
    # Add some test chunks
    chunks = [
        RAGChunk(
            content="Para obter CPF, vá até a Receita Federal ou agência dos Correios.",
            topic="cpf",
            applies_to=["has_cpf"],
            source="guia_cpf.pdf",
            created_at=utc_now(),
        ),
        RAGChunk(
            content="A DAP é obtida na EMATER ou Secretaria de Agricultura do município.",
            topic="dap",
            applies_to=["has_dap_caf"],
            source="guia_dap.pdf",
            created_at=utc_now(),
        ),
    ]
    await service.add_chunks(chunks)
    return service


@pytest.fixture
async def llm_client():
    """Create mock LLM client for tests."""
    return MockLLMClient()


@pytest.fixture
async def ai_service(rag_service, llm_client, mongo_client):
    """Create AI formalization service for tests."""
    db = get_database()
    onboarding_service = OnboardingService(db)
    producer_service = ProducerService(db)
    
    return AIFormalizationService(
        db=db,
        rag_service=rag_service,
        llm_client=llm_client,
        onboarding_service=onboarding_service,
        producer_service=producer_service,
    )


@pytest.fixture
async def seeded_onboarding_questions(mongo_client):
    """Seed onboarding questions for tests."""
    from app.core.db import get_database
    from app.modules.onboarding.schemas import OnboardingQuestion, QuestionType
    from seeds_onboarding import DEFAULT_ONBOARDING_QUESTIONS
    
    db = get_database()
    collection = db.onboarding_questions
    
    # Clear and insert
    await collection.delete_many({})
    for question in DEFAULT_ONBOARDING_QUESTIONS:
        doc = question.model_dump(exclude_none=True)
        await collection.insert_one(doc)
    
    yield
    
    # Cleanup handled by setup_test_db


@pytest.mark.asyncio
async def test_generate_guide_with_mock_llm(
    ai_service, 
    seeded_onboarding_questions,
    sample_producer_profile,
    client: AsyncClient,
    auth_headers
):
    """Test guide generation with mock LLM."""
    # Generate guide for has_cpf requirement
    response = await client.post(
        "/ai/formalization/guide",
        json={"requirement_id": "has_cpf"},
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have valid structure
    assert "summary" in data
    assert "steps" in data
    assert len(data["steps"]) >= 1


@pytest.mark.asyncio
async def test_guide_generation_endpoint(
    client: AsyncClient, 
    auth_headers,
    seeded_onboarding_questions
):
    """Test the guide generation endpoint."""
    response = await client.post(
        "/ai/formalization/guide",
        json={"requirement_id": "has_cpf"},
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert "summary" in data
    assert "steps" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) >= 1  # At least one step
    assert len(data["steps"]) <= 8  # Max 8 steps
    
    # Validate each step
    for i, step in enumerate(data["steps"], start=1):
        assert step["step"] == i  # Sequential numbering
        assert "title" in step
        assert "description" in step
        assert len(step["title"]) > 0
        assert len(step["description"]) > 0
    
    # Validate other fields
    assert "estimated_time_days" in data
    assert "where_to_go" in data
    assert "confidence_level" in data
    assert data["confidence_level"] in ["high", "medium", "low"]


@pytest.mark.asyncio
async def test_guide_generation_invalid_requirement(
    client: AsyncClient, 
    auth_headers,
    seeded_onboarding_questions
):
    """Test guide generation with invalid requirement_id."""
    response = await client.post(
        "/ai/formalization/guide",
        json={"requirement_id": "requirement_inexistente"},
        headers=auth_headers,
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_guide_generation_unauthorized(client: AsyncClient):
    """Test guide generation without authentication."""
    response = await client.post(
        "/ai/formalization/guide",
        json={"requirement_id": "has_cpf"},
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_rag_service_search(rag_service):
    """Test RAG service search functionality."""
    chunks = await rag_service.search_relevant_chunks("has_cpf", limit=10)
    
    assert len(chunks) > 0
    # Verify chunks have the requirement in applies_to
    for chunk in chunks:
        assert chunk.applies_to
        assert "has_cpf" in chunk.applies_to or len(chunk.applies_to) > 0


@pytest.mark.asyncio
async def test_mock_llm_client(llm_client):
    """Test mock LLM client."""
    prompt = "Test prompt"
    response = await llm_client.generate(prompt)
    
    import json
    data = json.loads(response)
    
    assert "summary" in data
    assert "steps" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) > 0
