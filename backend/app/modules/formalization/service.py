"""
Formalization module service.
Business logic for formalization diagnosis and tasks.
"""

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.formalization.diagnosis import calculate_eligibility, generate_formalization_tasks
from app.modules.formalization.producer_utils import is_individual_producer
from app.modules.formalization.repo import FormalizationRepository
from app.modules.formalization.rules import compute_required_tasks
from app.modules.formalization.schemas import (
    EligibilityLevel,
    FormalizationStatusInDB,
    FormalizationStatusResponse,
    FormalizationTaskInDB,
    FormalizationTaskUser,
    FormalizationTaskUserResponse,
    TaskCategory,
    TaskPriority,
)
from app.modules.onboarding.service import OnboardingService
from app.modules.producers.service import ProducerService
from app.shared.utils import to_object_id, utc_now


class FormalizationService:
    """Service for formalization operations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.status_collection = db.formalization_status
        self.tasks_collection = db.formalization_tasks  # Mantido para compatibilidade
        self.onboarding_service = OnboardingService(db)
        self.producer_service = ProducerService(db)
        self.repo = FormalizationRepository(db)
        self.logger = logging.getLogger(__name__)

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
        
        # Get producer profile to supplement/override responses
        # This ensures that when tasks are marked as done, the profile flags are used
        try:
            producer_profile = await self.db.producer_profiles.find_one({"user_id": user_oid})
            if producer_profile:
                # Use profile flags to override or supplement onboarding answers
                # This is important because tasks can update profile flags directly
                if producer_profile.get("producer_type"):
                    responses["producer_type"] = producer_profile.get("producer_type")
                
                # Override with profile flags if they exist (these are updated when tasks are completed)
                if "has_dap_caf" in producer_profile:
                    responses["has_dap_caf"] = producer_profile.get("has_dap_caf", False)
                if "has_family_farmer_registration" in producer_profile:
                    responses["has_family_farmer_registration"] = producer_profile.get("has_family_farmer_registration", False)
                    # Also set has_dap_caf if has_family_farmer_registration is True
                    if producer_profile.get("has_family_farmer_registration"):
                        responses["has_dap_caf"] = True
                
                if "has_bank_account" in producer_profile:
                    responses["has_bank_account"] = producer_profile.get("has_bank_account", False)
                
                if "has_cpf" in producer_profile:
                    responses["has_cpf"] = producer_profile.get("has_cpf", False)
                
                if "has_cnpj" in producer_profile:
                    responses["has_cnpj"] = producer_profile.get("has_cnpj", False)
                
                if "has_address_proof" in producer_profile:
                    responses["has_address_proof"] = producer_profile.get("has_address_proof", False)
                
                if "has_previous_sales" in producer_profile:
                    responses["has_previous_sales"] = producer_profile.get("has_previous_sales", False)
        except Exception as e:
            self.logger.warning(
                f"Failed to fetch producer profile for user {user_id}: {e}",
                exc_info=True,
                extra={"user_id": user_id}
            )

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

        # Always regenerate tasks based on producer profile (new system)
        # This ensures tasks match the current profile state
        await self.regenerate_tasks(user_id)
        
        # Calculate score based purely on task completion progress
        # Score = (completed tasks / total tasks) * 100
        user_tasks = await self.repo.get_user_tasks(user_id)
        total_tasks = len(user_tasks)
        completed_tasks = sum(1 for task in user_tasks if task.status == "done")
        
        if total_tasks > 0:
            progress_score = int((completed_tasks / total_tasks) * 100)
        else:
            progress_score = 0
        
        # Use progress-based score instead of diagnosis score
        # Keep diagnosis for requirements_met/missing, but score is pure progress
        score = progress_score
        
        if cached_doc:
            # Use cached diagnosis date
            now = cached_doc.get("diagnosed_at", now)

        return FormalizationStatusResponse(
            is_eligible=diagnosis["is_eligible"],
            eligibility_level=EligibilityLevel(diagnosis["eligibility_level"]),
            score=score,  # Progress-based score, not diagnosis score
            requirements_met=diagnosis["requirements_met"],
            requirements_missing=diagnosis["requirements_missing"],
            recommendations=diagnosis["recommendations"],
            diagnosed_at=now,
        )

    async def get_tasks(self, user_id: str) -> list[FormalizationTaskUserResponse]:
        """
        Get formalization tasks for a user (novo sistema baseado em CSV).

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            List of formalization tasks with catalog data
        """
        # Garantir que tasks estão sincronizadas
        await self.regenerate_tasks(user_id)

        # Buscar tasks do usuário
        user_tasks = await self.repo.get_user_tasks(user_id)

        # Buscar catálogo de tasks
        catalog_tasks = await self.repo.get_all_catalog_tasks()

        # Combinar dados do usuário com dados do catálogo
        result = []
        for user_task in user_tasks:
            catalog_task = catalog_tasks.get(user_task.task_code)
            if not catalog_task:
                self.logger.warning(
                    f"Task code '{user_task.task_code}' not found in catalog",
                    extra={"user_id": user_id, "task_code": user_task.task_code},
                )
                continue

            result.append(
                FormalizationTaskUserResponse(
                    id=user_task.id,
                    user_id=user_task.user_id,
                    task_code=user_task.task_code,
                    title=catalog_task.title,
                    description=catalog_task.description,
                    why=catalog_task.why,
                    status=user_task.status,
                    blocking=user_task.blocking,
                    estimated_time_days=catalog_task.estimated_time_days,
                    requirement_id=user_task.requirement_id,
                    created_at=user_task.created_at,
                    updated_at=user_task.updated_at,
                )
            )

        return result

    async def regenerate_tasks(self, user_id: str) -> None:
        """
        Recalcula e sincroniza tasks do usuário baseado no producer_profile.

        Args:
            user_id: User's MongoDB ObjectId as string
        """
        # Buscar producer_profile
        producer_profile = await self.producer_service.get_profile_by_user(user_id)
        if not producer_profile:
            self.logger.warning(
                f"Producer profile not found for user {user_id}, skipping task regeneration",
                extra={"user_id": user_id},
            )
            return

        # Converter profile para dict
        profile_dict = producer_profile.model_dump(exclude_none=True)

        # Calcular tasks necessárias usando regras
        required_task_codes = compute_required_tasks(profile_dict)

        # Sincronizar tasks
        await self.repo.sync_user_tasks(user_id, required_task_codes)

    async def update_task_status(
        self, user_id: str, task_code: str, status: str
    ) -> FormalizationTaskUser | None:
        """
        Update task status for a user.

        Args:
            user_id: User's MongoDB ObjectId as string
            task_code: Task code
            status: New status ("pending", "done", "skipped")

        Returns:
            Updated task if found, None otherwise

        Raises:
            ValueError: If status is invalid
        """
        if status not in ("pending", "done", "skipped"):
            raise ValueError(f"Invalid status: {status}. Must be 'pending', 'done', or 'skipped'")

        # Update task status
        updated_task = await self.repo.update_task_status(user_id, task_code, status)

        # If task is marked as done, update producer profile to reflect completion
        # This ensures the score is recalculated correctly
        if status == "done" and updated_task:
            await self._update_profile_from_task_completion(user_id, task_code)
            # Regenerate tasks after updating profile (new tasks may appear, old ones may disappear)
            await self.regenerate_tasks(user_id)

        # Invalidate cached status to force recalculation on next get_or_calculate_status call
        user_oid = to_object_id(user_id)
        await self.status_collection.delete_many({"user_id": user_oid})

        return updated_task

    async def _update_profile_from_task_completion(self, user_id: str, task_code: str) -> None:
        """
        Update producer profile flags and onboarding answers when a task is completed.
        
        Maps task codes to profile flags and question IDs so the score can be recalculated correctly.
        """
        user_oid = to_object_id(user_id)
        
        # Map task codes to profile flags and question IDs
        task_mapping = {
            "HAS_CPF": {
                "profile_flags": {"has_cpf": True},
                "question_id": "has_cpf",
                "answer": True,
            },
            "HAS_FAMILY_FARMER_REGISTRATION": {
                "profile_flags": {"has_family_farmer_registration": True, "has_dap_caf": True},
                "question_id": "has_dap_caf",
                "answer": True,
            },
            "HAS_BANK_ACCOUNT": {
                "profile_flags": {"has_bank_account": True},
                "question_id": "has_bank_account",
                "answer": True,
            },
            "HAS_ADDRESS_PROOF": {
                "profile_flags": {"has_address_proof": True},
                "question_id": "has_address_proof",
                "answer": True,
            },
        }
        
        if task_code in task_mapping:
            mapping = task_mapping[task_code]
            
            # Update producer profile FIRST (this is the source of truth for score calculation)
            if "profile_flags" in mapping:
                result = await self.db.producer_profiles.update_one(
                    {"user_id": user_oid},
                    {"$set": mapping["profile_flags"]},
                    upsert=False,  # Don't create if doesn't exist
                )
                self.logger.info(
                    f"Updated producer profile for task {task_code}: {result.modified_count} documents modified",
                    extra={"user_id": user_id, "task_code": task_code, "flags": mapping["profile_flags"]}
                )
            
            # Also update onboarding answer for consistency
            if "question_id" in mapping and "answer" in mapping:
                question_id = mapping["question_id"]
                answer_value = mapping["answer"]
                
                # Update onboarding answer directly (simpler and more reliable)
                now = utc_now()
                result = await self.onboarding_service.collection.update_one(
                    {"user_id": user_oid, "question_id": question_id},
                    {
                        "$set": {
                            "answer": answer_value,
                            "answered_at": now,
                        }
                    },
                    upsert=True,
                )
                self.logger.info(
                    f"Updated onboarding answer for task {task_code}: question_id={question_id}, answer={answer_value}",
                    extra={"user_id": user_id, "task_code": task_code, "question_id": question_id}
                )

    async def update_task_completion(
        self, user_id: str, task_id: str, completed: bool
    ) -> FormalizationTaskInDB:
        """
        Update task completion status (método legado para compatibilidade).

        Args:
            user_id: User's MongoDB ObjectId as string
            task_id: Task ID (task_id field, not MongoDB _id)
            completed: Whether the task is completed

        Returns:
            Updated task

        Raises:
            ValueError: If task not found
        """
        user_oid = to_object_id(user_id)
        now = utc_now()

        # Find task by task_id and user_id
        task_doc = await self.tasks_collection.find_one(
            {"user_id": user_oid, "task_id": task_id}
        )

        if not task_doc:
            raise ValueError(f"Task with task_id '{task_id}' not found for user")

        # Update completion status
        update_data = {
            "completed": completed,
            "completed_at": now if completed else None,
        }

        await self.tasks_collection.update_one(
            {"_id": task_doc["_id"], "user_id": user_oid},
            {"$set": update_data},
        )

        # Fetch updated task
        updated_doc = await self.tasks_collection.find_one(
            {"_id": task_doc["_id"], "user_id": user_oid}
        )
        return FormalizationTaskInDB(**updated_doc)

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
            except Exception as e:
                self.logger.warning(
                    f"Failed to fetch producer profile for user {user_id}: {e}",
                    exc_info=True,
                    extra={"user_id": user_id}
                )

        # Get onboarding questions for dynamic matching
        questions_dict: dict[str, Any] = {}
        try:
            questions_list = await self.onboarding_service._get_questions_list()
            for q in questions_list:
                questions_dict[q.question_id] = q
        except Exception as e:
            # If questions not available, pass None (fallback to old logic)
            self.logger.warning(
                f"Failed to fetch onboarding questions for user {user_id}: {e}",
                exc_info=True,
                extra={"user_id": user_id}
            )
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
        # Also remove CNPJ tasks for individual producers
        current_task_ids = {t["task_id"] for t in new_tasks}
        producer_type_pref = responses.get("producer_type") if responses else None
        is_individual = is_individual_producer(producer_type_pref)
        
        for existing_task_id, existing_task in existing_tasks_map.items():
            # Remove CNPJ task if producer is individual
            if existing_task_id == "obtain_cnpj" and is_individual:
                await self.tasks_collection.delete_one({"_id": existing_task.id})
                continue
            
            # Remove "learn_public_programs" task - not useful
            if existing_task_id == "learn_public_programs":
                await self.tasks_collection.delete_one({"_id": existing_task.id})
                continue
            
            # Remove completed tasks that are no longer in the list
            if existing_task_id not in current_task_ids and existing_task.completed:
                await self.tasks_collection.delete_one({"_id": existing_task.id})

    def _has_diagnosis_changed(self, cached_doc: dict[str, Any], new_diagnosis: dict[str, Any]) -> bool:
        """Check if diagnosis has changed compared to cached version."""
        return (
            cached_doc.get("is_eligible") != new_diagnosis["is_eligible"]
            or cached_doc.get("score") != new_diagnosis["score"]
            or set(cached_doc.get("requirements_met", [])) != set(new_diagnosis["requirements_met"])
            or set(cached_doc.get("requirements_missing", [])) != set(new_diagnosis["requirements_missing"])
        )
