# Guia de Desenvolvimento

Guia completo para desenvolvimento, testes, qualidade de código e contribuição.

## Setup Local

### Pré-requisitos

- Docker & Docker Compose (recomendado)
- OU Python 3.12+ e Node.js 18+ (desenvolvimento local)

### Usando Docker (Recomendado)

```bash
# Iniciar todos os serviços
docker-compose up

# Acessar serviços
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Desenvolvimento Local

#### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv ../.venv
source ../.venv/bin/activate  # Linux/Mac
# ou: ..\.venv\Scripts\activate  # Windows

# Instalar dependências
pip install -e ".[dev]"

# Configurar ambiente
cp .env.example .env
# Editar .env com sua MongoDB URI e outras configurações

# Rodar servidor
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Rodar servidor de desenvolvimento
npm run dev
```

## Variáveis de Ambiente

### Backend

Variáveis principais (veja `backend/app/core/config.py` para lista completa):

- `MONGODB_URI` - String de conexão MongoDB
- `DATABASE_NAME` - Nome do banco (padrão: `pnae_dev`)
- `JWT_SECRET` - Chave secreta JWT (obrigatória em produção)
- `LLM_PROVIDER` - Provedor LLM: `openai`, `deco`, ou `mock`
- `OPENAI_API_KEY` - Chave da API OpenAI (se usar OpenAI)

### Frontend

- `VITE_API_BASE_URL` - URL da API backend (padrão: `http://localhost:8000`)

**Dica**: Use `docker-compose.override.yml` para overrides locais.

## Qualidade de Código

### Backend

```bash
cd backend

# Lint
ruff check app/

# Formatar
ruff format app/

# Type check
mypy app
```

### Frontend

```bash
cd frontend

# Lint
npm run lint

# Type check
npm run typecheck

# Formatar (se configurado)
npm run format
```

## Testes

### Backend

#### Testes Unitários

**Localização**: `backend/tests/` (excluindo `tests/integration/`)

**Rodar:**
```bash
cd backend
source ../.venv/bin/activate
python -m pytest tests/ -m "not integration"
```

#### Testes de Integração

**Localização**: `backend/tests/integration/`

Testam fluxos completos:
- Autenticação (start → verify → me)
- Criação e atualização de perfil
- Fluxo de onboarding
- Diagnóstico de formalização
- Upload de documentos

**Rodar:**
```bash
cd backend
source ../.venv/bin/activate
python -m pytest tests/integration/ -v
```

**Problemas Comuns:**
- `ModuleNotFoundError: No module named 'motor'` → Ative o ambiente virtual
- Use `python -m pytest` ao invés de `pytest` diretamente

#### Testes de IA

**Localização**: `backend/tests/test_ai_formalization.py`

**Rodar:**
```bash
cd backend
python -m pytest tests/test_ai_formalization.py -v
```

**Preparação:**
```bash
# Popular perguntas de onboarding
python scripts/dev/seed_onboarding_questions.py

# (Opcional) Popular chunks RAG se tiver documentos
python scripts/ops/ingest_rag_documents.py
```

**Configuração:**
- Para desenvolvimento/testes (usa mock - não precisa API key): `LLM_PROVIDER=mock`
- Para testar com OpenAI real: `OPENAI_API_KEY=sk-sua-chave` e `LLM_PROVIDER=openai`

#### Cobertura

```bash
cd backend
python -m pytest tests/ --cov=app --cov-report=html
# Abrir htmlcov/index.html no navegador
```

### Frontend

#### Testes Unitários

**Localização**: `frontend/src/services/api/__tests__/`

Testam serviços de API:
- Auth service
- Onboarding service
- Documents service

**Rodar:**
```bash
cd frontend
npm run test:unit
```

**Modo watch:**
```bash
npm run test:unit:watch
```

#### Testes E2E

**Localização**: `frontend/e2e/`

Testam fluxos completos de usuário:
- Autenticação
- Onboarding
- Dashboard
- Upload de documentos
- Geração de guia com IA

**Pré-requisitos:**
- Backend rodando em `http://localhost:8000`
- Frontend rodando em `http://localhost:5173`
- MongoDB disponível

**Rodar:**
```bash
# Terminal 1: Iniciar serviços
docker-compose up

# Terminal 2: Rodar testes E2E
cd frontend
npm run test:e2e
```

**Opções:**
- `npm run test:e2e:ui` - UI interativa do Playwright
- `npm run test:e2e:headed` - Navegador visível
- `npm run test:e2e:debug` - Modo debug

## Tarefas Comuns

### Popular Banco de Dados

```bash
cd backend

# Popular perguntas de onboarding
python scripts/dev/seed_onboarding_questions.py

# Popular dados de exemplo (opcional, para desenvolvimento)
python scripts/dev/seeds.py
```

### Criar Índices

```bash
cd backend
python scripts/ops/create_indexes.py
```

### Ingerir Documentos RAG

