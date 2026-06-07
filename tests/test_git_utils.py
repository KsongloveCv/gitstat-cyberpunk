"""Test git_utils module."""
import sys
sys.path.insert(0, 'backend-py')
from git_utils import parse_git_log, git_log_cache, git_exec

SAMPLE_LOG = """---GITSTAT_COMMIT---
abc12345
Alice
alice@example.com
2024-01-15 10:30:00 +0800
Initial commit
10\t5
5\t3

---GITSTAT_COMMIT---
def67890
Bob
bob@example.com
2024-01-16 14:00:00 +0800
Add feature
20\t0
"""


def test_parse_git_log():
    commits = parse_git_log(SAMPLE_LOG)
    assert len(commits) == 2
    assert commits[0]["hash"] == "abc12345"
    assert commits[0]["author"] == "Alice"
    assert commits[0]["email"] == "alice@example.com"
    assert commits[0]["message"] == "Initial commit"
    assert commits[0]["additions"] == 15
    assert commits[0]["deletions"] == 8


def test_parse_git_log_empty():
    assert parse_git_log("") == []


def test_parse_git_log_no_commits():
    assert parse_git_log("random text\nno marker here\n") == []


def test_ttl_cache_set_get():
    git_log_cache.clear()
    git_log_cache.set("key1", [1, 2, 3])
    assert git_log_cache.get("key1") == [1, 2, 3]


def test_ttl_cache_miss():
    git_log_cache.clear()
    assert git_log_cache.get("nonexistent") is None


def test_ttl_cache_clear():
    git_log_cache.set("key2", "value")
    git_log_cache.clear()
    assert git_log_cache.get("key2") is None
