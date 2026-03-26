from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from backend.services.ai_analysis_service import OllamaService, AnalysisResult
import os

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize service from env vars
ollama_service = OllamaService(
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    model=os.getenv("OLLAMA_MODEL", "llama3"),
    timeout=int(os.getenv("OLLAMA_TIMEOUT", "120"))
)


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


@router.get("/health")
async def health():
    """Check if Ollama is reachable."""
    ok = await ollama_service.health_check()
    models = await ollama_service.list_models() if ok else []
    return {
        "ollama_reachable": ok,
        "current_model": ollama_service.model,
        "available_models": models
    }


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repo(request: AnalyzeRequest):
    """
    Analyze a GitHub repository for vulnerabilities using Ollama.

    - Fetches code from the repo
    - Sends to local LLM for root cause analysis
    - Returns structured security findings
    """
    result: AnalysisResult = await ollama_service.analyze_repo(
        repo_url=str(request.repo_url),
        github_token=request.github_token
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
        error=result.error
    )