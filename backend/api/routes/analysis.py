from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import os
import logging

# Database & auth imports
from backend.database import get_db
from backend.api.deps import get_current_user
from backend.models import User, AnalysisResult, Report, VulnerabilityScore, BugReport
from backend.services.pipeline_orchestrator import VulnerabilityPipeline
from backend.services.ai_analysis_service import OllamaService
from backend.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize services
settings = get_settings()
ollama_service = OllamaService(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.OLLAMA_MODEL,
    timeout=settings.OLLAMA_TIMEOUT,
)
pipeline = VulnerabilityPipeline()


# ===== Request/Response Models =====

class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl
    vulnerability_type: str = "SQL_INJECTION"
    affected_file: str = "main.py"
    affected_line: int | None = None
    github_token: str | None = None


class AnalyzeResponse(BaseModel):
    status: str
    analysis_id: str
    score: float | None = None
    severity: str | None = None
    report_url: str | None = None
    vulnerable: bool | None = None
    exploits_tested: int | None = None
    error: str | None = None


# =========================================================
# ===== HEALTH CHECK ENDPOINTS ===========================
# =========================================================

@router.get("/health")
async def health_check():
    """Check if all services are ready"""
    try:
        ollama_ok = await ollama_service.health_check()
        models = await ollama_service.list_models() if ollama_ok else []
        return {
            "status": "healthy",
            "ai_service": "ready" if ollama_ok else "unavailable",
            "available_models": models,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "ai_service": "unavailable",
            "error": str(e),
        }


