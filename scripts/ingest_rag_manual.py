#!/usr/bin/env python3
"""
Script para ingestão manual de chunks RAG.

Útil para adicionar chunks específicos sem precisar de PDFs.
Pode ser usado para adicionar conteúdo manualmente ou de outras fontes.

Usage:
    python scripts/ingest_rag_manual.py
"""

import asyncio
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.modules.ai_formalization.rag import RAGChunk, RAGService
from app.shared.utils import utc_now


# Chunks manuais de exemplo
# Você pode editar isso para adicionar seu próprio conteúdo
MANUAL_CHUNKS = [
    {
        "content": (
            "Para obter seu CPF, você pode ir até uma agência dos Correios "
            "ou uma unidade da Receita Federal. Leve um documento de identidade com foto "
            "(RG, CNH ou certidão de nascimento) e um comprovante de endereço recente. "
            "O processo é gratuito e você recebe o CPF na hora."
        ),
        "topic": "cpf",
        "applies_to": ["has_cpf"],
        "source": "manual_ingestion",
    },
    {
        "content": (
            "A DAP (Declaração de Aptidão ao Pronaf) é obtida na EMATER ou "
            "na Secretaria de Agricultura do seu município. Você precisa apresentar "
            "documentos como CPF, comprovante de propriedade ou uso da terra, e "
            "declaração de que pratica agricultura familiar. A DAP é gratuita e válida por 3 anos."
        ),
        "topic": "dap_caf",
        "applies_to": ["has_dap_caf"],
        "source": "manual_ingestion",
    },
    {
        "content": (
            "Para abrir uma conta bancária, você precisa ter CPF e RG. "
            "Vá até uma agência bancária e leve também um comprovante de endereço. "
            "Muitos bancos oferecem contas gratuitas para produtores rurais. "
            "Alguns bancos têm linhas específicas para agricultura familiar."
        ),
        "topic": "bank_account",
        "applies_to": ["has_bank_account"],
        "source": "manual_ingestion",
    },
    {
        "content": (
            "Para registrar CNPJ de uma cooperativa ou associação, você precisa "
            "ir até a Receita Federal com o estatuto social aprovado, lista de membros, "
            "e documentos dos representantes. O processo pode ser feito online pelo site "
            "da Receita Federal ou presencialmente. É gratuito para cooperativas."
        ),
        "topic": "cnpj",
        "applies_to": ["has_cnpj"],
        "source": "manual_ingestion",
    },
]


async def ingest_manual_chunks() -> None:
    """Ingest manual chunks into RAG system."""
    print(f"Connecting to MongoDB: {settings.mongodb_uri}")
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)  # type: ignore[type-arg]
    db = client[settings.database_name]

    print(f"Ingesting manual RAG chunks: {settings.database_name}\n")

    rag_service = RAGService(db)

    # Convert dicts to RAGChunk objects
    chunks = []
    for chunk_data in MANUAL_CHUNKS:
        chunk = RAGChunk(
            content=chunk_data["content"],
            topic=chunk_data["topic"],
            applies_to=chunk_data["applies_to"],
            source=chunk_data["source"],
            page=None,
            embedding=None,  # Embeddings podem ser gerados depois se necessário
            created_at=utc_now(),
        )
        chunks.append(chunk)
        print(f"  Prepared chunk: {chunk_data['topic']} -> {', '.join(chunk_data['applies_to'])}")

    # Add chunks to database
    await rag_service.add_chunks(chunks)
    print(f"\n✓ Ingested {len(chunks)} manual chunks")

    print("\n" + "=" * 50)
    print("Manual ingestion completed!")
    print("=" * 50)
    print("\nChunks estão prontos para uso pelo AI agent.")
    print("Para testar, gere um guia com POST /ai/formalization/guide")

    client.close()


if __name__ == "__main__":
    asyncio.run(ingest_manual_chunks())
