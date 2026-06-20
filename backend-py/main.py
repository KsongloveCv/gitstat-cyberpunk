#!/usr/bin/env python3
"""
GitStat Netrunner Edition — Python Backend
FastAPI + uvicorn，零外部依赖（除 fastapi/uvicorn）
功能完全对齐 Go 版本后端
"""

import subprocess
import os
import sys
import json
import re
import time
import threading
import math
import urllib.request
import urllib.parse
import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path.home() / ".gitstat"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(str(LOG_DIR / "gitstat.log"), maxBytes=10*1024*1024, backupCount=3, encoding="utf-8"),
    ]
)
log = logging.getLogger('gitstat')

from datetime import datetime, timedelta, date
from typing import Optional
from collections import defaultdict

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from brotli_asgi import BrotliMiddleware
import uvicorn

# Import from refactored modules
import database
from git_utils import (
    git_exec, get_git_version, parse_git_log, run_git_log,
    git_log_cache, get_repo_meta, get_remote_url, get_repo_size,
    EXT_LANG_MAP, EXACT_NAME_MAP,
)
from store import store
from gitee import gitee_router, clone_gitee_repo, gitee_api, gitee_list_repos, gitee_get_repo
from weather import weather_router
from insights import insights_router
from github_module import github_router
from security import (
    check_rate_limit, rate_limit_or_429, validate_repo_path, validate_scan_path,
    validate_gitee_clone_url, safe_static_path, verify_api_key, clamp_limit,
    ALLOWED_ORIGINS, API_KEY,
)
from config import (
    VERSION, MAX_COMMITS_PER_REPO, DEFAULT_HOST, DEFAULT_PORT, FRONTEND_DIST,
    DEFAULT_SCAN_ROOT, SCAN_SKIP_DIR_NAMES,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FASTAPI APP


def scan_metadata(repo_path: str) -> Optional[dict]:
    """扫描单个仓库元数据（不获取 commits）。"""
    try:
        current_branch = git_exec(repo_path, "rev-parse", "--abbrev-ref", "HEAD")
        user_email = git_exec(repo_path, "config", "user.email")
        last_commit_time = ""
        out = git_exec(repo_path, "log", "-1", "--format=%ci")
        if out:
            try:
                t = datetime.strptime(out, "%Y-%m-%d %H:%M:%S %z")
                last_commit_time = t.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        return {
            "path": repo_path,
            "name": Path(repo_path).name,
            "currentBranch": current_branch,
            "userEmail": user_email,
            "lastCommitTime": last_commit_time,
        }
    except Exception as e:
        log.warning("Failed to extract repo meta for %s: %s", repo_path, e)
        return None


def resolve_scan_path(path: str) -> str:
    """解析扫描路径；若目录下无仓库则向上查找父目录。"""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return str(p)

    current = p
    for _ in range(5):
        if discover_repos(str(current)):
            return str(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return str(p)


def _should_skip_dir_name(name: str) -> bool:
    return name in SCAN_SKIP_DIR_NAMES or name == ".git"


def discover_repos(root_path: str) -> list[dict]:
    """递归扫描 root_path 下所有 Git 仓库（跳过系统/缓存目录）。"""
    root = Path(root_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return []

    repos: list[dict] = []
    seen: set[str] = set()

    def walk(base: Path) -> None:
        try:
            with os.scandir(base) as entries:
                for entry in entries:
                    if not entry.is_dir(follow_symlinks=False):
                        continue
                    name = entry.name
                    if _should_skip_dir_name(name):
                        continue
                    path = Path(entry.path)
                    if (path / ".git").is_dir():
                        resolved = str(path.resolve())
                        if resolved not in seen:
                            meta = scan_metadata(resolved)
                            if meta:
                                repos.append(meta)
                                seen.add(resolved)
                    walk(path)
        except (OSError, PermissionError) as exc:
            log.debug("Skip unreadable directory %s: %s", base, exc)

    walk(root)
    repos.sort(key=lambda r: r.get("lastCommitTime") or "", reverse=True)
    return repos


def get_repo_meta(repo_path: str) -> dict:
    """获取仓库元信息（分支数、文件数等）。"""
    current_branch = git_exec(repo_path, "rev-parse", "--abbrev-ref", "HEAD")
    branch_count = 0
    out = git_exec(repo_path, "for-each-ref", "refs/heads", "--format=%(refname:short)")
    if out:
        branch_count = len(out.split("\n"))
    file_count = 0
    out = git_exec(repo_path, "ls-tree", "-r", "HEAD", "--name-only")
    if out:
        file_count = len(out.split("\n"))
    last_commit_time = ""
    out = git_exec(repo_path, "log", "-1", "--format=%ci")
    if out:
        try:
            t = datetime.strptime(out, "%Y-%m-%d %H:%M:%S %z")
            last_commit_time = t.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return {
        "path": repo_path,
        "name": Path(repo_path).name,
        "currentBranch": current_branch,
        "branchCount": branch_count,
        "fileCount": file_count,
        "lastCommitTime": last_commit_time,
    }


def get_remote_url(repo_path: str) -> str:
    return git_exec(repo_path, "remote", "get-url", "origin")


def get_repo_size(repo_path: str) -> int:
    """通过 git ls-tree 计算仓库 blob 总大小。"""
    out = git_exec(repo_path, "ls-tree", "-r", "-l", "HEAD")
    if not out:
        return 0
    total = 0
    for line in out.split("\n"):
        if "\t" not in line:
            continue
        meta_part = line[: line.index("\t")]
        fields = meta_part.split()
        if len(fields) >= 4 and fields[1] == "blob":
            try:
                total += int(fields[3])
            except ValueError:
                pass
    return total


def analyze_repo_deep(repo_path: str) -> dict:
    """深度分析：分支列表、文件数、语言占比、代码行数。"""
    current_branch = git_exec(repo_path, "rev-parse", "--abbrev-ref", "HEAD")

    # 分支
    branch_names = []
    out = git_exec(repo_path, "for-each-ref", "refs/heads", "--format=%(refname:short)")
    if out:
        branches = [b.strip() for b in out.split("\n") if b.strip()]
        current = [b for b in branches if b == current_branch]
        others = sorted(b for b in branches if b != current_branch)
        branch_names = [f"{b} (current)" for b in current] + others
    if not branch_names:
        branch_names = [f"{current_branch} (current)"]

    # 文件列表
    out = git_exec(repo_path, "ls-tree", "-r", "HEAD", "--name-only", "-z")
    file_paths = [f for f in out.split("\x00") if f.strip()] if out else []

    # 语言统计
    lang_map: dict[str, dict] = {}
    total_lines = 0
    for rel in file_paths:
        ext = Path(rel).suffix.lower()
        base = Path(rel).name
        lang = EXACT_NAME_MAP.get(base) or EXT_LANG_MAP.get(ext, "Other")
        # 统计行数
        lines = 0
        full_path = os.path.join(repo_path, rel)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = sum(1 for _ in f)
        except (OSError, UnicodeDecodeError):
            pass
        total_lines += lines
        if lang not in lang_map:
            lang_map[lang] = {"name": lang, "fileCount": 0, "lines": 0, "percentage": 0}
        lang_map[lang]["fileCount"] += 1
        lang_map[lang]["lines"] += lines

    languages = []
    for ls in lang_map.values():
        if total_lines > 0:
            ls["percentage"] = round(ls["lines"] / total_lines * 100, 2)
        languages.append(ls)

    languages.sort(key=lambda x: x["lines"], reverse=True)

    return {
        "name": Path(repo_path).name,
        "path": repo_path,
        "branchCount": len(branch_names),
        "branches": branch_names,
        "fileCount": len(file_paths),
        "totalLines": total_lines,
        "languages": languages,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LAZY LOAD — 按需加载 commit 数据
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def ensure_data_loaded(repo_paths: list[str] = None, start_date: Optional[datetime] = None):
    """确保指定仓库的 commit 数据已加载（懒加载 + 增量更新）。"""
    caches = store.get_all_caches()
    if not caches:
        return

    now = datetime.now()
    for path, cache in caches.items():
        if repo_paths and path not in repo_paths:
            continue
        _ensure_repo_loaded(path, start_date, now)


def _ensure_repo_loaded(repo_path: str, start_date: Optional[datetime], now: datetime):
    """单个仓库的懒加载逻辑。"""
    ok, initialized, earliest, latest = store.check_init_range(repo_path)
    if not ok:
        return

    if not initialized:
        # 首次加载
        commits = run_git_log(repo_path, since=start_date, until=now)
        if commits:
            store.set_repo_commits(repo_path, commits)
        return

    # 已初始化 → 增量更新
    if start_date and earliest and earliest > start_date:
        new_commits = run_git_log(repo_path, since=start_date, until=earliest)
        if new_commits:
            store.merge_commits(repo_path, new_commits)

    if latest and now > latest:
        new_commits = run_git_log(repo_path, since=latest, until=now)
        if new_commits:
            store.merge_commits(repo_path, new_commits)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AGGREGATOR — 数据聚合
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _filter_commits(commits: list[dict], user_email: str = "",
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> list[dict]:
    """通用过滤函数。"""
    result = []
    for c in commits:
        if user_email and c["email"] != user_email:
            continue
        if start_date and c["date"] < start_date:
            continue
        if end_date and c["date"] > end_date:
            continue
        result.append(c)
    return result


def aggregate_overview(repos: list[dict], user_email: str = "",
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> dict:
    """概览统计。"""
    total_commits = 0
    total_additions = 0
    total_deletions = 0
    author_map: dict[str, dict] = {}
    repo_set = set()

    for repo in repos:
        repo_set.add(repo["path"])
        for c in _filter_commits(repo["commits"], user_email, start_date, end_date):
            total_commits += 1
            total_additions += c["additions"]
            total_deletions += c["deletions"]

            key = c["email"]
            if key not in author_map:
                author_map[key] = {
                    "author": c["author"], "email": c["email"],
                    "commits": 0, "additions": 0, "deletions": 0,
                    "netChange": 0, "isMe": c["email"] == user_email,
                }
            author_map[key]["commits"] += 1
            author_map[key]["additions"] += c["additions"]
            author_map[key]["deletions"] += c["deletions"]
            author_map[key]["netChange"] = author_map[key]["additions"] - author_map[key]["deletions"]

    # 计算平均提交大小
    author_list = list(author_map.values())
    for a in author_list:
        if a["commits"] > 0:
            a["avgCommitSize"] = round((a["additions"] + a["deletions"]) / a["commits"], 2)
        else:
            a["avgCommitSize"] = 0
    author_list.sort(key=lambda x: x["commits"], reverse=True)

    return {
        "totalCommits": total_commits,
        "totalAdditions": total_additions,
        "totalDeletions": total_deletions,
        "activeAuthors": len(author_map),
        "repositoryCount": len(repo_set),
        "authors": author_list,
    }


def aggregate_daily_stats(repos: list[dict], user_email: str = "",
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> list[dict]:
    """每日统计（按仓库 × 作者）。"""
    result = []
    for repo in repos:
        author_map: dict[str, dict] = {}
        daily_map: dict[str, dict[str, dict]] = defaultdict(dict)

        for c in _filter_commits(repo["commits"], user_email, start_date, end_date):
            commit_date = c["date"].strftime("%Y-%m-%d")
            key = c["email"]

            if key not in author_map:
                author_map[key] = {
                    "author": c["author"], "email": c["email"],
                    "commits": 0, "additions": 0, "deletions": 0,
                    "isMe": c["email"] == user_email,
                }
            author_map[key]["commits"] += 1
            author_map[key]["additions"] += c["additions"]
            author_map[key]["deletions"] += c["deletions"]

            if commit_date not in daily_map[key]:
                daily_map[key][commit_date] = {"date": commit_date, "commits": 0, "additions": 0, "deletions": 0}
            daily_map[key][commit_date]["commits"] += 1
            daily_map[key][commit_date]["additions"] += c["additions"]
            daily_map[key][commit_date]["deletions"] += c["deletions"]

        if author_map:
            authors = []
            for email, stats in author_map.items():
                daily = sorted(daily_map[email].values(), key=lambda x: x["date"])
                stats["dailyData"] = daily
                authors.append(stats)
            authors.sort(key=lambda x: x["commits"], reverse=True)
            result.append({
                "repoName": repo["name"],
                "repoPath": repo["path"],
                "currentBranch": repo["currentBranch"],
                "lastCommitTime": repo["lastCommitTime"],
                "authors": authors,
            })
    return result


def _get_week_key(dt: datetime) -> str:
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"


def _get_month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def _get_year_key(dt: datetime) -> str:
    return dt.strftime("%Y")


def _aggregate_period_stats(repos: list[dict], user_email: str,
                            start_date, end_date,
                            period_key_fn) -> list[dict]:
    """通用的周期性聚合（周/月/年）。"""
    result = []
    for repo in repos:
        author_map: dict[str, dict] = {}
        period_map: dict[str, dict[str, dict]] = defaultdict(dict)

        for c in _filter_commits(repo["commits"], user_email, start_date, end_date):
            pkey = period_key_fn(c["date"])
            key = c["email"]

            if key not in author_map:
                author_map[key] = {
                    "author": c["author"], "email": c["email"],
                    "commits": 0, "additions": 0, "deletions": 0,
                    "isMe": c["email"] == user_email,
                }
            author_map[key]["commits"] += 1
            author_map[key]["additions"] += c["additions"]
            author_map[key]["deletions"] += c["deletions"]

            if pkey not in period_map[key]:
                period_map[key][pkey] = {"date": pkey, "commits": 0, "additions": 0, "deletions": 0}
            period_map[key][pkey]["commits"] += 1
            period_map[key][pkey]["additions"] += c["additions"]
            period_map[key][pkey]["deletions"] += c["deletions"]

        if author_map:
            authors = []
            for email, stats in author_map.items():
                pd = sorted(period_map[email].values(), key=lambda x: x["date"])
                stats["dailyData"] = pd  # 前端字段名固定为 dailyData
                authors.append(stats)
            authors.sort(key=lambda x: x["commits"], reverse=True)
            result.append({
                "repoName": repo["name"],
                "repoPath": repo["path"],
                "currentBranch": repo["currentBranch"],
                "lastCommitTime": repo["lastCommitTime"],
                "authors": authors,
            })
    return result


def aggregate_author_rank(repos: list[dict], user_email: str = "",
                          start_date=None, end_date=None) -> list[dict]:
    """作者排行榜。"""
    author_map: dict[str, dict] = {}
    last_times: dict[str, datetime] = {}

    for repo in repos:
        for c in _filter_commits(repo["commits"], user_email, start_date, end_date):
            key = c["email"]
            if key not in author_map:
                author_map[key] = {
                    "author": c["author"], "email": c["email"],
                    "commits": 0, "additions": 0, "deletions": 0,
                    "netChange": 0, "isMe": c["email"] == user_email,
                }
            author_map[key]["commits"] += 1
            author_map[key]["additions"] += c["additions"]
            author_map[key]["deletions"] += c["deletions"]
            author_map[key]["netChange"] = author_map[key]["additions"] - author_map[key]["deletions"]
            if c["date"] > last_times.get(key, datetime.min):
                last_times[key] = c["date"]
                author_map[key]["lastCommitDate"] = c["date"].strftime("%Y-%m-%d %H:%M:%S")

    result = list(author_map.values())
    for a in result:
        if a["commits"] > 0:
            a["avgCommitSize"] = round((a["additions"] + a["deletions"]) / a["commits"], 2)
        else:
            a["avgCommitSize"] = 0
    result.sort(key=lambda x: x["commits"], reverse=True)
    return result


def aggregate_activity_heatmap(repos: list[dict], user_email: str = "",
                               start_date=None, end_date=None) -> list[dict]:
    """活动热力图（dayOfWeek × hour）。"""
    heatmap: dict[str, int] = defaultdict(int)
    for repo in repos:
        for c in _filter_commits(repo["commits"], user_email, start_date, end_date):
            key = f"{c['date'].weekday()}-{c['date'].hour}"  # 0=Mon, 6=Sun
            heatmap[key] += 1

    result = []
    for key, count in heatmap.items():
        dow, hour = key.split("-")
        result.append({"dayOfWeek": int(dow), "hour": int(hour), "commitCount": count})
    result.sort(key=lambda x: (x["dayOfWeek"], x["hour"]))
    return result


def aggregate_repo_comparison(repos: list[dict], user_email: str = "",
                              start_date=None, end_date=None) -> list[dict]:
    """仓库对比。"""
    result = []
    for repo in repos:
        commit_set = set()
        author_set = set()
        commits = 0
        additions = 0
        deletions = 0

        for c in _filter_commits(repo["commits"], user_email, start_date, end_date):
            commits += 1
            additions += c["additions"]
            deletions += c["deletions"]
            author_set.add(c["email"])
            commit_set.add(c["date"].strftime("%Y-%m-%d"))

        if commits > 0:
            active_days = len(commit_set)
            avg = round(commits / active_days, 1) if active_days else 0
            result.append({
                "repoName": repo["name"],
                "repoPath": repo["path"],
                "commits": commits,
                "authors": len(author_set),
                "additions": additions,
                "deletions": deletions,
                "lastCommitTime": repo["lastCommitTime"],
                "activeDays": active_days,
                "avgCommitsPerDay": avg,
            })

    result.sort(key=lambda x: x["commits"], reverse=True)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TIME RANGE — 解析预设时间范围
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_time_range(time_range: str) -> tuple[Optional[datetime], datetime]:
    """解析时间范围字符串，返回 (start, end)。"""
    now = datetime.now()

    if time_range == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now
    elif time_range == "week":
        days_from_monday = now.weekday()
        start = (now - timedelta(days=days_from_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        return start, now
    elif time_range == "lastWeek":
        days_from_monday = now.weekday() + 7
        last_monday = (now - timedelta(days=days_from_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        return last_monday, last_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
    elif time_range == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now
    elif time_range == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now
    else:
        return None, now  # all — 不限制起始日期


def parse_time_params(start_date_str: str = "", end_date_str: str = "",
                      time_range: str = "", default_range: str = "") \
        -> tuple[Optional[datetime], Optional[datetime]]:
    """组合解析时间参数。"""
    if start_date_str and end_date_str:
        try:
            start = datetime.strptime(start_date_str, "%Y-%m-%d")
            end = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
            return start, end
        except ValueError:
            raise HTTPException(400, "Invalid date format, use YYYY-MM-DD")

    tr = time_range or default_range
    return parse_time_range(tr)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  UTILS — 统一响应 + 简易限流
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def ok(data=None, message: str = ""):
    """统一成功响应。"""
    return JSONResponse({"code": 200, "data": data, "message": message})


def err(code: int, message: str):
    """统一错误响应。"""
    return JSONResponse({"code": code, "message": message}, status_code=code)


rate_limited = JSONResponse(
    {"code": 429, "message": "Too many requests"}, status_code=429
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FASTAPI APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

app = FastAPI(
    title="GitStat Netrunner Edition",
    version=VERSION,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if not API_KEY else ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/") and not verify_api_key(request):
        return JSONResponse({"code": 401, "message": "Invalid API key"}, status_code=401)
    return await call_next(request)

# Brotli compression middleware
app.add_middleware(BrotliMiddleware, quality=6)

# Security headers middleware
@app.middleware("http")
async def security_headers_mw(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Path traversal guard
def _validate_path(p: str) -> str:
    resolved = Path(p).resolve()
    if ".." in p or not resolved.exists():
        raise HTTPException(400, "Invalid path")
    return str(resolved)

# Register module routes
app.include_router(gitee_router)
app.include_router(weather_router)
app.include_router(insights_router)
app.include_router(github_router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        content={"code": 500, "message": "Internal server error"},
        status_code=500
    )


def _load_repos(repo_paths: list[str] = None) -> list[dict]:
    """获取仓库列表，可选按路径筛选。"""
    repos = store.get_repositories()
    if repo_paths:
        path_set = set(repo_paths)
        repos = [r for r in repos if r["path"] in path_set]
    return repos


def _resolve_user_email(repos: list[dict], email: str = "") -> str:
    if email:
        return email
    for r in repos:
        if r.get("userEmail"):
            return r["userEmail"]
    return ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  API ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/api/scan/path")
def api_get_scan_path():
    path = store.get_scan_path()
    return {
        "code": 200,
        "data": {
            "path": path,
            "version": get_git_version(),
        },
    }


@app.post("/api/scan/path")
async def api_set_scan_path(request: Request):
    blocked = rate_limit_or_429("scan_path", 10, 60)
    if blocked:
        return blocked
    body = await request.json()
    path = body.get("path", "")
    validate_scan_path(path)
    resolved = await asyncio.to_thread(resolve_scan_path, path)
    store.clear_all()
    database.clear_repo_data()
    store.set_scan_path(resolved)
    database.save_scan_path(resolved)
    repos = await asyncio.to_thread(discover_repos, resolved)
    store.register_repos(repos)

    message = "Path set successfully, data will be loaded on demand"
    if resolved != str(Path(path).expanduser().resolve()):
        message = f"No repos in {path}; using parent directory {resolved}"

    return {
        "code": 200,
        "data": {"path": resolved},
        "message": message,
    }


@app.post("/api/scan/refresh")
def api_scan_refresh():
    """增量刷新：发现新仓库并拉取最新提交，不清空缓存。"""
    blocked = rate_limit_or_429("scan_refresh", 20, 60)
    if blocked:
        return blocked
    scan_root = store.get_scan_path()
    if not scan_root:
        raise HTTPException(400, "No scan path configured")
    discovered = discover_repos(scan_root)
    store.register_repos(discovered)
    now = datetime.now()
    for repo in discovered:
        _ensure_repo_loaded(repo["path"], None, now)
    return {"code": 200, "data": {"repoCount": len(discovered)}, "message": "Refresh complete"}


@app.get("/api/user/identity")
def api_user_identity():
    """返回当前用户邮箱（从已注册仓库的 git config 聚合）。"""
    emails = []
    for cache in store.get_all_caches().values():
        if cache.get("userEmail"):
            emails.append(cache["userEmail"])
    primary = emails[0] if emails else ""
    return {"code": 200, "data": {"email": primary, "emails": list(dict.fromkeys(emails))}}


@app.get("/api/repositories")
def api_get_repositories(includeCommits: bool = Query(default=False)):
    repos = store.get_repositories(include_commits=includeCommits)
    return {"code": 200, "data": repos}


@app.get("/api/repos/list")
def api_get_repos_list():
    caches = store.get_all_caches()
    infos = []
    for cache in caches.values():
        infos.append({
            "path": cache["path"],
            "name": cache["name"],
            "currentBranch": cache["currentBranch"],
            "branchCount": cache["branchCount"],
            "fileCount": cache["fileCount"],
            "lastCommitTime": cache["lastCommitTime"],
            "remoteUrl": cache["remoteUrl"],
        })
    infos.sort(key=lambda x: x["name"])
    return infos


@app.get("/api/repos/info")
def api_get_repo_info(path: str = Query(...)):
    path = validate_repo_path(path, store.registered_paths())
    cache = store.get_repo_cache(path)
    if not cache:
        raise HTTPException(404, "repo not found")

    branch_count = cache["branchCount"]
    file_count = cache["fileCount"]
    remote_url = cache["remoteUrl"]

    if branch_count == 0:
        info = get_repo_meta(path)
        branch_count = info["branchCount"]
        file_count = info["fileCount"]
        store.update_repo(path, branchCount=branch_count, fileCount=file_count)

    if not remote_url:
        remote_url = get_remote_url(path)
        cache["remoteUrl"] = remote_url

    return {
        "path": cache["path"],
        "name": cache["name"],
        "currentBranch": cache["currentBranch"],
        "branchCount": branch_count,
        "fileCount": file_count,
        "lastCommitTime": cache["lastCommitTime"],
        "remoteUrl": remote_url,
    }


@app.get("/api/repos/stats")
def api_get_repo_stats(path: str = Query(...)):
    path = validate_repo_path(path, store.registered_paths())
    cache = store.get_repo_cache(path)
    if not cache:
        raise HTTPException(404, "repo not found")

    repo = {"path": cache["path"], "name": cache["name"], "commits": cache["commits"],
            "currentBranch": cache["currentBranch"], "lastCommitTime": cache["lastCommitTime"],
            "userEmail": cache["userEmail"]}
    rank = aggregate_author_rank([repo], "")
    contributors = []
    for item in rank:
        contributors.append({
            "author": item["author"], "email": item["email"],
            "commitCount": item["commits"], "additions": item["additions"],
            "deletions": item["deletions"], "lastCommitDate": item.get("lastCommitDate", ""),
        })

    # 最近 20 条提交，按时间倒序
    all_commits = sorted(cache["commits"], key=lambda c: c["date"], reverse=True)
    recent = all_commits[:20]

    earliest_date = cache["earliestDate"].strftime("%Y-%m-%d %H:%M:%S") if cache["earliestDate"] else ""
    earliest_author = ""
    if cache["commits"]:
        earliest = min(cache["commits"], key=lambda c: c["date"])
        earliest_author = earliest["author"]

    repo_size = cache["repoSize"]
    if repo_size == 0:
        repo_size = get_repo_size(path)
        store.update_repo(path, repoSize=repo_size)

    stats = {
        "path": cache["path"],
        "name": cache["name"],
        "currentBranch": cache["currentBranch"],
        "lastCommitTime": cache["lastCommitTime"],
        "earliestDate": earliest_date,
        "earliestCommitAuthor": earliest_author,
        "repoSize": repo_size,
        "recentCommits": recent,
        "contributors": contributors,
    }

    if cache["analyzed"]:
        stats["analysis"] = {
            "name": cache["name"], "path": cache["path"],
            "branchCount": cache["branchCount"], "branches": cache["branches"],
            "fileCount": cache["fileCount"], "totalLines": cache["totalLines"],
            "languages": cache["languages"],
        }

    return stats


@app.post("/api/repos/analyze")
async def api_repo_analyze(request: Request):
    body = await request.json()
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "Path is required")
    blocked = rate_limit_or_429("analyze", 10, 60)
    if blocked:
        return blocked
    path = validate_repo_path(path, store.registered_paths())

    cache = store.get_repo_cache(path)
    if cache and cache["analyzed"]:
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


# ---- 统计接口 ----

@app.get("/api/stats/overview")
def api_stats_overview(
    repo: list[str] = Query(default=[]),
    startDate: str = "",
    endDate: str = "",
    email: str = "",
    range: str = "",
):
    start, end = parse_time_params(startDate, endDate, range, "today")
    ensure_data_loaded(repo, start)
    repos = _load_repos(repo)
    user = _resolve_user_email(repos, email)
    return aggregate_overview(repos, user, start, end)


@app.get("/api/stats/daily")
def api_stats_daily(
    repo: list[str] = Query(default=[]),
    email: str = "",
    range: str = "",
    startDate: str = "",
    endDate: str = "",
):
    start, end = parse_time_params(startDate, endDate, range)
    ensure_data_loaded(repo, start)
    repos = _load_repos(repo)
    user = _resolve_user_email(repos, email)
    return aggregate_daily_stats(repos, user, start, end)


@app.get("/api/stats/weekly")
def api_stats_weekly(
    repo: list[str] = Query(default=[]),
    email: str = "",
    range: str = "",
    startDate: str = "",
    endDate: str = "",
):
    start, end = parse_time_params(startDate, endDate, range)
    ensure_data_loaded(repo, start)
    repos = _load_repos(repo)
    user = _resolve_user_email(repos, email)
    return _aggregate_period_stats(repos, user, start, end, _get_week_key)


@app.get("/api/stats/monthly")
def api_stats_monthly(
    repo: list[str] = Query(default=[]),
    email: str = "",
    range: str = "",
    startDate: str = "",
    endDate: str = "",
):
    start, end = parse_time_params(startDate, endDate, range)
    ensure_data_loaded(repo, start)
    repos = _load_repos(repo)
    user = _resolve_user_email(repos, email)
    return _aggregate_period_stats(repos, user, start, end, _get_month_key)


@app.get("/api/stats/yearly")
def api_stats_yearly(
    repo: list[str] = Query(default=[]),
    email: str = "",
    range: str = "",
    startDate: str = "",
    endDate: str = "",
):
    start, end = parse_time_params(startDate, endDate, range)
    ensure_data_loaded(repo, start)
    repos = _load_repos(repo)
    user = _resolve_user_email(repos, email)
    return _aggregate_period_stats(repos, user, start, end, _get_year_key)


@app.get("/api/stats/authors")
def api_stats_authors(
    repo: list[str] = Query(default=[]),
    range: str = "",
    startDate: str = "",
    endDate: str = "",
):
    start, end = parse_time_params(startDate, endDate, range, "week")
    ensure_data_loaded(repo, start)
    repos = _load_repos(repo)
    user = _resolve_user_email(repos, "")
    return aggregate_author_rank(repos, user, start, end)


@app.get("/api/stats/activity-heatmap")
def api_stats_heatmap(
    repo: list[str] = Query(default=[]),
    startDate: str = "",
    endDate: str = "",
):
    start, end = parse_time_params(startDate, endDate, "month")
    ensure_data_loaded(repo, start)
    repos = _load_repos(repo)
    user = _resolve_user_email(repos, "")
    return aggregate_activity_heatmap(repos, user, start, end)


@app.get("/api/stats/repo-comparison")
def api_stats_repo_comparison(
    repo: list[str] = Query(default=[]),
    range: str = "",
    startDate: str = "",
    endDate: str = "",
):
    start, end = parse_time_params(startDate, endDate, range, "month")
    ensure_data_loaded(repo, start)
    repos = _load_repos(repo)
    user = _resolve_user_email(repos, "")
    return aggregate_repo_comparison(repos, user, start, end)


# ---- 数据导出 ----

@app.post("/api/export/json")
async def api_export(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    include_commits = body.get("includeCommits", True)
    repos = store.get_repositories(include_commits=include_commits)
    payload = {"code": 200, "exportedAt": datetime.now().isoformat(), "repos": repos}
    return Response(
        content=json.dumps(payload, default=str, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=gitstat-data.json"},
    )


@app.get("/api/export/csv")
def api_export_csv(repos: Optional[str] = Query(None), startDate: str = Query(""), endDate: str = Query("")):
    """导出提交数据为 CSV 格式。"""
    import csv, io
    start, end = parse_time_params(startDate, endDate, "year", "")
    repo_list = _load_repos(repos.split(",") if repos else None)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["仓库", "作者", "邮箱", "日期", "消息", "新增", "删除", "哈希"])
    for r in repo_list:
        for c in _filter_commits(r["commits"], "", start, end):
            writer.writerow([r["name"], c["author"], c["email"], c["date"].strftime("%Y-%m-%d %H:%M:%S"), c["message"], c["additions"], c["deletions"], c["hash"]])
    return Response(content=output.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=gitstat-export.csv"})


# ---- 提交详情列表 ----

@app.get("/api/stats/commit-list")
def api_commit_list(
    repo: list[str] = Query(default=[]),
    startDate: str = "",
    endDate: str = "",
    range: str = "",
    email: str = "",
    limit: int = Query(default=50),
    offset: int = Query(default=0),
):
    """返回指定时间范围内的提交详情列表（按时间倒序）。"""
    limit = clamp_limit(limit)
    offset = max(0, offset)
    start, end = parse_time_params(startDate, endDate, range, "today")
    ensure_data_loaded(repo, start)
    repos = _load_repos(repo)
    user = _resolve_user_email(repos, email)

    all_commits = []
    for r in repos:
        branch = r.get("currentBranch", "")
        for c in _filter_commits(r["commits"], user, start, end):
            all_commits.append({
                "hash": c["hash"],
                "author": c["author"],
                "email": c["email"],
                "date": c["date"].strftime("%Y-%m-%d %H:%M:%S"),
                "message": c["message"],
                "additions": c["additions"],
                "deletions": c["deletions"],
                "repoName": r["name"],
                "repoPath": r["path"],
                "branch": branch,
                "netChange": c["additions"] - c["deletions"],
            })

    all_commits.sort(key=lambda c: c["date"], reverse=True)
    return all_commits[offset: offset + limit]


@app.get("/api/stats/commits/search")
def api_search_commits(
    q: str = "",
    repo: str = "",
    email: str = "",
    limit: int = Query(default=50),
    offset: int = Query(default=0),
):
    """在 SQLite 缓存中搜索提交记录。"""
    return {
        "code": 200,
        "data": database.search_commits(
            query=q, repo_path=repo, email=email,
            limit=clamp_limit(limit), offset=max(0, offset),
        ),
    }


@app.get("/api/stats/summary")
def api_stats_summary(range: str = Query(default="week")):
    """CI/脚本友好的简要统计摘要。"""
    start, end = parse_time_params("", "", range, "week")
    ensure_data_loaded([], start)
    repos = _load_repos([])
    user = _resolve_user_email(repos, "")
    overview = aggregate_overview(repos, user, start, end)
    return {
        "code": 200,
        "data": {
            "range": range,
            "totalCommits": overview.get("totalCommits", 0),
            "totalAdditions": overview.get("totalAdditions", 0),
            "totalDeletions": overview.get("totalDeletions", 0),
            "repositoryCount": overview.get("repositoryCount", 0),
            "activeAuthors": overview.get("activeAuthors", 0),
        },
    }


# ---- 版本 + 健康检查 ----

@app.get("/api/version")
def api_version():
    return {"version": f"git {get_git_version()}"}


@app.get("/health")
def api_health():
    return "OK"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TOKEN ANALYTICS — 模型Token消耗统计
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 模型价格表（每1K tokens的美元价格） ──
MODEL_PRICING = {
    # OpenAI
    "gpt-4o":          {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":     {"input": 0.15,  "output": 0.60},
    "gpt-4-turbo":     {"input": 10.00, "output": 30.00},
    "gpt-4":           {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo":   {"input": 0.50,  "output": 1.50},
    "o1":              {"input": 15.00, "output": 60.00},
    "o1-mini":         {"input": 3.00,  "output": 12.00},
    "o1-pro":          {"input": 150.00, "output": 600.00},
    "o3":              {"input": 2.00,  "output": 8.00},
    "o3-mini":         {"input": 1.10,  "output": 4.40},
    "o4-mini":         {"input": 1.10,  "output": 4.40},
    # Anthropic
    "claude-sonnet-4":       {"input": 3.00,  "output": 15.00},
    "claude-opus-4":         {"input": 15.00, "output": 75.00},
    "claude-3.5-sonnet":     {"input": 3.00,  "output": 15.00},
    "claude-3.5-haiku":      {"input": 0.80,  "output": 4.00},
    "claude-3-opus":         {"input": 15.00, "output": 75.00},
    "claude-3-haiku":        {"input": 0.25,  "output": 1.25},
    # Google
    "gemini-2.5-pro":   {"input": 1.25,  "output": 10.00},
    "gemini-2.5-flash": {"input": 0.15,  "output": 0.60},
    "gemini-2.0-flash": {"input": 0.10,  "output": 0.40},
    "gemini-1.5-pro":   {"input": 1.25,  "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    # DeepSeek
    "deepseek-chat":    {"input": 0.27,  "output": 1.10},
    "deepseek-reasoner":{"input": 0.55,  "output": 2.19},
    "deepseek-v3":      {"input": 0.27,  "output": 1.10},
    "deepseek-v4-pro":  {"input": 0.55,  "output": 2.19},
    # Meta
    "llama-3.1-405b":   {"input": 2.40,  "output": 2.40},
    "llama-3.1-70b":    {"input": 0.26,  "output": 0.26},
    "llama-3.1-8b":     {"input": 0.03,  "output": 0.03},
    # Mistral
    "mistral-large":    {"input": 2.00,  "output": 6.00},
    "mistral-medium":   {"input": 0.75,  "output": 2.25},
    "mistral-small":    {"input": 0.15,  "output": 0.45},
    # 阿里云 DashScope
    "glm-5":            {"input": 0.50,  "output": 2.00},
    "glm-5.1":          {"input": 0.50,  "output": 2.00},
    "qwen-max":         {"input": 0.80,  "output": 2.00},
    "qwen-plus":        {"input": 0.40,  "output": 1.20},
    "qwen-turbo":       {"input": 0.10,  "output": 0.30},
}


def _parse_token_log(scan_path: str) -> list[dict]:
    """
    扫描目录中的 token 使用日志文件。
    支持多种格式：
    1. JSON日志（每行一个JSON对象）
    2. CSV日志
    3. Hermes Agent 的 session 日志
    
    查找路径：
    - scan_path 下所有 .token-log / .token_usage 文件
    - ~/.hermes/logs/ 下的 token 日志
    - ~/.hermes/cache/ 下含 token 数据的文件
    """
    records = []
    
    # 扫描 Hermes session 日志
    hermes_dir = Path.home() / ".hermes"
    sessions_dir = hermes_dir / "sessions"
    cache_dir = hermes_dir / "cache"
    
    token_dirs = [sessions_dir, cache_dir]
    
    for d in token_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                # 尝试从 Hermes session JSON 中提取 token 信息
                if isinstance(data, dict):
                    # 检查是否有 token 用量字段
                    usage = data.get("usage") or data.get("token_usage") or {}
                    model = data.get("model") or data.get("model_name") or ""
                    timestamp = data.get("timestamp") or data.get("created_at") or data.get("date") or ""
                    
                    if usage and model:
                        # 提取 input/output tokens
                        input_t = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
                        output_t = usage.get("completion_tokens") or usage.get("output_tokens") or usage.get("generated_tokens") or 0
                        
                        if input_t > 0 or output_t > 0:
                            # 清理模型名称
                            model_clean = _clean_model_name(model)
                            records.append({
                                "model": model_clean,
                                "input": input_t,
                                "output": output_t,
                                "timestamp": timestamp,
                            })
            except Exception as e:
                log.debug("Failed to parse Hermes session file %s: %s", f, e)
                continue

    # 扫描项目目录下的 token 日志
    for pattern in ["*.token-log", "*.token_usage", "token_log*.json", "token_log*.csv"]:
        for f in Path(scan_path).rglob(pattern):
            try:
                if f.suffix == ".json":
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    if isinstance(data, list):
                        for item in data:
                            model = item.get("model") or ""
                            input_t = item.get("input_tokens") or item.get("prompt_tokens") or 0
                            output_t = item.get("output_tokens") or item.get("completion_tokens") or 0
                            ts = item.get("timestamp") or item.get("date") or ""
                            if model and (input_t > 0 or output_t > 0):
                                records.append({
                                    "model": _clean_model_name(model),
                                    "input": input_t,
                                    "output": output_t,
                                    "timestamp": ts,
                                })
                    elif isinstance(data, dict):
                        model = data.get("model") or ""
                        input_t = data.get("input_tokens") or data.get("prompt_tokens") or 0
                        output_t = data.get("output_tokens") or data.get("completion_tokens") or 0
                        ts = data.get("timestamp") or data.get("date") or ""
                        if model and (input_t > 0 or output_t > 0):
                            records.append({"model": _clean_model_name(model), "input": input_t, "output": output_t, "timestamp": ts})
                elif f.suffix == ".csv":
                    import csv
                    with open(f, "r", encoding="utf-8") as fh:
                        reader = csv.DictReader(fh)
                        for row in reader:
                            model = row.get("model") or ""
                            input_t = int(row.get("input_tokens") or row.get("prompt_tokens") or 0)
                            output_t = int(row.get("output_tokens") or row.get("completion_tokens") or 0)
                            ts = row.get("timestamp") or row.get("date") or ""
                            if model and (input_t > 0 or output_t > 0):
                                records.append({"model": _clean_model_name(model), "input": input_t, "output": output_t, "timestamp": ts})
            except Exception as e:
                log.debug("Failed to parse token log: %s", e)
                continue
    
    return records


def _clean_model_name(raw: str) -> str:
    """清理模型名称，去除提供商前缀和版本后缀冗余。"""
    m = raw.strip().lower()
    # 去除常见前缀
    for prefix in ["openai/", "anthropic/", "google/", "deepseek/", "meta/", "mistral/", "dashscope/"]:
        if m.startswith(prefix):
            m = m[len(prefix):]
    return m


def _parse_token_timestamp(ts: str, today: date) -> date:
    """解析多种格式的时间戳，返回 date 对象。"""
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(ts[:26], fmt).date()
        except ValueError:
            continue
    return today


def _filter_token_records(records: list[dict], cutoff: date, model_filter, today: date) -> list[dict]:
    """按模型和时间范围过滤 token 记录。"""
    filtered = []
    for r in records:
        if model_filter and model_filter != "all" and r["model"] != model_filter:
            continue
        dt = _parse_token_timestamp(r.get("timestamp", ""), today) if r.get("timestamp") else today
        if dt < cutoff:
            continue
        r["_date"] = dt.strftime("%Y-%m-%d")
        filtered.append(r)
    return filtered or _generate_demo_token_data(today, cutoff, model_filter)


def _calc_token_costs(model_agg: dict) -> tuple[float, list[dict]]:
    """计算每个模型的成本和排名。"""
    total_cost = 0.0
    model_rank = []
    for m, agg in model_agg.items():
        pricing = MODEL_PRICING.get(m, {"input": 1.00, "output": 3.00})
        cost = (agg["input"] / 1000) * pricing["input"] + (agg["output"] / 1000) * pricing["output"]
        total_cost += cost
        model_rank.append({"model": m, "input": agg["input"], "output": agg["output"], "cost": round(cost, 4)})
    model_rank.sort(key=lambda x: x["input"] + x["output"], reverse=True)
    return total_cost, model_rank


def _aggregate_token_stats(records: list[dict], time_range: str, model_filter: Optional[str] = None) -> dict:
    """聚合 token 统计数据，含效率指标、成本预测、时段对比、对话Top10、热力图。"""
    today = date.today()
    range_map = {
        "thisWeek": timedelta(weeks=1), "lastWeek": timedelta(weeks=2),
        "thisMonth": timedelta(days=30), "lastMonth": timedelta(days=60),
        "thisYear": timedelta(days=365), "customPeriod": timedelta(days=365*2),
    }
    cutoff = today - range_map.get(time_range, timedelta(days=365))
    range_days = (today - cutoff).days
    prev_cutoff = cutoff - timedelta(days=range_days)

    filtered = _filter_token_records(records, cutoff, model_filter, today)
    prev_filtered = _filter_token_records(records, prev_cutoff, model_filter, cutoff)
    all_filtered = _filter_token_records(records, today - timedelta(days=365), model_filter, today)

    if not filtered:
        filtered = _generate_demo_token_data(today, cutoff, model_filter)
        prev_filtered = _generate_demo_token_data(cutoff - timedelta(days=1), prev_cutoff, model_filter)
        all_filtered = _generate_demo_token_data(today, today - timedelta(days=365), model_filter)

    total_input = sum(r["input"] for r in filtered)
    total_output = sum(r["output"] for r in filtered)
    total_tokens = total_input + total_output

    # ── 模型维度聚合 + 使用频次 ──
    model_agg: dict[str, dict] = {}
    model_sessions: dict[str, int] = {}
    for r in filtered:
        m = r["model"]
        model_agg.setdefault(m, {"input": 0, "output": 0})
        model_agg[m]["input"] += r["input"]
        model_agg[m]["output"] += r["output"]
        model_sessions[m] = model_sessions.get(m, 0) + 1

    total_cost, model_rank = _calc_token_costs(model_agg)

    # ── 效率指标 ──
    models_efficiency = []
    best_value_model = ""
    best_value_per_dollar = 0.0
    for m, agg in model_agg.items():
        pricing = MODEL_PRICING.get(m, {"input": 1.00, "output": 3.00})
        cost = (agg["input"] / 1000) * pricing["input"] + (agg["output"] / 1000) * pricing["output"]
        ratio = round(agg["output"] / max(agg["input"], 1), 3)
        per_dollar = round((agg["input"] + agg["output"]) / max(cost, 0.001), 1)
        models_efficiency.append({"model": m, "ratio": ratio, "perDollar": per_dollar})
        if per_dollar > best_value_per_dollar:
            best_value_per_dollar = per_dollar
            best_value_model = m
    avg_ratio = round(sum(e["ratio"] for e in models_efficiency) / max(len(models_efficiency), 1), 3)

    # ── 趋势数据（含成本） ──
    trend_map: dict[str, dict] = {}
    for r in filtered:
        ds = r.get("_date", "")
        trend_map.setdefault(ds, {"input": 0, "output": 0, "cost": 0.0})
        trend_map[ds]["input"] += r["input"]
        trend_map[ds]["output"] += r["output"]
        pricing = MODEL_PRICING.get(r["model"], {"input": 1.00, "output": 3.00})
        trend_map[ds]["cost"] += (r["input"] / 1000) * pricing["input"] + (r["output"] / 1000) * pricing["output"]
    trend = [{"date": k, "input": v["input"], "output": v["output"], "cost": round(v["cost"], 4)} for k, v in sorted(trend_map.items())]

    # ── 成本预测 ──
    days_in_range = max((today - cutoff).days, 1)
    daily_avg_cost = total_cost / days_in_range
    mid_point = len(trend) // 2
    if mid_point > 0 and len(trend) > mid_point:
        first_daily = sum(t["cost"] for t in trend[:mid_point]) / mid_point
        second_daily = sum(t["cost"] for t in trend[mid_point:]) / max(len(trend) - mid_point, 1)
        if second_daily > first_daily * 1.1:
            trend_dir = "up"
        elif second_daily < first_daily * 0.9:
            trend_dir = "down"
        else:
            trend_dir = "stable"
    else:
        trend_dir = "stable"
    monthly_estimate = round(daily_avg_cost * 30, 2)

    # ── 时段对比 ──
    prev_total_tokens = sum(r["input"] + r["output"] for r in prev_filtered)
    prev_total_cost = 0.0
    for r in prev_filtered:
        pricing = MODEL_PRICING.get(r["model"], {"input": 1.00, "output": 3.00})
        prev_total_cost += (r["input"] / 1000) * pricing["input"] + (r["output"] / 1000) * pricing["output"]
    change_pct = round(((total_tokens - prev_total_tokens) / max(prev_total_tokens, 1)) * 100, 1) if prev_total_tokens > 0 else 0.0

    # ── 对话Top10 ──
    session_agg = {}
    for r in filtered:
        sid = r.get("session_id") or f"{r.get('_date', 'unknown')}_{r['model']}"
        if sid not in session_agg:
            session_agg[sid] = {"sessionId": sid, "model": r["model"], "input": 0, "output": 0, "date": r.get("_date", "")}
        session_agg[sid]["input"] += r["input"]
        session_agg[sid]["output"] += r["output"]
    top_sessions = []
    for s in session_agg.values():
        pricing = MODEL_PRICING.get(s["model"], {"input": 1.00, "output": 3.00})
        cost = (s["input"] / 1000) * pricing["input"] + (s["output"] / 1000) * pricing["output"]
        s["cost"] = round(cost, 4)
        top_sessions.append(s)
    top_sessions.sort(key=lambda x: x["input"] + x["output"], reverse=True)
    top_sessions = top_sessions[:10]

    # ── 热力图数据 ──
    heat_map = {}
    for r in (all_filtered if all_filtered else filtered):
        ds = r.get("_date", "")
        heat_map[ds] = heat_map.get(ds, 0) + r["input"] + r["output"]
    heat_days = min((today - (today - timedelta(days=365))).days, 365)
    heatmap_data = []
    for i in range(heat_days):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        heatmap_data.append({"date": ds, "tokens": heat_map.get(ds, 0), "isToday": d == today})

    return {
        "totalInput": total_input, "totalOutput": total_output,
        "totalTokens": total_tokens, "totalCost": round(total_cost, 2),
        "modelRank": model_rank, "trend": trend,
        "availableModels": list(model_agg.keys()),
        # ── 新增字段 ──
        "efficiency": {
            "averageRatio": avg_ratio,
            "bestValueModel": best_value_model,
            "bestValuePerDollar": best_value_per_dollar,
            "modelsEfficiency": models_efficiency,
        },
        "costPrediction": {
            "monthlyEstimate": monthly_estimate,
            "dailyAvg": round(daily_avg_cost, 2),
            "trendDirection": trend_dir,
        },
        "periodComparison": {
            "currentPeriod": {"total": total_tokens, "cost": round(total_cost, 2)},
            "previousPeriod": {"total": prev_total_tokens, "cost": round(prev_total_cost, 2)},
            "changePercent": change_pct,
        },
        "topSessions": top_sessions,
        "heatmapData": heatmap_data,
        "modelSessions": model_sessions,
    }


def _generate_demo_token_data(today: date, cutoff: date, model_filter: Optional[str] = None) -> list[dict]:
    """生成演示 token 数据（用于无真实日志时的展示）。"""
    import random
    random.seed(42)
    
    demo_models = [
        "gpt-4o", "gpt-4o-mini", "claude-sonnet-4", "claude-3.5-sonnet",
        "glm-5.1", "deepseek-v4-pro", "gemini-2.5-pro", "gemini-2.5-flash",
        "qwen-max", "o3-mini",
    ]
    
    if model_filter and model_filter != "all":
        demo_models = [m for m in demo_models if m == model_filter]
    
    records = []
    days = min((today - cutoff).days, 60)
    for i in range(days):
        d = today - timedelta(days=i)
        for m in demo_models:
            # 不同模型有不同的典型用量
            base_input = random.randint(500, 8000)
            base_output = random.randint(200, 4000)
            # 大模型用量更大
            if "4o" in m and "mini" not in m:
                base_input *= 2; base_output *= 2
            if "opus" in m or "o1-pro" in m:
                base_input *= 4; base_output *= 4
            if "flash" in m or "mini" in m:
                base_input //= 2; base_output //= 2
            
            records.append({
                "model": m,
                "input": base_input,
                "output": base_output,
                "timestamp": d.strftime("%Y-%m-%dT%H:%M:%S"),
                "_date": d.strftime("%Y-%m-%d"),
            })
    return records


@app.get("/api/stats/tokens")
async def token_stats(
    range: str = Query("thisWeek", alias="range"),
    model: Optional[str] = Query(None),
):
    """Token 消耗统计 API。"""
    scan_dir = store.scan_path or os.getcwd()
    records = _parse_token_log(scan_dir)
    source = "logs" if records else "demo"
    result = _aggregate_token_stats(records, range, model)
    return JSONResponse({"data": result, "source": source})




# ── 预算管理 ──
BUDGET_FILE = Path.home() / ".hermes" / "token_budget.json"

def _read_budget() -> dict:
    if BUDGET_FILE.exists():
        try:
            with open(BUDGET_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"monthlyBudget": 100.0}

def _write_budget(data: dict) -> None:
    BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BUDGET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

@app.get("/api/stats/tokens/budget")
async def get_budget():
    budget_cfg = _read_budget()
    monthly = budget_cfg.get("monthlyBudget", 100.0)
    scan_dir = store.scan_path or os.getcwd()
    records = _parse_token_log(scan_dir)
    result = _aggregate_token_stats(records, "thisMonth", None)
    current_spent = result.get("totalCost", 0.0)
    pct = round(current_spent / max(monthly, 0.01) * 100, 1)
    return JSONResponse({
        "monthlyBudget": monthly, "currentSpent": current_spent,
        "percentUsed": pct, "isOverBudget": current_spent > monthly,
    })

@app.post("/api/stats/tokens/budget")
async def set_budget(request: Request):
    body = await request.json()
    monthly = body.get("monthlyBudget")
    if monthly is None:
        raise HTTPException(400, "monthlyBudget is required")
    budget_cfg = _read_budget()
    budget_cfg["monthlyBudget"] = float(monthly)
    _write_budget(budget_cfg)
    return JSONResponse({"success": True, "monthlyBudget": budget_cfg["monthlyBudget"]})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STREAK — 连续贡献天数统计
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_daily_commit_map(repo_list: list, repos_filter: Optional[list] = None) -> dict[str, int]:
    """按日期聚合所有作者的提交次数。"""
    daily_map: dict[str, int] = {}
    for repo in repo_list:
        if repos_filter and repo.get("repoPath") not in repos_filter and repo.get("repoName") not in repos_filter:
            continue
        for author in (repo.get("authors") or []):
            for day in (author.get("dailyData") or []):
                ds = day.get("date", "")
                if ds:
                    daily_map[ds] = daily_map.get(ds, 0) + day.get("commits", 0)
    return daily_map


def _calc_contribution_calendar(repo_list: list, repos_filter: Optional[list] = None,
                                days: int = 365) -> dict:
    """最近 N 天每日提交数（GitHub 贡献图数据源）。"""
    daily_map = _build_daily_commit_map(repo_list, repos_filter)
    today = date.today()
    range_start = today - timedelta(days=days - 1)

    cells = []
    total = 0
    cur = range_start
    while cur <= today:
        ds = cur.strftime("%Y-%m-%d")
        commits = daily_map.get(ds, 0)
        total += commits
        cells.append({
            "date": ds,
            "commits": commits,
            "isToday": cur == today,
        })
        cur += timedelta(days=1)

    return {
        "totalContributions": total,
        "days": days,
        "cells": cells,
    }


def _calc_streak(repo_list: list, repos_filter: Optional[list] = None) -> dict:
    """
    计算连续贡献天数（current streak / longest streak / weekly active / last 30 days）。
    基于 daily 统计数据，从今天往前回溯。
    """
    today = date.today()
    daily_map = _build_daily_commit_map(repo_list, repos_filter)

    # ---- 连续天数计算 ----
    streak_current = 0
    streak_longest = 0
    streak_running = 0
    checked = today

    # 检查今天是否有提交（从今天开始往前算）
    # 如果今天还没结束但已有提交，也算
    while True:
        ds = checked.strftime("%Y-%m-%d")
        if ds in daily_map and daily_map[ds] > 0:
            streak_current += 1
            streak_running = max(streak_running, streak_current)
            checked -= timedelta(days=1)
        else:
            # 如果是今天且今天还没有提交，可能是当天还没提交
            # 继续往前看（不中断连续）
            if checked == today:
                checked -= timedelta(days=1)
                continue
            else:
                # 如果是昨天也没有提交，中断
                # 但为了"当前连续"的准确性：如果今天没有提交但昨天有，
                # current streak = 昨天的连续数
                if checked == today - timedelta(days=1) and streak_current == 0:
                    # 今天没提交，从昨天开始重新检查
                    while True:
                        ds = checked.strftime("%Y-%m-%d")
                        if ds in daily_map and daily_map[ds] > 0:
                            streak_current += 1
                            streak_running = max(streak_running, streak_current)
                            checked -= timedelta(days=1)
                        else:
                            break
                break

    # 计算最长连续（从所有日期中扫描）
    all_dates = sorted(daily_map.keys(), reverse=True)
    longest_running = 0
    prev_date = None
    for ds in all_dates:
        if daily_map[ds] > 0:
            d = datetime.strptime(ds, "%Y-%m-%d").date()
            if prev_date and (prev_date - d).days == 1:
                longest_running += 1
            else:
                longest_running = 1
            prev_date = d
        else:
            longest_running = 0
            prev_date = None
    streak_longest = max(streak_longest, longest_running)

    # 当前连续：如果今天有提交就是 streak_current，否则看是否昨天开始的连续
    # 上面的逻辑已经处理了

    # ---- 本周活跃天数 ----
    week_start = today - timedelta(days=today.weekday())
    weekly_active = 0
    for i in range(7):
        ds = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        if ds in daily_map and daily_map[ds] > 0:
            weekly_active += 1

    # ---- 最近30天每日数据 ----
    last30 = []
    for i in range(30):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        last30.append({
            "date": ds,
            "commits": daily_map.get(ds, 0),
            "isToday": i == 0,
        })
    # 反转使日期从旧到新（左旧右新）
    last30.reverse()

    return {
        "current": streak_current,
        "longest": max(streak_longest, streak_current),
        "weeklyActiveDays": weekly_active,
        "last30Days": last30,
    }


@app.get("/api/stats/streak")
async def streak_stats(
    repo: Optional[str] = Query(None),
):
    """连续贡献天数统计 API。"""
    repos_filter = None
    if repo:
        repos_filter = [repo]

    start, end = parse_time_range("year")
    repo_paths = repos_filter if repos_filter else []
    ensure_data_loaded(repo_paths, start)
    repos = _load_repos(repo_paths)
    user = _resolve_user_email(repos, "")
    repo_list = aggregate_daily_stats(repos, user, start, end)
    result = _calc_streak(repo_list, repos_filter)
    return JSONResponse({"data": result})


@app.get("/api/stats/contribution-calendar")
async def contribution_calendar(
    repo: Optional[str] = Query(None),
    days: int = Query(365, ge=30, le=366),
):
    """最近 N 天贡献日历（GitHub 风格热力图）。"""
    repos_filter = [repo] if repo else []
    start = datetime.now() - timedelta(days=days)
    end = datetime.now()
    ensure_data_loaded(repos_filter, start)
    repos = _load_repos(repos_filter)
    user = _resolve_user_email(repos, "")
    repo_list = aggregate_daily_stats(repos, user, start, end)
    result = _calc_contribution_calendar(repo_list, repos_filter if repo else None, days)
    return JSONResponse({"data": result})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STATIC FILES — 前端 SPA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_frontend_dist = FRONTEND_DIST
_has_static = _frontend_dist.exists() and (_frontend_dist / "index.html").exists()

_MIME_MAP = {
    ".html": "text/html", ".js": "text/javascript",
    ".css": "text/css", ".svg": "image/svg+xml",
    ".json": "application/json", ".png": "image/png",
    ".ico": "image/x-icon", ".webp": "image/webp",
    ".woff2": "font/woff2", ".woff": "font/woff",
}

if _has_static:

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 如果路径匹配已有 API 路由，FastAPI 不会走到这里
        # 安全兜底：尝试作为静态文件返回
        file_path = safe_static_path(_frontend_dist, full_path)
        if file_path:
            ext = file_path.suffix.lower()
            media = _MIME_MAP.get(ext, "application/octet-stream")
            return FileResponse(file_path, media_type=media)

        # 其余所有路径 → index.html（SPA fallback）
        return FileResponse(
            _frontend_dist / "index.html",
            media_type="text/html",
            headers={"Cache-Control": "no-cache"},
        )


def open_browser(url: str):
    """自动打开浏览器。"""
    import platform
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", url])
        elif system == "Windows":
            subprocess.Popen(["cmd", "/c", "start", url])
        else:
            subprocess.Popen(["xdg-open", url])
    except Exception as e:
        log.debug("Failed to open browser: %s", e)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import argparse

    # Initialize SQLite database
    database.init_db()

    parser = argparse.ArgumentParser(
        description="GitStat Netrunner Edition — Python Backend"
    )
    parser.add_argument("scan_path", nargs="?", default=None,
                        help=f"Git 仓库扫描目录（默认: 已保存路径或 {DEFAULT_SCAN_ROOT}）")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help="监听端口（默认: 12580）")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST,
                        help="监听地址（默认: 127.0.0.1，远程访问用 0.0.0.0）")
    parser.add_argument("--no-browser", action="store_true",
                        help="不自动打开浏览器")
    args = parser.parse_args()

    # Prefer a saved path that still contains repos; otherwise resolve cwd/arg
    saved_path = database.get_scan_path()
    resolved_saved = resolve_scan_path(saved_path) if saved_path else ""
    if args.scan_path is not None:
        args.scan_path = resolve_scan_path(args.scan_path)
    elif resolved_saved and discover_repos(resolved_saved):
        args.scan_path = resolved_saved
    else:
        args.scan_path = resolve_scan_path(DEFAULT_SCAN_ROOT)
    database.save_scan_path(args.scan_path)
    store.set_scan_path(args.scan_path)
    repos = discover_repos(args.scan_path)
    store.register_repos(repos)
    discovered_paths = {r["path"] for r in repos}

    # Restore cached repos from DB (only those under current scan path)
    db_repos = database.load_repos()
    for db_repo in db_repos:
        if db_repo["path"] not in discovered_paths:
            continue
        if db_repo["path"] not in store.repos:
            store.repos[db_repo["path"]] = {
                "path": db_repo["path"], "name": db_repo["name"],
                "userEmail": db_repo["userEmail"],
                "currentBranch": db_repo["currentBranch"],
                "lastCommitTime": db_repo["lastCommitTime"],
                "initialized": True, "commits": [],
                "earliestDate": None, "latestDate": None,
                "branchCount": db_repo["branchCount"],
                "fileCount": db_repo["fileCount"],
                "remoteUrl": db_repo["remoteUrl"],
                "repoSize": db_repo["repoSize"],
                "analyzed": db_repo["analyzed"],
                "branches": db_repo["branches"],
                "totalLines": db_repo["totalLines"],
                "languages": db_repo["languages"],
            }
            # Hydrate commits from DB
            commits = database.load_commits(db_repo["path"])
            if commits:
                store.set_repo_commits(db_repo["path"], commits)

    print(f"Registered {len(repos)} repos from {args.scan_path} "
          f"(restored {len(db_repos)} from database)")

    url = f"http://localhost:{args.port}"
    print(f"GitStat Web Server (Python)")
    print(f"Scan directory: {args.scan_path}")
    print(f"Listening on {url}")

    if not args.no_browser:
        open_browser(url)

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
