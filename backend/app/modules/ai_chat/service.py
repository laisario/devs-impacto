"""
AI Chat service.
Conversational AI assistant for PNAE support using OpenAI.
"""

import logging
from typing import Any
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase
from openai import OpenAI

from app.core.config import settings
from app.modules.ai_chat.audio_service import AudioService
from app.modules.ai_chat.schemas import (
    ChatMessageRequest,
    ChatMessageResponseNew,
    ChatState,
    ClientCapabilities,
    ConversationState,
    SuggestedAction,
)
from app.modules.ai_chat.state_machine import ChatStateMachine
from app.modules.producers.schemas import ProducerProfileResponse
from app.shared.utils import to_object_id, utc_now

logger = logging.getLogger(__name__)


class AIChatService:
    """Service for AI-powered chat conversations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.conversations_collection = db.chat_conversations
        self.messages_collection = db.chat_messages
        self.audio_cache_collection = db.chat_audio_cache  # Cache for audio URLs
        self.openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.audio_service = AudioService()
        self.state_machine = ChatStateMachine()
        self.logger = logger

    async def get_or_create_conversation(self, user_id: str, conversation_id: str | None = None) -> dict[str, Any]:
        """
        Get or create a conversation.

        Args:
            user_id: User's MongoDB ObjectId as string
            conversation_id: Optional conversation ID to retrieve

        Returns:
            Conversation document
        """
        user_oid = to_object_id(user_id)

        if conversation_id:
            try:
                conv_oid = to_object_id(conversation_id)
                conv = await self.conversations_collection.find_one({"_id": conv_oid, "user_id": user_oid})
                if conv:
                    return conv
            except Exception:
                # Invalid conversation_id, create new
                pass

        # Create new conversation
        now = utc_now()
        conv_doc = {
            "user_id": user_oid,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.conversations_collection.insert_one(conv_doc)
        conv_doc["_id"] = result.inserted_id
        return conv_doc

    async def get_conversation_messages(self, conversation_id: str) -> list[dict[str, Any]]:
        """
        Get all messages from a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of message dictionaries
        """
        conv_oid = to_object_id(conversation_id)
        cursor = self.messages_collection.find({"conversation_id": conv_oid}).sort("created_at", 1)
        messages = []
        async for doc in cursor:
            messages.append({"role": doc["role"], "content": doc["content"]})
        return messages

    def _build_pnae_context(self) -> str:
        """
        Build PNAE context for the chatbot.

        Returns:
            Formatted string with PNAE information
        """
        return """
O PNAE (Programa Nacional de Alimentação Escolar) é um programa federal que repassa recursos para estados e municípios comprarem alimentos para escolas públicas.

PRINCIPAIS PONTOS:
- No mínimo 30% dos recursos devem ser usados para comprar da agricultura familiar
- As compras são feitas via Chamada Pública (edital)
- Produtores precisam ter DAP/CAF para participar
- Podem vender individualmente, em grupo informal ou grupo formal (CNPJ)
- Limite de R$ 40 mil por ano por Entidade Executora (individual/grupo informal)
- Para grupos formais, limite é número de membros × R$ 40 mil

DOCUMENTOS NECESSÁRIOS:
- DAP ou CAF
- CPF (para individual/informal) ou CNPJ (para formal)
- Comprovante de endereço
- Conta bancária
- Projeto de venda

PROCESSO:
1. Organização antes do edital (levantamento de produção)
2. Preparação (documentos)
3. Elaboração do projeto de venda
4. Entrega da proposta
5. Seleção e contrato
6. Entrega e recebimento

NOTA TÉCNICA 03/2020 (MPF):
Para povos indígenas e comunidades tradicionais, alguns produtos não precisam de registros sanitários se forem produzidos e consumidos na mesma comunidade.
"""

    async def generate_response(
        self,
        user_message: str,
        user_id: str,
        conversation_id: str | None = None,
        user_profile: ProducerProfileResponse | None = None,
    ) -> tuple[str, str]:
        """
        Generate AI response to user message.

        Args:
            user_message: User's message
            user_id: User's MongoDB ObjectId as string
            conversation_id: Optional conversation ID for context
            user_profile: Optional producer profile for context

        Returns:
            Tuple of (assistant_message, conversation_id)
        """
        # Get or create conversation
        conversation = await self.get_or_create_conversation(user_id, conversation_id)
        conv_id = str(conversation["_id"])

        # Get conversation history
        messages_history = await self.get_conversation_messages(conv_id)

        # Build PNAE context
        pnae_context = self._build_pnae_context()

        # Build user context from profile or onboarding answers
        user_context = ""
        if user_profile:
            user_context = f"""
