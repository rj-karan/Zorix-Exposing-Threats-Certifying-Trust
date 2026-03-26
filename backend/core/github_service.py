import httpx
import json
from typing import Optional
from backend.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class GitHubService:
    """Service to interact with GitHub API."""

    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.headers = {"Accept": "application/vnd.github.v3.raw"}
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        self.client = None

    async def fetch_file_content(
        self, repo_url: str, file_path: str, branch: str = "main"
    ) -> Optional[str]:
        """
        Fetch file content from GitHub repository.

        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
            file_path: Path to file in repository
            branch: Branch to fetch from (default: main)

        Returns:
            File content as string, or None if fetch failed
        """
        try:
            # Extract owner and repo from URL
            parts = repo_url.rstrip("/").split("/")
            if len(parts) < 2:
                logger.error(f"Invalid repo URL: {repo_url}")
                return None

            owner = parts[-2]
            repo = parts[-1].replace(".git", "")

            # Construct GitHub API URL
            api_url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"

            async with httpx.AsyncClient() as client:
                params = {"ref": branch}
                response = await client.get(api_url, headers=self.headers, params=params, timeout=10.0)

                if response.status_code == 200:
                    try:
                        # GitHub API returns JSON with content in base64
                        data = response.json()
                        if "content" in data:
                            import base64

                            content = base64.b64decode(data["content"]).decode("utf-8")
                            logger.info(f"Successfully fetched {file_path} from {repo}")
                            return content
                        else:
                            # If raw response, return directly
                            return response.text
                    except json.JSONDecodeError:
                        # Raw content
                        return response.text
                elif response.status_code == 404:
                    logger.warning(f"File not found: {file_path} in {repo}")
                    return None
                else:
                    logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                    return None

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching {file_path} from {repo_url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching file from GitHub: {str(e)}")
            return None

    async def extract_code_context(
        self, repo_url: str, file_path: str, affected_line: Optional[int] = None, context_lines: int = 10
    ) -> Optional[dict]:
        """
        Extract code context around affected line.

        Args:
            repo_url: GitHub repository URL
            file_path: Path to file in repository
            affected_line: Line number (1-indexed) where issue is located
            context_lines: Number of lines before/after to include

        Returns:
            Dictionary with extracted code and line numbers, or None if fetch failed
        """
        content = await self.fetch_file_content(repo_url, file_path)
        if not content:
            return None

        lines = content.split("\n")
        total_lines = len(lines)

        if affected_line is None:
            # Return full file
            return {"file_path": file_path, "file_content": content, "affected_line": None, "total_lines": total_lines}

        # Validate affected line
        if affected_line < 1 or affected_line > total_lines:
            logger.warning(f"Affected line {affected_line} out of range (1-{total_lines})")
            affected_line = min(max(affected_line, 1), total_lines)

        # Calculate context range
        start_line = max(0, affected_line - 1 - context_lines)
        end_line = min(total_lines, affected_line + context_lines)

        extracted_lines = lines[start_line:end_line]
        line_numbers = list(range(start_line + 1, end_line + 1))

        context_code = "\n".join(
            [f"{ln}: {code}" for ln, code in zip(line_numbers, extracted_lines)]
        )

        return {
            "file_path": file_path,
            "file_content": content,
            "context_code": context_code,
            "affected_line": affected_line,
            "start_line": start_line + 1,
            "end_line": end_line,
            "total_lines": total_lines,
        }


# Singleton instance
github_service = GitHubService()
