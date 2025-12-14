"""
Formalization seeds module.
Load tasks from CSV and populate catalog in MongoDB.
"""
import asyncio
import csv
import logging
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.formalization.schemas import FormalizationTaskCatalog


logger = logging.getLogger(__name__)


async def load_tasks_from_csv(
    csv_path: str | Path, db: AsyncIOMotorDatabase  # type: ignore[type-arg]
) -> list[FormalizationTaskCatalog]:
    """
    Load tasks from CSV file.

    Args:
        csv_path: Path to CSV file
        db: MongoDB database instance

    Returns:
        List of FormalizationTaskCatalog objects
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    tasks = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Debug: log header
        logger.debug(f"CSV headers: {reader.fieldnames}")
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
            try:
                # Debug: log row data
                logger.debug(f"Row {row_num} data: {dict(row)}")
                # Validate required fields
                if not row.get("code") or not row.get("title"):
                    logger.warning(f"Skipping row {row_num}: missing code or title")
                    continue
                
                # Parse blocking as boolean
                blocking_str = row.get("blocking", "").strip().lower()
                blocking = blocking_str in ("true", "1", "yes", "y", "t")
                
                # Parse estimated_time_days as int
                estimated_time_days_str = row.get("estimated_time_days", "0").strip()
                try:
                    estimated_time_days = int(estimated_time_days_str)
                except ValueError:
                    logger.warning(
                        f"Row {row_num}: Invalid estimated_time_days '{estimated_time_days_str}', using 0"
                    )
                    estimated_time_days = 0
                
                # Parse conditional_on (can be empty string)
                conditional_on = row.get("conditional_on", "").strip() or None

                task = FormalizationTaskCatalog(
                    code=row["code"].strip(),
                    title=row["title"].strip(),
                    description=row.get("description", "").strip(),
                    why=row.get("why", "").strip(),
                    blocking=blocking,
                    estimated_time_days=estimated_time_days,
                    conditional_on=conditional_on,
                )
                tasks.append(task)
            except Exception as e:
                logger.error(
                    f"Error parsing row {row_num}: {e}",
                    exc_info=True,
                    extra={"row": row, "row_num": row_num}
                )
                raise

    return tasks


async def seed_tasks_catalog(
    db: AsyncIOMotorDatabase, csv_path: str | Path | None = None  # type: ignore[type-arg]
) -> int:
    """
    Seed formalization tasks catalog from CSV.

    Args:
        db: MongoDB database instance
        csv_path: Path to CSV file. If None, uses default path.

    Returns:
        Number of tasks seeded
    """
    if csv_path is None:
        # Default path: backend/data/formalization_tasks.csv
        # Try multiple possible paths (works both locally and in Docker)
        possible_paths = [
            # Docker: /app/app/modules/formalization/seeds.py -> /app/data/
            Path(__file__).parent.parent.parent.parent / "data" / "formalization_tasks.csv",
            # Local: backend/app/modules/formalization/seeds.py -> backend/data/
            Path(__file__).parent.parent.parent / "data" / "formalization_tasks.csv",
            # Alternative: from app root
            Path(__file__).parent.parent.parent.parent / "backend" / "data" / "formalization_tasks.csv",
        ]
        
        for path in possible_paths:
            if path.exists():
                csv_path = path
                break
        else:
            # Default to first path if none found
            csv_path = possible_paths[0]

    logger.info(f"Loading tasks from CSV: {csv_path}")

    tasks = await load_tasks_from_csv(csv_path, db)

    catalog_collection = db.formalization_tasks_catalog
    count = 0

    for task in tasks:
        # Upsert task (update if exists, insert if not)
        result = await catalog_collection.update_one(
            {"code": task.code},
            {"$set": task.model_dump()},
            upsert=True,
        )
        if result.upserted_id or result.modified_count > 0:
            count += 1
            logger.debug(f"Seeded task: {task.code}")

    logger.info(f"Seeded {count} tasks to catalog")
    return count


# Script para rodar standalone
async def main() -> None:
    """Main function to run seeding."""
    from app.core.db import connect_db, close_db, get_database

    await connect_db()
    try:
        db = get_database()
        count = await seed_tasks_catalog(db)
        print(f"✅ Seeded {count} tasks to catalog")
    finally:
        await close_db()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