# =========================================================
# ===== FULL PIPELINE ANALYSIS ENDPOINT ==================
# =========================================================

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_vulnerability(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run complete vulnerability analysis pipeline
    
    Pipeline steps:
    1. Fetch repository from GitHub
    2. Run AI root cause analysis
    3. Generate and execute exploits in sandbox
    4. Run static code analysis
    5. Calculate CVSS vulnerability score
    6. Generate HTML/PDF report
    7. Return results with report URL
    
    Args:
        request: AnalyzeRequest with repo_url, vulnerability_type, affected_file
        
    Returns:
        AnalyzeResponse with analysis_id, score, severity, and report_url
    """
    
    try:
        logger.info(f"Starting analysis for {request.repo_url}")
        
        # Run full pipeline
        result = await pipeline.run_full_pipeline(
            repo_url=str(request.repo_url),
            vulnerability_type=request.vulnerability_type,
            affected_file=request.affected_file,
            affected_line=request.affected_line,
            github_token=request.github_token,
            db=db
        )
        
        if result["status"] == "completed":
            return AnalyzeResponse(
                status="completed",
                analysis_id=result["analysis_id"],
                score=result.get("score"),
                severity=result.get("severity"),
                report_url=result.get("report_url"),
                vulnerable=result.get("vulnerable"),
                exploits_tested=result.get("exploits_tested"),
            )
        else:
            return AnalyzeResponse(
                status="failed",
                analysis_id=result.get("analysis_id"),
                error=result.get("error"),
            )
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline error: {str(e)}"
        )


@router.get("/results")
async def get_all_results(db: AsyncSession = Depends(get_db)):
    """
    Get all analysis results
    Returns list of recent analyses with their scores and status
    """
    try:
        # Get all analysis results ordered by creation date
        stmt = select(AnalysisResult).order_by(AnalysisResult.created_at.desc())
        results = await db.execute(stmt)
        analyses = results.scalars().all()
        
        if not analyses:
            return {"results": [], "total": 0}
        
        # Get vulnerability scores and reports
        response_data = []
        for analysis in analyses:
            # Get score
            score_stmt = select(VulnerabilityScore).where(
                VulnerabilityScore.analysis_result_id == analysis.id
            )
            score_result = await db.execute(score_stmt)
            score = score_result.scalar()
            
            # Get bug report for repository info
            bug_stmt = select(BugReport).where(BugReport.analysis_result_id == analysis.id)
            bug_result = await db.execute(bug_stmt)
            bug_report = bug_result.scalar()
            
            response_data.append({
                "id": str(analysis.id),
                "repository": bug_report.repository_url if bug_report else "Unknown",
                "vulnerability_type": bug_report.vulnerability_type if bug_report else "Unknown",
                "status": "complete",
                "cvss_score": score.cvss_score if score else 0.0,
                "severity": score.severity if score else "UNKNOWN",
                "root_cause": analysis.root_cause,
                "confidence_score": analysis.confidence_score,
                "created_at": analysis.created_at.isoformat(),
            })
        
        return {"results": response_data, "total": len(response_data)}
        
    except Exception as e:
        logger.error(f"Failed to get all results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/results/{analysis_id}")
async def get_analysis_results(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get analysis results by analysis ID
    """
    try:
        stmt = select(AnalysisResult).where(AnalysisResult.id == analysis_id)
        analysis = await db.execute(stmt)
        result = analysis.scalar()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # Get vulnerability score
        from backend.models import VulnerabilityScore
        score_stmt = select(VulnerabilityScore).where(
            VulnerabilityScore.analysis_result_id == analysis_id
        )
        score_result = await db.execute(score_stmt)
        score = score_result.scalar()
        
        # Get report
        report_stmt = select(Report).where(Report.analysis_result_id == analysis_id)
        report_result = await db.execute(report_stmt)
        report = report_result.scalar()
        
        return {
            "analysis_id": str(analysis_id),
            "root_cause": result.root_cause,
            "confidence_score": result.confidence_score,
            "exploit_payload": result.exploit_payload,
            "suggested_patch": result.suggested_patch,
            "vulnerability_score": {
                "cvss_score": score.cvss_score if score else 0.0,
                "severity": score.severity if score else "UNKNOWN",
                "cvss_vector": score.cvss_vector if score else None,
            } if score else None,
            "report_url": f"/reports/{analysis_id}" if report else None,
            "created_at": result.created_at.isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to get results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/reports/{analysis_id}/{format}")
async def get_report(
    analysis_id: UUID,
    format: str = "html",
    db: AsyncSession = Depends(get_db)
):
    """
    Download generated report (html, pdf, json)
    """
    try:
        stmt = select(Report).where(Report.analysis_result_id == analysis_id)
        result = await db.execute(stmt)
        report = result.scalar()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=report.file_path,
            filename=f"zorix_report_{analysis_id}.{format}",
            media_type=f"text/{format}" if format in ["html", "json"] else "application/pdf"
        )
        
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/exploit-results/{analysis_id}")
async def get_exploit_results(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed exploit execution results
    """
    try:
        from backend.models import ExploitExecution
        
        stmt = select(ExploitExecution).where(
            ExploitExecution.analysis_result_id == analysis_id
        )
        result = await db.execute(stmt)
        executions = result.scalars().all()
        
        return {
            "analysis_id": str(analysis_id),
            "total_executions": len(executions),
            "vulnerable_exploits": sum(1 for e in executions if e.vulnerable),
            "executions": [
                {
                    "exploit_type": e.exploit_type,
                    "vulnerable": e.vulnerable,
                    "status": e.execution_status,
                    "return_code": e.return_code,
                    "execution_time_ms": e.execution_time_ms,
                    "stdout": e.stdout[:200] if e.stdout else None,
                    "stderr": e.stderr[:200] if e.stderr else None,
                }
                for e in executions
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get exploit results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =========================================================
# ===== LEGACY ENDPOINTS FOR COMPATIBILITY ==============
# =========================================================

@router.get("/ai-health")
async def ai_health():
    """Check if Ollama is reachable (legacy endpoint)"""
    ok = await ollama_service.health_check()
    models = await ollama_service.list_models() if ok else []

    return {
        "ollama_reachable": ok,
        "current_model": ollama_service.model,
        "available_models": models,
    }


