"""
Sales Project service.
AI-powered sales project generation for PNAE.
"""

import json
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from openai import OpenAI

from app.core.config import settings
from app.modules.onboarding.service import OnboardingService
from app.modules.producers.service import ProducerService
from app.modules.sales_project.schemas import (
    SalesProjectDraftRequest,
    SalesProjectInDB,
    SalesProjectResponse,
)
from app.shared.utils import to_object_id, utc_now


class SalesProjectService:
    """Service for sales project operations."""

    def __init__(self, db: AsyncIOMotorDatabase):  # type: ignore[type-arg]
        self.db = db
        self.collection = db.sales_projects
        self.producer_service = ProducerService(db)
        self.onboarding_service = OnboardingService(db)
        self.openai_client = (
            OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        )

    async def generate_draft_with_ai(
        self, user_id: str, request: SalesProjectDraftRequest
    ) -> SalesProjectResponse:
        """
        Generate sales project draft using AI.

        Args:
            user_id: User's MongoDB ObjectId as string
            request: Draft generation request

        Returns:
            Generated sales project
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        # Get producer information
        try:
            profile = await self.producer_service.get_profile_by_user(user_id)
        except Exception:
            raise ValueError("Producer profile not found. Complete onboarding first.")

        # Get onboarding answers
        answers = await self.onboarding_service.get_all_answers(user_id)
        answers_dict = {qid: ans.answer for qid, ans in answers.items()}

        # Extract relevant information
        main_products = answers_dict.get("main_products", [])
        if isinstance(main_products, list):
            products_str = ", ".join(main_products)
        else:
            products_str = str(main_products) if main_products else "Não informado"

        production_capacity = answers_dict.get("production_capacity", "Não informado")
        production_type = answers_dict.get("production_type", "Não informado")
        city = profile.city or "Não informado"
        state = profile.state or "Não informado"
        producer_type = profile.producer_type or "individual"

        # Build prompt
        prompt = f"""Você é um especialista em elaborar projetos de venda para o PNAE.

INFORMAÇÕES DO PRODUTOR:
- Nome/Razão Social: {profile.name}
- Localização: {city}, {state}
- Tipo: {producer_type}
- Tipo de produção: {production_type}
- Produtos principais: {products_str}
- Capacidade de produção: {production_capacity}
- DAP/CAF: {profile.dap_caf_number or 'Não informado'}

Gere um projeto de venda no formato do PNAE com:

1. RELAÇÃO DOS PRODUTOS:
   - Para cada produto principal listado, sugira quantidade mensal baseada na capacidade informada
   - Sugira preço unitário baseado em mercado local (pesquise preços médios para {city}, {state})
   - Calcule valor total por produto
   - Defina frequência de entrega apropriada (semanal, quinzenal, mensal)

2. CRONOGRAMA DE ENTREGA:
   - Sugira frequência de entrega considerando sazonalidade dos produtos
   - Distribua entregas ao longo do ano letivo (fevereiro a novembro)
   - Considere que o ano letivo tem 200 dias de aula

3. OBSERVAÇÕES:
   - Inclua informações sobre origem dos produtos
   - Mencione se são orgânicos/agroecológicos (se aplicável)
   - Informações sobre embalagem/transporte se relevante

IMPORTANTE:
- O valor total do projeto não deve exceder R$ 40.000,00 para produtor individual ou grupo informal
- Para grupo formal, o limite é número de membros × R$ 40.000,00
- Use apenas produtos que foram listados pelo produtor
- Seja realista com as quantidades baseado na capacidade informada

Responda APENAS com JSON válido, sem texto adicional:
{{
  "products": [
    {{
      "name": "nome do produto",
      "unit": "kg|litro|unidade",
      "quantity": número,
      "unit_price": número,
      "total_price": número,
      "delivery_frequency": "semanal|quinzenal|mensal"
    }}
  ],
  "delivery_schedule": {{
    "february": {{"products": ["produto1"], "quantity": 100}},
    "march": {{"products": ["produto1"], "quantity": 100}},
    "april": {{"products": ["produto1"], "quantity": 100}},
    "may": {{"products": ["produto1"], "quantity": 100}},
    "june": {{"products": ["produto1"], "quantity": 100}},
    "july": {{"products": ["produto1"], "quantity": 100}},
    "august": {{"products": ["produto1"], "quantity": 100}},
    "september": {{"products": ["produto1"], "quantity": 100}},
    "october": {{"products": ["produto1"], "quantity": 100}},
    "november": {{"products": ["produto1"], "quantity": 100}}
  }},
  "total_value": número,
  "notes": "observações gerais sobre o projeto"
}}
"""

        # Call OpenAI
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em projetos de venda para PNAE. Sempre responda APENAS com JSON válido, sem texto adicional.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            result_text = response.choices[0].message.content or "{}"
            # Extract JSON if wrapped in text
            start = result_text.find("{")
            end = result_text.rfind("}") + 1
            if start >= 0 and end > start:
                result_text = result_text[start:end]

            draft_data = json.loads(result_text)
        except Exception as e:
            raise ValueError(f"Erro ao gerar projeto com IA: {str(e)}")

        # Create sales project document
        now = utc_now()
        project_doc = {
            "user_id": to_object_id(user_id),
            "edital_id": request.edital_id,
            "products": draft_data.get("products", []),
            "delivery_schedule": draft_data.get("delivery_schedule", {}),
            "total_value": draft_data.get("total_value", 0.0),
            "ai_generated": True,
            "notes": draft_data.get("notes", ""),
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(project_doc)
        project_doc["_id"] = result.inserted_id

        return SalesProjectResponse(**project_doc)

    async def get_user_projects(
        self, user_id: str
    ) -> list[SalesProjectInDB]:
        """
        Get all sales projects for a user.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            List of sales projects
        """
        user_oid = to_object_id(user_id)
        cursor = self.collection.find({"user_id": user_oid}).sort("created_at", -1)
        projects = []
        async for doc in cursor:
            projects.append(SalesProjectInDB(**doc))
        return projects

    async def get_project_by_id(
        self, project_id: str, user_id: str
    ) -> SalesProjectInDB | None:
        """
        Get a sales project by ID.

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            Sales project if found, None otherwise
        """
        project_oid = to_object_id(project_id)
        user_oid = to_object_id(user_id)
        doc = await self.collection.find_one({"_id": project_oid, "user_id": user_oid})
        if not doc:
            return None
        return SalesProjectInDB(**doc)

    async def update_project(
        self, project_id: str, user_id: str, updates: dict[str, Any]
    ) -> SalesProjectInDB:
        """
        Update a sales project.

        Args:
            project_id: Project ID
            user_id: User ID
            updates: Fields to update

        Returns:
            Updated project
        """
        project_oid = to_object_id(project_id)
        user_oid = to_object_id(user_id)
        updates["updated_at"] = utc_now()

        await self.collection.update_one(
            {"_id": project_oid, "user_id": user_oid}, {"$set": updates}
        )

        doc = await self.collection.find_one({"_id": project_oid, "user_id": user_oid})
        if not doc:
            raise ValueError("Project not found")
        return SalesProjectInDB(**doc)
