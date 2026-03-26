import httpx
import base64
from urllib.parse import urlparse
import os

# File extensions worth analyzing
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".go", ".rb", ".php",
    ".c", ".cpp", ".cs", ".env", ".yml", ".yaml", ".json",
    ".sh", ".bash", ".sql", ".tf", ".toml", ".ini", ".cfg"
}

# Skip these folders entirely
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "dist", "build",
    "venv", ".venv", "vendor", "coverage", ".pytest_cache"
}

MAX_FILE_SIZE_BYTES = 5_000   # 20KB per file
MAX_FILES = 5                  # Max files to fetch per repo


def parse_repo_info(repo_url: str) -> tuple[str, str]:
    """Extract owner and repo name from GitHub URL."""
    path = urlparse(repo_url).path.strip("/")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    return parts[0], parts[1]


async def fetch_repo_files(repo_url: str, github_token: str | None = None) -> dict[str, str]:
    """
    Fetch all analyzable files from a GitHub repo.
    Returns dict of { file_path: file_content }
    """
    owner, repo = parse_repo_info(repo_url)

    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    async with httpx.AsyncClient(timeout=30) as client:
        tree = await _get_file_tree(client, headers, owner, repo)
        files = {}

        for item in tree:
            if len(files) >= MAX_FILES:
                break

            path: str = item.get("path", "")

            # Skip unwanted dirs
            if any(skip in path.split("/") for skip in SKIP_DIRS):
                continue

            # Only allowed extensions
            if not any(path.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                continue

            # Skip large files
            if item.get("size", 0) > MAX_FILE_SIZE_BYTES:
                continue

            content = await _fetch_file_content(client, headers, owner, repo, path)
            if content:
                files[path] = content

        return files


async def _get_file_tree(client: httpx.AsyncClient, headers: dict, owner: str, repo: str) -> list:
    """Get full recursive file tree from GitHub API."""
    # First get default branch
    repo_resp = await client.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers=headers
    )
    repo_resp.raise_for_status()
    default_branch = repo_resp.json().get("default_branch", "main")

    # Get tree recursively
    tree_resp = await client.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1",
        headers=headers
    )
    tree_resp.raise_for_status()
    return [item for item in tree_resp.json().get("tree", []) if item.get("type") == "blob"]


async def _fetch_file_content(
    client: httpx.AsyncClient,
    headers: dict,
    owner: str,
    repo: str,
    path: str
) -> str | None:
    """Fetch and decode a single file's content."""
    try:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        encoded = data.get("content", "")
        if encoded:
            return base64.b64decode(encoded).decode("utf-8", errors="replace")
    except Exception:
        return None
    return None