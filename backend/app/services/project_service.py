"""Project service with database-backed persistence."""

import uuid
from pathlib import Path
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import InvalidStateError
from app.logging_config import logger
from app.models.db_models import Project, ProjectType
from app.repositories import ProjectRepository


class ProjectService:
    """Service for project management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repo = ProjectRepository(session)

    async def create_project(
        self,
        name: str,
        project_type: str,
        genre: str,
        mood: str,
        duration: int,
        parameters: dict,
        output_file: Optional[str] = None,
        metadata: Optional[dict] = None,
        preset_used: Optional[str] = None,
        lyrics: Optional[str] = None,
        negative_prompts: Optional[list] = None,
        notes: Optional[str] = None,
        last_job_id: Optional[str] = None,
    ) -> dict:
        try:
            normalized_type = ProjectType(project_type).value
        except ValueError as exc:
            raise InvalidStateError(
                "Unbekannter Projekttyp",
                code="invalid_project_type",
                details={"project_type": project_type},
            ) from exc

        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            type=normalized_type,
            genre=genre,
            mood=mood,
            duration=duration,
            output_file=output_file,
            preset_used=preset_used,
            lyrics=lyrics,
            negative_prompts=negative_prompts or [],
            parameters=parameters or {},
            metadata_json=metadata or {},
            notes=notes,
            exports=[],
            last_export_at=None,
            last_job_id=last_job_id,
        )
        created = await self.project_repo.create(project)
        logger.info("project_created", project_id=created.id, name=name, project_type=normalized_type)
        return self._to_api_dict(created)

    async def get_project(self, project_id: str) -> Optional[dict]:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return None
        return self._to_api_dict(project)

    async def list_projects(
        self,
        project_type: Optional[str] = None,
        genre: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        try:
            type_filter = ProjectType(project_type) if project_type else None
            projects = await self.project_repo.get_all(project_type=type_filter, genre=genre, limit=limit)
            return [self._to_api_dict(project) for project in projects]
        except ValueError as exc:
            raise InvalidStateError(
                "Unbekannter Projekttyp",
                code="invalid_project_type",
                details={"project_type": project_type},
            ) from exc
        except Exception:
            logger.exception("project_list_failed")
            return []

    async def search_projects(
        self,
        search_term: Optional[str] = None,
        project_type: Optional[str] = None,
        genre: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        try:
            type_filter = ProjectType(project_type) if project_type else None
            projects = await self.project_repo.search(
                search_term=search_term,
                project_type=type_filter,
                genre=genre,
                limit=limit,
            )
            return [self._to_api_dict(project) for project in projects]
        except ValueError as exc:
            raise InvalidStateError(
                "Unbekannter Projekttyp",
                code="invalid_project_type",
                details={"project_type": project_type},
            ) from exc
        except Exception:
            logger.exception("project_search_failed")
            return []

    async def delete_project(self, project_id: str) -> bool:
        try:
            success = await self.project_repo.delete(project_id)
            if success:
                logger.info("project_deleted", project_id=project_id)
            return success
        except Exception:
            logger.exception("project_delete_failed", project_id=project_id)
            return False

    async def update_project_metadata(self, project_id: str, metadata: dict) -> Optional[dict]:
        try:
            project = await self.project_repo.get_by_id(project_id)
            if not project:
                return None
            current_metadata = project.metadata_json or {}
            current_metadata.update(metadata)
            updated = await self.project_repo.update(project_id, metadata_json=current_metadata)
            return self._to_api_dict(updated) if updated else None
        except Exception:
            logger.exception("project_metadata_update_failed", project_id=project_id)
            return None

    async def add_export(self, project_id: str, filename: str, path: str) -> Optional[dict]:
        try:
            updated = await self.project_repo.add_export(project_id, filename, path)
            if updated:
                logger.info("project_export_recorded", project_id=project_id, filename=filename)
            return self._to_api_dict(updated) if updated else None
        except Exception:
            logger.exception("project_export_add_failed", project_id=project_id)
            return None

    async def count_projects(self) -> int:
        return await self.project_repo.count()

    @staticmethod
    def _to_api_dict(project: Project) -> dict:
        result = project.to_dict()
        if project.output_file:
            filename = Path(project.output_file).name
            result["audio_url"] = f"/outputs/{filename}"
            result["download_url"] = result["audio_url"]
        return result
