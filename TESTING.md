# Guia de Testes

Este documento descreve como executar os diferentes tipos de testes do projeto.

## Visão Geral

O projeto possui três tipos de testes:

1. **Testes Unitários (Backend)**: Testes isolados de funções e módulos
2. **Testes de Integração (Backend)**: Testes de fluxos completos entre múltiplos endpoints
3. **Testes E2E (Frontend)**: Testes end-to-end usando Playwright

## Backend - Testes Unitários

Localização: `backend/tests/` (exceto `tests/integration/`)

```bash
cd backend
source ../.venv/bin/activate
python -m pytest tests/ -m "not integration"
```

## Backend - Testes de Integração

Localização: `backend/tests/integration/`

Testam fluxos completos:
- Autenticação completa (start → verify → me)
- Criação e atualização de perfis
- Fluxo de onboarding
- Diagnóstico de formalização
- Upload de documentos

```bash
cd backend
source ../.venv/bin/activate
python -m pytest tests/integration/ -v
```

**Problemas comuns:**
- `ModuleNotFoundError: No module named 'motor'` → Ative o ambiente virtual
- Use `python -m pytest` em vez de `pytest` diretamente
- Veja `backend/README_TESTS.md` para mais soluções

## Frontend - Testes Unitários

Localização: `frontend/src/services/api/__tests__/`

Testam os serviços de API:
- Auth service
- Onboarding service
- Documents service

```bash
cd frontend
npm run test:unit
```

## Frontend - Testes E2E

Localização: `frontend/e2e/`

Testam fluxos completos do usuário:
- Autenticação
- Onboarding
- Dashboard
- Upload de documentos
- Geração de guias IA

**Pré-requisitos:**
- Backend rodando em `http://localhost:8000`
- Frontend rodando em `http://localhost:5173`
- MongoDB disponível

```bash
# Terminal 1: Iniciar serviços
docker-compose up

# Terminal 2: Rodar testes E2E
cd frontend
npm run test:e2e
```

## Executando Todos os Testes

### Backend

```bash
cd backend
source ../.venv/bin/activate
python -m pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm run test:unit
# E2E requer serviços rodando separadamente
```

## Cobertura de Código

### Backend

```bash
cd backend
source ../.venv/bin/activate
python -m pytest tests/ --cov=app --cov-report=html
# Abra htmlcov/index.html no navegador
```

### Frontend

```bash
cd frontend
npm run test:unit -- --coverage
```

## Troubleshooting

### Backend: ModuleNotFoundError

**Solução:**
```bash
# Ative o ambiente virtual
source .venv/bin/activate  # ou venv/bin/activate

# Use python -m pytest
python -m pytest tests/
```

### Frontend: E2E tests não encontram serviços

**Solução:**
1. Verifique se os serviços estão rodando:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:5173
   ```

2. Configure a URL base se necessário:
   ```bash
   E2E_BASE_URL=http://localhost:5173 npm run test:e2e
   ```

### Testes E2E muito lentos

Os testes E2E podem ser lentos porque:
- Iniciam um servidor web real
- Abrem um navegador real
- Fazem requisições HTTP reais

Para desenvolvimento, use `test:e2e:headed` para ver o que está acontecendo.

## CI/CD

Para CI/CD, use:

```bash
# Backend
cd backend && python -m pytest tests/ --cov=app --cov-report=xml

# Frontend
cd frontend && npm run test:unit -- --coverage
cd frontend && npm run test:e2e  # Requer serviços em Docker
```
