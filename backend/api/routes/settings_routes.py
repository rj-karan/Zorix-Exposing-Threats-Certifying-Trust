"""
Settings and Stats API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from pydantic import BaseModel

from backend.database import get_db
from backend.models import (
    AppSetting, Analysis, AnalysisResult, VulnerabilityScore, Report,
)
from backend.config import get_settings

router = APIRouter(tags=["settings"])
settings = get_settings()


def _mask(val: str) -> str:
    """Mask sensitive value showing only last 4 chars."""
    if not val or len(val) < 8:
        return "****"
    return "*" * (len(val) - 4) + val[-4:]


@router.get("/settings")
async def get_current_settings(db: AsyncSession = Depends(get_db)):
    """Get current application settings (sensitive values masked)."""
    # Read overrides from DB
    stmt = select(AppSetting)
    result = await db.execute(stmt)
    db_settings = {s.key: s.value for s in result.scalars().all()}

    return {
        "ai": {
            "provider": db_settings.get("ai_provider", settings.AI_PROVIDER),
            "model": db_settings.get("ai_model", settings.OLLAMA_MODEL),
            "ollama_base_url": db_settings.get("ollama_base_url", settings.OLLAMA_BASE_URL),
            "anthropic_api_key": _mask(db_settings.get("anthropic_api_key", settings.ANTHROPIC_API_KEY)),
            "openai_api_key": _mask(db_settings.get("openai_api_key", settings.OPENAI_API_KEY)),
        },
        "scanners": {
            "bandit_enabled": db_settings.get("bandit_enabled", str(settings.BANDIT_ENABLED)).lower() == "true",
            "semgrep_enabled": db_settings.get("semgrep_enabled", str(settings.SEMGREP_ENABLED)).lower() == "true",
            "nuclei_enabled": db_settings.get("nuclei_enabled", str(settings.NUCLEI_ENABLED)).lower() == "true",
        },
        "sandbox": {
            "docker_socket": db_settings.get("docker_socket", settings.DOCKER_SOCKET),
            "sandbox_image": db_settings.get("sandbox_image", settings.SANDBOX_IMAGE),
            "sandbox_timeout": int(db_settings.get("sandbox_timeout", settings.SANDBOX_TIMEOUT)),
            "sandbox_memory": db_settings.get("sandbox_memory", settings.SANDBOX_MEMORY),
        },
        "database": {
            "type": settings.DATABASE_TYPE,
            "url": _mask(settings.DATABASE_URL),
        },
        "notifications": {
            "default_webhook_url": db_settings.get("default_webhook_url", settings.DEFAULT_WEBHOOK_URL),
            "email_notifications": db_settings.get("email_notifications", str(settings.EMAIL_NOTIFICATIONS)).lower() == "true",
            "notification_email": db_settings.get("notification_email", settings.NOTIFICATION_EMAIL),
        },
    }


class SettingsUpdate(BaseModel):
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    ollama_base_url: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    bandit_enabled: Optional[bool] = None
    semgrep_enabled: Optional[bool] = None
    nuclei_enabled: Optional[bool] = None
    docker_socket: Optional[str] = None
    sandbox_image: Optional[str] = None
    sandbox_timeout: Optional[int] = None
    sandbox_memory: Optional[str] = None
    default_webhook_url: Optional[str] = None
    email_notifications: Optional[bool] = None
    notification_email: Optional[str] = None


@router.patch("/settings")
async def update_settings(update: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    """Update application settings."""
    updates = update.model_dump(exclude_none=True)

    for key, value in updates.items():
        stmt = select(AppSetting).where(AppSetting.key == key)
        result = await db.execute(stmt)
        existing = result.scalar()

        if existing:
            existing.value = str(value)
        else:
            db.add(AppSetting(key=key, value=str(value)))

    await db.commit()
    return {"updated": True, "keys": list(updates.keys())}


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""
    # Total analyses
    total_stmt = select(func.count(Analysis.id))
    total_result = await db.execute(total_stmt)
    total_analyses = total_result.scalar() or 0

    # Also count from AnalysisResult (legacy)
    legacy_stmt = select(func.count(AnalysisResult.id))
    legacy_result = await db.execute(legacy_stmt)
    legacy_count = legacy_result.scalar() or 0
    total_analyses = max(total_analyses, legacy_count)

    # Severity counts from VulnerabilityScore
    critical_stmt = select(func.count(VulnerabilityScore.id)).where(
        VulnerabilityScore.severity == "CRITICAL"
    )
    critical_result = await db.execute(critical_stmt)
    critical_count = critical_result.scalar() or 0

    high_stmt = select(func.count(VulnerabilityScore.id)).where(
        VulnerabilityScore.severity == "HIGH"
    )
    high_result = await db.execute(high_stmt)
    high_count = high_result.scalar() or 0

    # Average score
    avg_stmt = select(func.avg(VulnerabilityScore.cvss_score))
    avg_result = await db.execute(avg_stmt)
    avg_score = avg_result.scalar() or 0.0

    # Reports generated
    reports_stmt = select(func.count(Report.id))
    reports_result = await db.execute(reports_stmt)
    reports_generated = reports_result.scalar() or 0

    # Last analysis
    last_stmt = select(Analysis.created_at).order_by(Analysis.created_at.desc()).limit(1)
    last_result = await db.execute(last_stmt)
    last_analysis = last_result.scalar()

    return {
        "total_analyses": total_analyses,
        "critical_count": critical_count,
        "high_count": high_count,
        "avg_score": round(float(avg_score), 1),
        "reports_generated": reports_generated,
        "last_analysis_at": last_analysis.isoformat() if last_analysis else None,
    }
