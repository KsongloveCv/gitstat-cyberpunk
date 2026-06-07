"""Store module tests."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend-py"))

from store import Store


def test_register_and_list():
    s = Store()
    s.register_repos([{"path": "/a", "name": "A", "userEmail": "a@x.com", "currentBranch": "main", "lastCommitTime": ""}])
    repos = s.get_repositories(include_commits=False)
    assert len(repos) == 1
    assert repos[0]["userEmail"] == "a@x.com"


def test_registered_paths():
    s = Store()
    s.register_repos([{"path": "/b", "name": "B", "userEmail": "", "currentBranch": "main", "lastCommitTime": ""}])
    assert "/b" in s.registered_paths()


def test_set_repo_commits_updates_range():
    s = Store()
    s.register_repos([{"path": "/c", "name": "C", "userEmail": "", "currentBranch": "main", "lastCommitTime": ""}])
    d1 = datetime(2024, 1, 1)
    d2 = datetime(2024, 6, 1)
    s.set_repo_commits("/c", [
        {"hash": "1", "author": "X", "email": "x@x.com", "date": d1, "message": "a", "additions": 1, "deletions": 0},
        {"hash": "2", "author": "X", "email": "x@x.com", "date": d2, "message": "b", "additions": 2, "deletions": 0},
    ])
    _, init, earliest, latest = s.check_init_range("/c")
    assert init is True
    assert earliest == d1
    assert latest == d2
