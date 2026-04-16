"""Repository for project database operations."""

from datetime import datetime, timezone
from typing import List, Optional

UTC = timezone.utc

from app.logging_config import logger
from app.models.db_models import Project, ProjectType
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession


def utc_now_naive() -> datetime:
    """Return a UTC timestamp compatible with the current naive DB schema."""
    return datetime.now(UTC).replace(tzinfo=None)


class ProjectRepository:
    """Repository für Projekt-Operationen."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, project: Project) -> Project:
        try:
            self.session.add(project)
            await self.session.flush()
            await self.session.refresh(project)
            logger.info(
                "project_repo_created", project_id=project.id, name=project.name
            )
            return project
        except Exception:
            logger.exception("project_repo_create_failed")
            raise

    async def get_by_id(self, project_id: str) -> Optional[Project]:
        try:
            result = await self.session.execute(
                select(Project).where(Project.id == project_id)
            )
            return result.scalar_one_or_none()
        except Exception:
            logger.exception("project_repo_get_failed", project_id=project_id)
            return None

    async def get_all(
        self,
        project_type: Optional[ProjectType] = None,
        genre: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Project]:
        try:
            query = select(Project).order_by(Project.created_at.desc())
            if project_type:
                query = query.where(Project.type == project_type.value)
            if genre:
                query = query.where(Project.genre == genre)
            if limit:
                query = query.limit(limit)
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception:
            logger.exception("project_repo_list_failed")
            return []

    async def search(
        self,
        search_term: Optional[str] = None,
        project_type: Optional[ProjectType] = None,
        genre: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Project]:
        try:
            query = select(Project).order_by(Project.created_at.desc())
            if search_term:
                query = query.where(
                    or_(
                        Project.name.ilike(f"%{search_term}%"),
                        Project.genre.ilike(f"%{search_term}%"),
                        Project.mood.ilike(f"%{search_term}%"),
                    )
                )
            if project_type:
                query = query.where(Project.type == project_type.value)
            if genre:
                query = query.where(Project.genre == genre)
            if limit:
                query = query.limit(limit)
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception:
            logger.exception("project_repo_search_failed")
            return []

    async def update(self, project_id: str, **kwargs) -> Optional[Project]:
        try:
            allowed_fields = {
                "name",
                "type",
                "genre",
                "mood",
                "duration",
                "output_file",
                "preset_used",
                "lyrics",
                "negative_prompts",
                "parameters",
                "metadata_json",
                "notes",
                "exports",
                "last_export_at",
                "last_job_id",
            }
            update_data = {
                key: value for key, value in kwargs.items() if key in allowed_fields
            }
            result = await self.session.execute(
                update(Project)
                .where(Project.id == project_id)
                .values(**update_data)
                .returning(Project)
            )
            project = result.scalar_one_or_none()
            if project:
                logger.info("project_repo_updated", project_id=project_id)
            return project
        except Exception:
            logger.exception("project_repo_update_failed", project_id=project_id)
            return None

    async def delete(self, project_id: str) -> bool:
        try:
            project = await self.get_by_id(project_id)
            if not project:
                return False
            await self.session.delete(project)
            logger.info("project_repo_deleted", project_id=project_id)
            return True
        except Exception:
            logger.exception("project_repo_delete_failed", project_id=project_id)
            return False

    async def add_export(
        self, project_id: str, filename: str, path: str
    ) -> Optional[Project]:
        try:
            project = await self.get_by_id(project_id)
            if not project:
                return None

            exports = project.exports or []
            exports.append(
                {
                    "filename": filename,
                    "path": path,
                    "exported_at": utc_now_naive().isoformat(),
                }
            )
            return await self.update(
                project_id, exports=exports, last_export_at=utc_now_naive()
            )
        except Exception:
            logger.exception("project_repo_add_export_failed", project_id=project_id)
            return None

    async def count(self) -> int:
        try:
            from sqlalchemy import func

            result = await self.session.execute(select(func.count(Project.id)))
            return result.scalar() or 0
        except Exception:
            logger.exception("project_repo_count_failed")
            return 0
