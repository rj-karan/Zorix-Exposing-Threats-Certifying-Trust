from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from backend.database import get_db
from backend.api.deps import get_current_user
from backend.models import User, Project, BugReport
from backend.schemas import (
    BugReportCreate,
    BugReportResponse,
    ProjectCreate,
    ProjectResponse,
    AnalysisResultResponse,
)
from backend.services import ProjectService, BugReportService, AnalysisService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])


# ===== Project Endpoints =====
@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_create: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Create new project."""
    project = await ProjectService.create_project(
        session, current_user.id, project_create.name, project_create.repository_url
    )
    return project


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get project details."""
    project = await ProjectService.get_project_by_id(session, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Verify ownership
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return project


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """List user's projects."""
    projects = await ProjectService.list_user_projects(session, current_user.id)
    return projects


# ===== Bug Report Endpoints =====
@router.post("/reports", response_model=BugReportResponse, status_code=status.HTTP_201_CREATED)
async def create_and_analyze_report(
    report_create: BugReportCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Create bug report and trigger full analysis pipeline.
    
    Pipeline:
    1. Fetch code from GitHub repository
    2. Extract affected file and context
    3. Create code snapshot
    4. Run AI analysis
    5. Compute severity score
    6. Return analysis results
    """
    # Verify project exists and belongs to user
    project = await ProjectService.get_project_by_id(session, report_create.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Create bug report
    bug_report = await BugReportService.create_bug_report(
        session,
        project_id=report_create.project_id,
        title=report_create.title,
        description=report_create.description,
        affected_file=report_create.affected_file,
        severity=report_create.severity,
        cve_id=report_create.cve_id,
        affected_line=report_create.affected_line,
        source=report_create.source,
    )

    # Trigger analysis pipeline
    logger.info(f"Starting analysis pipeline for bug report {bug_report.id}")
    analysis_result = await AnalysisService.create_and_analyze_report(session, bug_report, project)

    if not analysis_result:
        logger.warning(f"Analysis failed for bug report {bug_report.id}")

    return bug_report


@router.get("/reports/{report_id}", response_model=BugReportResponse)
async def get_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get bug report details."""
    bug_report = await BugReportService.get_bug_report_by_id(session, report_id)
    if not bug_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bug report not found",
        )
    
    # Verify ownership via project
    if bug_report.project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return bug_report


@router.get("/reports", response_model=list[BugReportResponse])
async def list_project_reports(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """List bug reports for project."""
    # Verify project exists and belongs to user
    project = await ProjectService.get_project_by_id(session, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    reports = await BugReportService.list_project_reports(session, project_id)
    return reports


# ===== Analysis Results Endpoint =====
@router.get("/analysis/{report_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get analysis results for bug report."""
    # Verify report exists and belongs to user
    bug_report = await BugReportService.get_bug_report_by_id(session, report_id)
    if not bug_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bug report not found",
        )
    
    if bug_report.project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Get analysis result
    analysis_result = await AnalysisService.get_analysis_result(session, report_id)
    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result not found or analysis pending",
        )
    
    return analysis_result