INFORMAÇÕES DO USUÁRIO:
- Localização: {user_profile.city or 'Não informado'}, {user_profile.state or 'Não informado'}
- Tipo: {user_profile.producer_type or 'Não informado'}
- DAP/CAF: {'Sim' if user_profile.dap_caf_number else 'Não'}
"""
        else:
            # Try to get context from onboarding answers
            try:
                from app.modules.onboarding.service import OnboardingService
                onboarding_service = OnboardingService(self.db)
                answers = await onboarding_service.get_all_answers(user_id)
                answers_dict = {qid: ans.answer for qid, ans in answers.items()}
                
                city = answers_dict.get("city", "Não informado")
                state = answers_dict.get("state", "Não informado")
                producer_type = answers_dict.get("producer_type", "Não informado")
                has_dap_caf = answers_dict.get("has_dap_caf", False)
                
                user_context = f"""
INFORMAÇÕES DO USUÁRIO:
- Localização: {city}, {state}
- Tipo: {producer_type}
- DAP/CAF: {'Sim' if has_dap_caf else 'Não'}
"""
            except Exception:
                # If can't get onboarding answers, continue without user context
                pass

        # Build prompt for LLM
        conversation_context = ""
        if messages_history:
            conversation_context = "\n\nHistórico da conversa:\n"
            for msg in messages_history[-5:]:  # Last 5 messages for context
                role_label = "Usuário" if msg["role"] == "user" else "Assistente"
                conversation_context += f"{role_label}: {msg['content']}\n"

        prompt = f"""Você é um assistente especializado em ajudar produtores rurais a participar do Programa Nacional de Alimentação Escolar (PNAE).

CONTEXTO SOBRE O PNAE:
{pnae_context}

{user_context}

{conversation_context}

INSTRUÇÕES:
1. Responda de forma clara, simples e acessível
2. Use exemplos práticos quando possível
3. Se não souber algo, seja honesto e sugira consultar a Emater ou órgão local
4. Foque em ajudar o produtor a entender o processo do PNAE
5. Se o usuário fizer parte de comunidade tradicional, mencione a Nota Técnica 03/2020 do MPF quando relevante
6. Mantenha respostas concisas (máximo 3 parágrafos)

PERGUNTA DO USUÁRIO: {user_message}

