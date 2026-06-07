"""Statistics API tests."""
from datetime import datetime


def _add_commit(sample_repo):
    from store import store
    store.set_repo_commits(sample_repo, [{
        "hash": "c1", "author": "Tester", "email": "tester@example.com",
        "date": datetime.now().replace(microsecond=0),
        "message": "feat: api test", "additions": 5, "deletions": 1,
    }])


def test_overview_stats(sample_repo, client):
    _add_commit(sample_repo)
    r = client.get("/api/stats/overview?range=year")
    assert r.status_code == 200
    assert r.json()["totalCommits"] >= 1


def test_daily_stats(sample_repo, client):
    _add_commit(sample_repo)
    r = client.get("/api/stats/daily?range=year")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_author_rank(sample_repo, client):
    _add_commit(sample_repo)
    r = client.get("/api/stats/authors?range=year")
    assert r.status_code == 200


def test_commit_list(sample_repo, client):
    _add_commit(sample_repo)
    r = client.get("/api/stats/commit-list?range=year&limit=10")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_commit_list_pagination(sample_repo, client):
    _add_commit(sample_repo)
    r = client.get("/api/stats/commit-list?range=year&limit=1&offset=0")
    assert len(r.json()) <= 1


def test_commit_search_endpoint(client):
    r = client.get("/api/stats/commits/search?q=none")
    assert r.status_code == 200
    assert r.json()["code"] == 200


def test_streak_stats(sample_repo, client):
    _add_commit(sample_repo)
    r = client.get("/api/stats/streak")
    assert r.status_code == 200
    assert "data" in r.json()
    assert "current" in r.json()["data"]


def test_token_stats_returns_source(client):
    r = client.get("/api/stats/tokens?range=thisWeek")
    assert r.status_code == 200
    body = r.json()
    assert "source" in body
    assert body["source"] in ("demo", "logs")


def test_token_budget_get(client):
    r = client.get("/api/stats/tokens/budget")
    assert r.status_code == 200
    assert "monthlyBudget" in r.json()


def test_token_budget_post(client):
    r = client.post("/api/stats/tokens/budget", json={"monthlyBudget": 88.5})
    assert r.status_code == 200
    assert r.json()["monthlyBudget"] == 88.5


def test_invalid_date_returns_400(client):
    r = client.get("/api/stats/overview?startDate=bad&endDate=2024-01-01")
    assert r.status_code == 400


def test_repo_comparison(sample_repo, client):
    _add_commit(sample_repo)
    r = client.get("/api/stats/repo-comparison?range=year")
    assert r.status_code == 200
