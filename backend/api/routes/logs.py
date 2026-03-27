"""
Logs API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import datetime

from backend.database import get_db
from backend.models import LogEntry

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def get_logs(
    analysis_id: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Get log entries with optional filters."""
    stmt = select(LogEntry).order_by(desc(LogEntry.timestamp))

    if analysis_id:
        from uuid import UUID
        try:
            uid = UUID(analysis_id)
            stmt = stmt.where(LogEntry.analysis_id == uid)
        except ValueError:
            pass

    if level:
        stmt = stmt.where(LogEntry.level == level.upper())

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    entries = result.scalars().all()

    return {
        "logs": [
            {
                "id": str(e.id),
                "analysis_id": str(e.analysis_id) if e.analysis_id else None,
                "stage": e.stage,
                "level": e.level,
                "message": e.message,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "extra": e.extra,
            }
            for e in entries
        ],
        "total": len(entries),
    }