Veja seção [Ingestão de Documentos RAG](#ingestão-de-documentos-rag) abaixo.

## Debugging

### Logs do Backend

```bash
docker-compose logs -f backend
```

### Frontend DevTools

Abra DevTools do navegador (F12) para debug do React.

### Acesso ao Banco de Dados

```bash
# Usando Docker
docker-compose exec mongo mongosh

# Ou conectar com cliente MongoDB
mongodb://localhost:27017
```

## Hot Reload

Tanto frontend quanto backend suportam hot reload:

- **Backend**: `uvicorn app.main:app --reload` (automático com Docker)
- **Frontend**: Vite HMR (automático com `npm run dev`)

## Ingestão de Documentos RAG

Este guia explica como injetar documentos de texto limpos no sistema RAG para que o agente AI possa usá-los ao gerar guias de formalização.

**IMPORTANTE:** O sistema processa arquivos `.txt` já limpos e padronizados, não PDFs brutos.

**NOVO:** Classificação automática! O sistema agora usa LLM para determinar automaticamente `topic` e `applies_to` de cada chunk, baseado nas perguntas de onboarding existentes.

### Estrutura

```
backend/data/rag/
├── raw/                    # Documentos originais (HTML, PDF, DOC)
├── processed/              # Arquivos de texto limpos (.txt) - USE ESTE PARA INGESTÃO
└── metadata/               # Metadados CSV e JSON
```

**Importante:** Os arquivos devem ser arquivos `.txt` já limpos e processados. Coloque-os em `backend/data/rag/processed/`.

### Passo a Passo

#### 1. Preparar arquivos de texto limpos

Os arquivos de texto devem estar já limpos e padronizados em `backend/data/rag/processed/`:

```bash
# Criar diretório (se não existir)
mkdir -p backend/data/rag/processed

# Adicionar arquivos .txt já processados/limpos
cp /caminho/para/seu/documento.txt backend/data/rag/processed/
```

**Nota:** O script processa arquivos `.txt` já limpos, não PDFs. Se você tem PDFs, precisa primeiro convertê-los e limpá-los usando scripts de pré-processamento.

#### 2. Verificar dependências

```bash
# MongoDB deve estar rodando
# Onboarding questions devem estar populadas
python scripts/dev/seed_onboarding_questions.py

# LLM configurado (opcional, mas recomendado para classificação)
# No .env: LLM_PROVIDER=openai (ou mock para testes)
```

#### 3. Executar ingestão

```bash
# Popular documentos
python scripts/ops/ingest_rag_documents.py
```

O script irá:
1. Ler todos os arquivos `.txt` de `backend/data/rag/processed/`
2. Ler o conteúdo de cada arquivo (já está em texto limpo)
3. Fazer chunking (dividir em pedaços)
4. **Classificar cada chunk automaticamente** usando LLM:
   - Determina `topic`
   - Determina `applies_to` (quais requirement_ids se aplicam)
   - Baseado nas perguntas de onboarding existentes
5. Gerar embeddings (se `OPENAI_API_KEY` estiver configurada)
6. Salvar no MongoDB na collection `rag_chunks`

**Modo manual (sem classificação automática):**
```bash
python scripts/ops/ingest_rag_documents.py --manual
```
(Isso requer configuração manual, não recomendado)

### Verificar Documentos Ingeridos

#### Via MongoDB shell:

```javascript
// Ver todos os chunks
db.rag_chunks.find().pretty()

// Ver chunks por requirement
db.rag_chunks.find({applies_to: "has_cpf"}).count()

// Ver por topic
db.rag_chunks.find({topic: "dap_caf"}).pretty()
```

#### Via código:

```python
from app.core.db import get_database
from app.modules.ai_formalization.rag import RAGService

db = get_database()
rag_service = RAGService(db)

# Listar todos os chunks
chunks = await rag_service.get_all_chunks()
print(f"Total chunks: {len(chunks)}")

# Buscar por requirement
relevant = await rag_service.search_relevant_chunks("has_cpf", limit=10)
print(f"Chunks para has_cpf: {len(relevant)}")
```

### Troubleshooting RAG

**Erro: "No .txt files found"**
- Verifique se os arquivos estão em `backend/data/rag/processed/`
- Verifique se os arquivos têm extensão `.txt`

**Embeddings não são gerados**
- Verifique se `OPENAI_API_KEY` está configurada no `.env`
- Chunks funcionam sem embeddings (usa filtro por `applies_to`)

**Chunks duplicados**
- O script não remove chunks existentes
- Se reexecutar, pode criar duplicatas
- Para limpar: `db.rag_chunks.delete_many({})` no MongoDB

**Classificação não funciona**
- Verifique se perguntas de onboarding estão populadas (`python scripts/dev/seed_onboarding_questions.py`)
- Verifique se `LLM_PROVIDER` está configurado (use `openai` para melhor classificação)
- Chunks com classificação falha usarão `topic="general"` como fallback

## Documentação da API

### Base URL

`http://localhost:8000` (ou a URL do seu ambiente)

### Autenticação

A maioria dos endpoints requer um token JWT no header:
```
Authorization: Bearer <access_token>
```

### Endpoints Principais

#### Health Check

- `GET /` - Health check básico
- `GET /health` - Health check detalhado

#### Autenticação

- `POST /auth/start` - Iniciar autenticação (envia OTP)
- `POST /auth/verify` - Verificar OTP e obter token
- `GET /auth/me` - Obter perfil do usuário autenticado

#### Perfil do Produtor

- `GET /producers/me` - Obter perfil do produtor
- `PUT /producers/me` - Atualizar perfil do produtor

#### Documentos

- `POST /documents/presign` - Obter URL pré-assinada para upload
- `POST /documents` - Criar registro de documento
- `GET /documents` - Listar documentos do usuário
- `GET /documents/{document_id}` - Obter documento específico

#### Onboarding

- `GET /onboarding/questions` - Listar perguntas de onboarding
- `POST /onboarding/answer` - Responder pergunta de onboarding
- `GET /onboarding/status` - Obter status do onboarding

#### Formalização

- `GET /formalization/status` - Obter status de formalização
- `GET /formalization/tasks` - Listar tarefas de formalização
- `PATCH /formalization/tasks/{task_id}/complete` - Marcar tarefa como completa

#### IA - Guia de Formalização

- `POST /ai/formalization/guide` - Gerar guia personalizado de formalização

### Documentação Interativa

Acesse http://localhost:8000/docs para documentação interativa completa com exemplos de requisições e respostas.

## Contribuindo

### Padrões de Código

#### Princípios Gerais

- **Clareza sobre inteligência**: Código deve ser legível por qualquer membro da equipe
- **Responsabilidade Única**: Funções e classes devem fazer uma coisa bem
- **DRY**: Don't Repeat Yourself - extrair lógica comum
- **Fail Fast**: Validar inputs cedo, fornecer mensagens de erro claras
- **Testabilidade**: Escrever código testável (funções puras quando possível)

#### Backend (Python)

**Estilo:**
- Seguir PEP 8
- Usar type hints para todas as assinaturas de função
- Comprimento máximo de linha: 100 caracteres
- Usar `ruff` para linting e formatação

**Tratamento de Erros:**
- Usar logging adequado (sem `print()`)
- Incluir contexto em mensagens de erro
- Usar logging estruturado com parâmetro `extra`

**Exemplo:**
```python
logger.error(
    "Falha ao processar requisição",
    exc_info=True,
    extra={"user_id": user_id, "operation": "process_request"}
)
```

#### Frontend (TypeScript/React)

**Estilo:**
- Usar TypeScript strict mode
- Preferir componentes funcionais com hooks
- Extrair lógica complexa para custom hooks
- Manter componentes abaixo de 200 linhas (extrair sub-componentes)

**Tratamento de Erros:**
- Usar error boundaries para erros React
- Tratar erros de API graciosamente com mensagens amigáveis
- Logar erros no console em desenvolvimento

### Workflow de Desenvolvimento

1. **Criar uma branch** a partir de `main`
   ```bash
   git checkout -b feature/nome-da-feature
   ```

2. **Fazer mudanças** seguindo padrões de código

3. **Rodar testes** antes de commitar
   ```bash
   # Backend
   cd backend && python -m pytest tests/
   
   # Frontend
   cd frontend && npm run test:unit
   ```

4. **Commit** com mensagens claras
   ```bash
   git commit -m "feat: adiciona validação de arquivo no upload"
   ```

5. **Push** e criar Pull Request

### Formato de Mensagem de Commit

Use conventional commits:

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Mudanças na documentação
- `refactor:` Refatoração de código
- `test:` Adições/mudanças de testes
- `chore:` Tarefas de manutenção

Exemplo: `feat: adiciona validação de tamanho de arquivo no upload de documentos`

### Processo de Pull Request

1. Garantir que todos os testes passem
2. Atualizar documentação se necessário
3. Solicitar revisão de pelo menos um membro da equipe
4. Responder ao feedback da revisão
5. Fazer merge após aprovação

### Diretrizes de Code Review

**Revisores devem verificar:**
- Código segue diretrizes de estilo
- Testes estão incluídos e passam
- Tratamento de erros é apropriado
- Sem problemas de segurança (sem secrets hardcoded, validação adequada)
- Documentação está atualizada se necessário

**Autores devem:**
- Manter PRs focados (uma feature/fix por PR)
- Escrever descrições claras de PR
- Responder ao feedback prontamente

## IDE Setup

### VS Code

Extensões recomendadas:
- Python
- ESLint
- Prettier
- Docker

### PyCharm

Configurar:
- Interpretador Python: `.venv/bin/python`
- Test runner: pytest
- Integração Docker Compose
