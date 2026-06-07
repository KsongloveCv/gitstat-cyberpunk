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
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format='%(levelname)s [%(name)s] %(message)s')
log = logging.getLogger('gitstat')

# Simple TTL cache for expensive operations
class TTLCache:
    """Thread-safe TTL cache with dict interface."""

    def __init__(self, ttl_seconds: float = 300):
        self._ttl = ttl_seconds
        self._data: dict[str, tuple[float, any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._data.get(key)
            if entry:
                ts, val = entry
                if time.time() - ts < self._ttl:
                    return val
                del self._data[key]
            return None

    def set(self, key: str, value: any):
        with self._lock:
            self._data[key] = (time.time(), value)

    def clear(self):
        with self._lock:
            self._data.clear()

git_log_cache = TTLCache(ttl_seconds=300)  # 5 min cache for git log results
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
    git_log_cache, get_repo_meta, get_remote_url, get_repo_size, EXT_LANG_MAP
)
from store import Store, store
from gitee import gitee_router, gitee_api, gitee_list_repos, gitee_get_repo, clone_gitee_repo, gitee_load_commits

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VERSION = "2.0.0-py"
MAX_COMMITS_PER_REPO = 5000
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

# Gitee API
GITEE_API_BASE = "https://gitee.com/api/v5"
GITEE_CACHE_DIR = Path.home() / ".gitstat-gitee-cache"
GITEE_ACCESS_TOKEN = os.environ.get("GITEE_TOKEN", "")  # 可选：设置环境变量提高限速


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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GIT EXEC — 调用 git 命令
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def git_exec(repo_path: str, *args: str) -> str:
    """在指定仓库路径执行 git 命令，返回 stdout 字符串。"""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.rstrip("\n\r ")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def get_git_version() -> str:
    """获取本机 git 版本号。"""
    try:
        out = subprocess.run(
            ["git", "--version"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
        m = re.search(r"\d+\.\d+\.\d+", out)
        return f"git {m.group()}" if m else out
    except Exception as e:
        log.warning("Failed to detect git version: %s", e)
        return "git not found"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STORE — 线程安全的内存仓库存储
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Store:
    """全局仓库缓存，线程安全。"""

    def __init__(self):
        self._lock = threading.RLock()
        self.scan_path = ""
        self.repos: dict[str, dict] = {}  # path -> repo_cache

    # ---- 扫描路径 ----
    def set_scan_path(self, path: str):
        with self._lock:
            self.scan_path = path

    def get_scan_path(self) -> str:
        with self._lock:
            return self.scan_path

    # ---- 仓库管理 ----
    def clear_all(self):
        with self._lock:
            self.scan_path = ""
            self.repos.clear()

    def register_repos(self, repo_list: list[dict]):
        """注册仓库元数据（未初始化，等待懒加载）。"""
        with self._lock:
            for repo in repo_list:
                rp = repo["path"]
                self.repos[rp] = {
                    "path": rp,
                    "name": repo.get("name", Path(rp).name),
                    "userEmail": repo.get("userEmail", ""),
                    "currentBranch": repo.get("currentBranch", ""),
                    "lastCommitTime": repo.get("lastCommitTime", ""),
                    "initialized": False,
                    "commits": [],
                    "earliestDate": None,
                    "latestDate": None,
                    "branchCount": 0,
                    "fileCount": 0,
                    "remoteUrl": "",
                    "repoSize": 0,
                    "analyzed": False,
                    "branches": [],
                    "totalLines": 0,
                    "languages": [],
                }

    def get_repositories(self) -> list[dict]:
        """返回所有仓库（含提交数据）。"""
        with self._lock:
            result = []
            for cache in self.repos.values():
                result.append({
                    "path": cache["path"],
                    "name": cache["name"],
                    "userEmail": cache["userEmail"],
                    "currentBranch": cache["currentBranch"],
                    "lastCommitTime": cache["lastCommitTime"],
                    "commits": cache["commits"],
                })
            return result

    def get_repo_cache(self, path: str) -> Optional[dict]:
        with self._lock:
            return self.repos.get(path)

    def get_all_caches(self) -> dict[str, dict]:
        with self._lock:
            return dict(self.repos)

    def check_init_range(self, path: str) -> tuple[bool, bool, Optional[datetime], Optional[datetime]]:
        """返回 (exists, initialized, earliest, latest)。"""
        with self._lock:
            cache = self.repos.get(path)
            if not cache:
                return False, False, None, None
            return True, cache["initialized"], cache["earliestDate"], cache["latestDate"]

    def set_repo_commits(self, path: str, commits: list[dict]):
        with self._lock:
            cache = self.repos.get(path)
            if cache:
                cache["commits"] = commits
                cache["initialized"] = True
                if commits:
                    dates = [c["date"] for c in commits]
                    cache["earliestDate"] = min(dates)
                    cache["latestDate"] = max(dates)
                # Persist to database
                try:
                    database.save_commits(path, commits)
                except Exception as e:
                    log.warning("Failed to save commits to DB: %s", e)

    def merge_commits(self, path: str, new_commits: list[dict]) -> bool:
        """增量合并去重，检查上限。"""
        with self._lock:
            cache = self.repos.get(path)
            if not cache:
                return False
            existing = {c["hash"] for c in cache["commits"]}
            unique = [c for c in new_commits if c["hash"] not in existing]
            if not unique:
                return True
            if len(cache["commits"]) + len(unique) > MAX_COMMITS_PER_REPO:
                return False
            cache["commits"].extend(unique)
            # 更新日期范围
            for c in unique:
                d = c["date"]
                if cache["earliestDate"] is None or d < cache["earliestDate"]:
                    cache["earliestDate"] = d
                if cache["latestDate"] is None or d > cache["latestDate"]:
                    cache["latestDate"] = d
            return True

    def update_repo(self, path: str, **kwargs):
        with self._lock:
            cache = self.repos.get(path)
            if cache:
                cache.update(kwargs)
                # Persist key metadata to database
                try:
                    database.save_repo_meta(cache)
                except Exception as e:
                    log.warning("Failed to save repo meta to DB: %s", e)


store = Store()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GITEE CLONE — 从 Gitee 克隆仓库到本地缓存
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GIT LOG PARSER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def parse_git_log(text: str) -> list[dict]:
    """解析 git log --format + --numstat 输出为 commit 列表。"""
    lines = text.split("\n")
    commits = []
    marker = "---GITSTAT_COMMIT---"

    i = 0
    while i < len(lines) and lines[i] != marker:
        i += 1

    while i < len(lines):
        if lines[i] != marker:
            i += 1
            continue
        i += 1  # skip marker

        if i + 4 >= len(lines):
            break

        commit_hash = lines[i].strip(); i += 1
        author = lines[i].strip(); i += 1
        email = lines[i].strip(); i += 1
        date_str = lines[i].strip(); i += 1
        subject = lines[i].strip(); i += 1

        # 解析日期（git 返回带时区的日期，统一转成 naive datetime 方便比较）
        commit_time = None
        for fmt in ["%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                # 如果带时区，转成本地时间后去掉 tzinfo
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                commit_time = dt
                break
            except ValueError:
                continue

        # 解析 numstat
        additions = 0
        deletions = 0
        while i < len(lines) and lines[i] != marker:
            line = lines[i].strip()
            i += 1
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                try:
                    additions += int(parts[0])
                except ValueError:
                    pass
                try:
                    deletions += int(parts[1])
                except ValueError:
                    pass

        commits.append({
            "hash": commit_hash,
            "author": author,
            "email": email,
            "date": commit_time or datetime.now(),
            "message": subject,
            "additions": additions,
            "deletions": deletions,
        })

    return commits


def run_git_log(repo_path: str, since: Optional[datetime] = None,
                until: Optional[datetime] = None, use_cache: bool = True) -> list[dict]:
    """在仓库中运行 git log 并返回解析后的 commit 列表（带 TTL 缓存）。"""
    cache_key = f"{repo_path}:{since}:{until}"
    if use_cache:
        cached = git_log_cache.get(cache_key)
        if cached is not None:
            return cached

    args = ["log", "--format=---GITSTAT_COMMIT---%n%H%n%an%n%ae%n%ci%n%s", "--numstat"]
    if since:
        args.append(f"--since={since.strftime('%Y-%m-%d %H:%M:%S')}")
    if until:
        args.append(f"--until={until.strftime('%Y-%m-%d %H:%M:%S')}")

    output = git_exec(repo_path, *args)
    if not output:
        return []
    result = parse_git_log(output)
    if use_cache:
        git_log_cache.set(cache_key, result)
    return result
    return parse_git_log(output)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SCANNER — 发现 Git 仓库 + 深度分析
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXT_LANG_MAP = {
    ".rs": "Rust", ".go": "Go", ".py": "Python", ".js": "JavaScript",
    ".jsx": "React (JSX)", ".ts": "TypeScript", ".tsx": "React (TSX)",
    ".vue": "Vue", ".svelte": "Svelte", ".java": "Java", ".kt": "Kotlin",
    ".kts": "Kotlin", ".scala": "Scala", ".c": "C", ".h": "C/C++ Header",
    ".cpp": "C++", ".cxx": "C++", ".hpp": "C++ Header", ".cs": "C#",
    ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".m": "Objective-C",
    ".mm": "Objective-C++", ".r": "R", ".dart": "Dart", ".lua": "Lua",
    ".hs": "Haskell", ".zig": "Zig", ".pl": "Perl", ".pm": "Perl",
    ".sql": "SQL", ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".fish": "Shell", ".ps1": "PowerShell", ".css": "CSS", ".scss": "SCSS",
    ".less": "Less", ".html": "HTML", ".htm": "HTML", ".xml": "XML",
    ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML", ".json": "JSON",
    ".jsonc": "JSON", ".md": "Markdown", ".rst": "reStructuredText",
    ".tex": "LaTeX", ".dockerfile": "Dockerfile", ".cmake": "CMake",
    ".gradle": "Gradle", ".proto": "Protobuf", ".graphql": "GraphQL",
    ".gql": "GraphQL",
}

EXACT_NAME_MAP = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "CMakeLists.txt": "CMake",
}


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
        log.warning("Failed to extract repo meta for %s: %s", path, e)
        return None


def discover_repos(root_path: str) -> list[dict]:
    """扫描目录下所有 Git 仓库。"""
    repos = []
    p = Path(root_path)

    # 检查 root_path 本身是不是 git repo
    if (p / ".git").exists():
        meta = scan_metadata(str(p))
        if meta:
            repos.append(meta)

    # 检查子目录
    if p.is_dir():
        for entry in p.iterdir():
            if entry.is_dir() and (entry / ".git").exists():
                meta = scan_metadata(str(entry))
                if meta:
                    repos.append(meta)

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
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
        return start, end

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


# Simple in-memory rate limiter
_rate_store: dict[str, list] = {}

def check_rate_limit(key: str, max_req: int = 60, window: int = 60) -> bool:
    """窗口内超过 max_req 次返回 False。"""
    now = time.time()
    bucket = _rate_store.get(key, [])
    bucket = [t for t in bucket if now - t < window]
    if len(bucket) >= max_req:
        return False
    bucket.append(now)
    _rate_store[key] = bucket
    return True

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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Brotli compression middleware
app.add_middleware(BrotliMiddleware, quality=6)

# Register Gitee module routes
app.include_router(gitee_router)


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
    body = await request.json()
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "Path is required")

    store.clear_all()
    store.set_scan_path(path)
    repos = discover_repos(path)
    store.register_repos(repos)

    return {
        "code": 200,
        "data": {"path": path},
        "message": "Path set successfully, data will be loaded on demand",
    }


@app.get("/api/repositories")
def api_get_repositories():
    repos = store.get_repositories()
    return repos


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
    cache = store.get_repo_cache(path)
    if not cache:
        raise HTTPException(404, "repo not found")

    branch_count = cache["branchCount"]
    file_count = cache["fileCount"]
    remote_url = cache["remoteUrl"]

    if branch_count == 0:
        meta = get_repo_meta(path)
        branch_count = meta["branchCount"]
        file_count = meta["fileCount"]
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
def api_export():
    repos = store.get_repositories()
    return Response(
        content=json.dumps(repos, default=str, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=gitstat-data.json"},
    )


# ---- 提交详情列表 ----

@app.get("/api/stats/commit-list")
def api_commit_list(
    repo: list[str] = Query(default=[]),
    startDate: str = "",
    endDate: str = "",
    range: str = "",
    email: str = "",
    limit: int = Query(default=50),
):
    """返回指定时间范围内的提交详情列表（按时间倒序）。"""
    start, end = parse_time_params(startDate, endDate, range, "today")
    ensure_data_loaded(repo, start)
    repos = _load_repos(repo)
    user = _resolve_user_email(repos, email)

    all_commits = []
    for r in repos:
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
            })

    all_commits.sort(key=lambda c: c["date"], reverse=True)
    return all_commits[:limit]


# ---- 版本 + 健康检查 ----

@app.get("/api/version")
def api_version():
    return {"version": f"git {get_git_version()}"}


@app.get("/health")
def api_health():
    return "OK"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WEATHER — 天气数据代理（Open-Meteo API）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WMO_WEATHER_CODE = {
    0: {"zh": "晴", "en": "Clear", "icon": "clear"},
    1: {"zh": "大部晴朗", "en": "Mainly clear", "icon": "mostly-clear"},
    2: {"zh": "多云", "en": "Partly cloudy", "icon": "partly-cloudy"},
    3: {"zh": "阴", "en": "Overcast", "icon": "overcast"},
    45: {"zh": "雾", "en": "Fog", "icon": "fog"},
    48: {"zh": "冻雾", "en": "Depositing rime fog", "icon": "fog"},
    51: {"zh": "小毛毛雨", "en": "Light drizzle", "icon": "drizzle"},
    53: {"zh": "毛毛雨", "en": "Moderate drizzle", "icon": "drizzle"},
    55: {"zh": "大毛毛雨", "en": "Dense drizzle", "icon": "drizzle"},
    56: {"zh": "冻毛毛雨", "en": "Light freezing drizzle", "icon": "drizzle"},
    57: {"zh": "冻毛毛雨", "en": "Dense freezing drizzle", "icon": "drizzle"},
    61: {"zh": "小雨", "en": "Slight rain", "icon": "rain"},
    63: {"zh": "中雨", "en": "Moderate rain", "icon": "rain"},
    65: {"zh": "大雨", "en": "Heavy rain", "icon": "rain"},
    66: {"zh": "冻雨", "en": "Light freezing rain", "icon": "rain"},
    67: {"zh": "冻雨", "en": "Heavy freezing rain", "icon": "rain"},
    71: {"zh": "小雪", "en": "Slight snow fall", "icon": "snow"},
    73: {"zh": "中雪", "en": "Moderate snow fall", "icon": "snow"},
    75: {"zh": "大雪", "en": "Heavy snow fall", "icon": "snow"},
    77: {"zh": "雪粒", "en": "Snow grains", "icon": "snow"},
    80: {"zh": "小阵雨", "en": "Slight rain showers", "icon": "rain"},
    81: {"zh": "中阵雨", "en": "Moderate rain showers", "icon": "rain"},
    82: {"zh": "大阵雨", "en": "Violent rain showers", "icon": "rain"},
    85: {"zh": "小阵雪", "en": "Slight snow showers", "icon": "snow"},
    86: {"zh": "大阵雪", "en": "Heavy snow showers", "icon": "snow"},
    95: {"zh": "雷暴", "en": "Thunderstorm", "icon": "thunderstorm"},
    96: {"zh": "雷暴+小冰雹", "en": "Thunderstorm with slight hail", "icon": "thunderstorm"},
    99: {"zh": "雷暴+大冰雹", "en": "Thunderstorm with heavy hail", "icon": "thunderstorm"},
}

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


def _fetch_open_meteo(params: dict) -> dict:
    """调用 Open-Meteo API 并返回 JSON。"""
    url = OPEN_METEO_BASE + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GitStat/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning("Open-Meteo API error: %s", e)
        return {}


def _weather_desc(code: int, lang: str = "zh") -> str:
    info = WMO_WEATHER_CODE.get(code, {"zh": "未知", "en": "Unknown", "icon": "unknown"})
    return info.get(lang, info["en"])


def _weather_icon(code: int) -> str:
    info = WMO_WEATHER_CODE.get(code, {"icon": "unknown"})
    return info["icon"]


@app.get("/api/weather/current")
def api_weather_current(lat: float = Query(...), lon: float = Query(...)):
    """获取当前天气（代理 Open-Meteo）。"""
    data = _fetch_open_meteo({
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature",
        "timezone": "auto",
    })
    if not data or "current" not in data:
        raise HTTPException(503, "Weather API unavailable")

    cur = data["current"]
    tz = data.get("timezone", "")
    tz_name = tz.replace("Asia/", "").replace("Europe/", "").replace("America/", "") if tz else ""

    return {
        "code": 200,
        "data": {
            "temperature": cur.get("temperature_2m"),
            "apparentTemperature": cur.get("apparent_temperature"),
            "humidity": cur.get("relative_humidity_2m"),
            "windSpeed": cur.get("wind_speed_10m"),
            "weatherCode": cur.get("weather_code"),
            "descriptionZh": _weather_desc(cur.get("weather_code", 0), "zh"),
            "descriptionEn": _weather_desc(cur.get("weather_code", 0), "en"),
            "icon": _weather_icon(cur.get("weather_code", 0)),
            "timezone": tz,
            "locationName": tz_name,
            "units": data.get("current_units", {}),
        },
    }


@app.get("/api/weather/forecast")
def api_weather_forecast(lat: float = Query(...), lon: float = Query(...), days: int = Query(default=7)):
    """获取未来几天天气预报（代理 Open-Meteo）。"""
    data = _fetch_open_meteo({
        "latitude": lat,
        "longitude": lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": min(days, 7),
    })
    if not data or "daily" not in data:
        raise HTTPException(503, "Weather API unavailable")

    daily = data["daily"]
    forecast = []
    for i in range(len(daily.get("time", []))):
        entry = {
            "date": daily["time"][i],
            "weatherCode": daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0,
            "temperatureMax": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
            "temperatureMin": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
            "apparentTemperatureMax": daily.get("apparent_temperature_max", [])[i] if i < len(daily.get("apparent_temperature_max", [])) else None,
            "apparentTemperatureMin": daily.get("apparent_temperature_min", [])[i] if i < len(daily.get("apparent_temperature_min", [])) else None,
            "sunrise": daily.get("sunrise", [])[i] if i < len(daily.get("sunrise", [])) else "",
            "sunset": daily.get("sunset", [])[i] if i < len(daily.get("sunset", [])) else "",
            "precipitation": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else 0,
            "windSpeedMax": daily.get("wind_speed_10m_max", [])[i] if i < len(daily.get("wind_speed_10m_max", [])) else None,
            "descriptionZh": _weather_desc(daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0, "zh"),
            "descriptionEn": _weather_desc(daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0, "en"),
            "icon": _weather_icon(daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0),
        }
        forecast.append(entry)

    return {
        "code": 200,
        "data": forecast,
    }


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
    """聚合 token 统计数据（已拆分为子函数）。"""
    today = date.today()
    range_map = {
        "thisWeek": timedelta(weeks=1), "lastWeek": timedelta(weeks=2),
        "thisMonth": timedelta(days=30), "lastMonth": timedelta(days=60),
        "thisYear": timedelta(days=365), "customPeriod": timedelta(days=365*2),
    }
    cutoff = today - range_map.get(time_range, timedelta(days=365))
    filtered = _filter_token_records(records, cutoff, model_filter, today)

    total_input = sum(r["input"] for r in filtered)
    total_output = sum(r["output"] for r in filtered)

    model_agg: dict[str, dict] = {}
    for r in filtered:
        m = r["model"]
        model_agg.setdefault(m, {"input": 0, "output": 0})
        model_agg[m]["input"] += r["input"]
        model_agg[m]["output"] += r["output"]

    total_cost, model_rank = _calc_token_costs(model_agg)

    # 趋势数据
    trend_map: dict[str, dict] = {}
    for r in filtered:
        ds = r.get("_date", "")
        trend_map.setdefault(ds, {"input": 0, "output": 0})
        trend_map[ds]["input"] += r["input"]
        trend_map[ds]["output"] += r["output"]
    trend = [{"date": k, "input": v["input"], "output": v["output"]} for k, v in sorted(trend_map.items())]

    return {
        "totalInput": total_input, "totalOutput": total_output,
        "totalTokens": total_input + total_output, "totalCost": round(total_cost, 2),
        "modelRank": model_rank, "trend": trend,
        "availableModels": list(model_agg.keys()),
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
    result = _aggregate_token_stats(records, range, model)
    return JSONResponse({"data": result})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STREAK — 连续贡献天数统计
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _calc_streak(repo_list: list, repos_filter: Optional[list] = None) -> dict:
    """
    计算连续贡献天数（current streak / longest streak / weekly active / last 30 days）。
    基于 daily 统计数据，从今天往前回溯。
    """
    today = date.today()
    # 收集所有每日提交数据，按日期聚合
    daily_map: dict[str, int] = {}  # date_str → total_commits

    for repo in repo_list:
        if repos_filter and repo["repoName"] not in repos_filter:
            continue
        for author in (repo.get("authors") or []):
            for day in (author.get("dailyData") or []):
                ds = day.get("date", "")
                if ds:
                    daily_map[ds] = daily_map.get(ds, 0) + day.get("commits", 0)

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

    # 获取较长时间范围的 daily 数据来计算 streak（最近60天）
    repo_list = aggregator.aggregate_daily(
        repos_filter=repos_filter,
        time_range="year",  # 用年范围确保覆盖足够数据
        start_date=None,
        end_date=None,
    )

    result = _calc_streak(repo_list, repos_filter)
    return JSONResponse({"data": result})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GITEE — 码云代码统计 API Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/api/gitee/repos")
def api_gitee_list_repos(
    owner: str = Query(..., description="Gitee 用户名或组织名"),
    page: int = Query(default=1),
    perPage: int = Query(default=30),
):
    """代理 Gitee API：获取某用户/组织的仓库列表。"""
    if not owner or not re.match(r'^[a-zA-Z0-9_-]+$', owner):
        raise HTTPException(400, "Invalid owner name")
    try:
        repos = gitee_list_repos(owner, page, perPage)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Gitee API error: {e}")
    return {"code": 200, "data": repos}


@app.get("/api/gitee/repos/info")
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


@app.post("/api/gitee/repos/clone")
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


@app.post("/api/gitee/repos/analyze")
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


@app.post("/api/gitee/repos/remove")
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
#  STATIC FILES — 前端 SPA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
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
        file_path = _frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
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
    parser.add_argument("scan_path", nargs="?", default=os.getcwd(),
                        help="Git 仓库扫描目录（默认: 当前目录）")
    parser.add_argument("--port", type=int, default=12580,
                        help="监听端口（默认: 12580）")
    parser.add_argument("--no-browser", action="store_true",
                        help="不自动打开浏览器")
    args = parser.parse_args()

    # Restore state from database if available, otherwise scan fresh
    saved_path = database.get_scan_path()
    if saved_path and not args.scan_path:
        args.scan_path = saved_path

    database.save_scan_path(args.scan_path)
    store.set_scan_path(args.scan_path)
    repos = discover_repos(args.scan_path)
    store.register_repos(repos)

    # Restore cached repos from DB
    db_repos = database.load_repos()
    for db_repo in db_repos:
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

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")
