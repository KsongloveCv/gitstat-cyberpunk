"""SQLite persistence layer for GitStat data."""
import sqlite3
import json
import threading
import logging
from datetime import datetime
from pathlib import Path
from config import GITSTAT_HOME

log = logging.getLogger('gitstat.db')
DB_PATH = GITSTAT_HOME / "gitstat.db"


def _get_conn() -> sqlite3.Connection:
    db_path = Path(DB_PATH) if not isinstance(DB_PATH, Path) else DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS repos (
            path TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            user_email TEXT DEFAULT '',
            current_branch TEXT DEFAULT '',
            last_commit_time TEXT DEFAULT '',
            remote_url TEXT DEFAULT '',
            repo_size INTEGER DEFAULT 0,
            analyzed INTEGER DEFAULT 0,
            branch_count INTEGER DEFAULT 0,
            file_count INTEGER DEFAULT 0,
            total_lines INTEGER DEFAULT 0,
            branches TEXT DEFAULT '[]',
            languages TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS commits (
            hash TEXT,
            repo_path TEXT,
            author TEXT,
            email TEXT,
            date TEXT,
            message TEXT,
            additions INTEGER DEFAULT 0,
            deletions INTEGER DEFAULT 0,
            PRIMARY KEY (hash, repo_path)
        );
        CREATE TABLE IF NOT EXISTS scan_state (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_commits_repo ON commits(repo_path);
        CREATE INDEX IF NOT EXISTS idx_commits_date ON commits(date);
    """)
    conn.commit()
    conn.close()
    log.info("Database initialized at %s", DB_PATH)


# Thread-safe singleton connection
_lock = threading.Lock()


def save_scan_path(path: str):
    with _lock, _get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO scan_state (key, value) VALUES (?, ?)",
            ("scan_path", path)
        )
        conn.commit()


def get_scan_path() -> str:
    with _lock, _get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM scan_state WHERE key='scan_path'"
        ).fetchone()
        return row[0] if row else ""


def save_repo_meta(repo: dict):
    with _lock, _get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO repos
            (path, name, user_email, current_branch, last_commit_time,
             remote_url, repo_size, analyzed, branch_count, file_count,
             total_lines, branches, languages)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            repo["path"], repo["name"],
            repo.get("userEmail", ""), repo.get("currentBranch", ""),
            repo.get("lastCommitTime", ""), repo.get("remoteUrl", ""),
            repo.get("repoSize", 0), 1 if repo.get("analyzed") else 0,
            repo.get("branchCount", 0), repo.get("fileCount", 0),
            repo.get("totalLines", 0),
            json.dumps(repo.get("branches", [])),
            json.dumps(repo.get("languages", [])),
        ))
        conn.commit()


def load_repos() -> list[dict]:
    with _lock, _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM repos ORDER BY name"
        ).fetchall()
        repos = []
        for r in rows:
            repos.append({
                "path": r["path"], "name": r["name"], "userEmail": r["user_email"],
                "currentBranch": r["current_branch"], "lastCommitTime": r["last_commit_time"],
                "remoteUrl": r["remote_url"], "repoSize": r["repo_size"],
                "analyzed": bool(r["analyzed"]), "branchCount": r["branch_count"],
                "fileCount": r["file_count"], "totalLines": r["total_lines"],
                "branches": json.loads(r["branches"]), "languages": json.loads(r["languages"]),
            })
        return repos


def save_commits(repo_path: str, commits: list[dict]):
    with _lock, _get_conn() as conn:
        conn.execute("DELETE FROM commits WHERE repo_path=?", (repo_path,))
        conn.executemany(
            "INSERT INTO commits VALUES (?,?,?,?,?,?,?,?)",
            [(c["hash"], repo_path, c["author"], c["email"],
              c["date"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(c["date"], datetime) else str(c["date"]),
              c["message"], c["additions"], c["deletions"])
             for c in commits]
        )
        conn.commit()


def load_commits(repo_path: str) -> list[dict]:
    with _lock, _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM commits WHERE repo_path=? ORDER BY date DESC",
            (repo_path,)
        ).fetchall()
        commits = []
        for r in rows:
            try:
                dt = datetime.strptime(r["date"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt = datetime.now()
            commits.append({
                "hash": r["hash"], "author": r["author"], "email": r["email"],
                "date": dt, "message": r["message"],
                "additions": r["additions"], "deletions": r["deletions"],
            })
        return commits


def search_commits(
    query: str = "",
    repo_path: str = "",
    email: str = "",
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Search commits in SQLite cache."""
    sql = "SELECT hash, repo_path, author, email, date, message, additions, deletions FROM commits WHERE 1=1"
    params: list = []
    if repo_path:
        sql += " AND repo_path=?"
        params.append(repo_path)
    if email:
        sql += " AND email=?"
        params.append(email)
    if query:
        sql += " AND (message LIKE ? OR hash LIKE ? OR author LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])
    sql += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with _lock, _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
    results = []
    for r in rows:
        results.append({
            "hash": r["hash"], "repoPath": r["repo_path"], "author": r["author"], "email": r["email"],
            "date": r["date"], "message": r["message"], "additions": r["additions"], "deletions": r["deletions"],
        })
    return results


def clear_repo_data():
    """Clear cached repos and commits; keep scan_state."""
    with _lock, _get_conn() as conn:
        conn.execute("DELETE FROM repos")
        conn.execute("DELETE FROM commits")
        conn.commit()


def clear_all():
    with _lock, _get_conn() as conn:
        conn.execute("DELETE FROM repos")
        conn.execute("DELETE FROM commits")
        conn.execute("DELETE FROM scan_state")
        conn.commit()
