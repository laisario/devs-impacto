"""
Prompt templates for the AI formalization agent.

The agent uses a fixed prompt template to ensure consistency and prevent
the model from making legal determinations.
"""

ENHANCED_AGENT_SYSTEM_PROMPT = """Você é um agente especializado em ajudar produtores rurais a se formalizarem para vender para programas públicos (PNAE, PAA, etc.).

CONTEXTO COMPLETO DO PRODUTOR:
{producer_profile_full}

SITUAÇÃO ATUAL DE FORMALIZAÇÃO:
{formalization_status_detailed}

DOCUMENTOS E TAREFAS:
{completed_vs_pending}

REQUISITO ESPECÍFICO:
{requirement}

FOCO CRÍTICO - ESTE GUIA É APENAS PARA ESTE REQUISITO:
- Você está gerando um guia APENAS para: {requirement}
- NÃO mencione outros requisitos (CNPJ, conta bancária, etc.) neste guia
- Cada passo deve ser uma ação GRANULAR e específica para completar APENAS este requisito
- Se o passo envolve ir a um local:
  * SEMPRE use os endereços fornecidos na seção "ENDEREÇOS DISPONÍVEIS" abaixo
  * Se não houver endereço disponível, use conhecimento geral para fornecer endereço específico baseado na cidade/estado
  * NUNCA peça ao usuário para "buscar no Google", "ligar para descobrir" ou "pesquisar"
  * Forneça endereço COMPLETO (rua, número, bairro, cidade, CEP) diretamente
  * Gere link Google Maps: https://www.google.com/maps/search/?api=1&query=[endereço_encoded]
  * Inclua telefone se disponível
  * Inclua horário de funcionamento se disponível
- Se o passo envolve documentos:
  * Liste EXATAMENTE quais documentos são necessários
  * Use campo documents_checklist
- Se o passo tem prazo:
  * Seja ESPECÍFICO: "na hora", "até 5 dias úteis", "15 minutos"

ENDEREÇOS DISPONÍVEIS (use estes endereços, não peça ao usuário buscar):
{office_addresses}

Se um endereço não estiver disponível acima, use conhecimento geral para fornecer endereço específico baseado na cidade/estado. NUNCA peça ao usuário para "buscar no Google" ou "ligar para descobrir".

DOCUMENTAÇÃO OFICIAL RELEVANTE (RAG):
{rag_chunks_enhanced}

LINGUAGEM SIMPLES - PRINCÍPIOS DA ENAP (OBRIGATÓRIO):
- Frases curtas: máximo 20 palavras por frase
- Uma ideia por frase
- Verbos no imperativo: "Vá", "Leve", "Peça" (não "Você deve ir", "É necessário levar")
- Palavras comuns: use "ir" não "comparecer", "documento" não "certidão", "pegar" não "obter"
- Ordem direta: "Você vai até a Emater" (não "Até a Emater você vai")
- Use "você" para aproximar do leitor
- Evite siglas: explique primeiro, depois use (ex: "DAP (Declaração de Aptidão ao Pronaf)")
- Evite voz passiva: "A DAP é emitida" → "A Emater emite a DAP"
- Evite negativas quando possível: "Não precisa de CNPJ" → "CNPJ não é necessário"
- Evite jargões técnicos: explique termos técnicos quando necessário
- Use números por extenso para valores pequenos: "três documentos" não "3 documentos"
- Evite abreviações: "você" não "vc", "com" não "c/"

CONHECIMENTO ESTRUTURADO - USE ESTAS INFORMAÇÕES:

CNPJ/Formalização:
- Para produtores INDIVIDUAIS: Pode abrir MEI (Microempreendedor Individual) online em gov.br/mei
  * MEI é gratuito e pode ser feito 100% online em ~15 minutos
  * Não precisa ir a lugar nenhum - tudo pelo site
  * Precisa apenas: CPF, título de eleitor ou recibo de declaração de imposto de renda
  * CNPJ sai na hora após cadastro
  * MEI permite emitir notas fiscais para vender aos programas públicos
- Para grupos FORMALS (cooperativas, associações): Precisa de CNPJ completo na Receita Federal
  * Processo mais complexo, pode ser online ou presencial
  * Site: receita.fazenda.gov.br
  * Pode precisar de ida à Receita Federal dependendo do caso

DAP/CAF:
- Emitido por: Emater, Sindicatos Rurais, Secretarias Municipais de Agricultura
- Processo: Geralmente presencial (levar documentos), mas pode ter agendamento online em alguns locais
- Gratuito
- Como encontrar: Buscar "Emater [CIDADE] [ESTADO]" no Google ou site emater.gov.br
- Alternativa: Sindicato dos Trabalhadores Rurais da cidade também emite

Conta Bancária:
- Pode ser aberta em qualquer banco (Banco do Brasil, Caixa, Bradesco, etc.)
- Processo: Presencial ou online (depende do banco)
- Documentos: CPF, RG, comprovante de endereço
- Alguns bancos permitem abertura 100% online

Comprovante de Endereço:
- Pode ser: Conta de luz, água, telefone dos últimos 3 meses
- Se não tiver, pode usar declaração de posse da terra ou contrato de arrendamento

Como encontrar órgãos específicos:
- Emater: Buscar "Emater [CIDADE] [ESTADO]" no Google ou site emater.gov.br. Telefone geral: 0800 721 3000
- Receita Federal: Buscar "Receita Federal [CIDADE]" ou usar site receita.fazenda.gov.br. Telefone: 146
- Prefeituras: Site da prefeitura de [CIDADE] ou telefone 156 (disque prefeitura)
- Sindicatos Rurais: Buscar "Sindicato Trabalhadores Rurais [CIDADE] [ESTADO]"

Processos Online Disponíveis:
- MEI: 100% online em gov.br/mei
- CNPJ completo: Pode ser iniciado online em receita.fazenda.gov.br
- Certidões negativas: Podem ser tiradas online em gov.br (Receita Federal, INSS, FGTS)
- Consulta de DAP: Pode ser consultada online no site do MDA

SE O RAG NÃO TIVER INFORMAÇÕES ESPECÍFICAS:
- Use conhecimento geral sobre processos brasileiros
- Mencione sites oficiais (gov.br, receita.fazenda.gov.br, emater.gov.br, etc.)
- Forneça instruções de como pesquisar: "Busque 'Emater [CIDADE] [ESTADO]' no Google" ou "Acesse o site emater.gov.br e procure o escritório da sua região"
- Mencione telefones de atendimento quando relevante (156 para prefeituras, 146 para Receita Federal, 0800 721 3000 para Emater)
- SEMPRE mencione alternativas (MEI para CNPJ individual)
- SEMPRE mencione se há processo online disponível
- Se não souber endereço exato, forneça instruções claras de como encontrar: "Busque no Google 'Emater [CIDADE] [ESTADO]' para encontrar endereço e telefone" ou "Ligue 156 (disque prefeitura) e peça o endereço da Secretaria de Agricultura"

INSTRUÇÕES CRÍTICAS - SEJA HIPERESPECÍFICO:
1. ANALISE PRIMEIRO: O que o produtor JÁ TEM vs o que FALTA (veja seção "DOCUMENTOS E TAREFAS")
2. LOCALIZAÇÃO É CRÍTICA: 
   - Se houver cidade/estado no contexto, você DEVE encontrar o local MAIS PRÓXIMO
   - Para cada step, forneça:
     * Nome COMPLETO do órgão/escritório
     * Endereço COMPLETO (rua, número, bairro, cidade, CEP se possível)
     * Telefone de contato (se disponível no RAG ou contexto)
     * Horário de funcionamento (se disponível)
     * Como chegar (referências próximas, se souber)
   - Se a cidade for pequena e não houver escritório local, indique a cidade MAIS PRÓXIMA com o endereço completo
   - Exemplo BOM: "Emater de Barra do Piraí - Rua Principal, 123, Centro, Barra do Piraí/RJ, CEP 27100-000. Telefone: (24) 1234-5678. Funciona de segunda a sexta, 8h às 17h."
   - Exemplo RUIM: "Vá até a Emater da sua cidade" ou "Procure a Emater mais próxima"
3. DOCUMENTOS ESPECÍFICOS: Liste EXATAMENTE o que o produtor precisa levar, baseado no que ele JÁ TEM:
   - Se já tem CPF, não mencione "precisa de CPF"
   - Se já tem conta bancária, não mencione "precisa de conta"
   - Liste apenas o que FALTA ou precisa ser atualizado
4. PERSONALIZE CADA PASSO:
   - Mencione o nome do produtor quando relevante
   - Mencione os produtos específicos que ele produz
   - Adapte instruções ao tipo de produtor (individual/formal/informal)
   - Considere o que ele já completou (não repita tarefas já feitas)
5. USE RAG INTENSIVAMENTE: 
   - Informações dos documentos oficiais são PRIORITÁRIAS
   - Se o RAG mencionar locais específicos, endereços, telefones, USE-OS
   - Se o RAG mencionar procedimentos específicos para a região, USE-OS
6. PRAZOS ESPECÍFICOS: Sempre mencione prazos realistas (ex: "5 dias úteis", "na hora", "até 15 dias")
7. LINGUAGEM: Simples, frases curtas, sem termos técnicos sem explicação
8. NUNCA: Dizer "obrigatório por lei" ou dar parecer jurídico
9. FOCO: Cada passo deve ser ACIONÁVEL IMEDIATAMENTE - o produtor deve saber EXATAMENTE onde ir, o que levar, quando ir

SAÍDA JSON:
{{
  "summary": "Resumo do que precisa ser feito APENAS para este requisito, considerando o que já foi feito. Mencione nome do produtor e produtos específicos.",
  "steps": [
    {{
      "step": 1,
      "title": "Título do passo GRANULAR e específico (ex: 'Reunir documentos necessários' ou 'Ir até Emater de [CIDADE], [ESTADO]')",
      "description": "Descrição HIPERESPECÍFICA do que fazer neste passo. Seja literalmente específico.",
      "documents_checklist": ["RG", "CPF", "Comprovante de endereço"] ou null,
      "address": "Endereço COMPLETO (rua, número, bairro, cidade, CEP)" ou null,
      "map_link": "https://www.google.com/maps/search/?api=1&query=[endereço_encoded]" ou null,
      "phone": "(XX) XXXX-XXXX" ou null,
      "opening_hours": "Segunda a sexta, 8h às 17h" ou null
    }}
  ],
  "estimated_time_days": 7,
  "where_to_go": ["Endereço COMPLETO do local 1 (rua, número, bairro, cidade, CEP)", "Endereço COMPLETO do local 2"],
  "confidence_level": "high"
}}

IMPORTANTE:
- Cada passo deve ser uma ação GRANULAR e específica
- Se o passo envolve documentos, use documents_checklist com lista exata
- Se o passo envolve ir a um local, SEMPRE forneça address e map_link
- Para map_link: use formato https://www.google.com/maps/search/?api=1&query=[endereço_completo_encoded]
- Para rota: https://www.google.com/maps/dir/[endereço_origem]/[endereço_destino]
- Se não souber endereço exato, forneça instruções claras de como encontrar e deixe address/map_link como null"""

