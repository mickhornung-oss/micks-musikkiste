"""Import legacy JSON projects into the PostgreSQL-backed project store."""

import asyncio
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import async_session_factory
from app.logging_config import logger
from app.models.db_models import Project, ProjectType
from app.repositories import ProjectRepository


async def main():
    imported = 0
    skipped = 0

    async with async_session_factory() as session:
        repo = ProjectRepository(session)
        for json_file in sorted(settings.PROJECTS_DIR.glob("*.json")):
            try:
                payload = json.loads(json_file.read_text(encoding="utf-8-sig"))
            except Exception:
                logger.exception("legacy_project_read_failed", file=str(json_file))
                continue

            project_id = payload.get("id") or str(uuid.uuid4())
            if await repo.get_by_id(project_id):
                skipped += 1
                continue

            project = Project(
                id=project_id,
                name=payload.get("name", json_file.stem),
                type=ProjectType(payload.get("type", "track")).value,
                genre=payload.get("genre", "unknown"),
                mood=payload.get("mood", "unknown"),
                duration=int(payload.get("duration", 120)),
                output_file=payload.get("output_file"),
                preset_used=payload.get("preset_used"),
                lyrics=payload.get("lyrics"),
                negative_prompts=payload.get("negative_prompts") or [],
                parameters=payload.get("parameters") or {},
                metadata_json=payload.get("metadata") or {},
                notes=payload.get("notes"),
                exports=payload.get("exports") or [],
                last_job_id=payload.get("last_job_id"),
            )
            await repo.create(project)
            imported += 1
        await session.commit()

    print(f"Imported: {imported}, skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(main())
