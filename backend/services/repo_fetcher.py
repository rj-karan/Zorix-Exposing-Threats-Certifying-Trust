"""
Repository Fetcher Service
Fetches source code from GitHub repositories for analysis.
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid as uuid_mod
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

import httpx

from backend.config import get_settings
from backend.core.logger import pipeline_logger, log_to_db

logger = logging.getLogger(__name__)
settings = get_settings()

# File extensions worth analyzing
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php",
    ".c", ".cpp", ".cs", ".env", ".yml", ".yaml", ".json",
    ".sh", ".bash", ".sql", ".tf", ".toml", ".ini", ".cfg",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "dist", "build",
    "venv", ".venv", "vendor", "coverage", ".pytest_cache",
    ".next", ".nuxt", "target",
}

MAX_FILE_SIZE_BYTES = 50_000  # 50KB per file
MAX_FILES = 50


async def fetch_repository(
    repo_url: str,
    snapshot_id: Optional[str] = None,
    github_token: Optional[str] = None,
    db=None,
    analysis_id=None,
) -> Dict:
    """
    Fetch repository source code for analysis.

    Tries git clone first, falls back to GitHub API.

    Returns:
        { snapshot_path, commit_hash, file_list, file_count, files }
    """
    snapshot_id = snapshot_id or str(uuid_mod.uuid4())
    token = github_token or settings.GITHUB_TOKEN
    snapshot_dir = Path(settings.SNAPSHOT_DIR) / snapshot_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    pipeline_logger.info(
        f"Fetching repository: {repo_url}",
        stage="FETCHING",
        analysis_id=str(analysis_id) if analysis_id else None,
    )

    # Try git clone first
    files = {}
    commit_hash = None

    try:
        files, commit_hash = await _try_git_clone(repo_url, snapshot_dir, token)
    except Exception as e:
        logger.warning(f"Git clone failed, falling back to API: {e}")

    # Fallback to GitHub API
    if not files:
        try:
            files = await _fetch_via_github_api(repo_url, token)
            commit_hash = "api-fetch"
        except Exception as e:
            logger.error(f"GitHub API fetch also failed: {e}")
            if db and analysis_id:
                await log_to_db(
                    db, "ERROR",
                    f"Failed to fetch repository: {e}",
                    stage="FETCHING",
                    analysis_id=analysis_id,
                )
            raise RuntimeError(f"Failed to fetch repository {repo_url}: {e}")

    # Save files to disk
    for fpath, content in files.items():
        target = snapshot_dir / fpath
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.write_text(content, encoding="utf-8")
        except Exception:
            pass

    file_list = list(files.keys())

    pipeline_logger.info(
        f"Fetched {len(file_list)} files, commit: {commit_hash}",
        stage="FETCHING",
        analysis_id=str(analysis_id) if analysis_id else None,
    )

    return {
        "snapshot_path": str(snapshot_dir),
        "commit_hash": commit_hash,
        "file_list": file_list,
        "file_count": len(file_list),
        "files": files,
    }


async def _try_git_clone(
    repo_url: str, snapshot_dir: Path, token: Optional[str]
) -> tuple:
    """Attempt to git clone the repository."""
    clone_url = repo_url
    if token and "github.com" in repo_url:
        parts = repo_url.replace("https://", "").replace("http://", "")
        clone_url = f"https://{token}@{parts}"

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, tmpdir + "/repo"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"git clone failed: {result.stderr}")

        repo_path = Path(tmpdir) / "repo"

        # Get commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(repo_path),
        )
        commit_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else "unknown"

        # Collect files
        files = {}
        for fpath in repo_path.rglob("*"):
            if not fpath.is_file():
                continue
            rel = fpath.relative_to(repo_path)
            if any(skip in rel.parts for skip in SKIP_DIRS):
                continue
            if fpath.suffix not in ALLOWED_EXTENSIONS:
                continue
            if fpath.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
            if len(files) >= MAX_FILES:
                break
            try:
                files[str(rel)] = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        # Copy to snapshot dir
        for fpath in repo_path.rglob("*"):
            if fpath.is_file():
                rel = fpath.relative_to(repo_path)
                if any(skip in rel.parts for skip in SKIP_DIRS):
                    continue
                dest = snapshot_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(str(fpath), str(dest))
                except Exception:
                    pass

        return files, commit_hash


async def _fetch_via_github_api(
    repo_url: str, token: Optional[str]
) -> dict:
    """Fetch files via GitHub REST API."""
    from urllib.parse import urlparse

    path = urlparse(repo_url).path.strip("/")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    owner, repo = parts[0], parts[1]

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30) as client:
        # Get default branch
        repo_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=headers,
        )
        repo_resp.raise_for_status()
        default_branch = repo_resp.json().get("default_branch", "main")

        # Get tree
        tree_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1",
            headers=headers,
        )
        tree_resp.raise_for_status()
        tree_items = [
            item
            for item in tree_resp.json().get("tree", [])
            if item.get("type") == "blob"
        ]

        files = {}
        for item in tree_items:
            if len(files) >= MAX_FILES:
                break
            fpath = item.get("path", "")
            if any(skip in fpath.split("/") for skip in SKIP_DIRS):
                continue
            if not any(fpath.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                continue
            if item.get("size", 0) > MAX_FILE_SIZE_BYTES:
                continue

            try:
                import base64

                content_resp = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/contents/{fpath}",
                    headers=headers,
                )
                content_resp.raise_for_status()
                data = content_resp.json()
                encoded = data.get("content", "")
                if encoded:
                    files[fpath] = base64.b64decode(encoded).decode(
                        "utf-8", errors="replace"
                    )
            except Exception:
                continue

        return files
