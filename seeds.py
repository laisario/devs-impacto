#!/usr/bin/env python3
"""
Seed script for development data.

Creates sample data for testing the PNAE API:
- A sample user
- A producer profile
- A call for proposals with products
- Sample documents

Usage:
    python seeds.py

Requires MongoDB to be running.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


async def seed_database() -> None:
    """Populate database with sample data for development."""
    print(f"Connecting to MongoDB: {settings.mongodb_uri}")
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)  # type: ignore[type-arg]
    db = client[settings.database_name]

    print(f"Seeding database: {settings.database_name}")

    # Clear existing data (optional - comment out to keep existing data)
    print("Clearing existing data...")
    await db.users.delete_many({})
    await db.producer_profiles.delete_many({})
    await db.documents.delete_many({})

    now = datetime.now(UTC)

    # Create sample user
    print("Creating sample user...")
    user_result = await db.users.insert_one({
        "phone_e164": "+5511999999999",
        "otp_code": None,
        "otp_expires_at": None,
        "created_at": now,
        "updated_at": now,
    })
    user_id = user_result.inserted_id
    print(f"  Created user: {user_id}")

    # Create producer profile
    print("Creating sample producer profile...")
    profile_result = await db.producer_profiles.insert_one({
        "user_id": user_id,
        "producer_type": "individual",
        "name": "João da Silva - Agricultor Familiar",
        "address": "Sítio Boa Vista, Estrada Rural km 5",
        "city": "Campinas",
        "state": "SP",
        "dap_caf_number": "SDW123456789012345678901234",
        "cpf": "12345678901",
        "bank_name": "Banco do Brasil",
        "bank_agency": "1234-5",
        "bank_account": "12345-6",
        "created_at": now,
        "updated_at": now,
    })
    profile_id = profile_result.inserted_id
    print(f"  Created producer profile: {profile_id}")

    # Create sample documents
    print("Creating sample documents...")
    docs_data = [
        {
            "user_id": user_id,
            "doc_type": "dap_caf",
            "file_url": f"{settings.mock_storage_base_url}/files/sample_dap.pdf",
            "file_key": f"{user_id}/sample_dap.pdf",
            "original_filename": "DAP_Joao_Silva.pdf",
            "uploaded_at": now,
        },
        {
            "user_id": user_id,
            "doc_type": "cpf",
            "file_url": f"{settings.mock_storage_base_url}/files/sample_cpf.pdf",
            "file_key": f"{user_id}/sample_cpf.pdf",
            "original_filename": "CPF_Joao_Silva.pdf",
            "uploaded_at": now,
        },
    ]

    for doc_data in docs_data:
        result = await db.documents.insert_one(doc_data)
        print(f"  Created document '{doc_data['doc_type']}': {result.inserted_id}")

    # Summary
    print("\n" + "=" * 50)
    print("Seed completed successfully!")
    print("=" * 50)
    print(f"\nSample user phone: +5511999999999")
    print(f"OTP code (mock): 123456")
    print(f"\nTo get a token, run:")
    print("  curl -X POST http://localhost:8000/auth/start \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"phone_e164": "+5511999999999"}\'')
    print("\n  curl -X POST http://localhost:8000/auth/verify \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"phone_e164": "+5511999999999", "otp": "123456"}\'')

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())

