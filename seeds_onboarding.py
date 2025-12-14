#!/usr/bin/env python3
"""
Seed script for onboarding questions.
Can be run separately or integrated into main seeds.py.

Usage:
    python seeds_onboarding.py

Requires MongoDB to be running.
"""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.modules.onboarding.schemas import OnboardingQuestion, QuestionType


# Perguntas de onboarding padrão
# Linguagem simples pensada para baixa alfabetização
DEFAULT_ONBOARDING_QUESTIONS: list[OnboardingQuestion] = [
    OnboardingQuestion(
        question_id="has_cpf",
        question_text="Você tem CPF cadastrado?",
        question_type=QuestionType.BOOLEAN,
        order=1,
        required=True,
        requirement_id="has_cpf",
    ),
    OnboardingQuestion(
        question_id="has_dap_caf",
        question_text="Você tem DAP ou CAF?",
        question_type=QuestionType.BOOLEAN,
        order=2,
        required=True,
        requirement_id="has_dap_caf",
    ),
    OnboardingQuestion(
        question_id="has_cnpj",
        question_text="Você tem CNPJ? (se for cooperativa ou associação)",
        question_type=QuestionType.BOOLEAN,
        order=3,
        required=False,
        requirement_id="has_cnpj",
    ),
    OnboardingQuestion(
        question_id="producer_type_preference",
        question_text="Você quer se cadastrar como:",
        question_type=QuestionType.CHOICE,
        options=["Individual", "Grupo informal", "Cooperativa/Associação"],
        order=4,
        required=True,
        requirement_id=None,  # Não gera requirement direto
    ),
    OnboardingQuestion(
        question_id="has_previous_public_sales",
        question_text="Você já vendeu para programas públicos antes? (ex: PNAE, PAA)",
        question_type=QuestionType.BOOLEAN,
        order=5,
        required=False,
        requirement_id=None,  # Não gera requirement
    ),
    OnboardingQuestion(
        question_id="has_bank_account",
        question_text="Você tem conta bancária para receber pagamentos?",
        question_type=QuestionType.BOOLEAN,
        order=6,
        required=False,
        requirement_id="has_bank_account",
    ),
    OnboardingQuestion(
        question_id="has_organized_documents",
        question_text="Você já tem documentos organizados? (CPF, DAP, comprovante de endereço)",
        question_type=QuestionType.BOOLEAN,
        order=7,
        required=False,
        requirement_id="has_organized_documents",
    ),
]


async def seed_onboarding_questions() -> None:
    """
    Seed onboarding questions into database.
    """
    print(f"Connecting to MongoDB: {settings.mongodb_uri}")
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)  # type: ignore[type-arg]
    db = client[settings.database_name]

    print(f"Seeding onboarding questions: {settings.database_name}")

    questions_collection = db.onboarding_questions

    # Clear existing questions (optional)
    print("Clearing existing onboarding questions...")
    await questions_collection.delete_many({})

    # Insert questions
    print(f"Inserting {len(DEFAULT_ONBOARDING_QUESTIONS)} onboarding questions...")
    for question in DEFAULT_ONBOARDING_QUESTIONS:
        doc = question.model_dump()
        await questions_collection.insert_one(doc)
        print(f"  Inserted question: {question.question_id} - {question.question_text[:50]}...")

    # Create unique index on question_id to prevent duplicates
    print("Creating indexes...")
    await questions_collection.create_index("question_id", unique=True)
    await questions_collection.create_index("order")

    print("\n" + "=" * 50)
    print("Onboarding questions seed completed!")
    print("=" * 50)

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_onboarding_questions())
