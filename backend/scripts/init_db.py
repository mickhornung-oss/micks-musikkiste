"""Initialize database tables for Micks Musikkiste."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db
from app.logging_config import logger


async def main():
    try:
        logger.info("starting_database_initialization")
        await init_db()
        logger.info("database_initialized")
        print("Database initialized successfully.")
    except Exception as exc:
        logger.error("database_initialization_failed", error=str(exc))
        print(f"Database initialization failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
