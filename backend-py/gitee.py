"""Gitee API — 码云代码统计模块."""
import json
import re
import urllib.request
import subprocess
import shutil
from pathlib import Path
import time
from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import JSONResponse
from store import store
from git_utils import run_git_log, get_repo_meta

GITEE_API_BASE = "https://gitee.com/api/v5"
GITEE_CACHE_DIR = Path.home() / ".gitstat-gitee-cache"
GITEE_ACCESS_TOKEN = __import__("os").environ.get("GITEE_TOKEN", "")

# Rate limiting
_rate_bucket: list = []

def _check_rate(max_req=30, window=60):
    """Simple sliding-window rate limiter for Gitee API calls."""
    now = time.time()
    global _rate_bucket
    _rate_bucket = [t for t in _rate_bucket if now - t < window]
    if len(_rate_bucket) >= max_req:
        raise HTTPException(429, "Too many requests, slow down")
    _rate_bucket.append(now)

def gitee_api(path: str) -> dict:
    """调用 Gitee Open API v5，返回 JSON。支持可选的 GITEE_TOKEN 认证。"""
    url = f"{GITEE_API_BASE}{path}"
    if "?" in path:
        url += f"&access_token={GITEE_ACCESS_TOKEN}" if GITEE_ACCESS_TOKEN else ""
    else:
        url += f"?access_token={GITEE_ACCESS_TOKEN}" if GITEE_ACCESS_TOKEN else ""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "GitStat/2.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(503, f"Gitee API unavailable: {e}")


def gitee_list_repos(owner: str, page: int = 1, per_page: int = 30) -> list[dict]:
    """获取某用户/组织的公开仓库列表（先尝试组织，再尝试用户）。"""
    raw = None
    # 先尝试组织
    try:
        raw = gitee_api(f"/orgs/{owner}/repos?page={page}&per_page={per_page}&sort=updated")
    except HTTPException:
        pass
    # 如果组织不成功，尝试用户
    if raw is None or not isinstance(raw, list):
        try:
            raw = gitee_api(f"/users/{owner}/repos?page={page}&per_page={per_page}&sort=updated")
        except HTTPException:
            pass
    if not isinstance(raw, list):
        return []
    return [{
        "id": r.get("id"),
        "name": r.get("name"),
        "fullName": r.get("full_name"),
        "description": r.get("description", ""),
        "htmlUrl": r.get("html_url", "").replace(".git", ""),
        "sshUrl": r.get("ssh_url"),
        "cloneUrl": f"https://gitee.com/{r.get('full_name')}.git",
        "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0),
        "language": r.get("language", ""),
        "owner": owner,
        "updatedAt": r.get("updated_at", ""),
        "pushedAt": r.get("pushed_at", ""),
        "createdAt": r.get("created_at", ""),
    } for r in raw]


def gitee_get_repo(owner: str, repo: str) -> dict:
    """获取单个仓库信息。"""
    r = gitee_api(f"/repos/{owner}/{repo}")
    return {
        "id": r.get("id"),
        "name": r.get("name"),
        "fullName": r.get("full_name"),
        "description": r.get("description", ""),
        "htmlUrl": r.get("html_url"),
        "sshUrl": r.get("ssh_url"),
        "cloneUrl": r.get("clone_url"),
        "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0),
        "language": r.get("language", ""),
        "updatedAt": r.get("updated_at", ""),
        "pushedAt": r.get("pushed_at", ""),
        "createdAt": r.get("created_at", ""),
        "commitsCount": r.get("commits_count", 0),
        "watchers": r.get("watchers_count", 0),
        "defaultBranch": r.get("default_branch", "master"),
    }


def clone_gitee_repo(clone_url: str, owner: str, repo: str) -> dict:
    """Clone 一个 Gitee 仓库到本地缓存目录，返回路径信息。"""
    GITEE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target_dir = GITEE_CACHE_DIR / f"{owner}_{repo}"

    if target_dir.exists():
        # 已存在则 pull
        try:
            subprocess.run(
                ["git", "-C", str(target_dir), "pull", "--ff-only"],
                capture_output=True, text=True, timeout=60
            )
        except (subprocess.TimeoutExpired, OSError):
            pass
    else:
        # Clone
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "100", clone_url, str(target_dir)],
                capture_output=True, text=True, timeout=120
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "Clone timed out")
        except OSError as e:
            raise HTTPException(500, f"Clone failed: {e}")

        if result.returncode != 0:
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)
            raise HTTPException(400, f"Clone failed: {result.stderr}")

    return {
        "path": str(target_dir),
        "name": repo,
        "owner": owner,
        "cloneUrl": clone_url,
    }


