"""
AI Formalization service.
Orchestrates guide generation using RAG and LLM.
"""

import json
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.errors import NotFoundError, ValidationError
from app.modules.ai_formalization.llm_client import LLMClient
from app.modules.ai_formalization.prompts import build_prompt
from app.modules.ai_formalization.rag import RAGService
from app.modules.ai_formalization.schemas import FormalizationGuideResponse
from app.modules.onboarding.schemas import OnboardingQuestion
from app.modules.onboarding.service import OnboardingService
from app.modules.producers.service import ProducerService


class AIFormalizationService:
    """Service for AI-powered formalization guide generation."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,  # type: ignore[type-arg]
        rag_service: RAGService,
        llm_client: LLMClient,
        onboarding_service: OnboardingService,
        producer_service: ProducerService,
    ):
        self.db = db
        self.rag_service = rag_service
        self.llm_client = llm_client
        self.onboarding_service = onboarding_service
        self.producer_service = producer_service

    async def generate_guide(
        self, user_id: str, requirement_id: str
    ) -> FormalizationGuideResponse:
        """
        Generate a personalized formalization guide for a requirement.

        Args:
            user_id: User's MongoDB ObjectId as string
            requirement_id: Requirement ID to generate guide for

        Returns:
            FormalizationGuideResponse with steps and instructions

        Raises:
            NotFoundError: If requirement_id doesn't exist
            ValidationError: If LLM response is invalid
        """
        # 1. Validate requirement_id - find corresponding OnboardingQuestion
        question = await self._get_question_by_requirement_id(requirement_id)
        if not question:
            raise NotFoundError("Requirement", requirement_id)

        # 2. Get producer profile (may be None)
        producer_profile = await self.producer_service.get_profile_by_user(user_id)
        profile_dict = None
        if producer_profile:
            profile_dict = producer_profile.model_dump(exclude_none=True)

        # 3. Get user's answer to this question (if exists)
        answers = await self.onboarding_service.get_all_answers(user_id)
        user_answer = answers.get(question.question_id)
        current_answer = None
        if user_answer:
            current_answer = user_answer.answer

        # 4. Format requirement text with context
        requirement_text = self._format_requirement_text(question, current_answer)

        # 5. Search relevant RAG chunks
        rag_chunks = await self.rag_service.search_relevant_chunks(
            requirement_id, limit=5
        )
        chunks_dict = [chunk.model_dump(exclude={"id", "embedding"}, exclude_none=True) for chunk in rag_chunks]

        # 6. Build prompt
        prompt = build_prompt(profile_dict, requirement_text, chunks_dict)

        # 7. Call LLM
        try:
            llm_response = await self.llm_client.generate(prompt)
        except Exception as e:
            # Fallback to generic guide if LLM fails
            return self._get_fallback_guide(question)

        # 8. Parse and validate JSON response
        try:
            response_data = json.loads(llm_response)
        except json.JSONDecodeError:
            # Fallback if JSON is invalid
            return self._get_fallback_guide(question)

        # 9. Validate and parse with Pydantic
        try:
            guide = FormalizationGuideResponse(**response_data)
        except Exception:
            # Fallback if validation fails
            return self._get_fallback_guide(question)

        # 10. Ensure steps are valid (already validated by Pydantic)
        return guide

    async def _get_question_by_requirement_id(
        self, requirement_id: str
    ) -> OnboardingQuestion | None:
        """
        Get OnboardingQuestion by requirement_id.

        Args:
            requirement_id: Requirement ID to search for

        Returns:
            OnboardingQuestion if found, None otherwise
        """
        # Access internal method - questions are cached
        questions_list = await self.onboarding_service._get_questions_list()
        for question in questions:
            if question.requirement_id == requirement_id:
                return question
        return None

    def _format_requirement_text(
        self, question: OnboardingQuestion, current_answer: Any | None
    ) -> str:
        """
        Format requirement text with context.

        Args:
            question: OnboardingQuestion for the requirement
            current_answer: User's current answer (if exists)

        Returns:
            Formatted requirement text
        """
        text = question.question_text
        if current_answer is not None:
            answer_str = "Sim" if current_answer else "Não" if isinstance(current_answer, bool) else str(current_answer)
            text += f"\nSituação atual: {answer_str}"
        return text

    def _get_fallback_guide(
        self, question: OnboardingQuestion
    ) -> FormalizationGuideResponse:
        """
        Generate a fallback generic guide if LLM fails.

        Args:
            question: OnboardingQuestion for the requirement

        Returns:
            Generic FormalizationGuideResponse
        """
        from app.modules.ai_formalization.schemas import GuideStep

        # Generic fallback steps
        steps = [
            GuideStep(
                step=1,
                title="Buscar informações",
                description=f"Procure informações sobre {question.question_text.lower()} na Secretaria de Agricultura ou EMATER do seu município.",
            ),
            GuideStep(
                step=2,
                title="Preparar documentos",
                description="Organize seus documentos pessoais (RG, CPF) para o processo.",
            ),
            GuideStep(
                step=3,
                title="Comparecer ao órgão",
                description="Vá até o órgão responsável para iniciar o processo.",
            ),
        ]

        return FormalizationGuideResponse(
            summary=f"Para resolver este requisito relacionado a {question.question_text.lower()}, siga os passos abaixo.",
            steps=steps,
            estimated_time_days=7,
            where_to_go=["Secretaria Municipal de Agricultura", "EMATER"],
            confidence_level="medium",
        )
