"""Security utility tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend-py"))

import pytest
from fastapi import HTTPException
from security import (
    check_rate_limit, validate_scan_path, validate_gitee_clone_url,
    safe_static_path, clamp_limit, validate_repo_path,
)


def test_rate_limit_allows_under_cap():
    assert check_rate_limit("test-key-a", 5, 60) is True


def test_rate_limit_blocks_over_cap():
    key = "test-key-b"
    for _ in range(3):
        check_rate_limit(key, 3, 60)
    assert check_rate_limit(key, 3, 60) is False


def test_validate_scan_path_missing(tmp_path):
    with pytest.raises(HTTPException) as exc:
        validate_scan_path(str(tmp_path / "nope"))
    assert exc.value.status_code == 400


def test_validate_scan_path_ok(tmp_path):
    assert validate_scan_path(str(tmp_path)) == str(tmp_path.resolve())


def test_validate_gitee_clone_url_ok():
    url = validate_gitee_clone_url("https://gitee.com/foo/bar.git")
    assert "gitee.com" in url


def test_validate_gitee_clone_url_rejects():
    with pytest.raises(HTTPException):
        validate_gitee_clone_url("https://evil.com/foo.git")


def test_safe_static_path_blocks_traversal(tmp_path):
    base = tmp_path / "dist"
    base.mkdir()
    (base / "index.html").write_text("ok")
    assert safe_static_path(base, "../secret") is None


def test_safe_static_path_allows_file(tmp_path):
    base = tmp_path / "dist"
    base.mkdir()
    f = base / "app.js"
    f.write_text("console.log(1)")
    result = safe_static_path(base, "app.js")
    assert result is not None
    assert result.name == "app.js"


def test_clamp_limit_default():
    assert clamp_limit(0) == 50


def test_clamp_limit_max():
    assert clamp_limit(9999) == 500


def test_validate_repo_path_unregistered():
    with pytest.raises(HTTPException) as exc:
        validate_repo_path("/tmp/x", set())
    assert exc.value.status_code == 403


def test_validate_repo_path_registered(tmp_path):
    p = str(tmp_path.resolve())
    assert validate_repo_path(p, {p}) == p