AGENT_SYSTEM_PROMPT = ENHANCED_AGENT_SYSTEM_PROMPT  # Keep for backward compatibility


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
        producer_type_map = {
            "individual": "produtor individual",
            "informal": "grupo informal",
            "formal": "grupo formal (CNPJ)"
        }
        producer_type_str = producer_type_map.get(profile.get("producer_type"), profile.get("producer_type", "produtor"))
        parts.append(f"Tipo: {producer_type_str}")
    if profile.get("city") and profile.get("state"):
        parts.append(f"Localização: {profile['city']}, {profile['state']}")
    if profile.get("address"):
        parts.append(f"Endereço: {profile['address']}")
    if profile.get("dap_caf_number"):
        parts.append(f"DAP/CAF: {profile['dap_caf_number']} (JÁ POSSUI)")
    elif profile.get("dap_caf_number") is None:
        parts.append("DAP/CAF: Ainda não possui (em processo de obtenção)")
    if profile.get("cnpj"):
        parts.append(f"CNPJ: {profile['cnpj']} (JÁ POSSUI)")
    if profile.get("cpf"):
        parts.append(f"CPF: {profile['cpf']} (JÁ POSSUI)")
    if profile.get("bank_name"):
        parts.append(f"Conta bancária: {profile.get('bank_name')} - Agência {profile.get('bank_agency')}")

    if not parts:
        return "Perfil básico criado."
    return "\n".join(parts)


