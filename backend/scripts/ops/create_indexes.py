#!/usr/bin/env python3
"""
Script to create MongoDB indexes for optimal query performance.

Run this script once to create all necessary indexes for the onboarding and formalization modules.

Usage:
    python scripts/ops/create_indexes.py

Requires MongoDB to be running.
"""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


async def create_indexes() -> None:
    """Create all necessary indexes for the application."""
    print(f"Connecting to MongoDB: {settings.mongodb_uri}")
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)  # type: ignore[type-arg]
    db = client[settings.database_name]

    print(f"Creating indexes for database: {settings.database_name}\n")

    # Onboarding answers indexes
    print("Creating indexes for onboarding_answers...")
    onboarding_answers = db.onboarding_answers
    await onboarding_answers.create_index(
        [("user_id", 1), ("question_id", 1)], unique=True, name="user_question_unique"
    )
    await onboarding_answers.create_index("user_id", name="user_id_idx")
    await onboarding_answers.create_index("answered_at", name="answered_at_idx")
    print("  ✓ Created indexes: user_question_unique, user_id_idx, answered_at_idx")

    # Onboarding questions indexes
    print("Creating indexes for onboarding_questions...")
    onboarding_questions = db.onboarding_questions
    await onboarding_questions.create_index("question_id", unique=True, name="question_id_unique")
    await onboarding_questions.create_index("order", name="order_idx")
    print("  ✓ Created indexes: question_id_unique, order_idx")

    # Formalization status indexes
    print("Creating indexes for formalization_status...")
    formalization_status = db.formalization_status
    await formalization_status.create_index("user_id", unique=True, name="user_id_unique")
    await formalization_status.create_index("diagnosed_at", name="diagnosed_at_idx")
    print("  ✓ Created indexes: user_id_unique, diagnosed_at_idx")

    # Formalization tasks indexes
    print("Creating indexes for formalization_tasks...")
    formalization_tasks = db.formalization_tasks
    await formalization_tasks.create_index("user_id", name="user_id_idx")
    await formalization_tasks.create_index(
        [("user_id", 1), ("task_id", 1)], unique=True, name="user_task_unique"
    )
    await formalization_tasks.create_index("completed", name="completed_idx")
    await formalization_tasks.create_index("priority", name="priority_idx")
    print("  ✓ Created indexes: user_id_idx, user_task_unique, completed_idx, priority_idx")

    # Producer profiles indexes (for onboarding fields)
    print("Creating indexes for producer_profiles...")
    producer_profiles = db.producer_profiles
    await producer_profiles.create_index("user_id", unique=True, name="user_id_unique")
    await producer_profiles.create_index("onboarding_status", name="onboarding_status_idx")
    print("  ✓ Created indexes: user_id_unique, onboarding_status_idx")

    # RAG chunks indexes
    print("Creating indexes for rag_chunks...")
    rag_chunks = db.rag_chunks
    await rag_chunks.create_index("topic", name="topic_idx")
    await rag_chunks.create_index("applies_to", name="applies_to_idx")
    await rag_chunks.create_index("source", name="source_idx")
    print("  ✓ Created indexes: topic_idx, applies_to_idx, source_idx")

    print("\n" + "=" * 50)
    print("All indexes created successfully!")
    print("=" * 50)

    client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())
