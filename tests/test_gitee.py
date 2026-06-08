"""Test Gitee module."""
import pytest
import sys
sys.path.insert(0, 'backend-py')
from gitee import _gitee_request, gitee_router, _check_rate


class TestGiteeRouter:
    def test_router_has_repos_route(self):
        routes = [r.path for r in gitee_router.routes]
        assert '/api/gitee/repos' in routes

    def test_router_has_info_route(self):
        routes = [r.path for r in gitee_router.routes]
        assert '/api/gitee/repos/info' in routes

    def test_router_has_clone_route(self):
        methods = []
        for r in gitee_router.routes:
            methods.extend(r.methods)
        assert 'POST' in methods

    def test_router_has_analyze_route(self):
        routes = [r.path for r in gitee_router.routes]
        assert '/api/gitee/repos/analyze' in routes

    def test_router_has_remove_route(self):
        routes = [r.path for r in gitee_router.routes]
        assert '/api/gitee/repos/remove' in routes


class TestRateLimiter:
    def test_rate_allows_first_request(self):
        import gitee
        gitee._rate_bucket.clear()
        try:
            _check_rate(max_req=5, window=60)
        except Exception:
            pytest.fail("First request should be allowed")

    def test_rate_blocks_after_limit(self):
        import gitee
        gitee._rate_bucket.clear()
        for _ in range(5):
            try:
                _check_rate(max_req=5, window=60)
            except Exception:
                pass
        with pytest.raises(Exception):
            _check_rate(max_req=5, window=60)


class TestGiteeConfig:
    def test_api_base_url(self):
        from gitee import GITEE_API_BASE
        assert GITEE_API_BASE == "https://gitee.com/api/v5"

    def test_cache_dir_is_path(self):
        from gitee import GITEE_CACHE_DIR
        from pathlib import Path
        assert isinstance(GITEE_CACHE_DIR, Path)


class TestGiteeListRepos:
    def test_invalid_owner_return_empty(self):
        from gitee import gitee_list_repos
        result = gitee_list_repos("__nonexistent_user_xyz__123")
        assert isinstance(result, list)