def format_onboarding_context(answers: dict) -> str:
    """
    Format onboarding answers for additional context.

    Args:
        answers: Dictionary mapping question_id to answer

    Returns:
        Formatted string with relevant context
    """
    context_parts = []
    
    # Localização (se não estiver no profile)
    city = answers.get("city")
    state = answers.get("state")
    if city or state:
        location_str = ", ".join(filter(None, [city, state]))
        if location_str:
            context_parts.append(f"Localização: {location_str}")
    
    # Produtos principais
    main_products = answers.get("main_products", [])
    if main_products:
        if isinstance(main_products, list):
            products_str = ", ".join(main_products)
        else:
            products_str = str(main_products)
        context_parts.append(f"Produtos principais: {products_str}")
    
    # Capacidade de produção
    production_capacity = answers.get("production_capacity")
    if production_capacity:
        context_parts.append(f"Capacidade de produção: {production_capacity}")
    
    # Tipo de produção
    production_type = answers.get("production_type")
    if production_type:
        context_parts.append(f"Tipo de produção: {production_type}")
    
    # Comunidade tradicional
    is_traditional = answers.get("is_indigenous_or_traditional", False)
    if is_traditional:
        context_parts.append("Faz parte de povo indígena ou comunidade tradicional (quilombola, ribeirinha, etc.)")
    
    # Experiência prévia
    has_previous_sales = answers.get("has_previous_sales", False)
    if has_previous_sales:
        context_parts.append("Já vendeu para programas públicos anteriormente")
    else:
        context_parts.append("Ainda não vendeu para programas públicos (primeira vez)")
    
    # DAP/CAF status
    has_dap_caf = answers.get("has_dap_caf", False)
    if has_dap_caf:
        context_parts.append("Já possui DAP/CAF")
    else:
        context_parts.append("Ainda não possui DAP/CAF (precisa obter)")
    
    if not context_parts:
        return ""
    
    return "\n".join(context_parts)


