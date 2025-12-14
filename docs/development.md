# Development Guide

Complete setup and development guide for PNAE Simplificado.

## Prerequisites

- Docker & Docker Compose (recommended)
- OR Python 3.12+ and Node.js 18+ (local development)

## Quick Start

### Using Docker (Recommended)

```bash
# Start all services
docker-compose up

# Access services
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

See [Quick Start Guide](quick-start.md) for detailed setup instructions.

## Local Development

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv ../.venv
source ../.venv/bin/activate  # Linux/Mac
# or: ..\.venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI and other settings

# Run server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Environment Variables

### Backend

Key variables (see `backend/app/core/config.py` for complete list):

- `MONGODB_URI` - MongoDB connection string
- `DATABASE_NAME` - Database name (default: `pnae_dev`)
- `JWT_SECRET` - JWT secret key (required in production)
- `LLM_PROVIDER` - LLM provider: `openai`, `deco`, or `mock`
- `OPENAI_API_KEY` - OpenAI API key (if using OpenAI)

### Frontend

- `VITE_API_BASE_URL` - Backend API URL (default: `http://localhost:8000`)

**Tip**: Use `docker-compose.override.yml` for local overrides.

## Code Quality

### Backend

```bash
cd backend

# Lint
ruff check app/

# Format
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

# Format (if configured)
npm run format
```

## Running Tests

See [Testing Guide](testing.md) for complete testing documentation.

## Project Structure

```
hackathon/
├── backend/          # FastAPI backend
│   ├── app/          # Application code
│   ├── tests/        # Test suite
│   ├── scripts/      # Operational scripts
│   └── data/         # Data files
├── frontend/         # React frontend
│   ├── src/          # Source code
│   └── e2e/          # E2E tests
└── docs/             # Documentation
```

## Common Tasks

### Seed Database

```bash
cd backend

# Seed onboarding questions
python scripts/dev/seed_onboarding_questions.py

# Seed sample data (optional, for development)
python scripts/dev/seeds.py
```

### Create Indexes

```bash
cd backend
python scripts/ops/create_indexes.py
```

### Ingest RAG Documents

```bash
cd backend

# Place cleaned .txt files in data/rag/processed/
# Then run:
python scripts/ops/ingest_rag_documents.py
```

## Debugging

### Backend Logs

```bash
docker-compose logs -f backend
```

### Frontend DevTools

Open browser DevTools (F12) for React debugging.

### Database Access

```bash
# Using Docker
docker-compose exec mongo mongosh

# Or connect with MongoDB client
mongodb://localhost:27017
```

## Hot Reload

Both frontend and backend support hot reload:

- **Backend**: `uvicorn app.main:app --reload` (automatic with Docker)
- **Frontend**: Vite HMR (automatic with `npm run dev`)

## IDE Setup

### VS Code

Recommended extensions:
- Python
- ESLint
- Prettier
- Docker

### PyCharm

Configure:
- Python interpreter: `.venv/bin/python`
- Test runner: pytest
- Docker Compose integration

## Next Steps

- [Testing Guide](testing.md)
- [API Documentation](api/endpoints.md)
- [Deployment Guide](deployment.md)
