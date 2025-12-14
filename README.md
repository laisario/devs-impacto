# PNAE Simplificado - Full Stack Application

Aplicação completa para guiar pequenos produtores (agricultura familiar) no processo de formalização para vender para o PNAE.

## Estrutura do Projeto

```
hackathon/
├── backend/          # FastAPI backend
├── frontend/         # React + TypeScript frontend
├── docker-compose.yml # Docker Compose para desenvolvimento
└── README.md
```

## Quick Start com Docker

### Desenvolvimento

```bash
# Iniciar todos os serviços
docker-compose up

# Ou em background
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

Serviços disponíveis:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MongoDB: localhost:27017

### Produção

```bash
# Iniciar com perfil de produção
docker-compose --profile production up
```

## Desenvolvimento Local (sem Docker)

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testes

### Backend

```bash
cd backend

# IMPORTANTE: Ative o ambiente virtual primeiro!
source ../.venv/bin/activate

# Todos os testes
python -m pytest tests/

# Apenas testes unitários
python -m pytest tests/ -m "not integration"

# Apenas testes de integração
python -m pytest tests/integration/ -v

# Com cobertura
python -m pytest tests/ --cov=app --cov-report=html

# Ou usando Makefile (ativa venv automaticamente)
make test
make test-unit
make test-integration
make coverage

# Ou usando o script helper
./run_tests.sh tests/integration/
```

**Nota:** Se encontrar erro `ModuleNotFoundError: No module named 'motor'`, certifique-se de que o ambiente virtual está ativado. Veja `backend/README_TESTS.md` para mais detalhes.

### Frontend

```bash
cd frontend

# Testes unitários (Vitest)
npm run test:unit

# Testes unitários em modo watch
npm run test:unit:watch

# Testes unitários com UI
npm run test:unit:ui

# Testes E2E (Playwright) - requer serviços rodando
npm run test:e2e

# Testes E2E com UI interativa
npm run test:e2e:ui

# Testes E2E com browser visível
npm run test:e2e:headed

# Testes E2E em modo debug
npm run test:e2e:debug
```

## Ambiente de Testes

### Testes E2E

Os testes E2E requerem que os serviços estejam rodando. Você tem duas opções:

**Opção 1: Usar Docker Compose (recomendado)**

```bash
# Terminal 1: Iniciar serviços
docker-compose up

# Terminal 2: Rodar testes E2E
cd frontend
npm run test:e2e
```

**Opção 2: Ambiente de testes isolado**

```bash
# Iniciar ambiente de testes
docker-compose -f docker-compose.test.yml up

# Em outro terminal, rodar testes
cd frontend
E2E_BASE_URL=http://localhost:8001 npm run test:e2e
```

**Opção 3: Serviços locais**

```bash
# Terminal 1: Backend
cd backend && source ../.venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: MongoDB (se não usar Docker)
# mongod --dbpath ./data/db

# Terminal 4: Testes E2E
cd frontend && npm run test:e2e
```

## Estrutura de Testes

### Backend
- `tests/` - Testes unitários
- `tests/integration/` - Testes de integração (fluxos completos)

### Frontend
- `src/services/api/__tests__/` - Testes unitários dos serviços API
- `e2e/` - Testes end-to-end com Playwright

## Variáveis de Ambiente

### Backend
Criar `backend/.env` (opcional, pode usar docker-compose.override.yml):
```
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=pnae_dev
JWT_SECRET=your-secret-key
OPENAI_API_KEY=sk-sua-chave-aqui  # Para funcionalidades GenAI
LLM_PROVIDER=openai               # "openai" ou "mock"
```

### Frontend
Criar `frontend/.env` (opcional):
```
VITE_API_BASE_URL=http://localhost:8000
```

**💡 Dica:** A forma mais fácil é editar `docker-compose.override.yml` e adicionar as variáveis lá. Veja `QUICK_START.md` para instruções detalhadas.

## Documentação da API

A documentação interativa está disponível em:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Documentação completa dos endpoints: `backend/API_ENDPOINTS.md`

## Comandos Úteis

### Docker
```bash
# Rebuild containers
docker-compose build

# Ver logs de um serviço específico
docker-compose logs -f backend

# Executar comando em container
docker-compose exec backend pytest tests/
docker-compose exec frontend npm run test:unit
```

### Desenvolvimento
```bash
# Backend: Lint
cd backend && ruff check app/

# Backend: Format
cd backend && ruff format app/

# Frontend: Lint
cd frontend && npm run lint

# Frontend: Type check
cd frontend && npm run typecheck
```