def format_formalization_status(status: dict | None) -> str:
    """
    Format formalization status for context with detailed information.

    Args:
        status: FormalizationStatusResponse object, dictionary, or None

    Returns:
        Formatted string with detailed status information
    """
    if not status:
        return "Status de formalização ainda não calculado."
    
    # Convert Pydantic model to dict if needed
    if hasattr(status, 'model_dump'):
        status = status.model_dump()
    elif hasattr(status, 'dict'):
        status = status.dict()
    elif not isinstance(status, dict):
        # If it's a Pydantic model, try to access attributes directly
        status = {
            "eligibility_level": getattr(status, "eligibility_level", None),
            "score": getattr(status, "score", None),
            "requirements_met": getattr(status, "requirements_met", []),
            "requirements_missing": getattr(status, "requirements_missing", []),
            "recommendations": getattr(status, "recommendations", []),
        }
    
    parts = []
    if status.get("eligibility_level"):
        eligibility_map = {
            "eligible": "Totalmente elegível",
            "partially_eligible": "Parcialmente elegível",
            "not_eligible": "Não elegível"
        }
        level = eligibility_map.get(status.get("eligibility_level"), status.get("eligibility_level"))
        parts.append(f"Status de elegibilidade: {level}")
    
    if status.get("score") is not None:
        parts.append(f"Pontuação: {status.get('score')}/100")
    
    if status.get("requirements_met"):
        met = ", ".join(status.get("requirements_met", []))
        parts.append(f"✅ Requisitos ATENDIDOS: {met}")
    
    if status.get("requirements_missing"):
        missing = ", ".join(status.get("requirements_missing", []))
        parts.append(f"❌ Requisitos FALTANTES: {missing}")
    
    if status.get("recommendations"):
        recommendations = "\n  - ".join(status.get("recommendations", []))
        parts.append(f"💡 Recomendações:\n  - {recommendations}")
    
    if not parts:
        return "Status de formalização ainda não calculado."
    
    return "\n".join(parts)


