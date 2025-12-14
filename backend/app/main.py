"""
PNAE Simplificado Backend MVP

FastAPI application for guiding small producers through PNAE public call process.

This API helps family farmers (agricultura familiar) to:
1. Register as producers (formal/informal/individual)
2. Organize required documents (Envelope 01)
3. Complete onboarding and formalization process

PNAE Reference:
- Programa Nacional de Alimentação Escolar
- Art. 24: Family agriculture purchases via public call (dispensa de licitação)
- Envelope 01: Qualification documents
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import close_db, connect_db
from app.core.errors import register_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
from app.modules.ai_formalization.router import router as ai_formalization_router
from app.modules.auth.router import router as auth_router
from app.modules.documents.router import router as documents_router
from app.modules.formalization.router import router as formalization_router
from app.modules.onboarding.router import router as onboarding_router
from app.modules.producers.router import router as producers_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Connect to MongoDB
    - Shutdown: Close MongoDB connection
    """
    # Startup
    await connect_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title="PNAE Simplificado API",
        description=(
            "API para guiar pequenos produtores (agricultura familiar) "
            "no processo de formalização para vender para o PNAE."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Register routers
    app.include_router(auth_router)
    app.include_router(producers_router)
    app.include_router(documents_router)
    app.include_router(onboarding_router)
    app.include_router(formalization_router)
    app.include_router(ai_formalization_router)

    @app.get("/", tags=["health"])
    async def root() -> dict[str, str]:
        """Health check endpoint."""
        return {
            "status": "ok",
            "service": "PNAE Simplificado API",
            "version": "0.1.0",
        }

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Detailed health check."""
        return {
            "status": "healthy",
            "database": settings.database_name,
            "storage_provider": settings.storage_provider,
        }

    return app


# Create application instance
app = create_app()

