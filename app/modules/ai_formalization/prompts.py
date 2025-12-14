"""
Prompt templates for the AI formalization agent.

The agent uses a fixed prompt template to ensure consistency and prevent
the model from making legal determinations.
"""

AGENT_SYSTEM_PROMPT = """Você é um agente de formalização de pequenos produtores rurais no Brasil.

Seu papel:
- explicar COMO o produtor pode cumprir um requisito específico
- usar apenas as informações fornecidas nos documentos de referência
- adaptar a explicação ao perfil do produtor

Regras obrigatórias:
- Linguagem simples
- Frases curtas
- Evitar termos técnicos; quando usar, explicar
- Nunca dizer que algo é "obrigatório por lei"
- Nunca dar parecer jurídico
- Sempre focar em passos práticos

Contexto do produtor:
{producer_profile}

Requisito a ser resolvido:
{requirement}

Documentos de referência:
{rag_chunks}

Tarefa:
Gere um passo a passo claro e específico para este produtor,
em no máximo 8 passos numerados.

Cada passo deve:
- começar com um verbo
- explicar onde ir ou o que fazer
- evitar abstrações

Saida estruturada (JSON válido):
{{
  "summary": "Para se formalizar como produtor, você precisa fazer um cadastro simples.",
  "steps": [
    {{
      "step": 1,
      "title": "Procurar apoio local",
      "description": "Vá até a Secretaria de Agricultura ou EMATER do seu município."
    }},
    {{
      "step": 2,
      "title": "Levar documentos básicos",
      "description": "Leve CPF, RG e um comprovante simples de que você produz alimentos."
    }}
  ],
  "estimated_time_days": 7,
  "where_to_go": [
    "Secretaria Municipal de Agricultura",
    "EMATER"
  ],
  "confidence_level": "high"
}}"""


def format_producer_profile(profile: dict | None) -> str:
    """
    Format producer profile for the prompt.

    Args:
        profile: Producer profile dictionary or None

    Returns:
        Formatted string for the prompt
    """
    if not profile:
        return "Perfil ainda não criado. Produtor está iniciando o processo."

    parts = []
    if profile.get("name"):
        parts.append(f"Nome: {profile['name']}")
    if profile.get("producer_type"):
        parts.append(f"Tipo: {profile['producer_type']}")
    if profile.get("city") and profile.get("state"):
        parts.append(f"Localização: {profile['city']}, {profile['state']}")

    if not parts:
        return "Perfil básico criado."
    return "\n".join(parts)


def format_rag_chunks(chunks: list[dict]) -> str:
    """
    Format RAG chunks for the prompt.

    Args:
        chunks: List of RAG chunk dictionaries

    Returns:
        Formatted string with chunk contents
    """
    if not chunks:
        return "Nenhum documento de referência específico disponível."

    formatted = []
    for i, chunk in enumerate(chunks, 1):
        content = chunk.get("content", "")
        source = chunk.get("source", "Documento")
        formatted.append(f"\n[Documento {i} - {source}]\n{content}")

    return "\n".join(formatted)


def build_prompt(
    producer_profile: dict | None,
    requirement_text: str,
    rag_chunks: list[dict],
) -> str:
    """
    Build the complete prompt for the LLM.

    Args:
        producer_profile: Producer profile dictionary or None
        requirement_text: Text description of the requirement
        rag_chunks: List of relevant RAG chunks

    Returns:
        Complete formatted prompt
    """
    profile_text = format_producer_profile(producer_profile)
    chunks_text = format_rag_chunks(rag_chunks)

    return AGENT_SYSTEM_PROMPT.format(
        producer_profile=profile_text,
        requirement=requirement_text,
        rag_chunks=chunks_text,
    )