def format_rag_chunks(chunks: list[dict]) -> str:
    """
    Format RAG chunks for the prompt with enhanced formatting.
    Emphasizes location-specific information.

    Args:
        chunks: List of RAG chunk dictionaries

    Returns:
        Formatted string with chunk contents
    """
    if not chunks:
        return "Nenhum documento de referência específico disponível."

    location_chunks = []
    online_chunks = []
    alternative_chunks = []
    general_chunks = []
    
    # Separate chunks by type
    for chunk in chunks:
        content = chunk.get("content", "").lower()
        topic = chunk.get("topic", "").lower()
        full_text = f"{content} {topic}"
        
        # Check for location-specific information
        location_keywords = ["emater", "endereço", "rua", "telefone", "horário", "funcionamento", 
                            "escritório", "secretaria", "municipal", "regional", "cidade", "município",
                            "avenida", "bairro", "cep", "contato", "atendimento", "localização"]
        if any(keyword in full_text for keyword in location_keywords):
            location_chunks.append(chunk)
            continue
        
        # Check for online process information
        online_keywords = ["online", "portal", "site", "gov.br", "internet", "web", "digital", 
                          "mei", "microempreendedor", "cadastro online", "sistema"]
        if any(keyword in full_text for keyword in online_keywords):
            online_chunks.append(chunk)
            continue
        
        # Check for alternative information (MEI, etc.)
        alternative_keywords = ["mei", "microempreendedor", "alternativa", "opção", "pode também",
                               "outra forma", "também é possível"]
        if any(keyword in full_text for keyword in alternative_keywords):
            alternative_chunks.append(chunk)
            continue
        
        general_chunks.append(chunk)
    
    # Prioritize: location > online > alternatives > general
    prioritized_chunks = location_chunks + online_chunks + alternative_chunks + general_chunks
    
    formatted = []
    for i, chunk in enumerate(prioritized_chunks, 1):
        content = chunk.get("content", "")
        source = chunk.get("source", "Documento")
        topic = chunk.get("topic", "")
        page = chunk.get("page")
        
        # Mark chunks by type
        if chunk in location_chunks:
            marker = "📍 "
        elif chunk in online_chunks:
            marker = "💻 "
        elif chunk in alternative_chunks:
            marker = "🔄 "
        else:
            marker = ""
        
        header = f"{marker}[Documento {i} - {source}"
        if topic:
            header += f" | Tópico: {topic}"
        if page:
            header += f" | Página {page}"
        header += "]"
        
        formatted.append(f"\n{header}\n{content}")

    # Add warnings about important chunks
    warnings = []
    if location_chunks:
        warnings.append("📍 Chunks marcados com 📍 contêm informações sobre LOCAIS, ENDEREÇOS COMPLETOS, TELEFONES, HORÁRIOS. USE-OS para fornecer endereços LITERALMENTE ESPECÍFICOS!")
    if online_chunks:
        warnings.append("💻 Chunks marcados com 💻 contêm informações sobre PROCESSOS ONLINE. SEMPRE mencione processos online quando disponíveis!")
    if alternative_chunks:
        warnings.append("🔄 Chunks marcados com 🔄 contêm informações sobre ALTERNATIVAS (ex: MEI para CNPJ). SEMPRE mencione alternativas quando aplicáveis!")
    
    if warnings:
        formatted.insert(0, "⚠️ ATENÇÃO CRÍTICA:\n" + "\n".join(warnings) + "\n")

    return "\n".join(formatted)

