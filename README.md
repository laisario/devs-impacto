# PNAE Simplificado - Backend MVP

API para guiar pequenos produtores (agricultura familiar) a vender para o **PNAE** (Programa Nacional de Alimentação Escolar) via **Chamada Pública**.

## Sobre o Projeto

O sistema auxilia agricultores familiares, muitos com baixa alfabetização, a:

1. **Cadastrar-se** como produtor (formal/informal/individual)
2. **Organizar documentos** necessários (Envelope 01 - habilitação)
3. **Montar o Projeto de Venda** com produtos, preços e cronograma
4. **Gerar PDF** do Projeto de Venda no formato oficial

### Referências PNAE

- Compra da agricultura familiar via dispensa de licitação (Art. 24)
- Envelope 01: Documentos de habilitação
- Envelope 02: Projeto de Venda

## Requisitos

- Docker e Docker Compose

**Ou para desenvolvimento local:**
- Python 3.12+
- MongoDB 7.0+

## Quick Start com Docker (Recomendado)

```bash
# Clonar e entrar no diretório
git clone <repo-url>
cd pnae-backend

# Iniciar todos os serviços (MongoDB + API)
docker compose up -d

# Verificar se está rodando
docker compose ps

# Ver logs
docker compose logs -f api
```

**Pronto!** A API estará disponível em:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Comandos Docker Úteis

```bash
# Popular banco com dados de teste
docker compose --profile seeds up seeds

# Parar todos os serviços
docker compose down

# Parar e remover volumes (limpa banco)
docker compose down -v

# Rebuild após mudanças
docker compose build --no-cache
docker compose up -d

# Executar testes
docker compose exec api pytest -v

# Acessar shell do container
docker compose exec api bash
```

### Produção

```bash
# Definir JWT_SECRET obrigatório
export JWT_SECRET="sua-chave-secreta-muito-segura"

# Subir com config de produção
docker compose -f docker-compose.prod.yml up -d
```

## Desenvolvimento Local (Sem Docker)

```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou: .venv\Scripts\activate  # Windows

# Instalar dependências
pip install -e ".[dev]"

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com sua MONGODB_URI

# Iniciar MongoDB (precisa estar rodando)
# Exemplo: docker run -d -p 27017:27017 mongo:7

# Iniciar servidor
uvicorn app.main:app --reload

# Popular banco com dados de teste
python seeds.py
```

## Testes

```bash
# Com Docker
docker compose exec api pytest -v

# Localmente (requer MongoDB rodando)
pytest -v

# Com cobertura
pytest --cov=app

# Testar módulo AI Formalization
pytest tests/test_ai_formalization.py -v

# Teste rápido via script (requer servidor rodando)
./scripts/test_ai_formalization.sh
```

**Ver também:** [TESTING_AI_FORMALIZATION.md](TESTING_AI_FORMALIZATION.md) - Guia completo de testes do módulo AI

## Linting e Formatação

```bash
# Verificar código
ruff check .

# Formatar código
ruff format .

# Type checking
mypy app
```

## Exemplos de Requests (curl)

### Autenticação

```bash
# 1. Iniciar autenticação (envia OTP - mock: sempre 123456)
curl -X POST http://localhost:8000/auth/start \
  -H "Content-Type: application/json" \
  -d '{"phone_e164": "+5511999999999"}'

# Resposta: {"ok": true, "message": "OTP sent successfully"}

# 2. Verificar OTP e obter token
curl -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"phone_e164": "+5511999999999", "otp": "123456"}'

# Resposta: {"access_token": "eyJ...", "token_type": "bearer"}

# 3. Obter dados do usuário autenticado
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### Perfil do Produtor

```bash
# Criar/atualizar perfil (produtor individual)
curl -X PUT http://localhost:8000/producer-profile \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "producer_type": "individual",
    "name": "João da Silva",
    "address": "Sítio Boa Vista, km 5",
    "city": "Campinas",
    "state": "SP",
    "dap_caf_number": "DAP123456789",
    "cpf": "12345678901"
  }'

# Criar perfil (cooperativa - formal)
curl -X PUT http://localhost:8000/producer-profile \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "producer_type": "formal",
    "name": "Cooperativa Agricultores Unidos",
    "address": "Rua Principal, 100",
    "city": "Ribeirão Preto",
    "state": "SP",
    "dap_caf_number": "DAP987654321",
    "cnpj": "12345678000195"
  }'

# Obter perfil
curl -X GET http://localhost:8000/producer-profile \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Documentos