IMPORTANTE: Responda APENAS com o texto da resposta em português brasileiro, sem formatação JSON, sem markdown, sem código. Apenas texto puro e direto."""

        # Call LLM using the same method as specialized response
        assistant_message = await self._call_llm(prompt)

        # Save messages
        now = utc_now()
        conv_oid = to_object_id(conv_id)

        await self.messages_collection.insert_many(
            [
                {
                    "conversation_id": conv_oid,
                    "role": "user",
                    "content": user_message,
                    "created_at": now,
                },
                {
                    "conversation_id": conv_oid,
                    "role": "assistant",
                    "content": assistant_message,
                    "created_at": now,
                }
            ]
        )

        # Update conversation
        await self.conversations_collection.update_one({"_id": conv_oid}, {"$set": {"updated_at": now}})

        return assistant_message, conv_id

    async def generate_specialized_response(
        self,
        request: ChatMessageRequest,
        user_id: str,
        user_profile: ProducerProfileResponse | None = None,
    ) -> ChatMessageResponseNew:
        """
        Generate specialized PNAE formalization response using state machine and RAG.

        Args:
            request: Chat message request (text or audio)
            user_id: User's MongoDB ObjectId as string
            user_profile: Optional producer profile for context

        Returns:
            ChatMessageResponseNew with structured response
        """
        # Step 1: Handle audio input (transcribe if needed)
        user_text = request.text
        if request.input_type == "audio" and request.audio_url:
            try:
                user_text = await self.audio_service.transcribe_audio(request.audio_url)
            except Exception as e:
                self.logger.error(f"Error transcribing audio: {e}", exc_info=True)
                return self._create_error_response(
                    request.conversation_id or "",
                    "Erro ao processar áudio. Por favor, tente novamente ou digite sua mensagem.",
                )

        if not user_text:
            return self._create_error_response(
                request.conversation_id or "",
                "Por favor, envie uma mensagem de texto ou áudio.",
            )

        # Step 2: Get or create conversation
        conversation = await self.get_or_create_conversation(user_id, request.conversation_id)
        conv_id = str(conversation["_id"])

        # Step 3: Get current conversation state
        current_state = ChatState(conversation.get("chat_state", ChatState.IDLE.value))
        current_task_code = conversation.get("current_task_code")

        # Step 4: Get formalization tasks
        from app.modules.formalization.service import FormalizationService

        formalization_service = FormalizationService(self.db)
        tasks = await formalization_service.get_tasks(user_id)

        # Step 5: Identify most important pending task
        pending_tasks = [t for t in tasks if t.status == "pending"]
        blocking_tasks = [t for t in pending_tasks if t.blocking]
        priority_task = blocking_tasks[0] if blocking_tasks else (pending_tasks[0] if pending_tasks else None)

        # Step 6: Determine intent and generate response
        intent = self._detect_intent(user_text.lower())

        # If user sent audio, always generate audio response (even if prefers_audio is False)
        should_generate_audio = request.client_capabilities.prefers_audio or request.input_type == "audio"
        self.logger.info(
            f"Audio generation decision: should_generate={should_generate_audio}, "
            f"input_type={request.input_type}, prefers_audio={request.client_capabilities.prefers_audio}"
        )

        if intent == "ask_what_missing" or (intent == "general" and not current_task_code and priority_task):
            # Explain the most important task
            return await self._explain_task(
                priority_task,
                conv_id,
                user_id,
                user_profile,
                request.client_capabilities,
                should_generate_audio=should_generate_audio,
            )
        elif intent == "confirm_task" and current_task_code:
            # User confirmed completing a task
            return await self._handle_task_confirmation(
                current_task_code,
                user_text,
                conv_id,
                user_id,
                request.client_capabilities,
                should_generate_audio=should_generate_audio,
            )
        elif current_task_code and current_state == ChatState.EXPLAINING_TASK:
            # Continue explaining current task
            return await self._continue_explanation(
                current_task_code,
                user_text,
                conv_id,
                user_id,
                user_profile,
                request.client_capabilities,
                should_generate_audio=should_generate_audio,
            )
        else:
            # General question - use RAG to answer
            return await self._answer_general_question(
                user_text,
                conv_id,
                user_id,
                user_profile,
                request.client_capabilities,
                should_generate_audio=should_generate_audio,
            )

    async def _explain_task(
        self,
        task,
        conv_id: str,
        user_id: str,
        user_profile: ProducerProfileResponse | None,
        client_capabilities: ClientCapabilities,
        should_generate_audio: bool = False,
    ) -> ChatMessageResponseNew:
        """Explain a formalization task using RAG."""
        if not task:
            return self._create_info_response(
                conv_id,
                "Parabéns! Você já completou todas as tarefas de formalização necessárias.",
                ChatState.IDLE,
                None,
                client_capabilities,
            )

        # Get RAG chunks for this task
        from app.modules.ai_formalization.rag import RAGService

        rag_service = RAGService(self.db)
        requirement_id = task.requirement_id or task.task_code.lower()

        try:
            chunks = await rag_service.search_relevant_chunks(requirement_id, limit=10)
            rag_context = "\n\n".join([chunk.content for chunk in chunks[:5]])
        except Exception:
            rag_context = ""

        # Build explanation prompt
        explanation_prompt = f"""Você é um especialista em formalização para o PNAE. Explique de forma SIMPLES e ACESSÍVEL como o produtor pode completar esta tarefa.

TAREFA: {task.title}
DESCRIÇÃO: {task.description}
POR QUE É NECESSÁRIO: {task.why}

INFORMAÇÕES RELEVANTES:
{rag_context}

INSTRUÇÕES:
1. Use linguagem MUITO SIMPLES (como se estivesse falando com alguém que não conhece burocracia)
2. Dê passos NUMERADOS e CLAROS
3. Seja ESPECÍFICO (não diga "procure o órgão", diga onde ir)
4. Máximo 150 palavras
5. NUNCA dê parecer jurídico
6. NUNCA invente regras