def format_complete_context(context: dict | None) -> str:
    """
    Format complete context (documents, tasks) for the prompt.

    Args:
        context: Dictionary with complete context

    Returns:
        Formatted string with context information
    """
    if not context:
        return ""
    
    parts = []
    
    # Documents
    documents = context.get("documents", [])
    if documents:
        doc_parts = []
        for doc in documents:
            doc_type = doc.get("type", "desconhecido")
            status = doc.get("status", "desconhecido")
            ai_validated = doc.get("ai_validated", False)
            status_str = f"{status}"
            if ai_validated:
                status_str += " (validado por IA)"
            doc_parts.append(f"  - {doc_type}: {status_str}")
        if doc_parts:
            parts.append("Documentos enviados:")
            parts.extend(doc_parts)
    
    # Completed tasks
    tasks_completed = context.get("tasks_completed", [])
    if tasks_completed:
        completed_parts = [f"  - {task.get('title', 'Tarefa')}" for task in tasks_completed]
        parts.append("✅ Tarefas COMPLETADAS:")
        parts.extend(completed_parts)
    
    # Pending tasks
    tasks_pending = context.get("tasks_pending", [])
    if tasks_pending:
        pending_parts = [f"  - {task.get('title', 'Tarefa')}" for task in tasks_pending]
        parts.append("⏳ Tarefas PENDENTES:")
        parts.extend(pending_parts)
    
    if not parts:
        return ""
    
    return "\n".join(parts)


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
        producer_profile_full=profile_text,
        formalization_status_detailed="",
        completed_vs_pending="",
        requirement=requirement_text,
        office_addresses="",
        rag_chunks_enhanced=chunks_text,
    )


def _get_map_link_instructions(city: str | None, state: str | None) -> str:
    """
    Get instructions for generating Google Maps links.
    
    Args:
        city: City name
        state: State abbreviation
    
    Returns:
        String with instructions for generating map links
    """
    if city and state:
        return f"""
INSTRUÇÕES PARA LINKS DE MAPAS:
- Para busca simples: https://www.google.com/maps/search/?api=1&query=[endereço_completo_encoded]
- Para rota: https://www.google.com/maps/dir/[endereço_origem]/[endereço_destino]
- Exemplo: Se o endereço for "Rua Principal, 123, Centro, {city}/{state}", o link seria:
  https://www.google.com/maps/search/?api=1&query=Rua+Principal+123+Centro+{city}+{state}
- Sempre encode espaços como + e caracteres especiais como %XX
- Se não souber endereço exato, deixe map_link como null e forneça instruções de como encontrar
"""
    return """
INSTRUÇÕES PARA LINKS DE MAPAS:
- Para busca simples: https://www.google.com/maps/search/?api=1&query=[endereço_completo_encoded]
- Para rota: https://www.google.com/maps/dir/[endereço_origem]/[endereço_destino]
- Sempre encode espaços como + e caracteres especiais como %XX
- Se não souber endereço exato, deixe map_link como null e forneça instruções de como encontrar
"""


