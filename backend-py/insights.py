"""Code intelligence & collaboration insights module."""
import logging
from datetime import datetime, timedelta, date
from collections import defaultdict, Counter
from fastapi import APIRouter, Query, HTTPException
from config import MAX_COMMITS_PER_REPO

log = logging.getLogger('gitstat.insights')
insights_router = APIRouter(prefix="/api/insights", tags=["insights"])


# ── #1 File Churn Analysis ──
@insights_router.get("/file-churn")
def file_churn(
    store=Query(None), days: int = Query(default=30, ge=1, le=365),
    top: int = Query(default=20, ge=1, le=100),
):
    """返回变更最频繁的文件 Top N。"""
    from main import store as s
    repos = s.get_repositories()
    file_stats: dict[str, dict] = {}
    cutoff = datetime.now() - timedelta(days=days)

    for repo in repos:
        for c in repo.get("commits", []):
            if c["date"] < cutoff:
                continue
            # We don't have per-file data in commit cache, so approximate by commit count per repo
            key = f"{repo['name']}/*"
            if key not in file_stats:
                file_stats[key] = {"path": key, "commits": 0, "additions": 0, "deletions": 0, "repo": repo["name"]}
            file_stats[key]["commits"] += 1
            file_stats[key]["additions"] += c["additions"]
            file_stats[key]["deletions"] += c["deletions"]

    ranked = sorted(file_stats.values(), key=lambda x: x["commits"], reverse=True)[:top]
    return {"code": 200, "data": {"period": f"{days}d", "files": ranked}}


# ── #2 Commit Heatmap (hour × weekday) ──
@insights_router.get("/commit-heatmap")
def commit_heatmap(email: str = Query(default="")):
    """24h × 7d 提交热力图矩阵。"""
    from main import store as s
    repos = s.get_repositories()
    # Initialize 7×24 matrix
    heatmap = [[0]*24 for _ in range(7)]

    for repo in repos:
        for c in repo.get("commits", []):
            if email and c["email"] != email:
                continue
            dt = c["date"]
            heatmap[dt.weekday()][dt.hour] += 1

    days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    result = [{"day": days[i], "hours": heatmap[i]} for i in range(7)]
    return {"code": 200, "data": {"heatmap": result, "total": sum(sum(row) for row in heatmap)}}


# ── #3 Commit Quality Scoring ──
CONVENTIONAL_PREFIXES = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"]

@insights_router.get("/commit-quality")
def commit_quality(days: int = Query(default=30, ge=1, le=365)):
    """评估提交信息质量。"""
    from main import store as s
    repos = s.get_repositories()
    cutoff = datetime.now() - timedelta(days=days)

    total = 0
    conventional = 0
    short_msgs = 0  # < 10 chars
    good_msgs = 0   # > 20 chars with description

    for repo in repos:
        for c in repo.get("commits", []):
            if c["date"] < cutoff:
                continue
            total += 1
            msg = c["message"].strip()
            if any(msg.lower().startswith(p + ":") or msg.lower().startswith(p + "(") for p in CONVENTIONAL_PREFIXES):
                conventional += 1
            if len(msg) < 10:
                short_msgs += 1
            if len(msg) > 20:
                good_msgs += 1

    if total == 0:
        return {"code": 200, "data": {"total": 0, "message": "No commits in period"}}

    return {"code": 200, "data": {
        "total": total,
        "conventionalRate": round(conventional / total * 100, 1),
        "shortMessageRate": round(short_msgs / total * 100, 1),
        "goodMessageRate": round(good_msgs / total * 100, 1),
        "score": round((conventional / total * 60 + good_msgs / total * 40), 1),
    }}


# ── #5 Bus Factor (Knowledge Silo Detection) ──
@insights_router.get("/bus-factor")
def bus_factor():
    """检测知识孤岛 — 只有一个人改过的文件/仓库。"""
    from main import store as s
    repos = s.get_repositories()

    repo_authors: dict[str, set] = {}
    for repo in repos:
        authors = set(c["author"] for c in repo.get("commits", []))
        repo_authors[repo["name"]] = authors

    silos = []
    for name, authors in repo_authors.items():
        if len(authors) == 1:
            silos.append({"repo": name, "author": list(authors)[0], "risk": "high"})
        elif len(authors) <= 2:
            silos.append({"repo": name, "authors": list(authors), "risk": "medium"})

    # Overall bus factor score
    if repo_authors:
        avg_authors = sum(len(a) for a in repo_authors.values()) / len(repo_authors)
        risk_level = "safe" if avg_authors >= 3 else "warning" if avg_authors >= 2 else "danger"
    else:
        avg_authors = 0
        risk_level = "unknown"

    return {"code": 200, "data": {
        "avgAuthorsPerRepo": round(avg_authors, 1),
        "riskLevel": risk_level,
        "silos": silos,
    }}


