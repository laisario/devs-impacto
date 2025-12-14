# PNAE Simplificado

Plataforma que guia agricultores familiares através do processo de formalização para vender ao Programa Nacional de Alimentação Escolar (PNAE).

## Visão Geral

O PNAE Simplificado ajuda pequenos agricultores familiares a navegar pelo complexo processo de formalização necessário para participar do Programa Nacional de Alimentação Escolar. A plataforma fornece guias personalizados passo a passo, alimentados por IA, tornando processos burocráticos acessíveis para agricultores com diferentes níveis de alfabetização digital.

**O que faz**: Guia agricultores através da coleta de documentos, requisitos de formalização e avaliação de elegibilidade para participação no PNAE.

**Para quem**: Agricultores familiares (agricultura familiar) que buscam vender para programas públicos.

**Por que existe**: Simplifica processos burocráticos complexos que impedem muitos agricultores de acessar oportunidades de compras públicas.

## Arquitetura

### Stack Tecnológico

- **Backend**: FastAPI + MongoDB
- **Frontend**: React + TypeScript + Vite
- **IA**: OpenAI/Deco API com RAG (Retrieval-Augmented Generation)
- **Storage**: S3-compatível (configurável: mock, S3, GCS)
- **Autenticação**: JWT + OTP via SMS (mock em desenvolvimento)

### Decisões de Arquitetura

#### Backend

**FastAPI** foi escolhido por:
- Performance assíncrona nativa (async/await)
- Validação automática com Pydantic
- Documentação automática (Swagger/ReDoc)
- Type hints nativos do Python
- Facilidade de desenvolvimento e manutenção

**MongoDB** foi escolhido por:
- Flexibilidade de schema (perfis de produtores variam)
- Suporte nativo a documentos aninhados
- Facilidade de escalar horizontalmente
- Suporte a arrays e objetos complexos (respostas de onboarding, tarefas)

**Padrões de Design**:
- **Service Layer**: Lógica de negócio isolada em classes Service
- **Repository Pattern**: Acesso a dados abstraído em repositórios (ex: `FormalizationRepository`)
- **Dependency Injection**: FastAPI `Depends()` para injeção de dependências
- **Pure Functions**: Funções de negócio puras e testáveis (ex: `calculate_eligibility`)
- **Schema Validation**: Pydantic para validação e serialização

#### Frontend

**React + TypeScript** foi escolhido por:
- Type safety em tempo de compilação
- Componentização e reutilização
- Ecossistema maduro e ferramentas de desenvolvimento

**Vite** foi escolhido por:
- Build rápido em desenvolvimento
- Hot Module Replacement (HMR) eficiente
- Otimizações automáticas de produção

**Padrões de Design**:
- **Feature-Based Structure**: Organização por funcionalidades
- **Custom Hooks**: Lógica reutilizável extraída (ex: `useFileUpload`)
- **Context API**: Estado global de autenticação
- **Component Composition**: Componentes pequenos e focados

#### IA e RAG

**RAG (Retrieval-Augmented Generation)** foi implementado para:
- Fornecer informações precisas baseadas em documentos oficiais
- Reduzir alucinações do modelo
- Permitir atualização de conhecimento sem retreinar o modelo

**Fluxo RAG**:
1. Documentos oficiais são processados e divididos em chunks
2. Chunks são classificados automaticamente por LLM (topic, applies_to)
3. Embeddings são gerados e armazenados no MongoDB
4. Na geração de guia, busca semântica encontra chunks relevantes
5. Chunks são injetados no prompt do LLM como contexto

### Estrutura do Backend

```
app/
├── core/              # Infraestrutura
│   ├── config.py      # Configurações (Pydantic Settings)
│   ├── db.py          # Conexão MongoDB
│   ├── security.py    # JWT + OTP
│   └── errors.py      # Exception handlers
│
├── modules/           # Módulos de funcionalidades
│   ├── auth/          # Autenticação (OTP + JWT)
│   │   ├── service.py # Lógica de autenticação
│   │   └── router.py  # Endpoints REST
│   │
│   ├── producers/     # Perfis de produtores
│   │   ├── service.py # Lógica de negócio
│   │   └── router.py  # Endpoints REST
│   │
│   ├── documents/     # Upload e validação
│   │   ├── service.py # Lógica de storage
│   │   └── router.py  # Endpoints REST
│   │
│   ├── onboarding/    # Questionário guiado
│   │   ├── service.py # Lógica de onboarding
│   │   └── router.py  # Endpoints REST
│   │
│   ├── formalization/ # Diagnóstico de elegibilidade
│   │   ├── service.py # Lógica de diagnóstico
│   │   ├── repo.py    # Repository pattern
│   │   ├── diagnosis.py # Funções puras
│   │   ├── rules.py   # Regras de negócio
│   │   └── router.py  # Endpoints REST
│   │
│   ├── ai_formalization/ # Geração de guias com IA
│   │   ├── service.py # Orquestração RAG + LLM
│   │   ├── rag.py     # RAG service
│   │   ├── prompts.py # Templates de prompt
│   │   └── router.py  # Endpoints REST
│   │
│   ├── ai_chat/       # Chatbot
│   └── sales_project/ # Gerador de projeto de venda
│
└── shared/            # Utilitários compartilhados
    ├── pagination.py
    └── utils.py
```

### Estrutura do Frontend

