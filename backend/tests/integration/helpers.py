"""
Helper functions for integration tests.
"""

from typing import Any

from httpx import AsyncClient


async def create_user_and_get_token(
    client: AsyncClient, cpf: str = "12345678900"
) -> dict[str, str]:
    """
    Helper to create a user and get auth token.

    Args:
        client: HTTP client
        cpf: User CPF

    Returns:
        Auth headers dict
    """
    response = await client.post(
        "/auth/login",
        json={"cpf": cpf},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_producer_profile(
    client: AsyncClient, headers: dict[str, str], profile_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Helper to create a producer profile.

    Args:
        client: HTTP client
        headers: Auth headers
        profile_data: Profile data

    Returns:
        Created profile response
    """
    response = await client.put("/producer-profile", json=profile_data, headers=headers)
    assert response.status_code == 200
    return response.json()


async def submit_onboarding_answer(
    client: AsyncClient,
    headers: dict[str, str],
    question_id: str,
    answer: bool | str | int,
) -> dict[str, Any]:
    """
    Helper to submit an onboarding answer.

    Args:
        client: HTTP client
        headers: Auth headers
        question_id: Question ID
        answer: Answer value

    Returns:
        Answer response
    """
    response = await client.post(
        "/onboarding/answer",
        json={"question_id": question_id, "answer": answer},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


async def get_onboarding_status(
    client: AsyncClient, headers: dict[str, str]
) -> dict[str, Any]:
    """
    Helper to get onboarding status.

    Args:
        client: HTTP client
        headers: Auth headers

    Returns:
        Status response
    """
    response = await client.get("/onboarding/status", headers=headers)
    assert response.status_code == 200
    return response.json()
