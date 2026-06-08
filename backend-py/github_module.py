"""GitHub API — repository statistics."""
import json
import re
import time as _time
import urllib.request as ur
from fastapi import APIRouter, Query, HTTPException

github_router = APIRouter(prefix="/api/github", tags=["github"])

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = __import__("os").environ.get("GITHUB_TOKEN", "")


def _github_request(url: str) -> dict:
    headers = {"User-Agent": "GitStat/2.0", "Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = ur.Request(url, headers=headers)
    with ur.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


@github_router.get("/repos")
def github_list_repos(
    owner: str = Query(..., description="GitHub username or org"),
    page: int = Query(default=1),
    perPage: int = Query(default=30),
):
    """List public repos for a GitHub user/org."""
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', owner):
        raise HTTPException(400, "Invalid owner name")

    try:
        raw = _github_request(f"{GITHUB_API_BASE}/users/{owner}/repos?page={page}&per_page={perPage}&sort=updated")
    except Exception:
        try:
            raw = _github_request(f"{GITHUB_API_BASE}/orgs/{owner}/repos?page={page}&per_page={perPage}&sort=updated")
        except Exception as e:
            raise HTTPException(502, f"GitHub API error: {e}")

    if not isinstance(raw, list):
        return {"code": 200, "data": []}

    repos = [{
        "id": r.get("id"), "name": r.get("name"), "fullName": r.get("full_name"),
        "description": r.get("description", ""), "htmlUrl": r.get("html_url"),
        "cloneUrl": r.get("clone_url"), "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0), "language": r.get("language", ""),
        "updatedAt": r.get("updated_at", ""), "pushedAt": r.get("pushed_at", ""),
        "owner": r.get("owner", {}).get("login", owner),
    } for r in raw]

    return {"code": 200, "data": repos}


@github_router.get("/repos/info")
def github_repo_info(owner: str = Query(...), repo: str = Query(...)):
    """Get single repo info."""
    try:
        r = _github_request(f"{GITHUB_API_BASE}/repos/{owner}/{repo}")
    except Exception as e:
        raise HTTPException(502, f"GitHub API error: {e}")

    return {"code": 200, "data": {
        "id": r.get("id"), "name": r.get("name"), "fullName": r.get("full_name"),
        "description": r.get("description", ""), "htmlUrl": r.get("html_url"),
        "cloneUrl": r.get("clone_url"), "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0), "language": r.get("language", ""),
        "defaultBranch": r.get("default_branch", "main"),
        "topics": r.get("topics", []),
        "license": r.get("license", {}).get("spdx_id", "") if r.get("license") else "",
    }}
