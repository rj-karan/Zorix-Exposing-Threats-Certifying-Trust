from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import os
import logging

# Database & auth imports
from backend.database import get_db
from backend.api.deps import get_current_user
from backend.models import User
from backend.schemas import (
    BugReportCreate,
    BugReportResponse,
    ProjectCreate,
    ProjectResponse,
    AnalysisResultResponse,
)

from backend.services import (
    ProjectService,
    BugReportService,
    AnalysisService,
)

# Your AI Service
from backend.services.ai_analysis_service import (
    OllamaService,
    AnalysisResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


# ===== Initialize Ollama AI Service =====
ollama_service = OllamaService(
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    model=os.getenv("OLLAMA_MODEL", "llama3"),
    timeout=int(os.getenv("OLLAMA_TIMEOUT", "120")),
)


# ===== Your AI Request Models =====

class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl
    github_token: str | None = None


class AnalyzeResponse(BaseModel):
    summary: str
    severity: str
    vulnerability_type: str
    affected_files: list[str]
    root_cause: str
    attack_vector: str
    proof_of_concept: str
    recommended_fix: str
    cwe_id: str
    cvss_score: float
    error: str | None = None


# =========================================================
# ===== YOUR AI ANALYSIS ENDPOINTS ========================
# =========================================================

@router.get("/ai-health")
async def ai_health():
    """Check if Ollama is reachable."""
    ok = await ollama_service.health_check()
    models = await ollama_service.list_models() if ok else []

    return {
        "ollama_reachable": ok,
        "current_model": ollama_service.model,
        "available_models": models,
    }


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repo(request: AnalyzeRequest):
    """
    Analyze GitHub repo using local AI.
    """

    result: AnalysisResult = await ollama_service.analyze_repo(
        repo_url=str(request.repo_url),
        github_token=request.github_token,
    )

    if result.error and result.severity == "UNKNOWN":
        raise HTTPException(status_code=500, detail=result.error)

    return AnalyzeResponse(
        summary=result.summary,
        severity=result.severity,
        vulnerability_type=result.vulnerability_type,
        affected_files=result.affected_files,
        root_cause=result.root_cause,
        attack_vector=result.attack_vector,
        proof_of_concept=result.proof_of_concept,
        recommended_fix=result.recommended_fix,
        cwe_id=result.cwe_id,
        cvss_score=result.cvss_score,
        error=result.error,
    )


# =========================================================
# ===== TEAM BACKEND PROJECT ENDPOINTS ====================
# =========================================================

@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project_create: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    project = await ProjectService.create_project(
        session,
        current_user.id,
        project_create.name,
        project_create.repository_url,
    )
    return project


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
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

    return project


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await ProjectService.list_user_projects(
        session,
        current_user.id,
    )


# =========================================================
# ===== BUG REPORT SYSTEM ================================
# =========================================================

@router.post(
    "/reports",
    response_model=BugReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_and_analyze_report(
    report_create: BugReportCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):

    project = await ProjectService.get_project_by_id(
        session,
        report_create.project_id,
    )

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

    logger.info(
        f"Starting analysis pipeline for bug report {bug_report.id}"
    )

    await AnalysisService.create_and_analyze_report(
        session,
        bug_report,
        project,
    )

    return bug_report


@router.get(
    "/analysis/{report_id}",
    response_model=AnalysisResultResponse,
)
async def get_analysis_result(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):

    bug_report = await BugReportService.get_bug_report_by_id(
        session,
        report_id,
    )

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

    analysis_result = await AnalysisService.get_analysis_result(
        session,
        report_id,
    )

    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result not found",
        )

    return analysis_result