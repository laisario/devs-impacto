# System Architecture

High-level architecture overview of PNAE Simplificado.

## Overview

PNAE Simplificado is a full-stack application helping family farmers formalize to sell to Brazil's National School Feeding Program (PNAE).

## Technology Stack

- **Backend**: FastAPI (Python 3.12+)
- **Frontend**: React 18 + TypeScript + Vite
- **Database**: MongoDB 7.0+
- **AI**: OpenAI GPT-4o / Deco API with RAG
- **Storage**: S3-compatible (configurable: S3, Local, Mock)

## Architecture Diagram

```
┌─────────────┐
│   Frontend  │  React + TypeScript
│  (Port 5173)│
└──────┬──────┘
       │ HTTP/REST
       │
┌──────▼──────┐
│   Backend   │  FastAPI
│  (Port 8000)│
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌─▼────┐
│Mongo│ │  S3  │
│ DB  │ │Storage│
└─────┘ └──────┘
```

## Backend Architecture

### Module Structure

```
app/
├── core/              # Infrastructure
│   ├── config.py      # Configuration
│   ├── db.py          # Database connection
│   ├── security.py    # JWT authentication
│   └── errors.py      # Exception handlers
│
├── modules/           # Feature modules
│   ├── auth/          # Authentication (OTP + JWT)
│   ├── producers/     # Producer profiles
│   ├── documents/     # Document upload & validation
│   ├── onboarding/    # Onboarding questionnaire
│   ├── formalization/ # Eligibility diagnosis
│   ├── ai_formalization/ # AI guide generation (RAG)
│   ├── ai_chat/       # Chatbot
│   └── sales_project/ # Sales project generator
│
└── shared/            # Shared utilities
    ├── pagination.py
    └── utils.py
```

### Key Design Patterns

- **Service Layer**: Business logic in service classes
- **Repository Pattern**: Database access through service layer
- **Dependency Injection**: FastAPI Depends() for services
- **Pure Functions**: Business logic functions are testable (e.g., `calculate_eligibility`)

## Frontend Architecture

### Feature-Based Structure

```
src/
├── app/               # App root component
├── components/        # Shared components
├── contexts/          # React contexts (Auth)
├── domain/            # Domain models
├── features/          # Feature modules
│   ├── auth/
│   ├── dashboard/
│   ├── onboarding/
│   └── ...
└── services/          # API services
    └── api/
```

### State Management

- **React Hooks**: useState, useEffect, useMemo
- **Context API**: AuthContext for authentication
- **Custom Hooks**: Reusable logic (e.g., `useFileUpload`)

## Data Flow

### User Registration Flow

```
User → Frontend → POST /auth/start
                → POST /auth/verify
                → JWT Token
                → Authenticated Requests
```

### Onboarding Flow

```
User → Answer Questions → POST /onboarding/answer
                        → Calculate Eligibility
                        → Generate Tasks
                        → Display Checklist
```

### AI Guide Generation

```
User → Request Guide → RAG Search
                    → Build Prompt
                    → LLM Generation
                    → Validate Response
                    → Display Guide
```

## AI Integration

### RAG System

1. **Document Ingestion**: Text files → Chunks → Embeddings → MongoDB
2. **Query**: User context → Semantic search → Relevant chunks
3. **Prompt Building**: Context + Chunks → LLM prompt
4. **Generation**: LLM → JSON response → Validation → Display

### LLM Providers

- **OpenAI**: GPT-4o-mini (text), GPT-4o (vision)
- **Deco API**: Alternative without API key
- **Mock**: Development/testing

## Security

- **Authentication**: JWT tokens
- **Authorization**: User-scoped data access
- **Input Validation**: Pydantic models
- **Error Handling**: Structured error responses

## Scalability Considerations

- **Stateless Backend**: Horizontal scaling possible
- **Database Indexes**: Optimized queries
- **Caching**: Formalization status cached
- **Async Operations**: Background tasks for AI processing

## Deployment

See [Deployment Guide](deployment.md) for production deployment details.
