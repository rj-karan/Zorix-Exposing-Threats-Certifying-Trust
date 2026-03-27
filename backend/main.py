"""
Zorix — AI Security Validation Platform
FastAPI Application Entry Point
"""
import sys
import os
import logging

# Fix Windows UTF-8 encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.database import init_db

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("zorix")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown."""
    logger.info("=" * 60)
    logger.info("ZORIX — AI Security Validation Platform Starting")
    logger.info("=" * 60)

    # Create tables
    await init_db()
    logger.info("Database initialized")

    # Create required directories
    for d in [settings.SNAPSHOT_DIR, settings.EXPLOIT_DIR, settings.REPORTS_DIR, settings.LOGS_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)

    # Check Docker availability
    docker_ok = False
    try:
        import docker
        client = docker.from_env()
        client.ping()
        docker_ok = True
        logger.info("Docker daemon connected")
    except Exception:
        logger.warning("Docker not available — sandbox will use simulation mode")

    logger.info(f"AI Provider: {settings.AI_PROVIDER} ({settings.OLLAMA_MODEL})")
    logger.info(f"Database: {settings.DATABASE_URL.split('://')[0] if '://' in settings.DATABASE_URL else 'sqlite'}")
    logger.info(f"Docker: {'OK' if docker_ok else 'SIMULATION'}")
    logger.info("=" * 60)

    yield

    logger.info("Zorix shutting down")


app = FastAPI(
    title="Zorix — AI Security Validation Platform",
    description="Automated vulnerability validation pipeline",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for reports
reports_dir = Path(settings.REPORTS_DIR)
reports_dir.mkdir(parents=True, exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(reports_dir)), name="reports")

# ---- API Routes ----
from backend.api.routes import analysis, auth
from backend.api.routes.logs import router as logs_router
from backend.api.routes.settings_routes import router as settings_router
from backend.api.routes.websocket import router as ws_router

app.include_router(analysis.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    docker_available = False
    try:
        import docker
        client = docker.from_env()
        client.ping()
        docker_available = True
    except Exception:
        pass

    ollama_available = False
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            ollama_available = r.status_code == 200
    except Exception:
        pass

    return {
        "status": "ok",
        "version": "2.0.0",
        "services": {
            "database": True,
            "docker": docker_available,
            "ollama": ollama_available,
            "ai_provider": settings.AI_PROVIDER,
        },
    }


@app.get("/api/health")
async def api_health():
    """API health check (proxied)."""
    return await health_check()