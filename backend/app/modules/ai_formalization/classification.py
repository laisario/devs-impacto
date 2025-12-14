"""
Classification service for RAG chunks.

Uses LLM to automatically classify chunks and determine:
- Topic
- Applies_to (which requirement_ids this chunk is relevant for)
"""

import json
import logging
from typing import Any

from app.modules.ai_formalization.llm_client import LLMClient
from app.modules.onboarding.schemas import OnboardingQuestion


CLASSIFICATION_PROMPT = """Analise o seguinte texto extraído de um documento sobre formalização de pequenos produtores rurais no Brasil.

Texto:
{chunk_content}

Perguntas de onboarding disponíveis e seus requirement_ids:
{questions_list}

Tarefa:
1. Determine o TOPIC principal do texto (uma palavra curta em minúsculas, ex: "cpf", "dap_caf", "cnpj", "bank_account", "documents", "general")
2. Liste quais requirement_ids são relevantes para este texto (pode ser múltiplos)
3. Um texto pode se aplicar a vários requirements se o conteúdo for relevante

Resposta APENAS em JSON válido (sem markdown, sem texto adicional):
{{
  "topic": "tipo_do_topico",
  "applies_to": ["has_cpf", "has_dap_caf"],
  "confidence": "high"
}}

Seja objetivo e preciso. Se o texto não se aplica claramente a nenhum requirement, use topic="general" e applies_to=[]."""


async def classify_chunk(
    chunk_content: str,
    questions: list[OnboardingQuestion],
    llm_client: LLMClient,
) -> dict[str, Any]:
    """
    Classify a chunk using LLM to determine topic and applies_to.

    Args:
        chunk_content: Text content of the chunk
        questions: List of onboarding questions (to get requirement_ids)
        llm_client: LLM client for classification

    Returns:
        Dictionary with:
        - topic: str
        - applies_to: list[str]
        - confidence: str
    """
    # Build questions list string (only questions with requirement_id)
    questions_with_requirements = [
        q for q in questions if q.requirement_id is not None
    ]
    
    questions_str = "\n".join(
        [
            f"- {q.question_id}: {q.question_text} (requirement_id: {q.requirement_id})"
            for q in questions_with_requirements
        ]
    )

    # Build prompt
    prompt = CLASSIFICATION_PROMPT.format(
        chunk_content=chunk_content[:2000],  # Limit chunk size for classification
        questions_list=questions_str,
    )

    # Get LLM response
    try:
        response = await llm_client.generate(prompt)
        classification = json.loads(response)
        
        # Validate and normalize
        topic = classification.get("topic", "general")
        applies_to = classification.get("applies_to", [])
        confidence = classification.get("confidence", "medium")
        
        # Ensure applies_to is a list
        if not isinstance(applies_to, list):
            applies_to = []
        
        # Filter applies_to to only valid requirement_ids
        valid_requirement_ids = {q.requirement_id for q in questions_with_requirements if q.requirement_id}
        applies_to = [rid for rid in applies_to if rid in valid_requirement_ids]
        
        # If no valid applies_to, try to infer from topic
        if not applies_to and topic != "general":
            # Simple mapping: topic -> requirement_id
            topic_to_requirement = {
                "cpf": "has_cpf",
                "dap_caf": "has_dap_caf",
                "dap": "has_dap_caf",
                "caf": "has_dap_caf",
                "cnpj": "has_cnpj",
                "bank_account": "has_bank_account",
                "conta": "has_bank_account",
                "bank": "has_bank_account",
                "documents": "has_organized_documents",
                "documentos": "has_organized_documents",
            }
            mapped = topic_to_requirement.get(topic.lower())
            if mapped and mapped in valid_requirement_ids:
                applies_to = [mapped]
        
        return {
            "topic": topic.lower(),
            "applies_to": applies_to,  # Can be empty list if not applicable
            "confidence": confidence,
        }
    except Exception as e:
        # Fallback classification
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Classification failed for chunk: {e}",
            exc_info=True,
            extra={"chunk_preview": chunk_content[:200] if chunk_content else None, "operation": "classify_chunk"}
        )
        return {
            "topic": "general",
            "applies_to": [],
            "confidence": "low",
        }
