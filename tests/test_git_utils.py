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


def test_parse_single_commit_additions():
    log = """---GITSTAT_COMMIT---
aaa11111
U
u@e.com
2024-03-01 09:00:00 +0800
only add
3\t0
"""
    commits = parse_git_log(log)
    assert commits[0]["additions"] == 3
    assert commits[0]["deletions"] == 0


def test_parse_commit_multiline_message():
    log = """---GITSTAT_COMMIT---
bbb22222
U
u@e.com
2024-03-02 09:00:00 +0800
line1
line2
1\t1
"""
    commits = parse_git_log(log)
    assert "line1" in commits[0]["message"]


def test_parse_commit_deletions_only():
    log = """---GITSTAT_COMMIT---
ccc33333
U
u@e.com
2024-03-03 09:00:00 +0800
remove
0\t4
"""
    commits = parse_git_log(log)
    assert commits[0]["deletions"] == 4


def test_parse_whitespace_log():
    assert parse_git_log("   \n\t  ") == []
