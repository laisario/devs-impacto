"""
AI Formalization service.
Orchestrates guide generation using RAG and LLM.
"""

import asyncio
import json
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.errors import NotFoundError, ValidationError
from app.modules.ai_formalization.llm_client import LLMClient
from app.modules.ai_formalization.prompts import build_prompt, build_personalized_prompt
from app.modules.ai_formalization.rag import RAGService
from app.modules.ai_formalization.schemas import (
    FormalizationGuideInDB,
    FormalizationGuideResponse,
)
from app.modules.onboarding.schemas import OnboardingQuestion
from app.modules.onboarding.service import OnboardingService
from app.modules.producers.service import ProducerService
from app.shared.utils import to_object_id, utc_now


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
        self.guides_collection = db.formalization_guides

    async def generate_guide(
        self, user_id: str, requirement_id: str, force_regenerate: bool = False
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

        # 2. Get producer profile (may be None - that's OK, we'll use onboarding answers)
        producer_profile = None
        profile_dict = None
        try:
            producer_profile = await self.producer_service.get_profile_by_user(user_id)
            if producer_profile:
                profile_dict = producer_profile.model_dump(exclude_none=True)
        except Exception:
            # Profile doesn't exist yet - try to get basic info from onboarding answers
            pass
        
        # If profile is None, try to get location from onboarding answers
        if not profile_dict:
            answers_for_profile = await self.onboarding_service.get_all_answers(user_id)
            answers_dict_for_profile = {qid: ans.answer for qid, ans in answers_for_profile.items()}
            # Build minimal profile dict from onboarding
            if answers_dict_for_profile:
                profile_dict = {
                    "name": answers_dict_for_profile.get("name", ""),
                    "city": answers_dict_for_profile.get("city", ""),
                    "state": answers_dict_for_profile.get("state", ""),
                    "address": answers_dict_for_profile.get("address", ""),
                    "producer_type": answers_dict_for_profile.get("producer_type", ""),
                }

        # 3. Get all onboarding answers for richer context
        answers = await self.onboarding_service.get_all_answers(user_id)
        answers_dict = {qid: ans.answer for qid, ans in answers.items()}
        user_answer = answers.get(question.question_id)
        current_answer = None
        if user_answer:
            current_answer = user_answer.answer

        # 4. Get formalization status (optional, for additional context)
        formalization_status = None
        try:
            from app.modules.formalization.service import FormalizationService
            formalization_service = FormalizationService(self.db)
            formalization_status = await formalization_service.get_or_calculate_status(user_id)
        except Exception:
            # If formalization service not available, continue without it
            pass

        # 5. Format requirement text with context
        requirement_text = self._format_requirement_text(question, current_answer)

        # 6. Search relevant RAG chunks (enhanced: more chunks and related terms)
        rag_chunks = await self.rag_service.search_relevant_chunks(
            requirement_id, limit=15
        )
        
        # Search for related terms based on requirement_id
        related_queries = []
        requirement_synonyms = {
            "cnpj": ["mei", "microempreendedor", "cnpj online", "formalização", "empresa"],
            "dap_caf": ["dap", "caf", "declaração aptidão", "pronaf"],
            "bank_account": ["conta bancária", "banco", "abrir conta"],
            "address_proof": ["comprovante endereço", "comprovante residência"],
        }
        
        if requirement_id in requirement_synonyms:
            related_queries.extend(requirement_synonyms[requirement_id])
        
        # Also search for online/portal terms
        online_queries = ["online", "portal", "site", "gov.br"]
        for online_term in online_queries:
            related_queries.append(f"{requirement_id} {online_term}")
        
        # If we have location info, also search for location-specific chunks
        location_queries = []
        if profile_dict:
            if profile_dict.get("city"):
                location_queries.append(profile_dict["city"])
            if profile_dict.get("state"):
                location_queries.append(profile_dict["state"])
            if profile_dict.get("city") and profile_dict.get("state"):
                location_queries.append(f"{profile_dict['city']} {profile_dict['state']}")
        elif answers_dict:
            city = answers_dict.get("city")
            state = answers_dict.get("state")
            if city:
                location_queries.append(str(city))
            if state:
                location_queries.append(str(state))
            if city and state:
                location_queries.append(f"{city} {state}")
        
        # Search for related chunks
        related_chunks = []
        for query in related_queries[:5]:  # Limit to avoid too many requests
            try:
                chunks = await self.rag_service.search_relevant_chunks(query, limit=3)
                related_chunks.extend(chunks)
            except Exception:
                pass
        
        # Search for location-specific chunks (Emater, Secretaria, etc. in that location)
        location_chunks = []
        for query in location_queries[:2]:  # Limit to avoid too many requests
            try:
                # Search for location + requirement combination
                loc_query = f"{query} {requirement_id}"
                loc_chunks = await self.rag_service.search_relevant_chunks(loc_query, limit=5)
                location_chunks.extend(loc_chunks)
            except Exception:
                pass
        
        # Combine and deduplicate chunks
        all_chunks = rag_chunks + related_chunks + location_chunks
        seen_ids = set()
        unique_chunks = []
        for chunk in all_chunks:
            chunk_id = str(chunk.id) if hasattr(chunk, 'id') else None
            if chunk_id and chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_chunks.append(chunk)
            elif not chunk_id:
                unique_chunks.append(chunk)
        
        chunks_dict = [chunk.model_dump(exclude={'id', 'embedding'}, exclude_none=True) for chunk in unique_chunks[:25]]

        # 7. Get complete context (documents, tasks, etc.)
        complete_context = await self._get_complete_context(user_id)
        
        # 8. Build personalized prompt with enriched context
        prompt = build_personalized_prompt(
            profile_dict, 
            requirement_text, 
            chunks_dict,
            answers_dict,
            formalization_status,
            complete_context,
            requirement_id=requirement_id
        )

        # 9. Call LLM
        try:
            llm_response = await self.llm_client.generate(prompt)
        except Exception as e:
            # Log error for debugging
            print(f"Error calling LLM: {e}")
            print(f"Prompt length: {len(prompt)}")
            # Fallback to generic guide if LLM fails
            # But try to make fallback more contextual
            return self._get_contextual_fallback_guide(question, profile_dict, answers_dict, formalization_status, requirement_id)

        # 10. Parse and validate JSON response
        try:
            # Try to parse JSON - might be wrapped or need cleaning
            response_data = json.loads(llm_response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks or other wrappers
            try:
                # Remove markdown code blocks if present
                cleaned = llm_response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                elif cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
                response_data = json.loads(cleaned)
            except (json.JSONDecodeError, ValueError):
                # Log the response for debugging
                print(f"Failed to parse LLM response as JSON. Response: {llm_response[:500]}")
                # Fallback if JSON is invalid - use contextual fallback
                return self._get_contextual_fallback_guide(question, profile_dict, answers_dict, formalization_status, requirement_id)

        # 11. Validate and parse with Pydantic
        try:
            guide = FormalizationGuideResponse(**response_data)
        except Exception as e:
            # Log validation error for debugging
            print(f"Failed to validate LLM response: {e}")
            print(f"Response data: {response_data}")
            # Fallback if validation fails
            return self._get_contextual_fallback_guide(question, profile_dict, answers_dict, formalization_status, requirement_id)

        # 12. Ensure steps are valid (already validated by Pydantic)
        # 13. Store guide in database
        await self._store_guide(user_id, requirement_id, guide)
        
        return guide

    async def _get_complete_context(self, user_id: str) -> dict[str, Any]:
        """
        Get complete context for prompt enhancement.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            Dictionary with complete context including documents, tasks, etc.
        """
        user_oid = to_object_id(user_id)
        context: dict[str, Any] = {
            "documents": [],
            "tasks_completed": [],
            "tasks_pending": [],
        }
        
        # Get documents
        try:
            from app.modules.documents.service import DocumentsService
            documents_service = DocumentsService(self.db)
            documents_cursor = self.db.documents.find({"user_id": user_oid})
            async for doc in documents_cursor:
                context["documents"].append({
                    "type": doc.get("doc_type"),
                    "status": doc.get("status"),
                    "ai_validated": doc.get("ai_validated"),
                })
        except Exception:
            pass
        
        # Get tasks
        try:
            from app.modules.formalization.service import FormalizationService
            formalization_service = FormalizationService(self.db)
            tasks = await formalization_service.get_tasks(user_id)
            for task in tasks:
                task_info = {
                    "task_id": task.task_id,
                    "title": task.title,
                    "requirement_id": task.requirement_id,
                }
                if task.completed:
                    context["tasks_completed"].append(task_info)
                else:
                    context["tasks_pending"].append(task_info)
        except Exception:
            pass
        
        return context

    async def get_or_generate_guide(
        self, user_id: str, requirement_id: str, force_regenerate: bool = False
    ) -> FormalizationGuideResponse:
        """
        Get stored guide or generate new one if not exists.

        Args:
            user_id: User's MongoDB ObjectId as string
            requirement_id: Requirement ID to get guide for
            force_regenerate: If True, regenerate even if guide exists

        Returns:
            FormalizationGuideResponse with steps and instructions
        """
        if not force_regenerate:
            # Try to get stored guide
            user_oid = to_object_id(user_id)
            stored = await self.guides_collection.find_one(
                {"user_id": user_oid, "requirement_id": requirement_id}
            )
            
            if stored:
                guide_data = stored.get("guide", {})
                return FormalizationGuideResponse(**guide_data)
        
        # If not found or force regenerate, generate new guide
        return await self.generate_guide(user_id, requirement_id, force_regenerate)

    async def generate_guides_for_user(self, user_id: str) -> None:
        """
        Generate guides for all tasks with requirement_id for a user.

        Args:
            user_id: User's MongoDB ObjectId as string
        """
        # Get all tasks for user
        from app.modules.formalization.service import FormalizationService
        formalization_service = FormalizationService(self.db)
        tasks = await formalization_service.get_tasks(user_id)
        
        # Generate guides for tasks with requirement_id
        for task in tasks:
            if task.requirement_id:
                try:
                    await self.generate_guide(user_id, task.requirement_id)
                except Exception as e:
                    # Log error but continue with other tasks
                    print(f"Error generating guide for requirement {task.requirement_id}: {e}")
                    continue

    async def _store_guide(
        self,
        user_id: str,
        requirement_id: str,
        guide: FormalizationGuideResponse,
    ) -> None:
        """
        Store guide in database.

        Args:
            user_id: User's MongoDB ObjectId as string
            requirement_id: Requirement ID
            guide: Generated guide to store
        """
        user_oid = to_object_id(user_id)
        now = utc_now()
        
        guide_dict = guide.model_dump()
        
        await self.guides_collection.update_one(
            {"user_id": user_oid, "requirement_id": requirement_id},
            {
                "$set": {
                    "guide": guide_dict,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "user_id": user_oid,
                    "requirement_id": requirement_id,
                    "generated_at": now,
                },
            },
            upsert=True,
        )

    def _is_profile_complete(self, profile: Any) -> bool:
        """
        Check if producer profile is complete enough to generate guides.

        Args:
            profile: Producer profile to check (ProducerProfileInDB or dict)

        Returns:
            True if profile has minimum required fields
        """
        # Profile is considered complete if it has:
        # - producer_type
        # - name
        # - address
        # - city
        # - state
        required_fields = ["producer_type", "name", "address", "city", "state"]
        if hasattr(profile, '__dict__'):
            # It's a Pydantic model
            return all(
                getattr(profile, field, None) for field in required_fields
            )
        elif isinstance(profile, dict):
            # It's a dict
            return all(
                profile.get(field) for field in required_fields
            )
        return False

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
        for question in questions_list:
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
        self, question: OnboardingQuestion, requirement_id: str | None = None
    ) -> FormalizationGuideResponse:
        """
        Generate a fallback generic guide if LLM fails.

        Args:
            question: OnboardingQuestion for the requirement
            requirement_id: Requirement ID (optional)

        Returns:
            Generic FormalizationGuideResponse
        """
        return self._get_contextual_fallback_guide(question, None, None, None, requirement_id)

    def _validate_guide_quality(
        self,
        guide: FormalizationGuideResponse,
        requirement_id: str,
        profile: dict | None,
    ) -> list[str]:
        """
        Validate guide quality and detect generic or incomplete guides.
        
        Args:
            guide: Generated guide to validate
            requirement_id: Requirement ID being addressed
            profile: Producer profile dictionary or None
        
        Returns:
            List of quality issues found (empty if guide is good)
        """
        issues = []
        
        # Check for generic phrases
        generic_phrases = ["procure", "busque", "informe-se", "vá até", "compareça ao órgão", 
                         "secretaria de agricultura", "emater do seu município", "órgão responsável"]
        guide_text = f"{guide.summary} {' '.join([s.description for s in guide.steps])}".lower()
        
        if any(phrase in guide_text for phrase in generic_phrases):
            issues.append("Guia contém frases genéricas demais")
        
        # Check for alternatives (MEI for CNPJ)
        if requirement_id == "cnpj":
            producer_type = None
            if profile:
                producer_type = profile.get("producer_type")
            
            if producer_type == "individual" and "mei" not in guide_text:
                issues.append("Faltando menção a MEI para produtor individual")
            
            if "online" not in guide_text and "gov.br" not in guide_text:
                issues.append("Faltando menção a processo online (MEI ou CNPJ)")
        
        # Check for online processes when applicable
        if requirement_id in ["cnpj", "bank_account"] and "online" not in guide_text:
            issues.append("Faltando menção a processo online quando disponível")
        
        # Check for specific addresses or instructions to find them
        address_indicators = ["rua", "avenida", "número", "bairro", "cep", "endereço completo",
                            "busque no google", "acesse o site", "ligue", "telefone"]
        if not any(indicator in guide_text for indicator in address_indicators):
            issues.append("Faltando endereços específicos ou instruções de como encontrar")
        
        # Check for minimum steps
        if len(guide.steps) < 3:
            issues.append("Guia tem poucos passos (menos de 3)")
        
        # Check step quality
        for step in guide.steps:
            step_text = step.description.lower()
            if len(step_text) < 50:
                issues.append(f"Passo {step.step} muito curto/vago")
            if any(phrase in step_text for phrase in ["procure", "busque", "informe-se"]):
                issues.append(f"Passo {step.step} contém instruções genéricas")
        
        return issues

    def _get_contextual_fallback_guide(
        self,
        question: OnboardingQuestion,
        profile: dict | None,
        answers: dict | None,
        status: dict | None,
        requirement_id: str | None = None,
    ) -> FormalizationGuideResponse:
        """
        Generate a contextual fallback guide with available information.

        Args:
            question: OnboardingQuestion for the requirement
            profile: Producer profile dictionary or None
            answers: Onboarding answers dictionary or None
            status: Formalization status dictionary or None

        Returns:
            Contextual FormalizationGuideResponse
        """
        from app.modules.ai_formalization.schemas import GuideStep

        # Try to get location from profile or answers
        location = ""
        city = ""
        state = ""
        producer_type = None
        
        if profile:
            city = profile.get("city", "")
            state = profile.get("state", "")
            producer_type = profile.get("producer_type")
        elif answers:
            city = str(answers.get("city", ""))
            state = str(answers.get("state", ""))
            producer_type = answers.get("producer_type")
        
        if city and state:
            location = f" em {city}, {state}"
        
        # Build improved fallback based on requirement_id
        steps = []
        where_to_go = []
        
        if requirement_id == "cnpj":
            # CNPJ fallback with MEI option
            if producer_type == "individual":
                steps = [
                    GuideStep(
                        step=1,
                        title="Abrir MEI online (recomendado para produtores individuais)",
                        description=f"Como você é produtor individual, a forma mais simples é abrir MEI (Microempreendedor Individual) online. Acesse gov.br/mei e faça o cadastro. É gratuito, leva cerca de 15 minutos e o CNPJ sai na hora. Você precisa apenas de CPF e título de eleitor ou recibo de declaração de imposto de renda. Não precisa sair de casa - tudo é feito pelo site.",
                    ),
                    GuideStep(
                        step=2,
                        title="Alternativa: CNPJ completo na Receita Federal",
                        description=f"Se preferir ou precisar de CNPJ completo (não MEI), você pode iniciar o processo online em receita.fazenda.gov.br ou comparecer à Receita Federal mais próxima{location}. Para encontrar o endereço, busque 'Receita Federal {city} {state}' no Google ou ligue 146. Leve: CPF, RG, comprovante de endereço.",
                    ),
                ]
                where_to_go = [
                    "Portal do Empreendedor (online): gov.br/mei",
                    f"Receita Federal {city} {state} - Busque no Google ou ligue 146"
                ]
            else:
                steps = [
                    GuideStep(
                        step=1,
                        title=f"Iniciar processo de CNPJ na Receita Federal{location}",
                        description=f"Para grupos formais (cooperativas, associações), é necessário CNPJ completo. Você pode iniciar o processo online em receita.fazenda.gov.br ou comparecer à Receita Federal mais próxima{location}. Para encontrar o endereço, busque 'Receita Federal {city} {state}' no Google ou ligue 146 (telefone da Receita Federal).",
                    ),
                    GuideStep(
                        step=2,
                        title="Preparar documentos necessários",
                        description="Organize os documentos: CPF dos responsáveis, RG, comprovante de endereço da sede, estatuto da cooperativa/associação (se aplicável).",
                    ),
                ]
                where_to_go = [
                    f"Receita Federal {city} {state} - Busque no Google 'Receita Federal {city} {state}' ou ligue 146",
                    "Site: receita.fazenda.gov.br"
                ]
        
        elif requirement_id == "dap_caf":
            steps = [
                GuideStep(
                    step=1,
                    title=f"Encontrar Emater ou órgão emissor{location}",
                    description=f"A DAP/CAF é emitida por Emater, Sindicatos Rurais ou Secretarias Municipais de Agricultura{location}. Para encontrar o endereço mais próximo: (1) Busque 'Emater {city} {state}' no Google, (2) Acesse emater.gov.br e procure o escritório da sua região, ou (3) Ligue 0800 721 3000 (telefone geral da Emater). Se não houver Emater na sua cidade, procure o Sindicato dos Trabalhadores Rurais ou a Secretaria Municipal de Agricultura - ligue 156 (disque prefeitura) e peça o endereço.",
                ),
                GuideStep(
                    step=2,
                    title="Preparar documentos necessários",
                    description="Leve: RG, CPF, comprovante de endereço atualizado (conta de luz, água ou telefone dos últimos 3 meses), documento da terra (escritura, contrato de arrendamento, declaração de posse ou autorização de uso). Se não tiver documento da terra, leve declaração do sindicato rural confirmando sua atividade.",
                ),
                GuideStep(
                    step=3,
                    title="Comparecer ao órgão com os documentos",
                    description=f"Vá até o órgão escolhido{location} com todos os documentos. O atendimento é gratuito. Um técnico fará uma entrevista sobre sua produção. A DAP/CAF geralmente sai na hora ou em poucos dias úteis.",
                ),
            ]
            where_to_go = [
                f"Emater {city} {state} - Busque no Google 'Emater {city} {state}' ou acesse emater.gov.br. Telefone: 0800 721 3000",
                f"Sindicato dos Trabalhadores Rurais {city} {state} - Busque no Google",
                f"Secretaria Municipal de Agricultura {city} - Ligue 156 (disque prefeitura) e peça o endereço"
            ]
        
        elif requirement_id == "bank_account":
            steps = [
                GuideStep(
                    step=1,
                    title="Escolher banco e verificar abertura online",
                    description=f"Você pode abrir conta em qualquer banco (Banco do Brasil, Caixa, Bradesco, Itaú, etc.){location}. Muitos bancos permitem abertura online. Acesse o site do banco escolhido e verifique se há opção de abertura online. Se preferir presencial, busque agências próximas no Google: 'Banco do Brasil agência {city}' ou 'Caixa Econômica agência {city}'.",
                ),
                GuideStep(
                    step=2,
                    title="Preparar documentos",
                    description="Você precisará de: CPF, RG, comprovante de endereço atualizado (conta de luz, água ou telefone dos últimos 3 meses).",
                ),
            ]
            where_to_go = [
                f"Agências bancárias {city} {state} - Busque no Google o banco escolhido + 'agência {city}'",
                "Sites dos bancos para abertura online (verifique no site de cada banco)"
            ]
        
        else:
            # Generic fallback for other requirements
            steps = [
                GuideStep(
                    step=1,
                    title=f"Encontrar órgão responsável{location}",
                    description=f"Para {question.question_text.lower()}{location}, você precisa encontrar o órgão responsável. Busque no Google termos como '{question.question_text.lower()} {city} {state}' ou consulte sites oficiais relevantes. Se não souber qual órgão, ligue 156 (disque prefeitura) e pergunte.",
                ),
                GuideStep(
                    step=2,
                    title="Preparar documentos necessários",
                    description="Organize seus documentos pessoais (RG, CPF) e documentos específicos relacionados ao requisito.",
                ),
                GuideStep(
                    step=3,
                    title=f"Comparecer ao órgão{location}",
                    description=f"Vá até o órgão responsável{location} com os documentos. Se não souber o endereço exato, ligue antes para confirmar endereço e horário de funcionamento.",
                ),
            ]
            where_to_go = [
                f"Busque no Google '{question.question_text.lower()} {city} {state}' para encontrar órgão responsável",
                f"Ligue 156 (disque prefeitura) para informações sobre órgãos municipais"
            ]
        
        summary = f"Para resolver este requisito relacionado a {question.question_text.lower()}, siga os passos abaixo."
        if location:
            summary += f" As instruções são específicas para sua localização{location}."
        if requirement_id == "cnpj" and producer_type == "individual":
            summary += " Como você é produtor individual, a opção mais simples é abrir MEI online em gov.br/mei (gratuito, ~15 minutos, CNPJ sai na hora)."

        return FormalizationGuideResponse(
            summary=summary,
            steps=steps,
            estimated_time_days=7 if requirement_id != "cnpj" or producer_type != "individual" else 1,
            where_to_go=where_to_go,
            confidence_level="low",  # Mark as low since it's a fallback
        )