```bash
# 1. Obter URL para upload
curl -X POST http://localhost:8000/documents/presign \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "dap.pdf", "content_type": "application/pdf"}'

# Resposta: {"upload_url": "...", "file_url": "...", "file_key": "..."}

# 2. Fazer upload para upload_url (simulado em mock)

# 3. Registrar documento após upload
curl -X POST http://localhost:8000/documents \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_type": "dap_caf",
    "file_url": "URL_RETORNADA",
    "file_key": "KEY_RETORNADA",
    "original_filename": "dap.pdf"
  }'

# Listar documentos
curl -X GET http://localhost:8000/documents \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Onboarding e Formalização

```bash
# Responder pergunta de onboarding (uma por vez, incremental)
curl -X POST http://localhost:8000/onboarding/answer \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "has_cpf",
    "answer": true
  }'

# Obter status do onboarding
curl -X GET http://localhost:8000/onboarding/status \
  -H "Authorization: Bearer SEU_TOKEN"

# Resposta: {"status": "in_progress", "progress_percentage": 14.3, ...}

# Obter diagnóstico de formalização
curl -X GET http://localhost:8000/formalization/status \
  -H "Authorization: Bearer SEU_TOKEN"

# Resposta: {"is_eligible": false, "eligibility_level": "partially_eligible", "score": 65, ...}

# Obter tarefas de formalização
curl -X GET http://localhost:8000/formalization/tasks \
  -H "Authorization: Bearer SEU_TOKEN"

# Resposta: [{"task_id": "obtain_cpf", "title": "Obter CPF", "priority": "high", ...}, ...]
```

### AI Formalization Guide

```bash
# Gerar guia personalizado para um requisito específico
curl -X POST http://localhost:8000/ai/formalization/guide \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement_id": "has_cpf"
  }'

# Resposta: {"summary": "...", "steps": [...], "estimated_time_days": 7, ...}
```

## Estrutura do Projeto

```
├── Dockerfile              # Multi-stage build (dev + prod)
├── docker-compose.yml      # Desenvolvimento
├── docker-compose.prod.yml # Produção
├── app/
│   ├── main.py             # FastAPI app
│   ├── core/
│   │   ├── config.py       # Configurações (env vars)
│   │   ├── security.py     # JWT auth
│   │   ├── db.py           # MongoDB connection
│   │   └── errors.py       # Exception handlers
│   ├── modules/
│   │   ├── auth/           # Autenticação OTP + JWT
│   │   ├── producers/      # Perfil do produtor
│   │   ├── documents/      # Upload de documentos
│   │   ├── onboarding/     # Onboarding guiado
│   │   ├── formalization/  # Diagnóstico de formalização
│   │   └── ai_formalization/ # Agente AI para guias de formalização
│   └── shared/
│       ├── pagination.py   # Paginação
│       └── utils.py        # Utilitários
├── tests/
├── seeds.py                # Dados de teste
├── seeds_onboarding.py     # Seeds para perguntas de onboarding
├── scripts/
│   ├── create_indexes.py   # Criar índices MongoDB
│   ├── ingest_rag_documents.py  # Ingestão de PDFs no RAG
│   └── ingest_rag_manual.py     # Ingestão manual de chunks RAG
└── pyproject.toml
```

## Tipos de Produtor

| Tipo | Descrição | Documentos Obrigatórios |
|------|-----------|------------------------|
| `individual` | Agricultor familiar individual | CPF, DAP/CAF |
| `formal` | Cooperativa ou Associação | CNPJ, DAP/CAF, Estatuto |
| `informal` | Grupo informal | CPFs dos membros, DAP/CAF |

## Tipos de Documentos (Envelope 01)

- `dap_caf` - DAP/CAF (Declaração de Aptidão ao Pronaf)
- `cpf` - CPF
- `cnpj` - CNPJ
- `proof_address` - Comprovante de endereço
- `bank_statement` - Dados bancários
- `statute` - Estatuto social
- `minutes` - Ata de assembleia
- `other` - Outros

## API Endpoints

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| POST | `/auth/start` | Iniciar autenticação | Não |
| POST | `/auth/verify` | Verificar OTP | Não |
| GET | `/auth/me` | Dados do usuário | Sim |
| PUT | `/producer-profile` | Criar/atualizar perfil | Sim |
| GET | `/producer-profile` | Obter perfil | Sim |
| POST | `/documents/presign` | URL para upload | Sim |
| POST | `/documents` | Registrar documento | Sim |
| GET | `/documents` | Listar documentos | Sim |
| POST | `/onboarding/answer` | Responder pergunta de onboarding | Sim |
| GET | `/onboarding/status` | Status do onboarding | Sim |
| GET | `/onboarding/summary` | Resumo agregado (onboarding + formalização) | Sim |
| GET | `/formalization/status` | Status de elegibilidade | Sim |
| GET | `/formalization/tasks` | Tarefas de formalização | Sim |
| POST | `/ai/formalization/guide` | Gerar guia personalizado de formalização | Sim |

## Onboarding e Formalização

O sistema inclui um módulo de onboarding guiado e diagnóstico de formalização:

### Onboarding

- **Incremental**: Responda uma pergunta por vez, pode parar e voltar quando quiser
- **Não bloqueia**: O onboarding é opcional, não afeta o uso do sistema existente
- **Progresso**: Sistema rastreia automaticamente o progresso e mostra próxima pergunta
- **Perguntas simples**: Linguagem clara pensada para baixa alfabetização

### Formalização

- **Diagnóstico automático**: Calculado automaticamente baseado nas respostas do onboarding
- **Elegibilidade**: Determina se o produtor está apto para vender em programas públicos (PNAE, PAA)
- **Tarefas guiadas**: Lista de tarefas personalizadas para ajudar na formalização
- **Recomendações**: Sugestões práticas de como melhorar a elegibilidade

### AI Formalization (RAG)

- **Guia personalizado**: Gera passo a passo adaptado ao perfil usando AI
- **RAG-powered**: Usa documentos oficiais como base de conhecimento
- **Linguagem simples**: Explicações claras para baixa alfabetização

**Injetar documentos no RAG:**
```bash
# Método 1: Ingestão manual (rápido para testes)
python scripts/ingest_rag_manual.py

