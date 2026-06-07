"""Test config module."""
import sys, os
sys.path.insert(0, 'backend-py')
from config import VERSION, Timeout, MAX_COMMITS_PER_REPO, FRONTEND_DIST, GIT_LOG_CACHE_TTL


class TestConfig:
    def test_version_is_string(self):
        assert isinstance(VERSION, str)
        assert '.' in VERSION

    def test_max_commits_positive(self):
        assert MAX_COMMITS_PER_REPO > 0

    def test_frontend_dist_exists(self):
        from pathlib import Path
        assert isinstance(FRONTEND_DIST, Path)

    def test_cache_ttl_positive(self):
        assert GIT_LOG_CACHE_TTL > 0


class TestTimeout:
    def test_git_exec_timeout(self):
        assert Timeout.GIT_EXEC == 30

    def test_git_clone_timeout(self):
        assert Timeout.GIT_CLONE == 120

    def test_http_api_timeout(self):
        assert Timeout.HTTP_API == 15

    def test_all_timeouts_positive(self):
        for attr in dir(Timeout):
            if attr.isupper():
                val = getattr(Timeout, attr)
                assert isinstance(val, int) and val > 0, f"{attr} should be positive int"