def gitee_load_commits(repo_path: str) -> list[dict]:
    """在已 clone 的 Gitee 仓库上运行 git log 解析。"""
    return run_git_log(repo_path)

gitee_router = APIRouter(prefix="/api/gitee", tags=["gitee"])

#  GITEE — 码云代码统计 API Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@gitee_router.get("/repos")
def api_gitee_list_repos(
    owner: str = Query(..., description="Gitee 用户名或组织名"),
    page: int = Query(default=1),
    perPage: int = Query(default=30),
):
    """代理 Gitee API：获取某用户/组织的仓库列表。"""
    _check_rate(max_req=30, window=60)
    if not owner or not re.match(r'^[a-zA-Z0-9_-]+$', owner):
        raise HTTPException(400, "Invalid owner name")
    try:
        repos = gitee_list_repos(owner, page, perPage)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Gitee API error: {e}")
    return {"code": 200, "data": repos}


@gitee_router.get("/repos/info")
def api_gitee_repo_info(
    owner: str = Query(...),
    repo: str = Query(...),
):
    """获取单个 Gitee 仓库详情。"""
    try:
        info = gitee_get_repo(owner, repo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Gitee API error: {e}")
    return {"code": 200, "data": info}


@gitee_router.post("/repos/clone")
async def api_gitee_clone(request: Request):
    """Clone Gitee 仓库到本地缓存，注册到 Store，返回基础提交统计。"""
    body = await request.json()
    owner = body.get("owner", "")
    repo_name = body.get("repo", "")
    clone_url = body.get("cloneUrl", "")

    if not clone_url and owner and repo_name:
        clone_url = f"https://gitee.com/{owner}/{repo_name}.git"
    if not clone_url:
        raise HTTPException(400, "cloneUrl is required")

    # Extract owner/repo from clone_url if not provided
    if not owner or not repo_name:
        m = re.search(r'gitee\.com/([^/]+)/([^/]+?)(?:\.git)?$', clone_url)
        if m:
            owner, repo_name = m.group(1), m.group(2)
        else:
            owner, repo_name = "unknown", clone_url.split("/")[-1].replace(".git", "")

    # Clone to cache
    clone_result = clone_gitee_repo(clone_url, owner, repo_name)
    local_path = clone_result["path"]

    # Parse git log
    commits = run_git_log(local_path)

    # Register in Store so existing stats APIs work
    repo_meta = get_repo_meta(local_path)
    store.register_repos([{
        "path": local_path,
        "name": f"[Gitee] {owner}/{repo_name}",
        "userEmail": "",
        "currentBranch": repo_meta.get("currentBranch", "master"),
        "lastCommitTime": repo_meta.get("lastCommitTime", ""),
    }])
    store.set_repo_commits(local_path, commits)

    return {
        "code": 200,
        "data": {
            "path": local_path,
            "name": f"{owner}/{repo_name}",
            "commitCount": len(commits),
            "cloneUrl": clone_url,
        },
        "message": "Clone and parse complete",
    }


@gitee_router.post("/repos/analyze")
async def api_gitee_analyze(request: Request):
    """对已 clone 的 Gitee 仓库进行深度分析（复用现有逻辑）。"""
    body = await request.json()
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "path is required")

    cache = store.get_repo_cache(path)
    if not cache:
        raise HTTPException(404, "Repo not found. Clone first.")

    if cache.get("analyzed"):
        return {
            "name": cache["name"], "path": cache["path"],
            "branchCount": cache["branchCount"], "branches": cache["branches"],
            "fileCount": cache["fileCount"], "totalLines": cache["totalLines"],
            "languages": cache["languages"],
        }

    result = analyze_repo_deep(path)
    store.update_repo(
        path,
        branchCount=result["branchCount"],
        branches=result["branches"],
        fileCount=result["fileCount"],
        totalLines=result["totalLines"],
        languages=result["languages"],
        analyzed=True,
    )
    return result


@gitee_router.post("/repos/remove")
async def api_gitee_remove(request: Request):
    """从 Store 中移除已加载的 Gitee 仓库（不删除本地缓存文件）。"""
    body = await request.json()
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "path is required")
    cache = store.get_repo_cache(path)
    if cache:
        cache["initialized"] = False
        cache["commits"] = []
        cache["analyzed"] = False
    return {"code": 200, "message": "Repo removed from memory"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