```
src/
├── app/               # Componente raiz
├── components/        # Componentes compartilhados
├── contexts/          # Contextos React (AuthContext)
├── domain/            # Modelos de domínio (TypeScript types)
├── features/          # Módulos de funcionalidades
│   ├── auth/
│   │   ├── components/
│   │   └── hooks/
│   ├── dashboard/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── utils/
│   └── onboarding/
│       └── components/
└── services/          # Serviços de API
    └── api/
        ├── client.ts  # Cliente HTTP
        ├── config.ts  # Endpoints
        └── *.ts       # Serviços por módulo
```

## Fluxos Principais

### 1. Autenticação

```
Usuário → POST /auth/start (telefone)
       → OTP enviado (mock: sempre 123456)
       → POST /auth/verify (telefone + OTP)
       → JWT token retornado
       → Token usado em requisições autenticadas
```

### 2. Onboarding e Formalização

```
Usuário → Responde perguntas de onboarding (incremental)
       → Sistema calcula elegibilidade automaticamente
       → Tarefas de formalização são geradas baseadas em regras
       → Score é calculado baseado em progresso das tarefas
       → Guias personalizados podem ser gerados por IA
```

**Sistema de Tarefas**:
- Tarefas são definidas em CSV (`backend/data/formalization_tasks.csv`)
- Regras determinam quais tarefas são necessárias (`rules.py`)
- Tarefas são sincronizadas com o perfil do produtor
- Status: `pending`, `done`, `skipped`
- Tarefas bloqueantes impedem elegibilidade completa

### 3. Geração de Guia com IA

```
Usuário → Solicita guia para um requisito (ex: "has_cpf")
       → Sistema busca chunks RAG relevantes
       → Constrói prompt com contexto do usuário
       → LLM gera guia personalizado
       → Resposta é validada e formatada
       → Guia é exibido com passos, locais, tempo estimado
```

### 4. Upload de Documentos

```
Usuário → Solicita URL pré-assinada
       → Upload direto para storage (S3/mock)
       → Documento é registrado no banco
       → (Opcional) Validação por IA
       → Documento aparece no dashboard
```

## Estrutura de Dados

### Relacionamentos Principais

```
users (auth)
  └── user_id (ObjectId)
      ├── producer_profiles
      │   ├── producer_type (individual/formal/informal)
      │   ├── has_cpf, has_dap_caf, has_cnpj, etc. (flags)
      │   └── onboarding_status
      │
      ├── onboarding_answers
      │   ├── question_id
      │   └── answer
      │
      ├── formalization_status (cache)
      │   ├── is_eligible
      │   ├── score (baseado em progresso)
      │   └── requirements_met/missing
      │
      ├── formalization_tasks (novo sistema)
      │   ├── task_code (referência ao catálogo)
      │   ├── status (pending/done/skipped)
      │   └── blocking
      │
      └── documents
          ├── doc_type
          └── file_url
```

### Coleções MongoDB

- `users`: Autenticação (telefone, OTP)
- `producer_profiles`: Perfil do produtor (tipo, flags, dados)
- `onboarding_questions`: Catálogo de perguntas (configurável)
- `onboarding_answers`: Respostas incrementais do usuário
- `formalization_status`: Cache do diagnóstico (invalidado quando necessário)
- `formalization_tasks`: Tarefas do usuário (sincronizadas com perfil)
- `documents`: Documentos enviados pelo usuário
- `rag_chunks`: Chunks de documentos para RAG (com embeddings)

## Princípios de Design

### Backend

1. **Separation of Concerns**: Router → Service → Repository
2. **Pure Functions**: Lógica de negócio testável sem dependências
3. **Type Safety**: Type hints em todas as funções
4. **Error Handling**: Logging estruturado com contexto
5. **Caching**: Status de formalização é cacheado (invalidado quando necessário)
6. **Idempotência**: Operações podem ser repetidas sem efeitos colaterais

### Frontend

1. **Componentização**: Componentes pequenos e focados (< 200 linhas)
2. **Custom Hooks**: Lógica reutilizável extraída
3. **Type Safety**: TypeScript strict mode
4. **Error Boundaries**: Tratamento gracioso de erros
5. **Optimistic UI**: Atualizações otimistas com rollback em caso de erro

## Quick Start

```bash
# Iniciar tudo com Docker
docker-compose up
```

**Acesso:**
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

Veja [QUICK_START.md](QUICK_START.md) para instruções detalhadas de configuração e [DESENVOLVIMENTO.md](DESENVOLVIMENTO.md) para guia completo de desenvolvimento.

## Estrutura do Projeto

```
hackathon/
├── backend/          # Aplicação FastAPI
│   ├── app/          # Código da aplicação
│   ├── tests/        # Testes
│   ├── scripts/      # Scripts operacionais
│   │   ├── dev/      # Scripts de desenvolvimento
│   │   └── ops/      # Scripts operacionais
│   └── data/         # Arquivos de dados
│       ├── formalization_tasks.csv  # Catálogo de tarefas
│       ├── onboarding_questions.csv # Catálogo de perguntas
│       └── rag/      # Documentos RAG
│           ├── raw/      # Documentos originais
│           ├── processed/ # Textos limpos (.txt)
│           └── metadata/  # Metadados
├── frontend/         # Aplicação React
│   ├── src/          # Código fonte
│   └── e2e/          # Testes E2E
└── docker-compose.yml
```

## Desenvolvimento

Veja [DESENVOLVIMENTO.md](DESENVOLVIMENTO.md) para guia completo incluindo setup local, testes, qualidade de código, ingestão de documentos RAG, documentação da API e contribuição.

## Qualidade de Código

**Backend:**
```bash
cd backend
ruff check app/ && ruff format app/
```

**Frontend:**
```bash
cd frontend
npm run lint && npm run typecheck
```

## API

Documentação interativa: http://localhost:8000/docs

## Licença

MIT