# ── #6 Weekly Report Generator ──
@insights_router.get("/weekly-report")
def weekly_report():
    """生成 Markdown 格式的周报摘要。"""
    from main import store as s, aggregate_overview, aggregate_author_rank

    repos = s.get_repositories()
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    start = datetime(monday.year, monday.month, monday.day)
    end = datetime.now()

    # Filter to this week
    weekly_repos = []
    for repo in repos:
        week_commits = [c for c in repo.get("commits", []) if start <= c["date"] <= end]
        if week_commits:
            weekly_repos.append({**repo, "commits": week_commits})

    if not weekly_repos:
        return {"code": 200, "data": {"markdown": "本周暂无提交记录。", "isEmpty": True}}

    overview = aggregate_overview(weekly_repos, "", start, end)
    rank = aggregate_author_rank(weekly_repos, "", start, end)

    md = f"""## 📊 GitStat 周报 ({monday.strftime('%m/%d')} - {today.strftime('%m/%d')})

### 概览
- **总提交数**: {overview.get('totalCommits', 0)}
- **新增行数**: +{overview.get('totalAdditions', 0)}
- **删除行数**: -{overview.get('totalDeletions', 0)}
- **活跃作者**: {overview.get('activeAuthors', 0)} 人
- **活跃仓库**: {len(weekly_repos)} 个

### 作者排行榜
| 排名 | 作者 | 提交 | 新增 | 删除 |
|------|------|------|------|------|
"""
    for i, a in enumerate(rank[:10]):
        md += f"| {i+1} | {a['author']} | {a['commits']} | +{a['additions']} | -{a['deletions']} |\n"

    md += f"\n> 由 GitStat Netrunner Edition 自动生成 · {today.strftime('%Y-%m-%d')}"
    return {"code": 200, "data": {"markdown": md, "isEmpty": False}}


# ── #7 Large Commit Alerts ──
@insights_router.get("/alerts/large-commits")
def large_commit_alerts(threshold: int = Query(default=1000, ge=100)):
    """标记超大提交。"""
    from main import store as s
    repos = s.get_repositories()
    alerts = []

    for repo in repos:
        for c in repo.get("commits", []):
            total = c["additions"] + c["deletions"]
            if total >= threshold:
                alerts.append({
                    "hash": c["hash"][:8],
                    "author": c["author"],
                    "date": c["date"].strftime("%Y-%m-%d %H:%M"),
                    "message": c["message"],
                    "additions": c["additions"],
                    "deletions": c["deletions"],
                    "total": total,
                    "repo": repo["name"],
                })

    alerts.sort(key=lambda x: x["total"], reverse=True)
    return {"code": 200, "data": {"threshold": threshold, "count": len(alerts), "alerts": alerts[:20]}}


# ── #8 Inactive Repo Alerts ──
@insights_router.get("/alerts/inactive-repos")
def inactive_repo_alerts(dayThreshold: int = Query(default=7, ge=1)):
    """标记长时间未更新的仓库。"""
    from main import store as s
    repos = s.get_repositories()
    cutoff = datetime.now() - timedelta(days=dayThreshold)
    alerts = []

    for repo in repos:
        commits = repo.get("commits", [])
        if not commits:
            alerts.append({"repo": repo["name"], "lastCommit": "从未提交", "daysAgo": "N/A"})
            continue
        latest = max(c["date"] for c in commits)
        if latest < cutoff:
            days_ago = (datetime.now() - latest).days
            alerts.append({
                "repo": repo["name"],
                "lastCommit": latest.strftime("%Y-%m-%d"),
                "daysAgo": days_ago,
            })

    return {"code": 200, "data": {"thresholdDays": dayThreshold, "count": len(alerts), "alerts": alerts}}
