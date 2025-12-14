"""
Onboarding seeds module.
Load questions from CSV and populate database.
"""
import asyncio
import csv
import logging
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.onboarding.schemas import OnboardingQuestion, QuestionType


logger = logging.getLogger(__name__)


def parse_answer_type(answer_type: str) -> QuestionType:
    """Convert CSV answer_type to QuestionType enum."""
    mapping = {
        "single_choice": QuestionType.CHOICE,
        "multi_choice": QuestionType.CHOICE,
        "boolean": QuestionType.BOOLEAN,
        "text": QuestionType.TEXT,
    }
    return mapping.get(answer_type.lower(), QuestionType.TEXT)


def parse_options(options_str: str | None) -> list[str] | None:
    """Parse options string from CSV (pipe-separated)."""
    if not options_str or not options_str.strip():
        return None
    return [opt.strip() for opt in options_str.split("|") if opt.strip()]


async def load_questions_from_csv(
    csv_path: str | Path, db: AsyncIOMotorDatabase  # type: ignore[type-arg]
) -> list[OnboardingQuestion]:
    """
    Load onboarding questions from CSV file.

    Args:
        csv_path: Path to CSV file
        db: MongoDB database instance

    Returns:
        List of OnboardingQuestion objects
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    questions = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            # Skip empty rows
            if not row.get("question", "").strip():
                continue
            
            # Parse options
            options = parse_options(row.get("options", ""))
            
            # Determine if multiple choice
            answer_type = row.get("answer_type", "").lower()
            allow_multiple = answer_type == "multi_choice"
            
            # Convert answer_type to QuestionType
            question_type = parse_answer_type(answer_type)
            
            # Get sets_flag, affects_task, and requirement_id
            sets_flag = row.get("sets_flag", "").strip() or None
            affects_task = row.get("affects_task", "").strip() or None
            requirement_id = row.get("requirement_id", "").strip() or None
            step = row.get("step", "").strip() or None
            
            # Use step as question_id if available, otherwise use index
            question_id = step if step else f"question_{idx}"

            question = OnboardingQuestion(
                question_id=question_id,
                question_text=row["question"].strip(),
                question_type=question_type,
                options=options,
                order=idx,
                required=True,
                requirement_id=requirement_id,  # Read from CSV
                allow_multiple=allow_multiple,
                sets_flag=sets_flag,
                affects_task=affects_task,
                step=step,
            )
            questions.append(question)

    return questions


async def seed_onboarding_questions(
    db: AsyncIOMotorDatabase, csv_path: str | Path | None = None  # type: ignore[type-arg]
) -> int:
    """
    Seed onboarding questions from CSV.

    Args:
        db: MongoDB database instance
        csv_path: Path to CSV file. If None, uses default path.

    Returns:
        Number of questions seeded
    """
    if csv_path is None:
        # Default path: backend/data/onboarding_questions.csv
        # Try multiple possible paths (works both locally and in Docker)
        possible_paths = [
            # Docker: /app/app/modules/onboarding/seeds.py -> /app/data/
            Path(__file__).parent.parent.parent.parent / "data" / "onboarding_questions.csv",
            # Local: backend/app/modules/onboarding/seeds.py -> backend/data/
            Path(__file__).parent.parent.parent / "data" / "onboarding_questions.csv",
            # Alternative: from app root
            Path(__file__).parent.parent.parent.parent / "backend" / "data" / "onboarding_questions.csv",
        ]
        
        for path in possible_paths:
            if path.exists():
                csv_path = path
                break
        else:
            # Default to first path if none found
            csv_path = possible_paths[0]

    logger.info(f"Loading onboarding questions from CSV: {csv_path}")

    questions = await load_questions_from_csv(csv_path, db)

    questions_collection = db.onboarding_questions
    count = 0

    for question in questions:
        # Upsert question (update if exists, insert if not)
        result = await questions_collection.update_one(
            {"question_id": question.question_id},
            {"$set": question.model_dump()},
            upsert=True,
        )
        if result.upserted_id or result.modified_count > 0:
            count += 1
            logger.debug(f"Seeded question: {question.question_id}")

    logger.info(f"Seeded {count} onboarding questions")
    return count


# Script para rodar standalone
async def main() -> None:
    """Main function to run seeding."""
    from app.core.db import connect_db, close_db, get_database

    await connect_db()
    try:
        db = get_database()
        count = await seed_onboarding_questions(db)
        print(f"✅ Seeded {count} onboarding questions")
    finally:
        await close_db()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
