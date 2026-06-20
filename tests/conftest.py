"""Pytest fixtures for GitStat API tests."""
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).parent.parent
os.environ.setdefault("GITSTAT_HOME", str(ROOT / ".pytest_cache" / "gitstat-home"))
sys.path.insert(0, str(ROOT / "backend-py"))

from store import store  # noqa: E402
import database  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_store():
    database.init_db()
    database.clear_all()
    store.clear_all()
    yield
    store.clear_all()
    database.clear_all()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_repo(tmp_path):
    repo = tmp_path / "demo-repo"
    repo.mkdir()
    import subprocess
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "tester@example.com"],
        cwd=repo, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Tester"],
        cwd=repo, check=True, capture_output=True,
    )
    readme = repo / "readme.txt"
    readme.write_text("hello\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=repo, check=True, capture_output=True,
        env={**__import__("os").environ, "GIT_AUTHOR_DATE": "2024-06-01T10:00:00", "GIT_COMMITTER_DATE": "2024-06-01T10:00:00"},
    )
    store.set_scan_path(str(tmp_path))
    store.register_repos([{
        "path": str(repo),
        "name": "demo-repo",
        "userEmail": "tester@example.com",
        "currentBranch": "main",
        "lastCommitTime": "2024-06-01 10:00:00",
    }])
    return str(repo)
