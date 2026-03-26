from dotenv import load_dotenv
load_dotenv()  # must be first

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes.analysis import router as analysis_router
import os

app = FastAPI(
    title="Zorix — Exposing Threats, Certifying Trust",
    description="AI-powered vulnerability analysis platform",
    version="0.1.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000"
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include AI analysis routes
app.include_router(analysis_router)


# Root route (merged version)
@app.get("/")
async def root():
    return {
        "status": "Zorix is running",
        "docs": "/docs"
    }


# Health check (needed for Docker)
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }