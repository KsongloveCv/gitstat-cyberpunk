"""Store — 线程安全的内存仓库存储."""
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

class Store:

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

store = Store()
