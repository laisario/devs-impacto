"""Prompt template sections for better maintainability."""

PRODUCER_CONTEXT_SECTION = """CONTEXTO COMPLETO DO PRODUTOR:
{producer_profile_full}
"""

FORMALIZATION_STATUS_SECTION = """SITUAÇÃO ATUAL DE FORMALIZAÇÃO:
{formalization_status_detailed}
"""

DOCUMENTS_TASKS_SECTION = """DOCUMENTOS E TAREFAS:
{completed_vs_pending}
"""

REQUIREMENT_SECTION = """REQUISITO ESPECÍFICO:
{requirement}
"""

FOCUS_SECTION = """FOCO CRÍTICO - ESTE GUIA É APENAS PARA ESTE REQUISITO:
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
"""

OFFICE_ADDRESSES_SECTION = """ENDEREÇOS DISPONÍVEIS (use estes endereços, não peça ao usuário buscar):
{office_addresses}

Se um endereço não estiver disponível acima, use conhecimento geral para fornecer endereço específico baseado na cidade/estado. NUNCA peça ao usuário para "buscar no Google" ou "ligar para descobrir".
"""

RAG_SECTION = """DOCUMENTAÇÃO OFICIAL RELEVANTE (RAG):
{rag_chunks_enhanced}
"""

LANGUAGE_SECTION = """LINGUAGEM SIMPLES - PRINCÍPIOS DA ENAP (OBRIGATÓRIO):
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
"""

KNOWLEDGE_BASE_SECTION = """CONHECIMENTO ESTRUTURADO - USE ESTAS INFORMAÇÕES:

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
"""

RAG_FALLBACK_SECTION = """SE O RAG NÃO TIVER INFORMAÇÕES ESPECÍFICAS:
- Use conhecimento geral sobre processos brasileiros
- Mencione sites oficiais (gov.br, receita.fazenda.gov.br, emater.gov.br, etc.)
- Forneça instruções de como pesquisar: "Busque 'Emater [CIDADE] [ESTADO]' no Google" ou "Acesse o site emater.gov.br e procure o escritório da sua região"
- Mencione telefones de atendimento quando relevante (156 para prefeituras, 146 para Receita Federal, 0800 721 3000 para Emater)
- SEMPRE mencione alternativas (MEI para CNPJ individual)
- SEMPRE mencione se há processo online disponível
- Se não souber endereço exato, forneça instruções claras de como encontrar: "Busque no Google 'Emater [CIDADE] [ESTADO]' para encontrar endereço e telefone" ou "Ligue 156 (disque prefeitura) e peça o endereço da Secretaria de Agricultura"
"""

INSTRUCTIONS_SECTION = """INSTRUÇÕES CRÍTICAS - SEJA HIPERESPECÍFICO:
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
"""

OUTPUT_FORMAT_SECTION = """SAÍDA JSON:
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
- Se não souber endereço exato, forneça instruções claras de como encontrar e deixe address/map_link como null
"""


def build_enhanced_prompt(
    producer_profile_full: str,
    formalization_status_detailed: str,
    completed_vs_pending: str,
    requirement: str,
    office_addresses: str,
    rag_chunks_enhanced: str,
) -> str:
    """Build complete prompt from sections."""
    prompt_parts = [
        "Você é um agente especializado em ajudar produtores rurais a se formalizarem para vender para programas públicos (PNAE, PAA, etc.).\n",
        PRODUCER_CONTEXT_SECTION,
        FORMALIZATION_STATUS_SECTION,
        DOCUMENTS_TASKS_SECTION,
        REQUIREMENT_SECTION,
        FOCUS_SECTION,
        OFFICE_ADDRESSES_SECTION,
        RAG_SECTION,
        LANGUAGE_SECTION,
        KNOWLEDGE_BASE_SECTION,
        RAG_FALLBACK_SECTION,
        INSTRUCTIONS_SECTION,
        OUTPUT_FORMAT_SECTION,
    ]
    
    prompt = "\n".join(prompt_parts)
    
    return prompt.format(
        producer_profile_full=producer_profile_full,
        formalization_status_detailed=formalization_status_detailed,
        completed_vs_pending=completed_vs_pending,
        requirement=requirement,
        office_addresses=office_addresses,
        rag_chunks_enhanced=rag_chunks_enhanced,
    )
