from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models import Project, BugReport
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project operations."""

    @staticmethod
    async def create_project(
        session: AsyncSession, user_id: UUID, name: str, repository_url: str
    ) -> Project:
        """Create new project."""
        project = Project(user_id=user_id, name=name, repository_url=repository_url)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        logger.info(f"Project created: {name}")
        return project

    @staticmethod
    async def get_project_by_id(session: AsyncSession, project_id: UUID) -> Project | None:
        """Get project by ID."""
        result = await session.execute(select(Project).where(Project.id == project_id))
        return result.scalars().first()

    @staticmethod
    async def list_user_projects(session: AsyncSession, user_id: UUID) -> list[Project]:
        """List all projects for user."""
        result = await session.execute(select(Project).where(Project.user_id == user_id))
        return result.scalars().all()


class BugReportService:
    """Service for bug report operations."""

    @staticmethod
    async def create_bug_report(
        session: AsyncSession,
        project_id: UUID,
        title: str,
        description: str,
        affected_file: str,
        severity: str | None = None,
        cve_id: str | None = None,
        affected_line: int | None = None,
        source: str = "manual",
    ) -> BugReport:
        """Create new bug report."""
        bug_report = BugReport(
            project_id=project_id,
            title=title,
            description=description,
            affected_file=affected_file,
            severity=severity,
            cve_id=cve_id,
            affected_line=affected_line,
            source=source,
        )
        session.add(bug_report)
        await session.commit()
        await session.refresh(bug_report)
        logger.info(f"Bug report created: {title}")
        return bug_report

    @staticmethod
    async def get_bug_report_by_id(session: AsyncSession, report_id: UUID) -> BugReport | None:
        """Get bug report by ID."""
        result = await session.execute(select(BugReport).where(BugReport.id == report_id))
        return result.scalars().first()

    @staticmethod
    async def list_project_reports(session: AsyncSession, project_id: UUID) -> list[BugReport]:
        """List all bug reports for project."""
        result = await session.execute(
            select(BugReport).where(BugReport.project_id == project_id)
        )
        return result.scalars().all()
