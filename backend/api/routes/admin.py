"""
Admin Panel API Routes
Provides endpoints for full backend observability:
  - Ollama prompts
  - Docker execution logs
  - Backend stage logs
  - Payload results
  - Dynamic scan activity
  - Repository change status
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from uuid import UUID

from backend.database import get_db
from backend.models import (
    OllamaPrompt, DockerLog, BackendStageLog,
    DynamicScanLog, PayloadResult, ExploitExecution, AnalysisResult
)

router = APIRouter(prefix="/admin", tags=["admin"])


# =========================================================
# 1. Ollama Prompts
# =========================================================

@router.get("/ollama-prompts")
async def get_ollama_prompts(
    analysis_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get all Ollama-generated prompts for admin visibility."""
    stmt = select(OllamaPrompt).order_by(desc(OllamaPrompt.generated_time))

    if analysis_id:
        try:
            uid = UUID(analysis_id)
            stmt = stmt.where(OllamaPrompt.analysis_result_id == uid)
        except ValueError:
            pass

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    prompts = result.scalars().all()

    return {
        "prompts": [
            {
                "id": str(p.id),
                "analysis_id": str(p.analysis_result_id),
                "prompt_type": p.prompt_type,
                "prompt_text": p.prompt_text,
                "response_text": p.response_text,
                "generated_time": p.generated_time.isoformat() if p.generated_time else None,
            }
            for p in prompts
        ],
        "total": len(prompts),
    }


# =========================================================
# 2. Docker Execution Logs
# =========================================================

