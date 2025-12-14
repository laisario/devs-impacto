"""
LLM client interface and implementations.
Supports OpenAI and mock provider for testing.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings


class LLMClient(ABC):
    """Abstract interface for LLM clients."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            The LLM's response as a string
        """
        pass


class OpenAIClient(LLMClient):
    """OpenAI implementation of LLM client."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY from env.
            model: Model name to use (default: gpt-4o-mini)
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai>=1.0.0"
            )

        self.api_key = api_key or getattr(settings, "openai_api_key", None)
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate(self, prompt: str) -> str:
        """
        Generate a response using OpenAI API.

        Args:
            prompt: The prompt to send

        Returns:
            The model's response as a string
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent responses
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")
        return content


class MockLLMClient(LLMClient):
    """Mock LLM client for testing and development."""

    def __init__(self, fixed_response: dict[str, Any] | None = None):
        """
        Initialize mock LLM client.

        Args:
            fixed_response: Fixed response to return. If None, uses default.
        """
        self.fixed_response = fixed_response or self._get_default_response()

    async def generate(self, prompt: str) -> str:
        """
        Generate a mock response.

        Args:
            prompt: The prompt (ignored in mock)

        Returns:
            Mock JSON response
        """
        import json

        return json.dumps(self.fixed_response, ensure_ascii=False, indent=2)

    @staticmethod
    def _get_default_response() -> dict[str, Any]:
        """Get default mock response."""
        return {
            "summary": "Para cumprir este requisito, siga os passos abaixo.",
            "steps": [
                {
                    "step": 1,
                    "title": "Procurar apoio local",
                    "description": "Vá até a Secretaria de Agricultura ou EMATER do seu município.",
                },
                {
                    "step": 2,
                    "title": "Levar documentos básicos",
                    "description": "Leve CPF, RG e um comprovante simples de que você produz alimentos.",
                },
                {
                    "step": 3,
                    "title": "Preencher formulário",
                    "description": "Preencha o formulário fornecido pelo órgão com seus dados.",
                },
            ],
            "estimated_time_days": 7,
            "where_to_go": ["Secretaria Municipal de Agricultura", "EMATER"],
            "confidence_level": "high",
        }


def create_llm_client() -> LLMClient:
    """
    Factory function to create LLM client based on configuration.

    Returns:
        LLMClient instance (OpenAI or Mock)
    """
    provider = getattr(settings, "llm_provider", "mock").lower()
    model = getattr(settings, "llm_model", "gpt-4o-mini")

    if provider == "mock":
        return MockLLMClient()
    elif provider == "openai":
        return OpenAIClient(model=model)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'openai' or 'mock'.")