IMPORTANTE: Responda APENAS com o texto da explicação em português brasileiro, sem formatação JSON, sem markdown, sem código. Apenas texto puro e direto."""

        # Generate explanation
        explanation = await self._call_llm(explanation_prompt)

        # Update conversation state
        await self._update_conversation_state(conv_id, ChatState.EXPLAINING_TASK, task.task_code)

        # Generate audio if requested or if user sent audio
        audio_url = None
        if should_generate_audio:
            self.logger.info(f"Generating audio for explanation (length: {len(explanation)})")
            audio_url = await self._generate_audio_url(explanation, user_id)
            self.logger.info(f"Audio URL generated: {audio_url}")

        # Create suggested action for marking task as done
        suggested_actions = [
            SuggestedAction(
                type="mark_task_done",
                task_code=task.task_code,
            )
        ]

        return ChatMessageResponseNew(
            conversation_id=conv_id,
            message_id=str(uuid4()),
            message_type="info",
            text=explanation,
            audio_url=audio_url,
            suggested_actions=suggested_actions,
            conversation_state=ConversationState(
                current_goal="formalization",
                current_task_code=task.task_code,
                chat_state=ChatState.EXPLAINING_TASK,
            ),
        )

    async def _handle_task_confirmation(
        self,
        task_code: str,
        user_text: str,
        conv_id: str,
        user_id: str,
        client_capabilities: ClientCapabilities,
        should_generate_audio: bool = False,
    ) -> ChatMessageResponseNew:
        """Handle user confirmation that they completed a task."""
        # Check if user confirmed (sim, já, completei, etc.)
        confirmations = ["sim", "sim", "já", "completei", "concluí", "feito", "pronto"]
        is_confirmed = any(conf in user_text.lower() for conf in confirmations)

        if is_confirmed:
            # Suggest marking task as done
            suggested_actions = [
                SuggestedAction(
                    type="mark_task_done",
                    task_code=task_code,
                )
            ]

            response_text = f"Ótimo! Vou marcar a tarefa '{task_code}' como concluída. Você pode verificar seu progresso na lista de tarefas."
        else:
            suggested_actions = []
            response_text = "Entendi. Se precisar de mais ajuda com esta tarefa, é só perguntar!"

        # Update conversation state
        await self._update_conversation_state(conv_id, ChatState.IDLE, None)

        audio_url = None
        if should_generate_audio:
            self.logger.info(f"Generating audio for task confirmation (length: {len(response_text)})")
            audio_url = await self._generate_audio_url(response_text, user_id)
            self.logger.info(f"Audio URL generated: {audio_url}")

        return ChatMessageResponseNew(
            conversation_id=conv_id,
            message_id=str(uuid4()),
            message_type="action" if is_confirmed else "info",
            text=response_text,
            audio_url=audio_url,
            suggested_actions=suggested_actions,
            conversation_state=ConversationState(
                current_goal="formalization",
                current_task_code=None,
                chat_state=ChatState.IDLE,
            ),
        )

    async def _continue_explanation(
        self,
        task_code: str,
        user_text: str,
        conv_id: str,
        user_id: str,
        user_profile: ProducerProfileResponse | None,
        client_capabilities: ClientCapabilities,
        should_generate_audio: bool = False,
    ) -> ChatMessageResponseNew:
        """Continue explaining or answer questions about current task."""
        # Use RAG to answer the question in context of the task
        from app.modules.ai_formalization.rag import RAGService

        rag_service = RAGService(self.db)

        try:
            chunks = await rag_service.search_relevant_chunks(task_code.lower(), limit=5)
            rag_context = "\n\n".join([chunk.content for chunk in chunks[:3]])
        except Exception:
            rag_context = ""

        answer_prompt = f"""O usuário está trabalhando na tarefa '{task_code}' e fez esta pergunta:

PERGUNTA: {user_text}

CONTEXTO RELEVANTE:
{rag_context}

INSTRUÇÕES:
- Responda de forma SIMPLES e DIRETA
- Máximo 100 palavras
- Se não souber, diga para consultar a Emater

