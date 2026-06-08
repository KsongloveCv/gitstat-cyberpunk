"""Git 操作工具函数."""
import subprocess
import re
import time
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from collections import defaultdict

log = logging.getLogger('gitstat')

# Simple TTL cache
class TTLCache:
    def __init__(self, ttl_seconds: float = 300):
        self._ttl = ttl_seconds
        self._data: dict = {}
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

    def set(self, key: str, value):
        with self._lock:
            self._data[key] = (time.time(), value)

    def clear(self):
        with self._lock:
            self._data.clear()

git_log_cache = TTLCache(ttl_seconds=300)


def git_exec(repo_path: str, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git"] + list(args), cwd=repo_path,
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.rstrip("\n\r ")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def get_git_version() -> str:
    try:
        out = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=5
        ).stdout.strip()
        m = re.search(r"\d+\.\d+\.\d+", out)
        return f"git {m.group()}" if m else out
    except Exception as e:
        log.warning("Failed to detect git version: %s", e)
        return "git not found"


def parse_git_log(text: str) -> list:
    lines = text.split("\n")
    commits = []
    marker = "---GITSTAT_COMMIT---"
    i = 0
    while i < len(lines) and lines[i] != marker:
        i += 1
    while i < len(lines):
        if lines[i] != marker:
            i += 1; continue
        i += 1
        if i + 4 >= len(lines): break
        commit_hash = lines[i].strip(); i += 1
        author = lines[i].strip(); i += 1
        email = lines[i].strip(); i += 1
        date_str = lines[i].strip(); i += 1
        subject = lines[i].strip(); i += 1
        commit_time = None
        for fmt in ["%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is not None: dt = dt.replace(tzinfo=None)
                commit_time = dt
                break
            except ValueError: continue
        additions = 0; deletions = 0
        while i < len(lines) and lines[i] != marker:
            line = lines[i].strip(); i += 1
            if not line: continue
            parts = line.split("\t")
            if len(parts) >= 2:
                try: additions += int(parts[0])
                except ValueError: pass
                try: deletions += int(parts[1])
                except ValueError: pass
        commits.append({
            "hash": commit_hash, "author": author, "email": email,
            "date": commit_time or datetime.now(), "message": subject,
            "additions": additions, "deletions": deletions,
        })
    return commits


def run_git_log(repo_path, since=None, until=None, use_cache=True):
    cache_key = f"{repo_path}:{since}:{until}"
    if use_cache:
        cached = git_log_cache.get(cache_key)
        if cached is not None: return cached

    args = ["log", "--format=---GITSTAT_COMMIT---%n%H%n%an%n%ae%n%ci%n%s", "--numstat"]
    if since: args.append(f"--since={since.strftime('%Y-%m-%d %H:%M:%S')}")
    if until: args.append(f"--until={until.strftime('%Y-%m-%d %H:%M:%S')}")
    output = git_exec(repo_path, *args)
    if not output: return []
    result = parse_git_log(output)
    if use_cache: git_log_cache.set(cache_key, result)
    return result


def get_repo_meta(path):
    branch = git_exec(path, "rev-parse", "--abbrev-ref", "HEAD") or "master"
    try:
        last_commit = git_exec(path, "log", "-1", "--format=%ci") or ""
    except Exception as e:
        log.warning("Failed to extract repo meta for %s: %s", path, e)
        return None
    user_email = git_exec(path, "config", "user.email") or ""
    return {
        "path": path, "name": Path(path).name,
        "currentBranch": branch, "lastCommitTime": last_commit,
        "userEmail": user_email, "branchCount": 0, "fileCount": 0, "remoteUrl": "",
    }


def get_remote_url(path):
    url = git_exec(path, "config", "--get", "remote.origin.url") or ""
    if url.startswith("git@"): url = url.replace(":", "/").replace("git@", "https://")
    return url


def get_repo_size(path):
    try:
        result = int(subprocess.check_output(["du", "-sk", path], text=True, timeout=10).split()[0])
        return result * 1024
    except Exception: return 0


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
