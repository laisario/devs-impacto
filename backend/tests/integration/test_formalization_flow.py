"""
Integration tests for formalization diagnosis and tasks flow.
"""

import pytest
from httpx import AsyncClient

from tests.integration.fixtures import sample_individual_profile
from tests.integration.helpers import (
    create_producer_profile,
    create_user_and_get_token,
)


@pytest.mark.asyncio
async def test_formalization_status_flow(client: AsyncClient) -> None:
    """Test getting formalization status."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Create profile first
    await create_producer_profile(client, headers, sample_individual_profile())

    # Get formalization status
    response = await client.get("/formalization/status", headers=headers)
    assert response.status_code == 200

    status = response.json()
    assert "is_eligible" in status
    assert "eligibility_level" in status
    assert "score" in status
    assert 0 <= status["score"] <= 100
    assert "requirements_met" in status
    assert "requirements_missing" in status
    assert "recommendations" in status
    assert "diagnosed_at" in status


@pytest.mark.asyncio
async def test_formalization_tasks_flow(client: AsyncClient) -> None:
    """Test getting formalization tasks."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Create profile first
    await create_producer_profile(client, headers, sample_individual_profile())

    # Get tasks
    response = await client.get("/formalization/tasks", headers=headers)
    assert response.status_code == 200

    tasks = response.json()
    assert isinstance(tasks, list)

    if len(tasks) > 0:
        task = tasks[0]
        # Backend may return _id or id
        assert "id" in task or "_id" in task
        assert "task_id" in task
        assert "title" in task
        assert "description" in task
        assert "category" in task
        assert "priority" in task
        assert "completed" in task
        assert "created_at" in task


@pytest.mark.asyncio
async def test_formalization_requires_profile(client: AsyncClient) -> None:
    """Test that formalization endpoints work even without profile."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Try to get status without profile (should still work)
    response = await client.get("/formalization/status", headers=headers)
    # Should either work or return appropriate error
    assert response.status_code in [200, 404, 422]

    # Try to get tasks without profile
    response = await client.get("/formalization/tasks", headers=headers)
    # Should either work or return appropriate error
    assert response.status_code in [200, 404, 422]


@pytest.mark.asyncio
async def test_formalization_requires_auth(client: AsyncClient) -> None:
    """Test that formalization endpoints require authentication."""
    # Try without auth
    response = await client.get("/formalization/status")
    assert response.status_code == 401

    response = await client.get("/formalization/tasks")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_formalization_status_consistency(client: AsyncClient) -> None:
    """Test that formalization status is consistent across requests."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Create profile
    await create_producer_profile(client, headers, sample_individual_profile())

    # Get status multiple times
    status1_response = await client.get("/formalization/status", headers=headers)
    status2_response = await client.get("/formalization/status", headers=headers)

    assert status1_response.status_code == 200
    assert status2_response.status_code == 200

    status1 = status1_response.json()
    status2 = status2_response.json()

    # Scores should be consistent (may vary slightly if diagnosis is recalculated)
    assert abs(status1["score"] - status2["score"]) <= 5  # Allow small variance


@pytest.mark.asyncio
async def test_formalization_tasks_consistency(client: AsyncClient) -> None:
    """Test that formalization tasks are consistent."""
    phone = "+5511999999999"
    headers = await create_user_and_get_token(client, phone)

    # Create profile
    await create_producer_profile(client, headers, sample_individual_profile())

    # Get tasks multiple times
    tasks1_response = await client.get("/formalization/tasks", headers=headers)
    tasks2_response = await client.get("/formalization/tasks", headers=headers)

    assert tasks1_response.status_code == 200
    assert tasks2_response.status_code == 200

    tasks1 = tasks1_response.json()
    tasks2 = tasks2_response.json()

    # Should have same number of tasks
    assert len(tasks1) == len(tasks2)
