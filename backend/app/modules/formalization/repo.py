"""
Formalization repository module.
Data access layer for formalization tasks catalog and user tasks.
"""

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.formalization.schemas import FormalizationTaskCatalog, FormalizationTaskUser
from app.shared.utils import to_object_id, utc_now


class FormalizationRepository:
    """Repository for formalization tasks."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.catalog_collection = db.formalization_tasks_catalog
        self.user_tasks_collection = db.formalization_tasks_user
        self.logger = logging.getLogger(__name__)

    async def get_task_catalog(self, task_code: str) -> FormalizationTaskCatalog | None:
        """
        Get a task from the catalog by code.

        Args:
            task_code: Task code

        Returns:
            Task catalog entry if found, None otherwise
        """
        doc = await self.catalog_collection.find_one({"code": task_code})
        if not doc:
            return None
        return FormalizationTaskCatalog(**doc)

    async def get_all_catalog_tasks(self) -> dict[str, FormalizationTaskCatalog]:
        """
        Get all tasks from the catalog.

        Returns:
            Dictionary mapping task_code to FormalizationTaskCatalog
        """
        cursor = self.catalog_collection.find()
        tasks = {}
        async for doc in cursor:
            task = FormalizationTaskCatalog(**doc)
            tasks[task.code] = task
        return tasks

    async def get_user_tasks(self, user_id: str) -> list[FormalizationTaskUser]:
        """
        Get all tasks for a user.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            List of user tasks
        """
        user_oid = to_object_id(user_id)
        cursor = self.user_tasks_collection.find({"user_id": user_oid}).sort("created_at", 1)
        tasks = []
        async for doc in cursor:
            tasks.append(FormalizationTaskUser(**doc))
        return tasks

    async def _get_requirement_id_for_task_code(self, task_code: str) -> str | None:
        """
        Busca requirement_id para um task_code baseado no affects_task do CSV de onboarding.
        
        Args:
            task_code: Task code (ex: HAS_CPF, HAS_BANK_ACCOUNT)
            
        Returns:
            requirement_id se encontrado, None caso contrário
        """
        try:
            from app.modules.onboarding.service import OnboardingService
            onboarding_service = OnboardingService(self.db)
            questions = await onboarding_service._get_questions()
            
            # Buscar pergunta que tem affects_task igual ao task_code
            for question in questions.values():
                if question.affects_task == task_code:
                    # Priorizar requirement_id da pergunta (é o que o sistema de IA espera)
                    if question.requirement_id:
                        return question.requirement_id
                    # Se não tem requirement_id, usar sets_flag como fallback
                    if question.sets_flag:
                        return question.sets_flag
            
            # Mapeamento direto para casos conhecidos
            # Mapeia task_code para requirement_id usado pelo sistema de IA
            # O sistema de IA espera requirement_ids específicos (dap_caf, bank_statement, etc.)
            # Baseado no código do ai_formalization, os requirement_ids esperados são:
            # - "dap_caf" (não "has_family_farmer_registration")
            # - "bank_statement" (não "has_bank_account")
            # - "has_cpf" ou "cpf"
            task_to_requirement_map = {
                "HAS_CPF": "has_cpf",  # Sistema pode usar "has_cpf" ou "cpf"
                "HAS_FAMILY_FARMER_REGISTRATION": "dap_caf",  # Sistema IA usa "dap_caf"
                "HAS_BANK_ACCOUNT": "bank_statement",  # Sistema IA usa "bank_statement"
                "HAS_ADDRESS_PROOF": "proof_address",  # Sistema IA usa "proof_address"
                "SALES_PROJECT_READY": None,  # Não tem requirement_id específico
                "PUBLIC_CALL_SUBMISSION_READY": None,  # Não tem requirement_id específico
                "PRODUCTION_IS_ELIGIBLE": None,  # Não tem requirement_id específico
                "BASIC_DOCUMENTS_READY": None,  # Não tem requirement_id específico
            }
            mapped_id = task_to_requirement_map.get(task_code)
            if mapped_id:
                return mapped_id
            
            # Se não encontrou no mapeamento, retornar None
            return None
        except Exception as e:
            self.logger.warning(
                f"Failed to get requirement_id for task_code {task_code}: {e}",
                exc_info=True,
                extra={"task_code": task_code}
            )
            return None

    async def sync_user_tasks(
        self, user_id: str, required_task_codes: list[str]
    ) -> None:
        """
        Sincroniza tasks do usuário com as tasks necessárias.

        Regras:
        1. Manter tasks já existentes
        2. Preservar status "done"
        3. Criar novas tasks se necessárias
        4. NÃO deletar tasks antigas (marcar como "skipped" se não aplicável)

        Args:
            user_id: User's MongoDB ObjectId as string
            required_task_codes: Lista de task_codes que devem estar ativas
        """
        user_oid = to_object_id(user_id)
        now = utc_now()

        # Get all catalog tasks to get blocking info
        catalog_tasks = await self.get_all_catalog_tasks()

        # Get existing user tasks
        existing_tasks = await self.get_user_tasks(user_id)
        existing_task_codes = {task.task_code for task in existing_tasks}
        existing_tasks_map = {task.task_code: task for task in existing_tasks}

        # Set of required task codes
        required_set = set(required_task_codes)

        # Process existing tasks
        for existing_task in existing_tasks:
            task_code = existing_task.task_code

            if task_code in required_set:
                # Task ainda é necessária - manter status se for "done", senão pode ser "pending"
                # Mas atualizar requirement_id se não existir
                if existing_task.status == "done":
                    # Manter como done, mas atualizar requirement_id se necessário
                    if not existing_task.requirement_id:
                        requirement_id = await self._get_requirement_id_for_task_code(task_code)
                        if requirement_id:
                            await self.user_tasks_collection.update_one(
                                {"_id": existing_task.id, "user_id": user_oid},
                                {"$set": {"requirement_id": requirement_id, "updated_at": now}},
                            )
                    continue
                elif existing_task.status == "skipped":
                    # Reativar task que estava skipped e atualizar requirement_id
                    requirement_id = await self._get_requirement_id_for_task_code(task_code)
                    update_data = {
                        "status": "pending",
                        "updated_at": now,
                    }
                    if requirement_id:
                        update_data["requirement_id"] = requirement_id
                    await self.user_tasks_collection.update_one(
                        {"_id": existing_task.id, "user_id": user_oid},
                        {"$set": update_data},
                    )
            else:
                # Task não é mais necessária - marcar como skipped se não estiver done
                if existing_task.status != "done":
                    await self.user_tasks_collection.update_one(
                        {"_id": existing_task.id, "user_id": user_oid},
                        {
                            "$set": {
                                "status": "skipped",
                                "updated_at": now,
                            }
                        },
                    )

        # Create new tasks that don't exist yet
        for task_code in required_task_codes:
            if task_code not in existing_task_codes:
                # Get task from catalog to get blocking info
                catalog_task = catalog_tasks.get(task_code)
                if not catalog_task:
                    self.logger.warning(
                        f"Task code '{task_code}' not found in catalog, skipping",
                        extra={"user_id": user_id, "task_code": task_code},
                    )
                    continue

                # Get requirement_id for AI guide generation
                requirement_id = await self._get_requirement_id_for_task_code(task_code)

                # Create new user task
                task_doc = {
                    "user_id": user_oid,
                    "task_code": task_code,
                    "status": "pending",
                    "blocking": catalog_task.blocking,
                    "requirement_id": requirement_id,
                    "created_at": now,
                    "updated_at": now,
                }
                await self.user_tasks_collection.insert_one(task_doc)

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
        """
        user_oid = to_object_id(user_id)
        now = utc_now()

        update_doc: dict[str, Any] = {
            "status": status,
            "updated_at": now,
        }

        result = await self.user_tasks_collection.find_one_and_update(
            {"user_id": user_oid, "task_code": task_code},
            {"$set": update_doc},
            return_document=True,
        )

        if not result:
            return None

        return FormalizationTaskUser(**result)
