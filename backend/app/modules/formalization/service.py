"""
Formalization module service.
Business logic for formalization diagnosis and tasks.
"""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.formalization.diagnosis import calculate_eligibility, generate_formalization_tasks
from app.modules.formalization.schemas import (
    EligibilityLevel,
    FormalizationStatusInDB,
    FormalizationStatusResponse,
    FormalizationTaskInDB,
    TaskCategory,
    TaskPriority,
)
from app.modules.onboarding.service import OnboardingService
from app.shared.utils import to_object_id, utc_now


class FormalizationService:
    """Service for formalization operations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.status_collection = db.formalization_status
        self.tasks_collection = db.formalization_tasks
        self.onboarding_service = OnboardingService(db)

    async def get_or_calculate_status(self, user_id: str) -> FormalizationStatusResponse:
        """
        Get formalization status, calculating if necessary.

        Can use cached status or calculate on-demand from onboarding answers.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            Formalization status with eligibility information
        """
        user_oid = to_object_id(user_id)

        # Try to get cached status (optional - can be calculated on-demand)
        cached_doc = await self.status_collection.find_one(
            {"user_id": user_oid}, sort=[("diagnosed_at", -1)]
        )

        # Get all onboarding answers
        answers_dict = await self.onboarding_service.get_all_answers(user_id)

        # Convert to simple dict format for diagnosis function
        responses: dict[str, Any] = {}
        for question_id, answer_doc in answers_dict.items():
            responses[question_id] = answer_doc.answer
        
        # If no onboarding answers, try to get producer_type from profile
        if not responses:
            try:
                producer_profile = await self.db.producer_profiles.find_one({"user_id": user_oid})
                if producer_profile and producer_profile.get("producer_type"):
                    responses["producer_type"] = producer_profile.get("producer_type")
            except Exception:
                pass

        # Calculate diagnosis (pure function)
        diagnosis = calculate_eligibility(responses)

        # If no cached status or diagnosis changed, save/update cache
        now = utc_now()
        # Always sync tasks to ensure they're up to date (even if diagnosis didn't change)
        # This ensures tasks are created even for new users
        if not cached_doc or self._has_diagnosis_changed(cached_doc, diagnosis):
            status_doc = {
                "user_id": user_oid,
                "is_eligible": diagnosis["is_eligible"],
                "eligibility_level": diagnosis["eligibility_level"],
                "score": diagnosis["score"],
                "requirements_met": diagnosis["requirements_met"],
                "requirements_missing": diagnosis["requirements_missing"],
                "recommendations": diagnosis["recommendations"],
                "diagnosed_at": now,
            }

            # Upsert status
            await self.status_collection.update_one(
                {"user_id": user_oid},
                {"$set": status_doc},
                upsert=True,
            )

        # Always sync tasks based on current diagnosis (even if status didn't change)
        # This ensures tasks are created/updated for all users
        await self._sync_tasks_from_diagnosis(user_id, diagnosis, responses)
        
        if cached_doc:
            # Use cached diagnosis date
            now = cached_doc.get("diagnosed_at", now)

        return FormalizationStatusResponse(
            is_eligible=diagnosis["is_eligible"],
            eligibility_level=EligibilityLevel(diagnosis["eligibility_level"]),
            score=diagnosis["score"],
            requirements_met=diagnosis["requirements_met"],
            requirements_missing=diagnosis["requirements_missing"],
            recommendations=diagnosis["recommendations"],
            diagnosed_at=now,
        )

    async def get_tasks(self, user_id: str) -> list[FormalizationTaskInDB]:
        """
        Get formalization tasks for a user.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            List of formalization tasks
        """
        user_oid = to_object_id(user_id)

        # Ensure status is calculated and tasks are synced
        await self.get_or_calculate_status(user_id)

        # Get all tasks for user
        cursor = self.tasks_collection.find({"user_id": user_oid}).sort("priority", -1)
        tasks = []
        async for doc in cursor:
            tasks.append(FormalizationTaskInDB(**doc))

        return tasks

    async def _sync_tasks_from_diagnosis(
        self, user_id: str, diagnosis: dict[str, Any], responses: dict[str, Any]
    ) -> None:
        """Sync formalization tasks based on current diagnosis."""
        user_oid = to_object_id(user_id)
        now = utc_now()

        # If no onboarding responses, try to get producer_type from profile
        if not responses or "producer_type" not in responses:
            try:
                profile_doc = await self.db.producer_profiles.find_one({"user_id": user_oid})
                if profile_doc and profile_doc.get("producer_type"):
                    responses["producer_type"] = profile_doc.get("producer_type")
            except Exception:
                pass

        # Get onboarding questions for dynamic matching
        questions_dict: dict[str, Any] = {}
        try:
            questions_list = await self.onboarding_service._get_questions_list()
            for q in questions_list:
                questions_dict[q.question_id] = q
        except Exception:
            # If questions not available, pass None (fallback to old logic)
            questions_dict = {}

        # Generate tasks from diagnosis with questions for dynamic matching
        # Pass None if questions_dict is empty to use fallback logic
        new_tasks = generate_formalization_tasks(
            diagnosis, responses, questions_dict if questions_dict else None
        )

        # Get existing tasks to preserve completion status
        existing_tasks_map: dict[str, FormalizationTaskInDB] = {}
        cursor = self.tasks_collection.find({"user_id": user_oid})
        async for doc in cursor:
            task = FormalizationTaskInDB(**doc)
            existing_tasks_map[task.task_id] = task

        # Sync tasks
        for task_data in new_tasks:
            task_id = task_data["task_id"]
            existing_task = existing_tasks_map.get(task_id)

            if existing_task:
                # Update existing task if needed (preserve completion status)
                # Always update requirement_id even if task is completed (for AI guide generation)
                update_fields = {
                    "title": task_data["title"],
                    "description": task_data["description"],
                    "category": task_data["category"],
                    "priority": task_data["priority"],
                    "requirement_id": task_data.get("requirement_id"),
                }
                
                # Only update other fields if task is not completed
                if not existing_task.completed:
                    await self.tasks_collection.update_one(
                        {"_id": existing_task.id, "user_id": user_oid},
                        {"$set": update_fields},
                    )
                else:
                    # Task is completed, but still update requirement_id for AI guide
                    await self.tasks_collection.update_one(
                        {"_id": existing_task.id, "user_id": user_oid},
                        {"$set": {"requirement_id": task_data.get("requirement_id")}},
                    )
            else:
                # Insert new task
                task_doc = {
                    "user_id": user_oid,
                    "task_id": task_id,
                    "title": task_data["title"],
                    "description": task_data["description"],
                    "category": task_data["category"],
                    "priority": task_data["priority"],
                    "completed": False,
                    "completed_at": None,
                    "created_at": now,
                    "requirement_id": task_data.get("requirement_id"),
                }
                await self.tasks_collection.insert_one(task_doc)

        # Remove tasks that are no longer relevant
        # (e.g., if user completed requirement, task can be removed)
        current_task_ids = {t["task_id"] for t in new_tasks}
        for existing_task_id, existing_task in existing_tasks_map.items():
            if existing_task_id not in current_task_ids and existing_task.completed:
                # Remove completed tasks that are no longer in the list
                await self.tasks_collection.delete_one({"_id": existing_task.id})

    def _has_diagnosis_changed(self, cached_doc: dict[str, Any], new_diagnosis: dict[str, Any]) -> bool:
        """Check if diagnosis has changed compared to cached version."""
        return (
            cached_doc.get("is_eligible") != new_diagnosis["is_eligible"]
            or cached_doc.get("score") != new_diagnosis["score"]
            or set(cached_doc.get("requirements_met", [])) != set(new_diagnosis["requirements_met"])
            or set(cached_doc.get("requirements_missing", [])) != set(new_diagnosis["requirements_missing"])
        )
