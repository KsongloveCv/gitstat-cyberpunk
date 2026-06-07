"""Test database persistence layer."""
import pytest
import sys, os, tempfile
from pathlib import Path
sys.path.insert(0, 'backend-py')
import database
from datetime import datetime


@pytest.fixture(autouse=True)
def use_temp_db():
    old = database.DB_PATH
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    database.DB_PATH = Path(path)
    database.init_db()
    yield
    database.clear_all()
    os.unlink(path)
    database.DB_PATH = old


class TestDatabaseInit:
    def test_init_creates_tables(self):
        conn = database._get_conn()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        names = [t[0] for t in tables]
        assert 'repos' in names
        assert 'commits' in names
        assert 'scan_state' in names

    def test_scan_path_save_and_get(self):
        database.save_scan_path('/test/path')
        assert database.get_scan_path() == '/test/path'

    def test_scan_path_empty_default(self):
        database.clear_all()
        database.init_db()
        assert database.get_scan_path() == ''


class TestRepoPersistence:
    def test_save_and_load_repo(self):
        repo = {
            "path": "/tmp/test-repo", "name": "test-repo",
            "userEmail": "a@b.com", "currentBranch": "main",
            "lastCommitTime": "2024-01-01", "remoteUrl": "https://example.com",
            "repoSize": 1024, "analyzed": True, "branchCount": 3,
            "fileCount": 10, "totalLines": 500,
            "branches": ["main", "dev"], "languages": [{"name": "Python", "percent": 80}],
        }
        database.save_repo_meta(repo)
        repos = database.load_repos()
        assert len(repos) >= 1
        loaded = [r for r in repos if r["path"] == "/tmp/test-repo"][0]
        assert loaded["name"] == "test-repo"
        assert loaded["analyzed"] is True
        assert loaded["branchCount"] == 3

    def test_load_repos_empty(self):
        database.clear_all()
        database.init_db()
        assert database.load_repos() == []


class TestCommitPersistence:
    def test_save_and_load_commits(self):
        commits = [
            {"hash": "abc123", "author": "Alice", "email": "a@b.com",
             "date": datetime(2024, 1, 15), "message": "Initial", "additions": 10, "deletions": 5},
            {"hash": "def456", "author": "Bob", "email": "b@c.com",
             "date": datetime(2024, 1, 16), "message": "Fix", "additions": 3, "deletions": 1},
        ]
        database.save_commits("/tmp/test-repo", commits)
        loaded = database.load_commits("/tmp/test-repo")
        assert len(loaded) == 2
        assert loaded[0]["author"] == "Bob"
        assert loaded[1]["author"] == "Alice"

    def test_save_commits_replaces_previous(self):
        commits1 = [{"hash": "aaa", "author": "X", "email": "x@x.com",
                      "date": datetime.now(), "message": "X", "additions": 1, "deletions": 0}]
        commits2 = [{"hash": "bbb", "author": "Y", "email": "y@y.com",
                      "date": datetime.now(), "message": "Y", "additions": 2, "deletions": 0}]
        database.save_commits("/tmp/test-repo", commits1)
        database.save_commits("/tmp/test-repo", commits2)
        loaded = database.load_commits("/tmp/test-repo")
        assert len(loaded) == 1
        assert loaded[0]["author"] == "Y"


class TestDatabaseEdgeCases:
    def test_clear_all(self):
        database.save_scan_path('/tmp')
        database.save_repo_meta({"path": "/tmp/x", "name": "x", "userEmail": "", "currentBranch": "", "lastCommitTime": "", "remoteUrl": "", "repoSize": 0, "analyzed": False, "branchCount": 0, "fileCount": 0, "totalLines": 0, "branches": [], "languages": []})
        database.clear_all()
        assert database.get_scan_path() == ''
        assert database.load_repos() == []

    def test_clear_repo_data(self):
        database.save_scan_path('/kept')
        database.save_repo_meta({"path": "/tmp/y", "name": "y", "userEmail": "", "currentBranch": "", "lastCommitTime": "", "remoteUrl": "", "repoSize": 0, "analyzed": False, "branchCount": 0, "fileCount": 0, "totalLines": 0, "branches": [], "languages": []})
        database.clear_repo_data()
        assert database.get_scan_path() == '/kept'
        assert database.load_repos() == []
