"""
Structured Logging Module for Zorix Pipeline
Provides DB-backed, file-backed, and console logging with analysis context.
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from backend.config import get_settings


settings = get_settings()


class ZorixLogger:
    """Pipeline-aware structured logger that writes to console, file, and DB."""

    def __init__(self, name: str = "zorix"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            # Console handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            fmt = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            ch.setFormatter(fmt)
            self.logger.addHandler(ch)

            # File handler
            logs_dir = Path(settings.LOGS_DIR)
            logs_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            fh = logging.FileHandler(
                logs_dir / f"zorix_{date_str}.log", encoding="utf-8"
            )
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(fmt)
            self.logger.addHandler(fh)

    def log(
        self,
        level: str,
        message: str,
        stage: Optional[str] = None,
        analysis_id: Optional[str] = None,
        extra: Optional[dict] = None,
    ):
        """Log a structured message."""
        prefix_parts = []
        if analysis_id:
            prefix_parts.append(f"[{str(analysis_id)[:8]}]")
        if stage:
            prefix_parts.append(f"[{stage}]")
        prefix = " ".join(prefix_parts)
        full_msg = f"{prefix} {message}" if prefix else message

        log_fn = getattr(self.logger, level.lower(), self.logger.info)
        log_fn(full_msg)

    def info(self, message: str, **kwargs):
        self.log("info", message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log("error", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.log("warning", message, **kwargs)

    def debug(self, message: str, **kwargs):
        self.log("debug", message, **kwargs)

    def critical(self, message: str, **kwargs):
        self.log("critical", message, **kwargs)


# Async DB logger helper — call from pipeline stages
async def log_to_db(
    db,
    level: str,
    message: str,
    stage: Optional[str] = None,
    analysis_id=None,
    extra: Optional[dict] = None,
):
    """Insert a log entry into the database."""
    from backend.models import LogEntry

    entry = LogEntry(
        analysis_id=analysis_id,
        stage=stage,
        level=level.upper(),
        message=message,
        extra=json.dumps(extra) if extra else None,
    )
    db.add(entry)
    try:
        await db.flush()
    except Exception:
        pass  # Don't break pipeline if logging fails


# Module-level singleton
pipeline_logger = ZorixLogger("zorix.pipeline")
