"""
WebSocket Routes for Pipeline and Log Streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import asyncio
import json

from backend.services.pipeline_orchestrator import register_ws, unregister_ws

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/pipeline/{analysis_id}")
async def pipeline_ws(websocket: WebSocket, analysis_id: str):
    """Real-time pipeline stage updates via WebSocket."""
    await websocket.accept()
    register_ws(analysis_id, websocket)

    try:
        while True:
            # Keep connection alive; actual messages sent by pipeline stages
            data = await websocket.receive_text()
            # Client can send ping
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        unregister_ws(analysis_id, websocket)
    except Exception:
        unregister_ws(analysis_id, websocket)


@router.websocket("/ws/logs")
async def logs_ws(websocket: WebSocket, analysis_id: Optional[str] = Query(None)):
    """Stream live log entries via WebSocket."""
    await websocket.accept()

    try:
        from backend.database import AsyncSessionLocal
        from backend.models import LogEntry
        from sqlalchemy import select, desc

        last_id = None
        while True:
            async with AsyncSessionLocal() as db:
                stmt = select(LogEntry).order_by(desc(LogEntry.timestamp)).limit(5)
                if analysis_id:
                    from uuid import UUID
                    try:
                        uid = UUID(analysis_id)
                        stmt = stmt.where(LogEntry.analysis_id == uid)
                    except ValueError:
                        pass

                result = await db.execute(stmt)
                entries = result.scalars().all()

                new_entries = []
                for e in reversed(entries):
                    eid = str(e.id)
                    if last_id is None or eid != last_id:
                        new_entries.append({
                            "id": eid,
                            "level": e.level,
                            "stage": e.stage,
                            "message": e.message,
                            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        })

                if entries:
                    last_id = str(entries[0].id)

                if new_entries:
                    await websocket.send_text(json.dumps({"logs": new_entries}))

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
