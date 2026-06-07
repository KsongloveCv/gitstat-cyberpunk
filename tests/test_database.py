"""Database layer tests."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend-py"))

import database


def test_save_and_load_scan_path(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    database.save_scan_path("/data/projects")
    assert database.get_scan_path() == "/data/projects"


def test_save_and_load_commits(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    repo = "/fake/repo"
    commits = [{
        "hash": "abc123", "author": "A", "email": "a@x.com",
        "date": datetime(2024, 1, 1, 12, 0, 0),
        "message": "feat: test", "additions": 10, "deletions": 2,
    }]
    database.save_commits(repo, commits)
    loaded = database.load_commits(repo)
    assert len(loaded) == 1
    assert loaded[0]["email"] == "a@x.com"
    assert loaded[0]["date"].year == 2024


def test_search_commits_by_message(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    repo = "/r1"
    database.save_commits(repo, [{
        "hash": "h1", "author": "B", "email": "b@x.com",
        "date": datetime(2024, 2, 1), "message": "fix weather bug",
        "additions": 1, "deletions": 0,
    }])
    hits = database.search_commits(query="weather")
    assert len(hits) == 1
    assert hits[0]["message"] == "fix weather bug"


def test_search_commits_pagination(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    repo = "/r2"
    commits = []
    for i in range(5):
        commits.append({
            "hash": f"h{i}", "author": "C", "email": "c@x.com",
            "date": datetime(2024, 3, i + 1), "message": f"msg {i}",
            "additions": 1, "deletions": 0,
        })
    database.save_commits(repo, commits)
    page = database.search_commits(limit=2, offset=1)
    assert len(page) == 2


def test_clear_repo_data_keeps_scan_state(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    database.save_scan_path("/keep")
    database.save_repo_meta({
        "path": "/r", "name": "r", "userEmail": "", "currentBranch": "main",
        "lastCommitTime": "", "remoteUrl": "", "repoSize": 0, "analyzed": False,
        "branchCount": 1, "fileCount": 1, "totalLines": 0, "branches": [], "languages": [],
    })
    database.clear_repo_data()
    assert database.get_scan_path() == "/keep"
    assert database.load_repos() == []


def test_load_commits_date_column_index(tmp_path, monkeypatch):
    """Regression: date must come from column 4 not email column 3."""
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    repo = "/r3"
    database.save_commits(repo, [{
        "hash": "x1", "author": "D", "email": "d@x.com",
        "date": datetime(2024, 5, 10, 8, 30, 0),
        "message": "ok", "additions": 0, "deletions": 0,
    }])
    loaded = database.load_commits(repo)
    assert loaded[0]["date"].month == 5
    assert loaded[0]["date"].day == 10