# Método 2: Ingestão de arquivos de texto limpos (produção)
# 1. Coloque arquivos .txt já limpos em data/rag_text/
# 2. python scripts/ingest_rag_documents.py
# O sistema classifica automaticamente usando LLM!
```

**Ver também:** [RAG_INGESTION_GUIDE.md](RAG_INGESTION_GUIDE.md) - Guia completo de ingestão de documentos

### Coleções MongoDB

- `onboarding_questions` - Perguntas de onboarding (configurável)
- `onboarding_answers` - Respostas incrementais do onboarding (linkadas por `user_id`)
- `formalization_status` - Cache do diagnóstico de elegibilidade (linkado por `user_id`)
- `formalization_tasks` - Tarefas de formalização para cada usuário (linkadas por `user_id`)
- `rag_chunks` - Chunks de documentos para RAG (têm `applies_to` com requirement IDs)

### Estrutura de Dados Linkados

Todas as informações estão linkadas através do `user_id` (ObjectId do usuário):

```
users (auth)
  └── user_id
      ├── producer_profiles (onboarding_status, onboarding_completed_at)
      ├── onboarding_answers (todas as respostas)
      ├── formalization_status (diagnóstico e pontuação)
      └── formalization_tasks (lista de tarefas)
```

**Facilidades para usar essas informações:**

1. **Endpoint agregado**: `GET /onboarding/summary` - retorna resumo completo com:
   - Status e progresso do onboarding
   - Pontuação e elegibilidade de formalização
   - Contagem de tarefas e respostas
   - Se tem perfil criado

2. **Índices otimizados**: Script `scripts/create_indexes.py` cria índices para:
   - Busca rápida por `user_id` em todas as coleções
   - Índice único em `(user_id, question_id)` para evitar duplicatas
   - Ordenação eficiente por data e prioridade

3. **Métodos helpers**:
   - `get_all_answers(user_id)` - Todas as respostas de um usuário
   - `get_producer_summary(user_id)` - Resumo agregado completo
   - `get_status(user_id)` - Status detalhado do onboarding

## Variáveis de Ambiente

| Variável | Descrição | Default |
|----------|-----------|---------|
| `MONGODB_URI` | URI de conexão MongoDB | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Nome do banco | `pnae_dev` |
| `JWT_SECRET` | Chave secreta JWT | (obrigatório em prod) |
| `JWT_ALGORITHM` | Algoritmo JWT | `HS256` |
| `JWT_EXPIRE_MINUTES` | Expiração do token | `1440` (24h) |
| `STORAGE_PROVIDER` | Provider de storage | `mock` |
| `OPENAI_API_KEY` | Chave API OpenAI (para AI formalization) | (opcional) |
| `LLM_PROVIDER` | Provider LLM (openai/mock) | `mock` |
| `LLM_MODEL` | Modelo LLM a usar | `gpt-4o-mini` |
| `RAG_EMBEDDING_MODEL` | Modelo de embeddings | `text-embedding-3-small` |

## Licença

MIT
