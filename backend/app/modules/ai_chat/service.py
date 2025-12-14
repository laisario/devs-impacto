"""
AI Chat service.
Conversational AI assistant for PNAE support using OpenAI.
"""

from typing import Any
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase
from openai import OpenAI

from app.core.config import settings
from app.modules.producers.schemas import ProducerProfileResponse
from app.shared.utils import to_object_id, utc_now


class AIChatService:
    """Service for AI-powered chat conversations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.conversations_collection = db.chat_conversations
        self.messages_collection = db.chat_messages
        self.openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

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
        if not self.openai_client:
            # Fallback response if OpenAI not configured
            return (
                "Desculpe, o assistente de IA não está disponível no momento. Por favor, consulte a Emater ou órgão local para mais informações sobre o PNAE.",
                "",
            )

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

        system_prompt = f"""Você é um assistente especializado em ajudar produtores rurais a participar do Programa Nacional de Alimentação Escolar (PNAE).

CONTEXTO SOBRE O PNAE:
{pnae_context}

{user_context}

INSTRUÇÕES:
1. Responda de forma clara, simples e acessível
2. Use exemplos práticos quando possível
3. Se não souber algo, seja honesto e sugira consultar a Emater ou órgão local
4. Foque em ajudar o produtor a entender o processo do PNAE
5. Se o usuário fizer parte de comunidade tradicional, mencione a Nota Técnica 03/2020 do MPF quando relevante
6. Mantenha respostas concisas (máximo 3 parágrafos)

Responda em português brasileiro, de forma amigável e empática."""

        # Build messages for OpenAI
        openai_messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last 10 messages)
        for msg in messages_history[-10:]:
            openai_messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user message
        openai_messages.append({"role": "user", "content": user_message})

        # Call OpenAI
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=openai_messages,  # type: ignore
                temperature=0.7,
                max_tokens=500,
            )

            assistant_message = response.choices[0].message.content or "Desculpe, não consegui gerar uma resposta."
        except Exception as e:
            # Fallback on error
            assistant_message = "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente ou consulte a Emater para mais informações."

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