IMPORTANTE: Responda APENAS com o texto da resposta em português brasileiro, sem formatação JSON, sem markdown, sem código. Apenas texto puro e direto."""

        answer = await self._call_llm(answer_prompt)

        audio_url = None
        if should_generate_audio:
            self.logger.info(f"Generating audio for continue explanation (length: {len(answer)})")
            audio_url = await self._generate_audio_url(answer, user_id)
            self.logger.info(f"Audio URL generated: {audio_url}")

        return ChatMessageResponseNew(
            conversation_id=conv_id,
            message_id=str(uuid4()),
            message_type="info",
            text=answer,
            audio_url=audio_url,
            suggested_actions=[],
            conversation_state=ConversationState(
                current_goal="formalization",
                current_task_code=task_code,
                chat_state=ChatState.EXPLAINING_TASK,
            ),
        )

    async def _answer_general_question(
        self,
        user_text: str,
        conv_id: str,
        user_id: str,
        user_profile: ProducerProfileResponse | None,
        client_capabilities: ClientCapabilities,
        should_generate_audio: bool = False,
    ) -> ChatMessageResponseNew:
        """Answer general PNAE questions using RAG."""
        # Use RAG to find relevant information
        from app.modules.ai_formalization.rag import RAGService

        rag_service = RAGService(self.db)

        try:
            chunks = await rag_service.search_relevant_chunks(user_text, limit=5)
            rag_context = "\n\n".join([chunk.content for chunk in chunks[:3]])
        except Exception:
            rag_context = ""

        pnae_context = self._build_pnae_context()

        answer_prompt = f"""Você é um especialista em PNAE. Responda esta pergunta de forma SIMPLES.

PERGUNTA: {user_text}

CONTEXTO SOBRE PNAE:
{pnae_context}

INFORMAÇÕES RELEVANTES:
{rag_context}

INSTRUÇÕES:
1. Responda de forma CLARA e SIMPLES
2. Máximo 150 palavras
3. Se não souber, sugira consultar a Emater
4. NUNCA dê parecer jurídico
5. NUNCA invente regras

