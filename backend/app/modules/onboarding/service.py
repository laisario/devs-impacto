"""
Onboarding module service.
Business logic for onboarding operations.
"""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.onboarding.schemas import (
    OnboardingAnswerCreate,
    OnboardingAnswerInDB,
    OnboardingQuestion,
    OnboardingStatus,
    OnboardingStatusResponse,
    ProducerOnboardingSummary,
    QuestionType,
)
from app.shared.utils import to_object_id, utc_now


class OnboardingService:
    """Service for onboarding operations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.collection = db.onboarding_answers
        self.questions_collection = db.onboarding_questions
        self.profiles_collection = db.producer_profiles
        # Cache de perguntas (carregado sob demanda)
        self._questions_cache: dict[str, OnboardingQuestion] | None = None

        # Ensure indexes exist (idempotent, safe to call multiple times)
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """
        Ensure database indexes exist for optimal query performance.
        Should be called on service initialization.
        """
        # Note: In production, indexes should be created via migration scripts
        # This is a convenience method for development
        # Motor doesn't support synchronous index creation, so we skip this
        # Indexes should be created manually or via migration:
        # - onboarding_answers: unique index on (user_id, question_id)
        # - onboarding_answers: index on user_id
        # - onboarding_questions: unique index on question_id
        # - onboarding_questions: index on order
        pass

    async def _get_questions(self) -> dict[str, OnboardingQuestion]:
        """
        Get all onboarding questions from database.
        Uses cache for performance.

        Returns:
            Dictionary mapping question_id to OnboardingQuestion
        """
        if self._questions_cache is not None:
            return self._questions_cache

        # Load questions from database
        cursor = self.questions_collection.find().sort("order", 1)
        questions = {}
        async for doc in cursor:
            # Remove _id if present
            doc.pop("_id", None)
            question = OnboardingQuestion(**doc)
            questions[question.question_id] = question

        # Cache for next calls
        self._questions_cache = questions
        return questions

    async def _get_question_by_id(self, question_id: str) -> OnboardingQuestion | None:
        """
        Get a specific question by ID.

        Args:
            question_id: Question ID

        Returns:
            OnboardingQuestion if found, None otherwise
        """
        questions = await self._get_questions()
        return questions.get(question_id)

    async def _get_questions_list(self) -> list[OnboardingQuestion]:
        """
        Get all questions as a sorted list.

        Returns:
            List of OnboardingQuestion sorted by order
        """
        questions = await self._get_questions()
        questions_list = list(questions.values())
        questions_list.sort(key=lambda q: q.order)
        return questions_list

    def _invalidate_cache(self) -> None:
        """Invalidate questions cache. Useful when questions are updated in database."""
        self._questions_cache = None

    async def get_producer_summary(self, user_id: str) -> ProducerOnboardingSummary:
        """
        Get aggregated summary of producer's onboarding and formalization data.
        Useful for dashboards and overview screens.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            ProducerOnboardingSummary with aggregated data
        """
        user_oid = to_object_id(user_id)

        # Get onboarding status
        onboarding_status_resp = await self.get_status(user_id)

        # Get producer profile to check if exists and get onboarding fields
        profile_doc = await self.profiles_collection.find_one({"user_id": user_oid})
        has_profile = profile_doc is not None
        onboarding_status = None
        onboarding_completed_at = None

        if profile_doc:
            onboarding_status_str = profile_doc.get("onboarding_status")
            if onboarding_status_str:
                onboarding_status = OnboardingStatus(onboarding_status_str)
            onboarding_completed_at = profile_doc.get("onboarding_completed_at")

        # Get formalization status (if available)
        # Import here to avoid circular dependency
        try:
            from app.modules.formalization.service import FormalizationService

            formalization_service = FormalizationService(self.db)
            formalization_status = await formalization_service.get_or_calculate_status(user_id)
            formalization_eligible = formalization_status.is_eligible
            formalization_score = formalization_status.score

            # Get tasks count
            tasks = await formalization_service.get_tasks(user_id)
            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t.completed)
        except Exception:
            # If formalization not available yet, set to None
            formalization_eligible = None
            formalization_score = None
            total_tasks = 0
            completed_tasks = 0

        # Get answers count
        answers = await self.get_all_answers(user_id)
        total_answers = len(answers)

        return ProducerOnboardingSummary(
            user_id=user_oid,
            onboarding_status=onboarding_status or onboarding_status_resp.status,
            onboarding_completed_at=onboarding_completed_at or onboarding_status_resp.completed_at,
            onboarding_progress=onboarding_status_resp.progress_percentage,
            formalization_eligible=formalization_eligible,
            formalization_score=formalization_score,
            has_profile=has_profile,
            total_answers=total_answers,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
        )

    async def save_answer(
        self, user_id: str, data: OnboardingAnswerCreate
    ) -> OnboardingAnswerInDB:
        """
        Save or update an onboarding answer.

        Args:
            user_id: User's MongoDB ObjectId as string
            data: Answer data

        Returns:
            Saved answer
        """
        question = await self._get_question_by_id(data.question_id)
        if not question:
            from app.core.errors import ValidationError

            raise ValidationError(f"Question ID '{data.question_id}' not found")

        user_oid = to_object_id(user_id)
        now = utc_now()

        # Validate answer type based on question type
        if question.question_type == QuestionType.BOOLEAN and not isinstance(data.answer, bool):
            from app.core.errors import ValidationError

            raise ValidationError("Answer must be boolean for this question type")

        # Prepare document
        doc = {
            "user_id": user_oid,
            "question_id": data.question_id,
            "answer": data.answer,
            "answered_at": now,
        }

        # Upsert answer (user can update their answer)
        result = await self.collection.find_one_and_update(
            {"user_id": user_oid, "question_id": data.question_id},
            {"$set": doc},
            upsert=True,
            return_document=True,
        )

        # Update producer profile onboarding status
        await self._update_profile_status(user_id)

        return OnboardingAnswerInDB(**result)

    async def get_status(self, user_id: str) -> OnboardingStatusResponse:
        """
        Get onboarding status for a user.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            Onboarding status with progress and next question
        """
        user_oid = to_object_id(user_id)

        # Get all answers for user
        cursor = self.collection.find({"user_id": user_oid})
        answered_question_ids = set()
        async for doc in cursor:
            answered_question_ids.add(doc["question_id"])

        # Get all questions
        all_questions = await self._get_questions_list()
        total_questions = len(all_questions)
        answered_count = len(answered_question_ids)

        if answered_count == 0:
            status = OnboardingStatus.NOT_STARTED
        elif answered_count >= total_questions:
            status = OnboardingStatus.COMPLETED
        else:
            status = OnboardingStatus.IN_PROGRESS

        # Find next unanswered question (by order)
        next_question = None
        unanswered = [q for q in all_questions if q.question_id not in answered_question_ids]
        if unanswered:
            # Already sorted by order from _get_questions_list
            next_question = unanswered[0]

        # Calculate progress
        progress = (answered_count / total_questions * 100) if total_questions > 0 else 0

        # Get completion date if completed
        completed_at = None
        if status == OnboardingStatus.COMPLETED:
            # Get the latest answered_at
            cursor = self.collection.find({"user_id": user_oid}).sort("answered_at", -1).limit(1)
            latest_doc = await cursor.to_list(length=1)
            if latest_doc:
                completed_at = latest_doc[0]["answered_at"]

        return OnboardingStatusResponse(
            status=status,
            progress_percentage=round(progress, 1),
            total_questions=total_questions,
            answered_questions=answered_count,
            next_question=next_question,
            completed_at=completed_at,
        )

    async def get_all_answers(self, user_id: str) -> dict[str, OnboardingAnswerInDB]:
        """
        Get all answers for a user.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            Dictionary mapping question_id to answer
        """
        user_oid = to_object_id(user_id)
        cursor = self.collection.find({"user_id": user_oid})

        answers = {}
        async for doc in cursor:
            answer = OnboardingAnswerInDB(**doc)
            answers[answer.question_id] = answer

        return answers

    async def is_completed(self, user_id: str) -> bool:
        """
        Check if onboarding is completed for a user.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            True if all required questions are answered
        """
        status = await self.get_status(user_id)
        return status.status == OnboardingStatus.COMPLETED

    async def _update_profile_status(self, user_id: str) -> None:
        """Update onboarding status in producer profile."""
        status = await self.get_status(user_id)

        update_doc: dict[str, Any] = {"onboarding_status": status.status.value}

        if status.status == OnboardingStatus.COMPLETED and status.completed_at:
            update_doc["onboarding_completed_at"] = status.completed_at

        user_oid = to_object_id(user_id)
        await self.profiles_collection.update_one(
            {"user_id": user_oid},
            {"$set": update_doc},
        )
