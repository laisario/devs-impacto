"""
Script to seed onboarding questions into the database.
Run this script to populate the onboarding_questions collection.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


ONBOARDING_QUESTIONS = [
    {
        "question_id": "has_dap_caf",
        "question_text": "Você possui DAP/CAF (Declaração de Aptidão ao Pronaf)?",
        "question_type": "boolean",
        "options": None,
        "order": 1,
        "required": True,
        "requirement_id": "dap_caf",
    },
    {
        "question_id": "producer_type",
        "question_text": "Qual é o tipo do seu empreendimento?",
        "question_type": "choice",
        "options": ["Individual", "Informal", "Formal (CNPJ)"],
        "order": 2,
        "required": True,
        "requirement_id": None,
    },
    {
        "question_id": "has_cnpj",
        "question_text": "Você possui CNPJ?",
        "question_type": "boolean",
        "options": None,
        "order": 3,
        "required": True,
        "requirement_id": "cnpj",
    },
    {
        "question_id": "has_cpf",
        "question_text": "Você possui CPF?",
        "question_type": "boolean",
        "options": None,
        "order": 4,
        "required": True,
        "requirement_id": "cpf",
    },
    {
        "question_id": "has_address_proof",
        "question_text": "Você possui comprovante de endereço?",
        "question_type": "boolean",
        "options": None,
        "order": 5,
        "required": True,
        "requirement_id": "proof_address",
    },
    {
        "question_id": "has_bank_account",
        "question_text": "Você possui conta bancária?",
        "question_type": "boolean",
        "options": None,
        "order": 6,
        "required": True,
        "requirement_id": "bank_statement",
    },
    {
        "question_id": "production_type",
        "question_text": "Qual tipo de produção você realiza?",
        "question_type": "choice",
        "options": ["Agricultura", "Pecuária", "Agricultura e Pecuária", "Outro"],
        "order": 7,
        "required": True,
        "requirement_id": None,
    },
    {
        "question_id": "has_previous_sales",
        "question_text": "Você já vendeu para programas públicos anteriormente?",
        "question_type": "boolean",
        "options": None,
        "order": 8,
        "required": True,
        "requirement_id": None,
    },
]


async def seed_questions():
    """Seed onboarding questions into the database."""
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    collection = db.onboarding_questions

    print(f"Connecting to database: {settings.database_name}")
    print(f"Seeding {len(ONBOARDING_QUESTIONS)} onboarding questions...")

    # Clear existing questions (optional - comment out if you want to keep existing)
    # await collection.delete_many({})
    # print("Cleared existing questions")

    inserted_count = 0
    updated_count = 0

    for question in ONBOARDING_QUESTIONS:
        result = await collection.update_one(
            {"question_id": question["question_id"]},
            {"$set": question},
            upsert=True,
        )
        if result.upserted_id:
            inserted_count += 1
            print(f"  ✓ Inserted: {question['question_id']}")
        else:
            updated_count += 1
            print(f"  ↻ Updated: {question['question_id']}")

    print(f"\n✅ Done! Inserted: {inserted_count}, Updated: {updated_count}")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_questions())