def _get_requirement_specific_instructions(requirement_id: str, producer_type: str | None = None, city: str | None = None, state: str | None = None) -> str:
    """
    Get specific instructions for a requirement based on requirement_id.
    
    Args:
        requirement_id: The requirement ID (e.g., "cnpj", "dap_caf")
        producer_type: Producer type (individual, formal, informal)
        city: City name for location-specific instructions
        state: State abbreviation for location-specific instructions
    
    Returns:
        String with specific instructions for the requirement
    """
    map_instructions = _get_map_link_instructions(city, state)
    
    instructions_map = {
        "cnpj": f"""
IMPORTANTE - CNPJ/Formalização (ESTE GUIA É APENAS PARA CNPJ):
- Este guia é APENAS para obter CNPJ. NÃO mencione outros requisitos.
- Se o produtor for INDIVIDUAL: 
  * Passo 1: Reunir documentos (CPF, título de eleitor ou recibo de declaração de imposto de renda)
  * Passo 2: Acessar gov.br/mei e fazer cadastro online (100% online, ~15 minutos, CNPJ sai na hora)
  * Não precisa de address/map_link pois é online
- Se for grupo FORMAL: 
  * Passo 1: Reunir documentos (CPF dos responsáveis, RG, comprovante de endereço da sede, estatuto)
  * Passo 2: Iniciar processo online em receita.fazenda.gov.br OU comparecer à Receita Federal
  * Se presencial: forneça address completo e map_link da Receita Federal mais próxima
  * Telefone: 146
- SEMPRE mencione a opção online primeiro quando disponível
{map_instructions}
        """,
        "dap_caf": f"""
IMPORTANTE - DAP/CAF (ESTE GUIA É APENAS PARA DAP/CAF):
- Este guia é APENAS para obter DAP/CAF. NÃO mencione outros requisitos.
- Passo 1: Reunir documentos necessários
  * Use documents_checklist: ["RG", "CPF", "Comprovante de endereço atualizado (conta de luz, água ou telefone dos últimos 3 meses)", "Documento da terra (escritura, contrato de arrendamento, declaração de posse ou autorização de uso)"]
- Passo 2: Ir até Emater/Sindicato/Secretaria de Agricultura
  * USE os endereços fornecidos na seção "ENDEREÇOS DISPONÍVEIS" do prompt
  * Se houver endereço de Emater disponível, use esse endereço COMPLETO
  * Se não houver, use conhecimento geral para fornecer endereço específico baseado em {city} {state}
  * NUNCA peça ao usuário para "buscar no Google" ou "ligar para descobrir"
  * Forneça address COMPLETO diretamente (rua, número, bairro, cidade, CEP)
  * Gere map_link usando formato: https://www.google.com/maps/search/?api=1&query=[endereço_encoded]
  * Inclua phone se disponível
  * Inclua opening_hours se disponível (geralmente "Segunda a sexta, 8h às 17h")
  * Se realmente não souber endereço: forneça endereço genérico mas específico como "Emater geralmente fica na Secretaria de Agricultura da prefeitura de {city}. Vá até a prefeitura e pergunte onde fica a Emater."
- Passo 3: Aguardar emissão
  * Prazo específico: "na hora" ou "até 5 dias úteis"
- Órgãos que emitem: Emater, Sindicatos Rurais, Secretarias Municipais de Agricultura
{map_instructions}
        """,
        "bank_account": f"""
IMPORTANTE - Conta Bancária (ESTE GUIA É APENAS PARA CONTA BANCÁRIA):
- Este guia é APENAS para abrir conta bancária. NÃO mencione outros requisitos.
- Passo 1: Reunir documentos
  * Use documents_checklist: ["CPF", "RG", "Comprovante de endereço atualizado (conta de luz, água ou telefone dos últimos 3 meses)"]
- Passo 2: Escolher banco e verificar abertura online
  * Muitos bancos permitem abertura online (mencione isso primeiro)
  * Se presencial: forneça endereço específico baseado em {city} {state}
  * Use conhecimento geral: "Banco do Brasil geralmente tem agência no centro de {city}" ou "Caixa Econômica fica na [endereço conhecido]"
  * NUNCA peça ao usuário para "buscar no Google"
  * Forneça endereço ou instrução clara: "Vá até o centro de {city} e procure agência do Banco do Brasil ou Caixa"
{map_instructions}
        """,
        "address_proof": f"""
IMPORTANTE - Comprovante de Endereço (ESTE GUIA É APENAS PARA COMPROVANTE):
- Este guia é APENAS para obter comprovante de endereço. NÃO mencione outros requisitos.
- Passo 1: Verificar se já possui
  * Conta de luz, água, telefone dos últimos 3 meses
- Passo 2: Se não tiver, obter alternativas
  * Declaração de posse da terra
  * Contrato de arrendamento
  * Solicitar declaração no sindicato rural ou Emater
  * Se precisar ir a algum local: forneça address e map_link
{map_instructions}
        """,
    }
    
    base_instruction = instructions_map.get(requirement_id, "")
    
    # Add producer type specific instructions for CNPJ
    if requirement_id == "cnpj" and producer_type == "individual":
        return instructions_map["cnpj"] + "\n\n⚠️ ATENÇÃO ESPECIAL: Este produtor é INDIVIDUAL. A opção MEI online é a MAIS SIMPLES e RÁPIDA. Destaque isso claramente no Passo 2!"
    
    return base_instruction


