"""
Analysis API Routes — Complete Pipeline Endpoints
"""
import os
import sys
import json
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import (
    AnalysisResult, BugReport, Project, User, Analysis,
    PipelineRun, VulnerabilityScore, ScanResult, Report,
)
from backend.services.pipeline_orchestrator import VulnerabilityPipeline
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/analysis", tags=["analysis"])


# ============================================
# Request / Response Schemas
# ============================================

class AnalyzeRequest(BaseModel):
    repo_url: str
    vulnerability_type: str = "SQL_INJECTION"
    affected_file: str = "main.py"
    affected_line: Optional[int] = None
    github_token: Optional[str] = None
    bug_description: Optional[str] = ""


class PipelineAnalyzeRequest(BaseModel):
    repo_url: str
    bug_description: str = ""
    webhook_url: Optional[str] = None
    github_token: Optional[str] = None
    vulnerability_type: str = "SQL_INJECTION"
    affected_file: str = ""


# ============================================
# Pipeline Endpoints
# ============================================

@router.post("/analyze")
async def start_analysis(
    req: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start complete vulnerability analysis pipeline."""
    logger.info(f"Analysis requested for: {req.repo_url}")

    pipeline = VulnerabilityPipeline()

    try:
        result = await pipeline.run_full_pipeline(
            repo_url=req.repo_url,
            vulnerability_type=req.vulnerability_type,
            affected_file=req.affected_file,
            affected_line=req.affected_line,
            bug_description=req.bug_description or "",
            github_token=req.github_token,
            db=db,
        )

        return result

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Get pipeline status for an analysis."""
    try:
        uid = UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")

    analysis = (await db.execute(
        select(Analysis).where(Analysis.id == uid)
    )).scalar()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Get pipeline stages
    stages_result = await db.execute(
        select(PipelineRun).where(PipelineRun.analysis_id == uid).order_by(PipelineRun.started_at)
    )
    stages = stages_result.scalars().all()

    all_stages = [
        "FETCHING", "ANALYZING", "PATCHING", "GENERATING_EXPLOIT",
        "EXECUTING", "SCANNING_STATIC", "SCANNING_DYNAMIC", "SCORING", "REPORTING",
    ]

    completed = sum(1 for s in stages if s.status == "completed")
    progress = int((completed / len(all_stages)) * 100)

    return {
        "analysis_id": str(analysis.id),
        "status": analysis.status,
        "current_stage": analysis.current_stage,
        "progress_percent": progress,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
        "stages": [
            {
                "name": s.stage_name,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "error": s.error_message,
            }
            for s in stages
        ],
    }


@router.get("/results")
async def get_results(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all analysis results with pagination."""
    # Try getting from Analysis table first
    analysis_stmt = select(Analysis).order_by(desc(Analysis.created_at))
    analysis_result = await db.execute(analysis_stmt)
    analyses = analysis_result.scalars().all()

    results_list = []

    for analysis in analyses:
        # Get associated analysis result
        ar_stmt = select(AnalysisResult).where(AnalysisResult.analysis_id == analysis.id).limit(1)
        ar = (await db.execute(ar_stmt)).scalar()

        # Get score
        score = None
        if ar:
            vs_stmt = select(VulnerabilityScore).where(VulnerabilityScore.analysis_result_id == ar.id).limit(1)
            score = (await db.execute(vs_stmt)).scalar()

        sev = score.severity if score else "UNKNOWN"
        cvss = score.cvss_score if score else 0.0

        if severity and sev != severity.upper():
            continue
        if status and analysis.status != status:
            continue

        results_list.append({
            "id": str(analysis.id),
            "repository": analysis.repo_url,
            "vulnerability_type": analysis.bug_description or "Unknown",
            "status": analysis.status,
            "cvss_score": cvss,
            "severity": sev,
            "root_cause": ar.root_cause if ar else "",
            "confidence_score": ar.confidence_score if ar else 0.0,
            "cwe_id": ar.cwe_id if ar else "",
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
        })

    # Also get legacy AnalysisResult entries without Analysis parent
    legacy_stmt = select(AnalysisResult).where(AnalysisResult.analysis_id == None).order_by(desc(AnalysisResult.created_at))
    legacy_result = await db.execute(legacy_stmt)
    for ar in legacy_result.scalars().all():
        results_list.append({
            "id": str(ar.id),
            "repository": ar.vulnerable_file or "Unknown",
            "vulnerability_type": "Legacy",
            "status": "complete",
            "cvss_score": ar.confidence_score,
            "severity": "MEDIUM",
            "root_cause": ar.root_cause or "",
            "confidence_score": ar.confidence_score,
            "created_at": ar.created_at.isoformat() if ar.created_at else None,
        })

    paginated = results_list[offset: offset + limit]

    return {"results": paginated, "total": len(results_list)}


@router.get("/reports/{analysis_id}/{format}")
async def download_report(analysis_id: str, format: str, db: AsyncSession = Depends(get_db)):
    """Download generated report."""
    try:
        uid = UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")

    report = (await db.execute(
        select(Report).where(
            Report.analysis_result_id == uid, Report.report_format == format
        )
    )).scalar()

    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report not found")

    media_type = "application/pdf" if format == "pdf" else "text/html"
    return FileResponse(report.file_path, media_type=media_type, filename=os.path.basename(report.file_path))


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an analysis and all related data."""
    try:
        uid = UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")

    analysis = (await db.execute(select(Analysis).where(Analysis.id == uid))).scalar()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    await db.delete(analysis)
    await db.commit()
    return {"deleted": True, "analysis_id": analysis_id}


# Health check for AI service
@router.get("/ai-health")
async def ai_health():
    """Check AI service health."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if r.status_code == 200:
                models = r.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                return {
                    "status": "available",
                    "provider": settings.AI_PROVIDER,
                    "models": model_names,
                    "default_model": settings.OLLAMA_MODEL,
                }
    except Exception as e:
        pass

    return {
        "status": "unavailable",
        "provider": settings.AI_PROVIDER,
        "models": [],
        "message": f"Cannot connect to {settings.AI_PROVIDER} at {settings.OLLAMA_BASE_URL}",
    }
