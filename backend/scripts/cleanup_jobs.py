"""Local maintenance helper for stale/test jobs in the shared PostgreSQL DB."""

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session_factory, close_db
from app.logging_config import logger
from app.repositories import JobRepository


async def print_summary(session) -> None:
    rows = await session.execute(
        text("SELECT status, count(*) FROM jobs GROUP BY status ORDER BY status")
    )
    print("Job summary:")
    for status, count in rows.fetchall():
        print(f"  {status}: {count}")


async def cleanup_jobs(delete_test_jobs: bool, recover_stale: bool) -> dict:
    deleted = 0
    recovered = 0
    failed = 0

    async with async_session_factory() as session:
        repo = JobRepository(session)

        if recover_stale:
            result = await repo.recover_stuck_jobs()
            recovered = result["recovered"]
            failed = result["failed"]
            await session.commit()

        if delete_test_jobs:
            await session.execute(text("""
                    UPDATE projects
                    SET last_job_id = NULL
                    WHERE last_job_id IN (
                        SELECT id FROM jobs
                        WHERE title LIKE 'pytest-mm-%'
                           OR title LIKE 'final-manual-%'
                           OR title LIKE 'queue-%'
                           OR title LIKE 'recovery-check-%'
                           OR title = 'Block1 Mock Validation'
                    )
                    """))
            result = await session.execute(text("""
                    DELETE FROM jobs
                    WHERE title LIKE 'pytest-mm-%'
                       OR title LIKE 'final-manual-%'
                       OR title LIKE 'queue-%'
                       OR title LIKE 'recovery-check-%'
                       OR title = 'Block1 Mock Validation'
                    """))
            deleted = result.rowcount or 0
            await session.commit()

        await print_summary(session)

    await close_db()
    return {"deleted": deleted, "recovered": recovered, "failed": failed}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cleanup local stale/test jobs.")
    parser.add_argument(
        "--delete-test-jobs",
        action="store_true",
        help="Delete local test/mock validation jobs.",
    )
    parser.add_argument(
        "--recover-stale",
        action="store_true",
        help="Recover stale running/claimed jobs before cleanup.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    result = await cleanup_jobs(
        delete_test_jobs=args.delete_test_jobs,
        recover_stale=args.recover_stale,
    )
    logger.info("cleanup_jobs_finished", **result)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