IMPORTANTE: Responda APENAS com o texto da resposta em português brasileiro, sem formatação JSON, sem markdown, sem código. Apenas texto puro e direto."""

        answer = await self._call_llm(answer_prompt)

        audio_url = None
        if should_generate_audio:
            self.logger.info(f"Generating audio for general question (length: {len(answer)})")
            audio_url = await self._generate_audio_url(answer, user_id)
            self.logger.info(f"Audio URL generated: {audio_url}")

        return ChatMessageResponseNew(
            conversation_id=conv_id,
            message_id=str(uuid4()),
            message_type="info",
            text=answer,
            audio_url=audio_url,
            suggested_actions=[],
            conversation_state=ConversationState(
                current_goal="formalization",
                current_task_code=None,
                chat_state=ChatState.IDLE,
            ),
        )

    def _detect_intent(self, text: str) -> str:
        """Detect user intent from text."""
        text_lower = text.lower()

        if any(word in text_lower for word in ["o que falta", "o que preciso", "próxima tarefa", "o que falta fazer"]):
            return "ask_what_missing"
        elif any(word in text_lower for word in ["sim", "já", "completei", "concluí", "feito", "pronto"]):
            return "confirm_task"
        else:
            return "general"

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM to generate response using configured provider."""
        try:
            from app.core.config import settings

            provider = getattr(settings, "llm_provider", "mock").lower()

            # For OpenAI, use direct client if available
            if provider == "openai" and self.openai_client:
                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=300,
                    )
                    return response.choices[0].message.content or "Desculpe, não consegui gerar uma resposta."
                except Exception as e:
                    self.logger.error(f"Error calling OpenAI: {e}", exc_info=True)

            # For Deco or other providers, use LLMClient but extract text
            from app.modules.ai_formalization.llm_client import create_llm_client

            llm_client = create_llm_client()
            response = await llm_client.generate(prompt)

            # LLMClient may return JSON, try to extract text
            try:
                import json

                # Remove markdown code blocks if present
                cleaned = response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                elif cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                parsed = json.loads(cleaned)
                # If it's a JSON object, try to extract text
                if isinstance(parsed, dict):
                    # Look for common text fields
                    text = parsed.get("text") or parsed.get("content") or parsed.get("response") or parsed.get("message")
                    if text:
                        return str(text)
                    # If it's a guide structure, extract summary
                    if "summary" in parsed:
                        return str(parsed["summary"])
            except (json.JSONDecodeError, ValueError):
                # Not JSON, return as-is (remove any markdown formatting)
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    # Extract content from code block
                    lines = cleaned.split("\n")
                    if len(lines) > 2:
                        return "\n".join(lines[1:-1])
                return cleaned

            return response
        except ValueError as e:
            # Provider not configured
            self.logger.warning(f"LLM provider not configured: {e}")
            return "Desculpe, o assistente de IA não está configurado no momento. Por favor, consulte a Emater para mais informações."
        except Exception as e:
            self.logger.error(f"Error calling LLM: {e}", exc_info=True)
            return "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente ou consulte a Emater para mais informações."

    async def _generate_audio_url(self, text: str, user_id: str) -> str | None:
        """
        Generate audio from text and return URL.
        Uses cache to avoid regenerating same audio.
        """
        try:
            # Create cache key from text (normalized)
            import hashlib

            text_normalized = text.strip().lower()
            cache_key = hashlib.md5(text_normalized.encode()).hexdigest()

            # Check cache first
            cached = await self.audio_cache_collection.find_one({"cache_key": cache_key})
            if cached and cached.get("audio_url"):
                self.logger.info(f"Audio cache hit for text: {text[:50]}...")
                return cached["audio_url"]

            # Cache miss - generate new audio
            self.logger.info(f"Audio cache miss, generating for text: {text[:50]}...")
            audio_data = await self.audio_service.synthesize_speech(text)

            if not audio_data:
                self.logger.warning(f"Audio synthesis returned empty data for text: {text[:50]}...")
                return None
            
            self.logger.info(f"Audio synthesis successful, got {len(audio_data)} bytes")

            # Upload to storage (reuse documents storage)
            from app.modules.documents.storage import get_storage_provider

            storage = get_storage_provider()
            presigned = storage.generate_presigned_upload(
                filename="chat_audio.mp3",
                content_type="audio/mpeg",
                user_id=user_id,
            )

            # Upload audio data
            import httpx

            async with httpx.AsyncClient() as client:
                await client.put(presigned.upload_url, content=audio_data, timeout=30.0)

            audio_url = presigned.file_url

            # Store in cache
            await self.audio_cache_collection.update_one(
                {"cache_key": cache_key},
                {
                    "$set": {
                        "cache_key": cache_key,
                        "text": text_normalized,
                        "audio_url": audio_url,
                        "created_at": utc_now(),
                    }
                },
                upsert=True,
            )

            self.logger.info(f"Audio URL stored in cache: {audio_url}")
            return audio_url
        except Exception as e:
            self.logger.error(f"Error generating audio: {e}", exc_info=True)
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def _update_conversation_state(
        self, conv_id: str, chat_state: ChatState, current_task_code: str | None
    ) -> None:
        """Update conversation state in database."""
        conv_oid = to_object_id(conv_id)
        update_doc = {
            "chat_state": chat_state.value,
            "updated_at": utc_now(),
        }
        if current_task_code:
            update_doc["current_task_code"] = current_task_code
        else:
            update_doc["current_task_code"] = None

        await self.conversations_collection.update_one({"_id": conv_oid}, {"$set": update_doc})

    def _create_error_response(self, conv_id: str, error_message: str) -> ChatMessageResponseNew:
        """Create error response."""
        return ChatMessageResponseNew(
            conversation_id=conv_id or str(uuid4()),
            message_id=str(uuid4()),
            message_type="error",
            text=error_message,
            audio_url=None,
            suggested_actions=[],
            conversation_state=ConversationState(
                current_goal=None,
                current_task_code=None,
                chat_state=ChatState.ERROR,
            ),
        )

    def _create_info_response(
        self,
        conv_id: str,
        text: str,
        chat_state: ChatState,
        current_task_code: str | None,
        client_capabilities: ClientCapabilities,
    ) -> ChatMessageResponseNew:
        """Create info response."""
        return ChatMessageResponseNew(
            conversation_id=conv_id,
            message_id=str(uuid4()),
            message_type="info",
            text=text,
            audio_url=None,  # Can be generated later if needed
            suggested_actions=[],
            conversation_state=ConversationState(
                current_goal="formalization",
                current_task_code=current_task_code,
                chat_state=chat_state,
            ),
        )

