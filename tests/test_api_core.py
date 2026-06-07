"""Core API endpoint tests."""
import json


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.text == '"OK"' or r.text == "OK"


def test_version(client):
    r = client.get("/api/version")
    assert r.status_code == 200
    assert "version" in r.json()


def test_scan_path_get_empty(client):
    r = client.get("/api/scan/path")
    assert r.status_code == 200
    assert r.json()["code"] == 200


def test_scan_path_post_invalid(client):
    r = client.post("/api/scan/path", json={"path": ""})
    assert r.status_code == 400


def test_scan_path_post_valid(tmp_path, client):
    r = client.post("/api/scan/path", json={"path": str(tmp_path)})
    assert r.status_code == 200
    assert r.json()["data"]["path"]


def test_user_identity_empty(client):
    r = client.get("/api/user/identity")
    assert r.status_code == 200
    assert r.json()["data"]["email"] == ""


def test_user_identity_with_repo(sample_repo, client):
    r = client.get("/api/user/identity")
    assert r.json()["data"]["email"] == "tester@example.com"


def test_repositories_lightweight(sample_repo, client):
    r = client.get("/api/repositories")
    body = r.json()
    assert body["code"] == 200
    assert body["data"][0]["name"] == "demo-repo"
    assert "commits" not in body["data"][0]


def test_repositories_with_commits_flag(sample_repo, client):
    r = client.get("/api/repositories?includeCommits=true")
    assert "commits" in r.json()["data"][0]


def test_repo_info_requires_registration(client):
    r = client.get("/api/repos/info?path=/not/registered")
    assert r.status_code == 403


def test_repo_info_ok(sample_repo, client):
    r = client.get(f"/api/repos/info?path={sample_repo}")
    assert r.status_code == 200
    assert r.json()["name"] == "demo-repo"


def test_export_json_post(sample_repo, client):
    r = client.post("/api/export/json", json={"includeCommits": False})
    assert r.status_code == 200
    data = json.loads(r.content)
    assert "repos" in data


def test_scan_refresh_no_path(client):
    r = client.post("/api/scan/refresh")
    assert r.status_code == 400


def test_scan_refresh_ok(sample_repo, client):
    r = client.post("/api/scan/refresh")
    assert r.status_code == 200
    assert r.json()["data"]["repoCount"] >= 1


def test_stats_summary(sample_repo, client):
    r = client.get("/api/stats/summary?range=year")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "totalCommits" in data
    assert "repositoryCount" in data
