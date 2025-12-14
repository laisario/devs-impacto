#!/usr/bin/env python3
"""
Script to ingest text documents into RAG system.

This script reads cleaned text files from data/rag_text/ directory,
chunks them semantically, classifies them automatically using LLM,
generates embeddings, and stores in MongoDB.

Usage:
    python scripts/ingest_rag_documents.py

Requires:
    - MongoDB to be running
    - Cleaned text files in data/rag_text/ directory (.txt files)
    - Onboarding questions seeded (python seeds_onboarding.py)
    - LLM configured (LLM_PROVIDER=openai or mock)
    - OPENAI_API_KEY environment variable (for embeddings, optional)
"""

import asyncio
import os
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.modules.ai_formalization.classification import classify_chunk
from app.modules.ai_formalization.llm_client import create_llm_client
from app.modules.ai_formalization.rag import RAGChunk, RAGService, generate_embedding
from app.modules.onboarding.service import OnboardingService


async def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Simple text chunking by sentences/paragraphs.

    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks in characters

    Returns:
        List of text chunks
    """
    # Simple splitting by paragraphs first
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


async def read_text_file(text_path: str) -> str:
    """
    Read text from a cleaned text file.

    Args:
        text_path: Path to text file

    Returns:
        Text content
    """
    try:
        with open(text_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {text_path}: {e}")
        return ""


async def ingest_document(
    text_path: str,
    rag_service: RAGService,
    onboarding_service: OnboardingService,
    llm_client,
    auto_classify: bool = True,
    manual_topic: str | None = None,
    manual_applies_to: list[str] | None = None,
) -> int:
    """
    Ingest a single cleaned text document into RAG.

    Args:
        text_path: Path to cleaned text file
        rag_service: RAGService instance
        onboarding_service: OnboardingService to get questions
        llm_client: LLM client for auto-classification
        auto_classify: If True, use LLM to classify chunks automatically
        manual_topic: Manual topic (if auto_classify=False)
        manual_applies_to: Manual applies_to (if auto_classify=False)

    Returns:
        Number of chunks created
    """
    print(f"Processing: {text_path}")

    # Read cleaned text file
    text = await read_text_file(text_path)
    if not text:
        print(f"  ⚠ Could not read text from {text_path}")
        return 0
    
    if len(text.strip()) < 50:
        print(f"  ⚠ Text file too short, skipping")
        return 0

    # Chunk text
    text_chunks = await chunk_text(text)
    print(f"  Extracted {len(text_chunks)} chunks")

    # Get onboarding questions for classification
    questions = []
    if auto_classify:
        questions = await onboarding_service._get_questions_list()
        print(f"  Using {len(questions)} onboarding questions for classification")

    # Create RAG chunks
    chunks = []
    filename = Path(text_path).name

    for i, chunk_text_content in enumerate(text_chunks, 1):
        # Classify chunk (automatic or manual)
        if auto_classify:
            try:
                classification = await classify_chunk(chunk_text_content, questions, llm_client)
                topic = classification["topic"]
                applies_to_list = classification["applies_to"]
                confidence = classification.get("confidence", "medium")
                print(f"  Chunk {i}/{len(text_chunks)}: topic={topic}, applies_to={applies_to_list}, confidence={confidence}")
            except Exception as e:
                print(f"  ⚠ Classification failed for chunk {i}: {e}, using fallback")
                topic = manual_topic or "general"
                applies_to_list = manual_applies_to or []
        else:
            topic = manual_topic or "general"
            applies_to_list = manual_applies_to or []

        # Generate embedding (optional - can be None)
        embedding = None
        try:
            embedding = await generate_embedding(chunk_text_content)
        except Exception as e:
            print(f"  ⚠ Could not generate embedding for chunk {i}: {e}")

        # Ensure applies_to is not empty (use general as fallback)
        final_applies_to = applies_to_list if applies_to_list else ["general"]
        
        chunk = RAGChunk(
            content=chunk_text_content,
            topic=topic,
            applies_to=final_applies_to,
            source=filename,
            page=None,  # Could parse page numbers if needed
            embedding=embedding,
        )
        chunks.append(chunk)

    # Save to database
    await rag_service.add_chunks(chunks)
    print(f"  ✓ Ingested {len(chunks)} chunks")

    return len(chunks)


async def main() -> None:
    """Main ingestion function."""
    import sys

    # Parse arguments
    auto_classify = "--manual" not in sys.argv
    if auto_classify:
        print("🤖 Modo: Classificação automática com LLM")
        print("   (use --manual para classificação manual)\n")
    else:
        print("📝 Modo: Classificação manual\n")

    print(f"Connecting to MongoDB: {settings.mongodb_uri}")
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)  # type: ignore[type-arg]
    db = client[settings.database_name]

    print(f"Ingesting RAG documents for database: {settings.database_name}\n")

    rag_service = RAGService(db)
    onboarding_service = OnboardingService(db)
    llm_client = create_llm_client() if auto_classify else None

    # Text documents directory (cleaned/preprocessed files)
    texts_dir = Path("data/rag_text")
    if not texts_dir.exists():
        print(f"⚠ Directory {texts_dir} does not exist. Creating it...")
        texts_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Please add cleaned .txt files to {texts_dir} and run again.")
        client.close()
        return

    # Find all text files
    text_files = list(texts_dir.glob("*.txt"))
    if not text_files:
        print(f"⚠ No .txt files found in {texts_dir}")
        print(f"  Please add cleaned text files and run again.")
        client.close()
        return

    print(f"Found {len(text_files)} text file(s)\n")

    total_chunks = 0
    for text_file in text_files:
        filename = text_file.name
        print(f"\n📄 Processing: {filename}")

        try:
            chunks_count = await ingest_document(
                str(text_file),
                rag_service,
                onboarding_service,
                llm_client,
                auto_classify=auto_classify,
            )
            total_chunks += chunks_count
        except Exception as e:
            print(f"  ✗ Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 50)
    print(f"✅ Ingestion completed! Total chunks: {total_chunks}")
    print("=" * 50)
    print("\nChunks estão prontos para uso pelo AI agent.")
    print("Para testar, gere um guia com POST /ai/formalization/guide")
    print(f"\nArquivos processados: {len(text_files)}")
    print(f"Chunks médios por arquivo: {total_chunks / len(text_files) if text_files else 0:.1f}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