@router.get("/docker-logs")
async def get_docker_logs(
    analysis_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get Docker container execution logs."""
    stmt = select(DockerLog).order_by(desc(DockerLog.created_at))

    if analysis_id:
        try:
            uid = UUID(analysis_id)
            stmt = stmt.where(DockerLog.analysis_result_id == uid)
        except ValueError:
            pass

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return {
        "docker_logs": [
            {
                "id": str(l.id),
                "analysis_id": str(l.analysis_result_id),
                "container_id": l.container_id,
                "log_output": l.log_output[:500] if l.log_output else None,
                "stdout": l.stdout[:300] if l.stdout else None,
                "stderr": l.stderr[:300] if l.stderr else None,
                "exit_code": l.exit_code,
                "execution_time": l.execution_time,
                "status": l.status,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": len(logs),
    }


# =========================================================
# 3. Backend Stage Logs (Pipeline Trace)
# =========================================================

@router.get("/stage-logs")
async def get_stage_logs(
    analysis_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get backend pipeline stage execution logs."""
    stmt = select(BackendStageLog).order_by(desc(BackendStageLog.created_at))

    if analysis_id:
        try:
            uid = UUID(analysis_id)
            stmt = stmt.where(BackendStageLog.analysis_result_id == uid)
        except ValueError:
            pass

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return {
        "stage_logs": [
            {
                "id": str(l.id),
                "analysis_id": str(l.analysis_result_id),
                "stage_name": l.stage_name,
                "status": l.status,
                "start_time": l.start_time.isoformat() if l.start_time else None,
                "end_time": l.end_time.isoformat() if l.end_time else None,
                "output_message": l.output_message,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": len(logs),
    }


# =========================================================
# 4. Dynamic Scan Activity
# =========================================================

@router.get("/dynamic-scans")
async def get_dynamic_scans(
    analysis_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get dynamic scan activity and repository change detection logs."""
    stmt = select(DynamicScanLog).order_by(desc(DynamicScanLog.created_at))

    if analysis_id:
        try:
            uid = UUID(analysis_id)
            stmt = stmt.where(DynamicScanLog.analysis_result_id == uid)
        except ValueError:
            pass

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return {
        "dynamic_scans": [
            {
                "id": str(l.id),
                "analysis_id": str(l.analysis_result_id),
                "repo_url": l.repo_url,
                "change_detected": l.change_detected,
                "change_log": l.change_log,
                "scan_status": l.scan_status,
                "scan_output": l.scan_output,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": len(logs),
    }


# =========================================================
# 5. Payload Results (per analysis)
# =========================================================

@router.get("/payload-results")
async def get_all_payload_results(
    analysis_id: Optional[str] = Query(None),
    success_only: bool = Query(False),
    limit: int = Query(200, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get payload execution results — the key visibility fix."""
    stmt = select(PayloadResult).order_by(desc(PayloadResult.created_at))

    if analysis_id:
        try:
            uid = UUID(analysis_id)
            stmt = stmt.where(PayloadResult.analysis_result_id == uid)
        except ValueError:
            pass

    if success_only:
        stmt = stmt.where(PayloadResult.exploit_success == True)

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    payloads = result.scalars().all()

    return {
        "payload_results": [
            {
                "id": str(p.id),
                "analysis_id": str(p.analysis_result_id),
                "payload_id": p.payload_id,
                "payload_type": p.payload_type,
                "payload_category": p.payload_category,
                "payload_string": p.payload_string,
                "execution_status": p.execution_status,
                "response_output": p.response_output,
                "exploit_success": p.exploit_success,
                "execution_time_ms": p.execution_time_ms,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payloads
        ],
        "total": len(payloads),
        "successful": sum(1 for p in payloads if p.exploit_success),
        "failed": sum(1 for p in payloads if not p.exploit_success),
    }


@router.get("/payload-results/{analysis_id}")
async def get_payload_results_by_analysis(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get full payload results for a specific analysis — for dashboard display."""
    stmt = select(PayloadResult).where(
        PayloadResult.analysis_result_id == analysis_id
    ).order_by(PayloadResult.created_at)

    result = await db.execute(stmt)
    payloads = result.scalars().all()

    successful = [p for p in payloads if p.exploit_success]
    failed = [p for p in payloads if not p.exploit_success]

    return {
        "analysis_id": str(analysis_id),
        "total_payloads": len(payloads),
        "successful_count": len(successful),
        "failed_count": len(failed),
        "confidence_score": round((len(successful) / max(len(payloads), 1)) * 100, 1),
        "successful_payloads": [
            {
                "payload_id": p.payload_id,
                "payload_string": p.payload_string,
                "payload_category": p.payload_category,
                "execution_status": p.execution_status,
                "response_output": p.response_output,
                "execution_time_ms": p.execution_time_ms,
            }
            for p in successful
        ],
        "failed_payloads": [
            {
                "payload_id": p.payload_id,
                "payload_string": p.payload_string,
                "payload_category": p.payload_category,
                "execution_status": p.execution_status,
                "response_output": p.response_output,
                "execution_time_ms": p.execution_time_ms,
            }
            for p in failed
        ],
    }


# =========================================================
# 6. Repository Change Status
# =========================================================

@router.get("/repo-changes")
async def get_repo_changes(
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get repository change monitoring status."""
    stmt = select(DynamicScanLog).order_by(desc(DynamicScanLog.created_at)).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return {
        "repo_changes": [
            {
                "repo_url": l.repo_url,
                "change_detected": l.change_detected,
                "status": "Changes detected" if l.change_detected else "No changes detected",
                "scan_status": l.scan_status,
                "last_checked": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": len(logs),
    }


# =========================================================
# 7. Exploit Code Snapshots
# =========================================================

@router.get("/exploit-code")
async def get_exploit_code(
    analysis_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get generated exploit code / payload snapshots from executions."""
    stmt = select(ExploitExecution).order_by(desc(ExploitExecution.created_at))

    if analysis_id:
        try:
            uid = UUID(analysis_id)
            stmt = stmt.where(ExploitExecution.analysis_result_id == uid)
        except ValueError:
            pass

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    executions = result.scalars().all()

    return {
        "exploit_code": [
            {
                "id": str(e.id),
                "analysis_id": str(e.analysis_result_id),
                "exploit_type": e.exploit_type,
                "exploit_payload": e.exploit_payload,
                "execution_status": e.execution_status,
                "vulnerable": e.vulnerable,
                "stdout": e.stdout[:300] if e.stdout else None,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in executions
        ],
        "total": len(executions),
    }