def format_office_addresses(office_addresses: dict[str, dict]) -> str:
    """
    Format office addresses for the prompt.
    
    Args:
        office_addresses: Dictionary mapping office type to OfficeInfo dict
    
    Returns:
        Formatted string with office addresses
    """
    if not office_addresses:
        return "Nenhum endereço específico encontrado. Use conhecimento geral para fornecer endereço baseado na cidade/estado."
    
    parts = []
    for office_type, info in office_addresses.items():
        name = info.get("name", office_type)
        address = info.get("address", "")
        phone = info.get("phone", "")
        opening_hours = info.get("opening_hours", "")
        maps_link = info.get("google_maps_link", "")
        
        office_text = f"{name}:\n"
        if address:
            office_text += f"  Endereço: {address}\n"
        if phone:
            office_text += f"  Telefone: {phone}\n"
        if opening_hours:
            office_text += f"  Horário: {opening_hours}\n"
        if maps_link:
            office_text += f"  Link Maps: {maps_link}\n"
        
        parts.append(office_text)
    
    return "\n".join(parts)


def build_personalized_prompt(
    producer_profile: dict | None,
    requirement_text: str,
    rag_chunks: list[dict],
    onboarding_answers: dict | None = None,
    formalization_status: dict | None = None,
    complete_context: dict | None = None,
    requirement_id: str | None = None,
    office_addresses: dict[str, dict] | None = None,
) -> str:
    """
    Build a personalized prompt with enriched context from onboarding and formalization.

    Args:
        producer_profile: Producer profile dictionary or None
        requirement_text: Text description of the requirement
        rag_chunks: List of relevant RAG chunks
        onboarding_answers: Dictionary of onboarding answers (question_id -> answer)
        formalization_status: FormalizationStatusResponse dictionary or None
        complete_context: Dictionary with complete context (documents, tasks)

    Returns:
        Complete formatted prompt with personalized context
    """
    # Build base profile context (enhanced with all fields)
    profile_text = format_producer_profile(producer_profile)
    
    # Add onboarding context (always include, even if profile exists)
    onboarding_context = ""
    if onboarding_answers:
        onboarding_context = format_onboarding_context(onboarding_answers)
        if onboarding_context:
            if profile_text and "Perfil ainda não criado" not in profile_text:
                profile_text += "\n\nInformações adicionais do onboarding:\n" + onboarding_context
            else:
                # If no profile, use onboarding context as main profile info
                profile_text = "Informações do produtor (do onboarding):\n" + onboarding_context
    
    # Add formalization status context (detailed)
    status_context = format_formalization_status(formalization_status)
    
    # Add complete context (documents and tasks)
    context_text = format_complete_context(complete_context)
    
    # Format RAG chunks (enhanced)
    chunks_text = format_rag_chunks(rag_chunks)
    
    # Build enhanced prompt
    prompt = ENHANCED_AGENT_SYSTEM_PROMPT
    
    # Add instructions for traditional communities
    if onboarding_answers and onboarding_answers.get("is_indigenous_or_traditional"):
        prompt = prompt.replace(
            "INSTRUÇÕES:",
            "IMPORTANTE: Este produtor faz parte de comunidade tradicional. Considere a Nota Técnica 03/2020 do MPF, que permite autoconsumo sem registros sanitários para produtos produzidos e consumidos na mesma comunidade.\n\nINSTRUÇÕES:"
        )
    
    # Format office addresses
    addresses_text = format_office_addresses(office_addresses or {})
    
    return prompt.format(
        producer_profile_full=profile_text,
        formalization_status_detailed=status_context,
        completed_vs_pending=context_text,
        requirement=requirement_text,
        rag_chunks_enhanced=chunks_text,
        office_addresses=addresses_text,
    )
