"""Security helpers — path validation, static file safety, rate limits."""
import os
import re
import time
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

# Optional API key (set GITSTAT_API_KEY to enable)
API_KEY = os.environ.get("GITSTAT_API_KEY", "")
ALLOWED_ORIGINS = os.environ.get(
    "GITSTAT_CORS_ORIGINS",
    "http://127.0.0.1:12580,http://localhost:12580,http://127.0.0.1:5173,http://localhost:5173",
).split(",")

GITEE_CLONE_PATTERN = re.compile(
    r"^https://gitee\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?$"
)

_rate_store: dict[str, list[float]] = {}


def check_rate_limit(key: str, max_req: int = 60, window: int = 60) -> bool:
    now = time.time()
    bucket = [t for t in _rate_store.get(key, []) if now - t < window]
    if len(bucket) >= max_req:
        return False
    bucket.append(now)
    _rate_store[key] = bucket
    return True


def rate_limit_or_429(key: str, max_req: int = 60, window: int = 60):
    if not check_rate_limit(key, max_req, window):
        return JSONResponse({"code": 429, "message": "Too many requests"}, status_code=429)
    return None


def validate_repo_path(path: str, registered_paths: set[str]) -> str:
    """Ensure path is an absolute registered repo before git operations."""
    if not path:
        raise HTTPException(400, "path is required")
    resolved = str(Path(path).expanduser().resolve())
    if resolved not in registered_paths:
        raise HTTPException(403, "Repository not registered; scan path first")
    return resolved


def validate_scan_path(path: str) -> str:
    if not path:
        raise HTTPException(400, "Path is required")
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise HTTPException(400, f"Path does not exist: {path}")
    if not resolved.is_dir():
        raise HTTPException(400, f"Path is not a directory: {path}")
    return str(resolved)


def validate_gitee_clone_url(url: str) -> str:
    url = url.strip()
    if not GITEE_CLONE_PATTERN.match(url):
        raise HTTPException(400, "cloneUrl must be a https://gitee.com/owner/repo.git URL")
    return url


def safe_static_path(base: Path, relative: str) -> Optional[Path]:
    """Resolve static asset path; return None if outside base (path traversal)."""
    if not relative or relative == "/":
        return None
    try:
        candidate = (base / relative).resolve()
        base_resolved = base.resolve()
        if not str(candidate).startswith(str(base_resolved)):
            return None
        if candidate.is_file():
            return candidate
    except (ValueError, OSError):
        return None
    return None


def verify_api_key(request: Request) -> bool:
    if not API_KEY:
        return True
    header = request.headers.get("X-GitStat-Key", "")
    return header == API_KEY


def clamp_limit(limit: int, default: int = 50, maximum: int = 500) -> int:
    if limit <= 0:
        return default
    return min(limit, maximum)
