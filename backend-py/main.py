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
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional
from collections import defaultdict

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VERSION = "2.0.0-py"
MAX_COMMITS_PER_REPO = 5000
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

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
    except Exception:
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


store = Store()

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
                until: Optional[datetime] = None) -> list[dict]:
    """在仓库中运行 git log 并返回解析后的 commit 列表。"""
    args = ["log", "--format=---GITSTAT_COMMIT---%n%H%n%an%n%ae%n%ci%n%s", "--numstat"]
    if since:
        args.append(f"--since={since.strftime('%Y-%m-%d %H:%M:%S')}")
    if until:
        args.append(f"--until={until.strftime('%Y-%m-%d %H:%M:%S')}")

    output = git_exec(repo_path, *args)
    if not output:
        return []
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
    except Exception:
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


# ---- 版本 + 健康检查 ----

@app.get("/api/version")
def api_version():
    return {"version": f"git {get_git_version()}"}


@app.get("/health")
def api_health():
    return "OK"


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
    except Exception:
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import argparse

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

    # 注册仓库
    store.set_scan_path(args.scan_path)
    repos = discover_repos(args.scan_path)
    store.register_repos(repos)
    print(f"Registered {len(repos)} repos from {args.scan_path}")

    url = f"http://localhost:{args.port}"
    print(f"GitStat Web Server (Python)")
    print(f"Scan directory: {args.scan_path}")
    print(f"Listening on {url}")

    if not args.no_browser:
        open_browser(url)

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")
