# Testing Guide

Complete guide to testing the PNAE Simplificado platform.

## Overview

The project has three types of tests:

1. **Unit Tests (Backend)**: Isolated function and module tests
2. **Integration Tests (Backend)**: Full flow tests across multiple endpoints
3. **E2E Tests (Frontend)**: End-to-end tests using Playwright

## Backend Testing

### Unit Tests

**Location**: `backend/tests/` (excluding `tests/integration/`)

**Run:**
```bash
cd backend
source ../.venv/bin/activate
python -m pytest tests/ -m "not integration"
```

### Integration Tests

**Location**: `backend/tests/integration/`

Tests complete flows:
- Authentication (start → verify → me)
- Profile creation and updates
- Onboarding flow
- Formalization diagnosis
- Document upload

**Run:**
```bash
cd backend
source ../.venv/bin/activate
python -m pytest tests/integration/ -v
```

**Common Issues:**

- `ModuleNotFoundError: No module named 'motor'` → Activate virtual environment
- Use `python -m pytest` instead of `pytest` directly
- See [Testing Troubleshooting Guide](testing-troubleshooting.md) for detailed solutions

### AI Formalization Testing

**Location**: `backend/tests/test_ai_formalization.py`

**Run:**
```bash
cd backend
python -m pytest tests/test_ai_formalization.py -v
```

See [AI Testing Guide](testing-ai.md) for detailed AI module testing.

### Coverage

```bash
cd backend
python -m pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## Frontend Testing

### Unit Tests

**Location**: `frontend/src/services/api/__tests__/`

Tests API services:
- Auth service
- Onboarding service
- Documents service

**Run:**
```bash
cd frontend
npm run test:unit
```

**Watch mode:**
```bash
npm run test:unit:watch
```

### E2E Tests

**Location**: `frontend/e2e/`

Tests complete user flows:
- Authentication
- Onboarding
- Dashboard
- Document upload
- AI guide generation

**Prerequisites:**
- Backend running at `http://localhost:8000`
- Frontend running at `http://localhost:5173`
- MongoDB available

**Run:**
```bash
# Terminal 1: Start services
docker-compose up

# Terminal 2: Run E2E tests
cd frontend
npm run test:e2e
```

**Options:**
- `npm run test:e2e:ui` - Interactive Playwright UI
- `npm run test:e2e:headed` - Visible browser
- `npm run test:e2e:debug` - Debug mode

## Test Environment

### Using Docker Compose (Recommended)

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up

# Run tests
cd frontend
E2E_BASE_URL=http://localhost:8001 npm run test:e2e
```

### Local Services

```bash
# Terminal 1: Backend
cd backend && source ../.venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: E2E Tests
cd frontend && npm run test:e2e
```

## Troubleshooting

See [Testing Troubleshooting](testing-troubleshooting.md) for common issues and solutions.

## CI/CD

For CI/CD pipelines:

```bash
# Backend
cd backend && python -m pytest tests/ --cov=app --cov-report=xml

# Frontend
cd frontend && npm run test:unit -- --coverage
cd frontend && npm run test:e2e  # Requires services in Docker
```
