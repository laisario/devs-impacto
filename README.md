# PNAE Simplificado

Plataforma que guia agricultores familiares através do processo de formalização para vender ao Programa Nacional de Alimentação Escolar (PNAE).

## Visão Geral

O PNAE Simplificado ajuda pequenos agricultores familiares a navegar pelo complexo processo de formalização necessário para participar do Programa Nacional de Alimentação Escolar. A plataforma fornece guias personalizados passo a passo, alimentados por IA, tornando processos burocráticos acessíveis para agricultores com diferentes níveis de alfabetização digital.

**O que faz**: Guia agricultores através da coleta de documentos, requisitos de formalização e avaliação de elegibilidade para participação no PNAE.

**Para quem**: Agricultores familiares (agricultura familiar) que buscam vender para programas públicos.

**Por que existe**: Simplifica processos burocráticos complexos que impedem muitos agricultores de acessar oportunidades de compras públicas.

## Arquitetura

- **Backend**: FastAPI + MongoDB
- **Frontend**: React + TypeScript + Vite
- **IA**: OpenAI/Deco API com RAG (Retrieval-Augmented Generation)
- **Storage**: S3-compatível (configurável)

### Estrutura do Backend

```
app/
├── core/              # Infraestrutura (config, db, security)
├── modules/           # Módulos de funcionalidades
│   ├── auth/          # Autenticação (OTP + JWT)
│   ├── producers/     # Perfis de produtores
│   ├── documents/     # Upload e validação de documentos
│   ├── onboarding/    # Questionário de onboarding
│   ├── formalization/ # Diagnóstico de elegibilidade
│   ├── ai_formalization/ # Geração de guias com IA (RAG)
│   ├── ai_chat/       # Chatbot
│   └── sales_project/ # Gerador de projeto de venda
└── shared/            # Utilitários compartilhados
```

### Estrutura do Frontend

```
src/
├── app/               # Componente raiz
├── components/        # Componentes compartilhados
├── contexts/          # Contextos React (Auth)
├── domain/            # Modelos de domínio
├── features/          # Módulos de funcionalidades
│   ├── auth/
│   ├── dashboard/
│   └── onboarding/
└── services/          # Serviços de API
```

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
