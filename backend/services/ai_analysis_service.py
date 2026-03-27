import httpx
import json
import logging
import re
from dataclasses import dataclass
import os
from backend.core.prompts import SYSTEM_PROMPT, build_rca_prompt
from backend.services.github_service import fetch_repo_files

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
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
    raw_response: str = ""
    error: str | None = None


class OllamaService:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: int = 120
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def analyze_repo(
        self,
        repo_url: str,
        github_token: str | None = None
    ) -> AnalysisResult:
        logger.info(f"Fetching files from {repo_url}")
        try:
            github_token = github_token or os.getenv("GITHUB_TOKEN")
            file_contents = await fetch_repo_files(
                repo_url,
                github_token=github_token
            )
        except Exception as e:
            return _error_result(f"Failed to fetch repo: {str(e)}")

        if not file_contents:
            return _error_result("No analyzable files found in repository")

        logger.info(f"Fetched {len(file_contents)} files. Sending to Ollama ({self.model})")

        user_prompt = build_rca_prompt(repo_url, file_contents)

        raw_response = await self._call_ollama(user_prompt)
        if raw_response is None:
            return _error_result("Ollama did not return a response")

        return _parse_response(raw_response)

    async def _call_ollama(self, user_prompt: str) -> str | None:
        """Send prompt to Ollama /api/chat endpoint."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": 4096
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"Ollama raw response: {data}")
                content = data.get("message", {}).get("content")
                if not content:
                    logger.error("Empty content returned from Ollama")
                    return None
                return content

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama.")
            return None
        except httpx.TimeoutException:
            logger.error(f"Ollama timed out after {self.timeout}s")
            return None
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    async def list_models(self) -> list[str]:
        """Return available models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = resp.json().get("models", [])
                return [m["name"] for m in models]
        except Exception:
            return []

    async def health_check(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False


def _parse_response(raw: str) -> AnalysisResult:
    """Extract and parse JSON from Ollama's response."""
    text = raw.strip()

    # Strip markdown fences (```json ... ``` or ``` ... ```)
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()

    # Extract JSON object if there's surrounding text
    if not text.startswith("{"):
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            text = match.group(0).strip()

    try:
        data = json.loads(text)
        return AnalysisResult(
            summary=data.get("summary", "No summary provided"),
            severity=data.get("severity", "UNKNOWN").upper(),
            vulnerability_type=data.get("vulnerability_type", "Unknown"),
            affected_files=data.get("affected_files", []),
            root_cause=data.get("root_cause", ""),
            attack_vector=data.get("attack_vector", ""),
            proof_of_concept=data.get("proof_of_concept", ""),
            recommended_fix=data.get("recommended_fix", ""),
            cwe_id=data.get("cwe_id", ""),
            cvss_score=float(data.get("cvss_score", 0.0)),
            raw_response=raw
        )
    except json.JSONDecodeError as e:
        logger.warning(f"Could not parse JSON from LLM response: {e}")
        # Safely log raw response by encoding it
        safe_response = raw[:500].encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        logger.warning(f"Raw response was: {safe_response}")
        return AnalysisResult(
            summary="Analysis complete — could not parse structured output",
            severity="UNKNOWN",
            vulnerability_type="Unknown",
            affected_files=[],
            root_cause=raw,
            attack_vector="",
            proof_of_concept="",
            recommended_fix="",
            cwe_id="",
            cvss_score=0.0,
            raw_response=raw,
            error="LLM returned unstructured response"
        )


def _error_result(message: str) -> AnalysisResult:
    return AnalysisResult(
        summary=message,
        severity="UNKNOWN",
        vulnerability_type="Unknown",
        affected_files=[],
        root_cause="",
        attack_vector="",
        proof_of_concept="",
        recommended_fix="",
        cwe_id="",
        cvss_score=0.0,
        error=message
    )