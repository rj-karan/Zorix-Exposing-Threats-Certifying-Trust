from .security import hash_password, verify_password, create_access_token, decode_access_token
from .github_service import github_service
from .scoring import scoring_service
from backend.services.ai_analysis_service import OllamaService

# Create default OllamaService instance
ai_analysis_service = OllamaService()

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "github_service",
    "ai_analysis_service",
    "scoring_service",
]
