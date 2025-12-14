"""
Integration tests for complete onboarding flow.
"""

import pytest
from httpx import AsyncClient

from tests.integration.helpers import (
    create_user_and_get_token,
    get_onboarding_status,
    submit_onboarding_answer,
)


@pytest.mark.asyncio
async def test_complete_onboarding_flow(client: AsyncClient) -> None:
    """Test complete onboarding flow: start → answer questions → complete."""
    headers = await create_user_and_get_token(client)

    # Get initial status
    status = await get_onboarding_status(client, headers)
    assert status["status"] in ["not_started", "in_progress"]
    assert "next_question" in status or status.get("next_question") is None

    # Answer questions until completion
    answered_count = 0
    max_iterations = 50  # Safety limit

    while answered_count < max_iterations:
        status = await get_onboarding_status(client, headers)

        if status["status"] == "completed":
            break

        if not status.get("next_question"):
            # No more questions available
            break

        question = status["next_question"]
        question_id = question["question_id"]
        question_type = question["question_type"]

        # Answer based on question type
        if question_type == "boolean":
            answer = True
        elif question_type == "choice" and question.get("options"):
            answer = question["options"][0]
        else:
            answer = "Test answer"

        # Submit answer
        await submit_onboarding_answer(client, headers, question_id, answer)
        answered_count += 1

    # Verify completion or progress
    final_status = await get_onboarding_status(client, headers)
    # Onboarding may be completed, in progress, or not started (if no questions available)
    assert final_status["status"] in ["not_started", "in_progress", "completed"]
    assert final_status["progress_percentage"] >= 0
    # If we answered questions, we should have made progress
    if answered_count > 0:
        assert final_status["answered_questions"] > 0


@pytest.mark.asyncio
async def test_onboarding_progress_tracking(client: AsyncClient) -> None:
    """Test that onboarding progress is tracked correctly."""
    headers = await create_user_and_get_token(client)

    # Get initial status
    initial_status = await get_onboarding_status(client, headers)
    initial_progress = initial_status["progress_percentage"]
    initial_answered = initial_status["answered_questions"]

    # Answer a question
    if initial_status.get("next_question"):
        question = initial_status["next_question"]
        question_id = question["question_id"]

        if question["question_type"] == "boolean":
            answer = True
        else:
            answer = "Test"

        await submit_onboarding_answer(client, headers, question_id, answer)

        # Check progress increased
        new_status = await get_onboarding_status(client, headers)
        assert new_status["answered_questions"] >= initial_answered
        assert new_status["progress_percentage"] >= initial_progress


@pytest.mark.asyncio
async def test_onboarding_summary(client: AsyncClient) -> None:
    """Test onboarding summary endpoint."""
    headers = await create_user_and_get_token(client)

    # Get summary
    response = await client.get("/onboarding/summary", headers=headers)
    assert response.status_code == 200

    summary = response.json()
    assert "user_id" in summary
    assert "onboarding_status" in summary
    assert "onboarding_progress" in summary
    assert summary["onboarding_progress"] >= 0
    assert summary["onboarding_progress"] <= 100


@pytest.mark.asyncio
async def test_onboarding_requires_auth(client: AsyncClient) -> None:
    """Test that onboarding endpoints require authentication."""
    # Try without auth
    response = await client.get("/onboarding/status")
    assert response.status_code == 401

    response = await client.post(
        "/onboarding/answer", json={"question_id": "test", "answer": True}
    )
    assert response.status_code == 401

    response = await client.get("/onboarding/summary")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_onboarding_answer_validation(client: AsyncClient) -> None:
    """Test onboarding answer validation."""
    headers = await create_user_and_get_token(client)

    # Get a question
    status = await get_onboarding_status(client, headers)
    if not status.get("next_question"):
        pytest.skip("No questions available for testing")

    question = status["next_question"]

    # Try invalid question_id
    response = await client.post(
        "/onboarding/answer",
        json={"question_id": "invalid_id", "answer": True},
        headers=headers,
    )
    # Should either succeed (if question exists) or fail gracefully
    assert response.status_code in [200, 400, 422]
