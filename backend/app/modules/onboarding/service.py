"""
Onboarding module service.
Business logic for onboarding operations.
"""

import logging
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
        self.logger = logging.getLogger(__name__)
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
        Auto-seeds questions if database is empty.

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

        # If no questions found, auto-seed from CSV
        if not questions:
            try:
                from app.modules.onboarding.seeds import seed_onboarding_questions
                await seed_onboarding_questions(self.db)
            except Exception as e:
                # Fallback to default questions if CSV fails
                self.logger.warning(
                    f"Failed to load questions from CSV, using default: {e}",
                    exc_info=True,
                )
                await self.seed_default_questions()
            # Reload after seeding
            cursor = self.questions_collection.find().sort("order", 1)
            async for doc in cursor:
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
        
        # Validate multi-select answers
        if question.allow_multiple:
            if not isinstance(data.answer, list):
                from app.core.errors import ValidationError
                raise ValidationError("Answer must be a list for multi-select questions")
            if not all(isinstance(item, str) for item in data.answer):
                from app.core.errors import ValidationError
                raise ValidationError("All items in multi-select answer must be strings")
            if len(data.answer) == 0:
                from app.core.errors import ValidationError
                raise ValidationError("At least one option must be selected for multi-select questions")

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

        # Update producer profile incrementally based on answer
        await self._update_profile_from_answer(user_id, data.question_id, data.answer)
        
        # Update producer profile onboarding status (creates profile if needed)
        await self._update_profile_status(user_id)
        
        # If onboarding just completed, create/update profile from all answers
        onboarding_status = await self.get_status(user_id)
        if onboarding_status.status == OnboardingStatus.COMPLETED:
            await self._create_profile_from_answers(user_id)

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
        
        # Filter answered_count to only include questions that still exist
        # This prevents progress > 100% if questions were removed from catalog
        valid_question_ids = {q.question_id for q in all_questions}
        answered_count = len([qid for qid in answered_question_ids if qid in valid_question_ids])
        
        if answered_count == 0:
            status = OnboardingStatus.NOT_STARTED
        elif answered_count >= total_questions:
            status = OnboardingStatus.COMPLETED
        else:
            status = OnboardingStatus.IN_PROGRESS

        # Find next unanswered question (by order)
        next_question = None
        unanswered = [q for q in all_questions if q.question_id not in answered_question_ids]
        
        # Skip cnpj if producer_type is not formal
        for question in unanswered:
            if question.question_id == "cnpj":
                producer_type_answer = await self.get_answer_value(user_id, "producer_type")
                if producer_type_answer not in ["Formal (CNPJ)", "Formal", "Grupo Formal (CNPJ)"]:
                    continue  # Skip CNPJ for non-formal producers
            
            # This question should be shown
            next_question = question
            break

        # Calculate progress (ensure it never exceeds 100%)
        if total_questions > 0:
            progress = min((answered_count / total_questions * 100), 100.0)
        else:
            progress = 0.0

        # Get completion date if completed
        completed_at = None
        if status == OnboardingStatus.COMPLETED:
            # Get the latest answered_at
            cursor = self.collection.find({"user_id": user_oid}).sort("answered_at", -1).limit(1)
            latest_doc = await cursor.to_list(length=1)
            if latest_doc:
                completed_at = latest_doc[0]["answered_at"]
            
            # Ensure profile exists if onboarding is completed (only if not already checking)
            # Avoid recursion by checking if profile exists first
            existing_profile = await self.profiles_collection.find_one({"user_id": user_oid})
            if not existing_profile:
                try:
                    await self._ensure_profile_exists(user_id)
                except Exception as e:
                    # Log error but don't fail the status request
                    import traceback
                    print(f"Error ensuring profile exists: {e}")
                    print(traceback.format_exc())

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
    
    async def get_answer_value(self, user_id: str, question_id: str) -> Any | None:
        """
        Get a specific answer value for a user.

        Args:
            user_id: User's MongoDB ObjectId as string
            question_id: Question ID

        Returns:
            Answer value if found, None otherwise
        """
        answers = await self.get_all_answers(user_id)
        answer = answers.get(question_id)
        return answer.answer if answer else None

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

    async def _update_profile_from_answer(self, user_id: str, question_id: str, answer: Any) -> None:
        """Update producer profile incrementally based on onboarding answer."""
        try:
            user_oid = to_object_id(user_id)
            now = utc_now()
            
            # Get or create profile
            existing = await self.profiles_collection.find_one({"user_id": user_oid})
            if not existing:
                # Create minimal profile
                await self.profiles_collection.insert_one({
                    "user_id": user_oid,
                    "created_at": now,
                    "updated_at": now,
                })
            
            # Update profile based on question
            update_doc: dict[str, Any] = {"updated_at": now}
            
            # Get question to check sets_flag
            question = await self._get_question_by_id(question_id)
            
            # Handle legacy question IDs for backward compatibility
            if question_id == "producer_type":
                producer_type_map = {
                    "Individual": "individual",
                    "Informal": "informal",
                    "Formal (CNPJ)": "formal",
                    "Grupo Informal": "informal",
                    "Grupo Formal (CNPJ)": "formal",
                    "sozinho": "individual",
                    "grupo": "informal",
                }
                producer_type_str = str(answer)
                update_doc["producer_type"] = producer_type_map.get(producer_type_str, "individual")
            
            elif question_id == "name":
                update_doc["name"] = str(answer).strip()
            
            elif question_id == "address":
                update_doc["address"] = str(answer).strip()
            
            elif question_id == "city":
                update_doc["city"] = str(answer).strip()
            
            elif question_id == "state":
                update_doc["state"] = str(answer).strip().upper()[:2]
            
            elif question_id == "cnpj":
                cnpj_clean = "".join(filter(str.isdigit, str(answer)))[:14]
                if cnpj_clean:
                    update_doc["cnpj"] = cnpj_clean
            
            # Use sets_flag from CSV if available
            if question and question.sets_flag:
                # Convert answer to appropriate type based on question type
                if question.question_type == QuestionType.CHOICE and not question.allow_multiple:
                    # For single_choice, check if answer is "sim" or True
                    # Handle both string and boolean answers
                    if isinstance(answer, str):
                        bool_value = answer.lower() in ["sim", "yes", "true", "1"]
                    else:
                        bool_value = bool(answer)
                    update_doc[question.sets_flag] = bool_value
                elif question.question_type == QuestionType.BOOLEAN:
                    update_doc[question.sets_flag] = bool(answer)
                elif question.allow_multiple:
                    # For multi_choice, store as list
                    if isinstance(answer, list):
                        update_doc[question.sets_flag] = answer
                    else:
                        update_doc[question.sets_flag] = [answer] if answer else []
                else:
                    # For other types (text, etc), store the value directly
                    # But apply special formatting for specific fields
                    if question.sets_flag == "name":
                        update_doc[question.sets_flag] = str(answer).strip()
                    elif question.sets_flag == "address":
                        update_doc[question.sets_flag] = str(answer).strip()
                    elif question.sets_flag == "city":
                        update_doc[question.sets_flag] = str(answer).strip()
                    elif question.sets_flag == "state":
                        update_doc[question.sets_flag] = str(answer).strip().upper()[:2]
                    else:
                        update_doc[question.sets_flag] = answer
                
                # Special handling for producer_mode -> producer_type mapping
                if question.sets_flag == "producer_mode":
                    # Map producer_mode to producer_type
                    producer_mode_map = {
                        "sozinho": "individual",
                        "grupo": "informal",
                    }
                    if isinstance(answer, str):
                        producer_type = producer_mode_map.get(answer.lower(), "individual")
                        update_doc["producer_type"] = producer_type
                
                # Special handling for has_family_farmer_registration
                if question.sets_flag == "has_family_farmer_registration":
                    if isinstance(answer, str):
                        bool_value = answer.lower() in ["sim", "yes", "true", "1"]
                    else:
                        bool_value = bool(answer)
                    update_doc["has_dap_caf"] = bool_value
            
            # Legacy handling for backward compatibility
            elif question_id == "has_dap_caf":
                update_doc["has_dap_caf"] = bool(answer)
                update_doc["has_family_farmer_registration"] = bool(answer)
            
            elif question_id == "has_bank_account":
                update_doc["has_bank_account"] = bool(answer)
            
            elif question_id == "has_cnpj":
                update_doc["has_cnpj"] = bool(answer)
            
            elif question_id == "has_previous_sales" or question_id == "experience_1":
                # Usar como proxy para wants_to_sell_to_school se não tiver sido setado
                if "wants_to_sell_to_school" not in update_doc:
                    update_doc["wants_to_sell_to_school"] = bool(answer)
            
            # Update profile
            if update_doc:
                await self.profiles_collection.update_one(
                    {"user_id": user_oid},
                    {"$set": update_doc},
                )
        except Exception as e:
            # Don't fail if profile update fails
            self.logger.warning(
                f"Failed to update profile from answer for user {user_id}: {e}",
                exc_info=True,
                extra={"user_id": user_id, "question_id": question_id, "operation": "_update_profile_from_answer"}
            )

    async def _update_profile_status(self, user_id: str) -> None:
        """Update onboarding status in producer profile. Creates profile if it doesn't exist."""
        status = await self.get_status(user_id)

        update_doc: dict[str, Any] = {"onboarding_status": status.status.value}

        if status.status == OnboardingStatus.COMPLETED and status.completed_at:
            update_doc["onboarding_completed_at"] = status.completed_at

        user_oid = to_object_id(user_id)
        now = utc_now()
        
        # Use upsert to create profile if it doesn't exist
        await self.profiles_collection.update_one(
            {"user_id": user_oid},
            {
                "$set": {**update_doc, "updated_at": now},
                "$setOnInsert": {
                    "user_id": user_oid,
                    "created_at": now,
                },
            },
            upsert=True,
        )

    async def _create_profile_from_answers(self, user_id: str) -> None:
        """Create producer profile automatically from onboarding answers."""
        try:
            # Get all answers
            answers = await self.get_all_answers(user_id)
            
            # Check if profile already exists with required fields
            user_oid = to_object_id(user_id)
            existing = await self.profiles_collection.find_one({"user_id": user_oid})
            if existing:
                # Check only truly required fields (dap_caf_number is optional)
                required_fields = {"producer_type", "name", "address", "city", "state"}
                existing_fields = set(existing.keys())
                # Check if all required fields exist and are not placeholder values
                placeholder_values = {"Nome não informado", "Endereço não informado", "Cidade não informada", "XX"}
                has_all_required = required_fields.issubset(existing_fields) and all(
                    existing.get(field) and str(existing.get(field)) not in placeholder_values 
                    for field in required_fields
                )
                if has_all_required:
                    # Profile already exists with all required fields and real values (not placeholders)
                    return
                # If profile exists but has placeholders, continue to update it with real values
            
            # Map answers to profile fields
            producer_type_map = {
                "Individual": "individual",
                "Informal": "informal",
                "Formal (CNPJ)": "formal",
                "Grupo Informal": "informal",
                "Grupo Formal (CNPJ)": "formal",
            }
            
            producer_type_answer = answers.get("producer_type")
            if not producer_type_answer:
                return  # Can't create profile without producer type
            
            producer_type_str = str(producer_type_answer.answer)
            producer_type = producer_type_map.get(producer_type_str, "individual")
            
            # Get DAP/CAF number from profile (saved directly when user entered it)
            user_oid_check = to_object_id(user_id)
            profile_doc = await self.profiles_collection.find_one({"user_id": user_oid_check})
            dap_caf_number = profile_doc.get("dap_caf_number", "") if profile_doc else ""
            
            # DAP/CAF can be None - we'll create profile anyway (can be added later)
            
            # Build profile data
            name_answer = answers.get("name")
            address_answer = answers.get("address")
            city_answer = answers.get("city")
            state_answer = answers.get("state")
            
            # Build profile data with minimal validation (frontend handles detailed validation)
            profile_data = {
                "producer_type": producer_type,
                "name": str(name_answer.answer).strip() if name_answer else "Nome não informado",
                "address": str(address_answer.answer).strip() if address_answer else "Endereço não informado",
                "city": str(city_answer.answer).strip() if city_answer else "Cidade não informada",
                "state": str(state_answer.answer).strip().upper()[:2] if state_answer else "XX",
                "dap_caf_number": dap_caf_number or None,  # Can be None
            }
            
            # Adicionar flags do onboarding para formalização usando sets_flag do CSV
            questions = await self._get_questions()
            for question_id, answer_doc in answers.items():
                question = questions.get(question_id)
                if question and question.sets_flag:
                    answer = answer_doc.answer
                    # Convert answer to appropriate type
                    if question.question_type == QuestionType.CHOICE and not question.allow_multiple:
                        # For single_choice, check if answer is "sim"
                        if isinstance(answer, str):
                            bool_value = answer.lower() in ["sim", "yes", "true", "1"]
                        else:
                            bool_value = bool(answer)
                        profile_data[question.sets_flag] = bool_value
                    elif question.question_type == QuestionType.BOOLEAN:
                        profile_data[question.sets_flag] = bool(answer)
                    elif question.allow_multiple:
                        # For multi_choice, store as list
                        if isinstance(answer, list):
                            profile_data[question.sets_flag] = answer
                        else:
                            profile_data[question.sets_flag] = [answer] if answer else []
                    else:
                        # For other types, store the value directly
                        profile_data[question.sets_flag] = answer
                    
                    # Special handling for producer_mode -> producer_type mapping
                    if question.sets_flag == "producer_mode":
                        # Map producer_mode to producer_type
                        producer_mode_map = {
                            "sozinho": "individual",
                            "grupo": "informal",
                        }
                        if isinstance(answer, str):
                            producer_type = producer_mode_map.get(answer.lower(), "individual")
                            profile_data["producer_type"] = producer_type
                    
                    # Special handling for has_family_farmer_registration
                    if question.sets_flag == "has_family_farmer_registration":
                        if isinstance(answer, str):
                            bool_value = answer.lower() in ["sim", "yes", "true", "1"]
                        else:
                            bool_value = bool(answer)
                        profile_data["has_dap_caf"] = bool_value
            
            # Legacy handling for backward compatibility
            has_dap_caf_answer = answers.get("has_dap_caf")
            if has_dap_caf_answer and "has_dap_caf" not in profile_data:
                profile_data["has_dap_caf"] = bool(has_dap_caf_answer.answer)
                profile_data["has_family_farmer_registration"] = bool(has_dap_caf_answer.answer)
            
            has_bank_account_answer = answers.get("has_bank_account")
            if has_bank_account_answer and "has_bank_account" not in profile_data:
                profile_data["has_bank_account"] = bool(has_bank_account_answer.answer)
            
            # has_cpf pode vir do auth, mas vamos verificar se está no profile
            # Se não estiver, assumir True (CPF é necessário para login)
            if "has_cpf" not in profile_data:
                profile_data["has_cpf"] = True  # CPF vem do auth/login
            
            # Add CNPJ based on producer type (CPF comes from login/auth)
            # Note: has_cnpj is a boolean question, not the CNPJ number itself
            # For now, we don't have the CNPJ number in onboarding, so we skip it
            # User can add it later via profile update
            
            # Ensure all required fields have values (use existing values or defaults)
            # Try to preserve existing values if they're better than defaults
            if existing:
                for field in ["name", "address", "city", "state"]:
                    existing_value = existing.get(field)
                    current_value = profile_data.get(field)
                    # Use existing value if current is a placeholder
                    if existing_value and (
                        current_value in ["Nome não informado", "Endereço não informado", "Cidade não informada", "XX"] or
                        not current_value
                    ):
                        profile_data[field] = existing_value
            
            # Final validation - only producer_type is truly required
            if not profile_data.get("producer_type"):
                self.logger.error(
                    f"Missing producer_type for profile creation",
                    extra={"user_id": user_id, "operation": "_create_profile_from_answers"}
                )
                return
            
            # Create profile using ProducerService
            from app.modules.producers.service import ProducerService
            from app.modules.producers.schemas import ProducerProfileCreate
            
            producer_service = ProducerService(self.db)
            profile_create = ProducerProfileCreate(**profile_data)
            await producer_service.upsert_profile(user_id, profile_create)
            
        except Exception as e:
            self.logger.error(
                f"Failed to create profile from answers for user {user_id}: {e}",
                exc_info=True,
                extra={"user_id": user_id, "operation": "_create_profile_from_answers"}
            )
            # Don't raise - profile creation failure shouldn't break onboarding

    async def _ensure_profile_exists(self, user_id: str) -> None:
        """Ensure producer profile exists for user. Creates minimal profile if missing."""
        try:
            user_oid = to_object_id(user_id)
            existing = await self.profiles_collection.find_one({"user_id": user_oid})
            
            if not existing:
                now = utc_now()
                # Get onboarding status without calling get_status (to avoid recursion)
                user_oid_check = to_object_id(user_id)
                cursor = self.collection.find({"user_id": user_oid_check})
                answered_question_ids = set()
                async for doc in cursor:
                    answered_question_ids.add(doc["question_id"])
                
                all_questions = await self._get_questions_list()
                total_questions = len(all_questions)
                answered_count = len(answered_question_ids)
                
                if answered_count >= total_questions:
                    onboarding_status = OnboardingStatus.COMPLETED
                    # Get completion date
                    cursor = self.collection.find({"user_id": user_oid_check}).sort("answered_at", -1).limit(1)
                    latest_doc = await cursor.to_list(length=1)
                    completed_at = latest_doc[0]["answered_at"] if latest_doc else None
                else:
                    onboarding_status = OnboardingStatus.IN_PROGRESS if answered_count > 0 else OnboardingStatus.NOT_STARTED
                    completed_at = None
                
                await self.profiles_collection.insert_one({
                    "user_id": user_oid,
                    "onboarding_status": onboarding_status.value,
                    "onboarding_completed_at": completed_at,
                    "created_at": now,
                    "updated_at": now,
                })
        except Exception as e:
            # Log error but don't fail - profile creation is not critical for status endpoint
            self.logger.warning(
                f"Failed to ensure profile exists for user {user_id}: {e}",
                exc_info=True,
                extra={"user_id": user_id, "operation": "_ensure_profile_exists"}
            )
            # Re-raise only if it's not a duplicate key error (profile might have been created concurrently)
            if "duplicate" not in str(e).lower() and "E11000" not in str(e):
                raise

    async def seed_default_questions(self) -> None:
        """Seed default onboarding questions into the database based on PNAE guide."""
        default_questions = [
            # Etapa 1: Identificação do Produtor
            {
                "question_id": "producer_type",
                "question_text": "Qual é o tipo do seu empreendimento?",
                "question_type": QuestionType.CHOICE,
                "options": ["Individual", "Grupo Informal", "Grupo Formal (CNPJ)"],
                "order": 1,
                "required": True,
                "requirement_id": None,
                "allow_multiple": False,
            },
            {
                "question_id": "name",
                "question_text": "Qual é o seu nome completo ou razão social?",
                "question_type": QuestionType.TEXT,
                "options": None,
                "order": 2,
                "required": True,
                "requirement_id": None,
                "allow_multiple": False,
            },
            {
                "question_id": "address",
                "question_text": "Qual é o seu endereço completo?",
                "question_type": QuestionType.TEXT,
                "options": None,
                "order": 3,
                "required": True,
                "requirement_id": None,
                "allow_multiple": False,
            },
            {
                "question_id": "city",
                "question_text": "Em qual cidade você está localizado?",
                "question_type": QuestionType.TEXT,
                "options": None,
                "order": 4,
                "required": True,
                "requirement_id": None,
                "allow_multiple": False,
            },
            {
                "question_id": "state",
                "question_text": "Qual é o seu estado (UF)?",
                "question_type": QuestionType.TEXT,
                "options": None,
                "order": 5,
                "required": True,
                "requirement_id": None,
                "allow_multiple": False,
            },
            # Etapa 2: Documentação Essencial
            {
                "question_id": "has_dap_caf",
                "question_text": "Você possui DAP/CAF (Declaração de Aptidão ao Pronaf)?",
                "question_type": QuestionType.BOOLEAN,
                "options": None,
                "order": 6,
                "required": True,
                "requirement_id": "dap_caf",
                "allow_multiple": False,
            },
            {
                "question_id": "has_cnpj",
                "question_text": "Você possui CNPJ? (obrigatório para grupos formais)",
                "question_type": QuestionType.BOOLEAN,
                "options": None,
                "order": 7,
                "required": True,
                "requirement_id": "cnpj",
                "allow_multiple": False,
            },
            {
                "question_id": "has_address_proof",
                "question_text": "Você possui comprovante de endereço?",
                "question_type": QuestionType.BOOLEAN,
                "options": None,
                "order": 8,
                "required": True,
                "requirement_id": "proof_address",
                "allow_multiple": False,
            },
            {
                "question_id": "has_bank_account",
                "question_text": "Você possui conta bancária?",
                "question_type": QuestionType.BOOLEAN,
                "options": None,
                "order": 9,
                "required": True,
                "requirement_id": "bank_statement",
                "allow_multiple": False,
            },
            # Etapa 3: Produção
            {
                "question_id": "production_type",
                "question_text": "Qual tipo de produção você realiza?",
                "question_type": QuestionType.CHOICE,
                "options": ["Agricultura", "Pecuária", "Agricultura e Pecuária", "Extrativismo", "Outro"],
                "order": 10,
                "required": True,
                "requirement_id": None,
                "allow_multiple": False,
            },
            {
                "question_id": "main_products",
                "question_text": "Quais são seus principais produtos? (selecione todos que se aplicam)",
                "question_type": QuestionType.CHOICE,
                "options": [
                    # Frutas
                    "Abacaxi", "Banana", "Melancia", "Pupunha", "Açaí", "Bacaba",
                    # Vegetais e Hortaliças
                    "Couve", "Macaxeira/Mandioca", "Batata", "Cebola", "Tomate",
                    # Processados
                    "Farinha de Mandioca", "Beiju", "Goma/Tapioca", "Polpa de Frutas", "Suco de Frutas",
                    # Proteínas
                    "Peixe", "Galinha Caipira", "Pato", "Ovo",
                    # Grãos e Cereais
                    "Arroz", "Feijão", "Milho",
                    # Outros
                    "Mel", "Outro"
                ],
                "order": 11,
                "required": True,
                "requirement_id": None,
                "allow_multiple": True,  # Multi-select
            },
            {
                "question_id": "production_capacity",
                "question_text": "Qual é sua capacidade de produção mensal aproximada? (em kg ou litros)",
                "question_type": QuestionType.TEXT,
                "options": None,
                "order": 12,
                "required": True,
                "requirement_id": None,
                "allow_multiple": False,
            },
            # Etapa 4: Experiência
            {
                "question_id": "has_previous_sales",
                "question_text": "Você já vendeu para programas públicos anteriormente? (PNAE, PAA, etc.)",
                "question_type": QuestionType.BOOLEAN,
                "options": None,
                "order": 13,
                "required": True,
                "requirement_id": None,
                "allow_multiple": False,
            },
            {
                "question_id": "is_indigenous_or_traditional",
                "question_text": "Você faz parte de povo indígena ou comunidade tradicional? (quilombola, ribeirinha, etc.)",
                "question_type": QuestionType.BOOLEAN,
                "options": None,
                "order": 14,
                "required": True,
                "requirement_id": None,
                "allow_multiple": False,
            },
        ]

        for question_data in default_questions:
            question = OnboardingQuestion(**question_data)
            await self.questions_collection.update_one(
                {"question_id": question.question_id},
                {"$set": question.model_dump()},
                upsert=True,
            )

        # Invalidate cache to reload questions
        self._invalidate_cache()
