# Gitee Stats Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Gitee (码云) code statistics page using Gitee Open API for repo browsing + local git clone for deep analysis.

**Architecture:** Backend adds `/api/gitee/*` routes proxying Gitee API v5 with no auth (public repos only), plus clone-to-cache + git-log parsing reusing existing `run_git_log()` and `analyze_repo_deep()`. Frontend adds a `GiteeStats.vue` page with a search bar, repo list panel, and deep analysis results panel, accessible via a new nav tab.

**Tech Stack:** Python 3 (FastAPI + urllib + subprocess/git), Vue 3 + ECharts (matches existing stack)

---

### Task 1: Backend — Gitee API helpers

**Files:**
- Modify: `backend-py/main.py` (insert after CONFIG section, around line 36)

- [ ] **Step 1: Add Gitee API constants and helper function**

Insert after `VERSION` and `MAX_COMMITS_PER_REPO` lines (after line 34):

```python
# Gitee API
GITEE_API_BASE = "https://gitee.com/api/v5"
GITEE_CACHE_DIR = Path.home() / ".gitstat-gitee-cache"


def gitee_api(path: str) -> dict:
    """调用 Gitee Open API v5，返回 JSON。"""
    url = f"{GITEE_API_BASE}{path}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "GitStat/2.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(503, f"Gitee API unavailable: {e}")


def gitee_list_repos(owner: str, page: int = 1, per_page: int = 30) -> list[dict]:
    """获取某用户/组织的公开仓库列表。"""
    raw = gitee_api(f"/users/{owner}/repos?page={page}&per_page={per_page}&sort=updated")
    if not isinstance(raw, list):
        return []
    return [{
        "id": r.get("id"),
        "name": r.get("name"),
        "fullName": r.get("full_name"),
        "description": r.get("description", ""),
        "htmlUrl": r.get("html_url"),
        "sshUrl": r.get("ssh_url"),
        "cloneUrl": r.get("clone_url"),
        "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0),
        "language": r.get("language", ""),
        "updatedAt": r.get("updated_at", ""),
        "pushedAt": r.get("pushed_at", ""),
        "createdAt": r.get("created_at", ""),
    } for r in raw]


def gitee_get_repo(owner: str, repo: str) -> dict:
    """获取单个仓库信息。"""
    r = gitee_api(f"/repos/{owner}/{repo}")
    return {
        "id": r.get("id"),
        "name": r.get("name"),
        "fullName": r.get("full_name"),
        "description": r.get("description", ""),
        "htmlUrl": r.get("html_url"),
        "sshUrl": r.get("ssh_url"),
        "cloneUrl": r.get("clone_url"),
        "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0),
        "language": r.get("language", ""),
        "updatedAt": r.get("updated_at", ""),
        "pushedAt": r.get("pushed_at", ""),
        "createdAt": r.get("created_at", ""),
        "commitsCount": r.get("commits_count", 0),
        "watchers": r.get("watchers_count", 0),
        "defaultBranch": r.get("default_branch", "master"),
    }
```

- [ ] **Step 2: Run backend to verify no syntax errors**

```bash
cd backend-py && python3 -c "import main; print('OK')"
```

Expected: "OK" (no import errors)

- [ ] **Step 3: Commit**

```bash
git add backend-py/main.py
git commit -m "feat: add Gitee API helper functions"
```

---

### Task 2: Backend — Clone + Analyze helpers

**Files:**
- Modify: `backend-py/main.py` (insert after Task 1's code)

- [ ] **Step 1: Add clone_gitee_repo function**

```python
def clone_gitee_repo(clone_url: str, owner: str, repo: str) -> dict:
    """Clone 一个 Gitee 仓库到本地缓存目录，返回路径信息。"""
    GITEE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target_dir = GITEE_CACHE_DIR / f"{owner}_{repo}"

    if target_dir.exists():
        # 已存在则 pull
        try:
            result = subprocess.run(
                ["git", "-C", str(target_dir), "pull", "--ff-only"],
                capture_output=True, text=True, timeout=60
            )
        except (subprocess.TimeoutExpired, OSError):
            pass
    else:
        # Clone
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "100", clone_url, str(target_dir)],
                capture_output=True, text=True, timeout=120
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "Clone timed out")
        except OSError as e:
            raise HTTPException(500, f"Clone failed: {e}")

        if result.returncode != 0:
            # 清理失败的目录
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)
            raise HTTPException(400, f"Clone failed: {result.stderr}")

    return {
        "path": str(target_dir),
        "name": repo,
        "owner": owner,
        "cloneUrl": clone_url,
    }


def gitee_load_commits(repo_path: str) -> list[dict]:
    """在已 clone 的 Gitee 仓库上运行 git log 解析。"""
    return run_git_log(repo_path)
```

- [ ] **Step 2: Run backend to verify no syntax errors**

```bash
cd backend-py && python3 -c "import main; print('OK')"
```

Expected: "OK"

- [ ] **Step 3: Commit**

```bash
git add backend-py/main.py
git commit -m "feat: add Gitee clone and git-log helpers"
```

---

### Task 3: Backend — Gitee API Routes

**Files:**
- Modify: `backend-py/main.py` (insert before the Static Files section, around line 1775)

- [ ] **Step 1: Add /api/gitee/repos route**

```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GITEE — 码云代码统计 API Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/api/gitee/repos")
def api_gitee_list_repos(
    owner: str = Query(..., description="Gitee 用户名或组织名"),
    page: int = Query(default=1),
    perPage: int = Query(default=30),
):
    """代理 Gitee API：获取某用户/组织的仓库列表。"""
    if not owner or not re.match(r'^[a-zA-Z0-9_-]+$', owner):
        raise HTTPException(400, "Invalid owner name")
    try:
        repos = gitee_list_repos(owner, page, perPage)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Gitee API error: {e}")
    return {"code": 200, "data": repos}
```

- [ ] **Step 2: Add /api/gitee/repos/info route**

```python
@app.get("/api/gitee/repos/info")
def api_gitee_repo_info(
    owner: str = Query(...),
    repo: str = Query(...),
):
    """获取单个 Gitee 仓库详情。"""
    try:
        info = gitee_get_repo(owner, repo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Gitee API error: {e}")
    return {"code": 200, "data": info}
```

- [ ] **Step 3: Add /api/gitee/repos/clone route**

```python
@app.post("/api/gitee/repos/clone")
async def api_gitee_clone(request: Request):
    """Clone Gitee 仓库到本地缓存，注册到 Store，返回基础提交统计。"""
    body = await request.json()
    owner = body.get("owner", "")
    repo_name = body.get("repo", "")
    clone_url = body.get("cloneUrl", "")

    if not clone_url and owner and repo_name:
        clone_url = f"https://gitee.com/{owner}/{repo_name}.git"
    if not clone_url:
        raise HTTPException(400, "cloneUrl is required")

    # Extract owner/repo from clone_url if not provided
    if not owner or not repo_name:
        m = re.search(r'gitee\.com/([^/]+)/([^/]+?)(?:\.git)?$', clone_url)
        if m:
            owner, repo_name = m.group(1), m.group(2)
        else:
            owner, repo_name = "unknown", clone_url.split("/")[-1].replace(".git", "")

    # Clone to cache
    clone_result = clone_gitee_repo(clone_url, owner, repo_name)
    local_path = clone_result["path"]

    # Parse git log
    commits = run_git_log(local_path)

    # Register in Store so existing stats APIs work
    repo_meta = get_repo_meta(local_path)
    store.register_repos([{
        "path": local_path,
        "name": f"[Gitee] {owner}/{repo_name}",
        "userEmail": "",
        "currentBranch": repo_meta.get("currentBranch", "master"),
        "lastCommitTime": repo_meta.get("lastCommitTime", ""),
    }])
    store.set_repo_commits(local_path, commits)

    return {
        "code": 200,
        "data": {
            "path": local_path,
            "name": f"{owner}/{repo_name}",
            "commitCount": len(commits),
            "cloneUrl": clone_url,
        },
        "message": "Clone and parse complete",
    }
```

- [ ] **Step 4: Add /api/gitee/repos/analyze route**

```python
@app.post("/api/gitee/repos/analyze")
async def api_gitee_analyze(request: Request):
    """对已 clone 的 Gitee 仓库进行深度分析（复用现有逻辑）。"""
    body = await request.json()
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "path is required")

    cache = store.get_repo_cache(path)
    if not cache:
        raise HTTPException(404, "Repo not found. Clone first.")

    if cache.get("analyzed"):
        return {
            "name": cache["name"], "path": cache["path"],
            "branchCount": cache["branchCount"], "branches": cache["branches"],
            "fileCount": cache["fileCount"], "totalLines": cache["totalLines"],
            "languages": cache["languages"],
        }

    result = analyze_repo_deep(path)
    store.update_repo(
        path,
        branchCount=result["branchCount"],
        branches=result["branches"],
        fileCount=result["fileCount"],
        totalLines=result["totalLines"],
        languages=result["languages"],
        analyzed=True,
    )
    return result
```

- [ ] **Step 5: Add /api/gitee/repos/remove route**

```python
@app.post("/api/gitee/repos/remove")
async def api_gitee_remove(request: Request):
    """从 Store 中移除已加载的 Gitee 仓库（不删除本地缓存文件）。"""
    body = await request.json()
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "path is required")
    # Store doesn't have a direct remove, but we can clear its commits
    cache = store.get_repo_cache(path)
    if cache:
        cache["initialized"] = False
        cache["commits"] = []
        cache["analyzed"] = False
    return {"code": 200, "message": "Repo removed from memory"}
```

- [ ] **Step 6: Verify routes load correctly**

```bash
cd backend-py && python3 -c "
import main
routes = [r.path for r in main.app.routes]
assert '/api/gitee/repos' in routes
assert '/api/gitee/repos/info' in routes
assert '/api/gitee/repos/clone' in routes
assert '/api/gitee/repos/analyze' in routes
assert '/api/gitee/repos/remove' in routes
print('All Gitee routes registered OK')
"
```

Expected: "All Gitee routes registered OK"

- [ ] **Step 7: Commit**

```bash
git add backend-py/main.py
git commit -m "feat: add Gitee API routes (list/info/clone/analyze/remove)"
```

---

### Task 4: Frontend — i18n strings

**Files:**
- Modify: `frontend/src/i18n.js` (add `gitee` section to both `zh` and `en`)

- [ ] **Step 1: Add Gitee i18n strings**

In `zh.nav`, add `gitee: 'Gitee'` after the `github: 'GitHub'` line. In `en.nav`, add `gitee: 'Gitee'` after the `github: 'GitHub'` line.

Then add a top-level `gitee` section to both `zh` and `en`:

```javascript
// Add to zh object after 'weather' section:
    gitee: {
      title: 'Gitee 代码统计',
      subtitle: '码云仓库浏览 · 深度分析 · 混合模式',
      searchPlaceholder: '输入 Gitee 用户名或组织名...',
      scanRepos: '扫描仓库',
      scanning: '扫描中...',
      repoList: '仓库列表',
      deepAnalyze: '深度分析',
      analyzing: '分析中...',
      analyzed: '已分析',
      cachedRepos: '已缓存仓库',
      noData: '请输入用户名开始探索 Gitee 仓库',
      loading: '加载中...',
      stars: '星',
      commits: '次提交',
      updated: '更新于',
      cloneFirst: '请先克隆仓库',
      removeRepo: '移除',
      totalCommits: '总提交数',
      totalAdditions: '新增行数',
      totalDeletions: '删除行数',
      activeAuthors: '活跃作者',
    },

// Add to en object after 'weather' section:
    gitee: {
      title: 'Gitee Stats',
      subtitle: 'Repo Browser · Deep Analysis · Hybrid Mode',
      searchPlaceholder: 'Enter Gitee username or org...',
      scanRepos: 'Scan Repos',
      scanning: 'Scanning...',
      repoList: 'Repository List',
      deepAnalyze: 'Deep Analyze',
      analyzing: 'Analyzing...',
      analyzed: 'Analyzed',
      cachedRepos: 'Cached Repos',
      noData: 'Enter a username to explore Gitee repositories',
      loading: 'Loading...',
      stars: 'stars',
      commits: 'commits',
      updated: 'updated',
      cloneFirst: 'Clone the repo first',
      removeRepo: 'Remove',
      totalCommits: 'Total Commits',
      totalAdditions: 'Additions',
      totalDeletions: 'Deletions',
      activeAuthors: 'Active Authors',
    },
```

- [ ] **Step 2: Verify i18n structure**

```bash
cd frontend && node -e "
const fs = require('fs');
eval(fs.readFileSync('src/i18n.js', 'utf8').replace('export function', 'function'));
// Just verify the file parses without error
console.log('i18n OK');
"
```

Expected: "i18n OK" (no parse errors)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/i18n.js
git commit -m "feat: add Gitee i18n strings (zh/en)"
```

---

### Task 5: Frontend — API functions

**Files:**
- Modify: `frontend/src/api/index.js` (append new functions)

- [ ] **Step 1: Add Gitee API functions**

Append to `src/api/index.js`:

```javascript
// ━━━ Gitee API ━━━

export async function getGiteeRepos(owner, page = 1, perPage = 30) {
  const params = new URLSearchParams({ owner, page, perPage })
  const response = await fetch(`${API_BASE}/gitee/repos?${params}`)

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to fetch Gitee repos')
  }

  const data = await response.json()
  return data.data || []
}

export async function getGiteeRepoInfo(owner, repo) {
  const params = new URLSearchParams({ owner, repo })
  const response = await fetch(`${API_BASE}/gitee/repos/info?${params}`)

  if (!response.ok) {
    throw new Error('Failed to fetch Gitee repo info')
  }

  const data = await response.json()
  return data.data
}

export async function cloneGiteeRepo(owner, repo, cloneUrl) {
  const response = await fetch(`${API_BASE}/gitee/repos/clone`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ owner, repo, cloneUrl })
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to clone Gitee repo')
  }

  const data = await response.json()
  return data.data
}

export async function analyzeGiteeRepo(path) {
  const response = await fetch(`${API_BASE}/gitee/repos/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  })

  if (!response.ok) {
    throw new Error('Failed to analyze Gitee repo')
  }

  return response.json()
}

export async function removeGiteeRepo(path) {
  const response = await fetch(`${API_BASE}/gitee/repos/remove`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  })

  if (!response.ok) {
    throw new Error('Failed to remove Gitee repo')
  }

  return response.json()
}
```

- [ ] **Step 2: Verify the file parses**

```bash
cd frontend && node -e "
const fs = require('fs');
const src = fs.readFileSync('src/api/index.js', 'utf8');
// Verify exports exist
console.log('Exports found:', (src.match(/export async function/g) || []).length);
console.log('API OK');
"
```

Expected: shows 25+ exports, "API OK"

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "feat: add Gitee API frontend functions"
```

---

### Task 6: Frontend — App.vue navigation

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Register GiteeStats component and add nav entry**

In `<script setup>`, add the component import (after the Settings import):

```javascript
const GiteeStats = defineAsyncComponent(() => import('./views/GiteeStats.vue'))
```

Update `componentMap` to include gitee:

```javascript
const componentMap = {
  dashboard: Dashboard, analytics: Analytics, tokens: TokenAnalytics,
  repos: RepoSection, gitee: GiteeStats, settings: Settings
}
```

In the `<template>`, add the nav link after the "仓库信息" nav link (after line 47):

```html
<a @click="setView('gitee')" :class="{ active: currentView === 'gitee' }">
  <span class="nav-icon">◆</span>
  {{ t('nav.gitee') }}
</a>
```

- [ ] **Step 2: Verify the file compiles in dev mode**

Since Vite dev server proxies to the Python backend, first ensure the backend is running, then:

```bash
cd frontend && npx vite build --emptyOutDir 2>&1 | tail -5
```

Expected: "✓ built in X.XXs" (no errors)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat: add GiteeStats nav entry in App.vue"
```

---

### Task 7: Frontend — GiteeStats.vue page

**Files:**
- Create: `frontend/src/views/GiteeStats.vue`

- [ ] **Step 1: Create the main GiteeStats page component**

```vue
<template>
  <div class="gitee-page">
    <!-- Header -->
    <div class="page-header">
      <h2 class="page-title">
        <span class="title-icon">◆</span>
        {{ t('gitee.title') }}
      </h2>
      <p class="page-subtitle">{{ t('gitee.subtitle') }}</p>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <input
        v-model="ownerName"
        class="search-input"
        :placeholder="t('gitee.searchPlaceholder')"
        @keyup.enter="scanRepos"
      />
      <button
        class="search-btn"
        :disabled="!ownerName.trim() || loading"
        @click="scanRepos"
      >
        <span v-if="!loading">{{ t('gitee.scanRepos') }}</span>
        <span v-else class="btn-loading">⚡ {{ t('gitee.scanning') }}</span>
      </button>
    </div>

    <!-- No data state -->
    <div v-if="!hasScanned" class="empty-state">
      <div class="empty-icon">🔍</div>
      <p>{{ t('gitee.noData') }}</p>
    </div>

    <!-- Main content -->
    <div v-else class="gitee-content">
      <!-- Repo List -->
      <div class="repo-list-panel">
        <h3 class="panel-title">{{ t('gitee.repoList') }}</h3>
        <div v-if="repos.length === 0 && loading" class="loading-state">
          {{ t('gitee.loading') }}
        </div>
        <div v-else-if="repos.length === 0" class="empty-state small">
          没有找到公开仓库
        </div>
        <div v-else class="repo-cards">
          <div
            v-for="repo in repos"
            :key="repo.id"
            class="repo-card"
            :class="{ 'is-analyzing': analyzingPath === repo.cloneUrl }"
          >
            <div class="repo-card-header">
              <span class="repo-name">{{ repo.fullName }}</span>
              <span class="repo-lang" v-if="repo.language">{{ repo.language }}</span>
            </div>
            <p class="repo-desc" v-if="repo.description">{{ repo.description }}</p>
            <div class="repo-meta">
              <span>⭐ {{ repo.stars }}</span>
              <span>🕐 {{ formatDate(repo.pushedAt) }}</span>
            </div>
            <div class="repo-actions">
              <button
                class="action-btn clone-btn"
                :disabled="analyzingPath === repo.cloneUrl"
                @click="cloneAndAnalyze(repo)"
              >
                <span v-if="analyzingPath !== repo.cloneUrl">{{ t('gitee.deepAnalyze') }}</span>
                <span v-else>⚡ {{ t('gitee.analyzing') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Analysis Results Panel -->
      <div class="analysis-panel">
        <h3 class="panel-title">📊 深度分析结果</h3>
        <div v-if="cachedRepos.length === 0" class="empty-state small">
          <p>{{ t('gitee.cloneFirst') }}</p>
        </div>

        <div v-for="cr in cachedRepos" :key="cr.path" class="cached-repo">
          <div class="cached-header">
            <span class="cached-name">[Gitee] {{ cr.name }}</span>
            <button class="remove-btn" @click="removeRepo(cr.path)">✕ {{ t('gitee.removeRepo') }}</button>
          </div>

          <!-- Overview stats -->
          <div v-if="cr.stats" class="stats-row">
            <div class="stat-item">
              <span class="stat-val">{{ cr.stats.commitCount || 0 }}</span>
              <span class="stat-label">{{ t('gitee.totalCommits') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-val add">+{{ cr.stats.totalAdditions || 0 }}</span>
              <span class="stat-label">{{ t('gitee.totalAdditions') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-val del">-{{ cr.stats.totalDeletions || 0 }}</span>
              <span class="stat-label">{{ t('gitee.totalDeletions') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-val">{{ cr.stats.contributorCount || 0 }}</span>
              <span class="stat-label">{{ t('gitee.activeAuthors') }}</span>
            </div>
          </div>

          <!-- Analyze button -->
          <button
            v-if="!cr.analyzed"
            class="action-btn analyze-btn"
            :disabled="analyzingRepoPath === cr.path"
            @click="runDeepAnalyze(cr)"
          >
            <span v-if="analyzingRepoPath !== cr.path">🔬 深度分析代码结构</span>
            <span v-else>⚡ {{ t('gitee.analyzing') }}</span>
          </button>

          <!-- Analysis result -->
          <div v-if="cr.analyzed && cr.analysis" class="analysis-result">
            <div class="analysis-row">
              <span class="alabel">分支数</span>
              <span>{{ cr.analysis.branchCount }}</span>
            </div>
            <div class="analysis-row">
              <span class="alabel">文件数</span>
              <span>{{ cr.analysis.fileCount }}</span>
            </div>
            <div class="analysis-row">
              <span class="alabel">总行数</span>
              <span>{{ cr.analysis.totalLines.toLocaleString() }}</span>
            </div>
            <div class="analysis-langs" v-if="cr.analysis.languages?.length">
              <span
                v-for="lang in cr.analysis.languages.slice(0, 5)"
                :key="lang.name"
                class="lang-tag"
              >{{ lang.name }} {{ lang.percent }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useI18n } from '../i18n'
import * as api from '../api'

const { t } = useI18n()

const ownerName = ref('')
const loading = ref(false)
const hasScanned = ref(false)
const repos = ref([])
const analyzingPath = ref('')
const analyzingRepoPath = ref('')
const cachedRepos = reactive([])

async function scanRepos() {
  const owner = ownerName.value.trim()
  if (!owner) return

  loading.value = true
  hasScanned.value = true
  try {
    repos.value = await api.getGiteeRepos(owner)
  } catch (err) {
    console.error('Scan Gitee repos failed:', err)
    repos.value = []
  } finally {
    loading.value = false
  }
}

async function cloneAndAnalyze(repo) {
  analyzingPath.value = repo.cloneUrl
  try {
    const result = await api.cloneGiteeRepo(repo.owner || repo.fullName.split('/')[0], repo.name, repo.cloneUrl)
    // Compute stats from local repo
    const stats = await api.getRepoStats(result.path)
    const commits = stats.recentCommits || []
    const contributors = stats.contributors || []
    const totalAdditions = commits.reduce((sum, c) => sum + (c.additions || 0), 0)
    const totalDeletions = commits.reduce((sum, c) => sum + (c.deletions || 0), 0)

    cachedRepos.push({
      path: result.path,
      name: result.name,
      cloneUrl: repo.cloneUrl,
      analyzed: false,
      analysis: null,
      stats: {
        commitCount: result.commitCount,
        totalAdditions,
        totalDeletions,
        contributorCount: contributors.length,
      },
    })
  } catch (err) {
    console.error('Clone failed:', err)
    alert(`克隆失败: ${err.message}`)
  } finally {
    analyzingPath.value = ''
  }
}

async function runDeepAnalyze(cr) {
  analyzingRepoPath.value = cr.path
  try {
    const analysis = await api.analyzeGiteeRepo(cr.path)
    cr.analyzed = true
    cr.analysis = analysis
  } catch (err) {
    console.error('Analyze failed:', err)
  } finally {
    analyzingRepoPath.value = ''
  }
}

async function removeRepo(path) {
  try {
    await api.removeGiteeRepo(path)
    const idx = cachedRepos.findIndex(cr => cr.path === path)
    if (idx >= 0) cachedRepos.splice(idx, 1)
  } catch (err) {
    console.error('Remove failed:', err)
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now - d
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 30) return `${days} 天前`
  if (days < 365) return `${Math.floor(days / 30)} 个月前`
  return `${Math.floor(days / 365)} 年前`
}
</script>

<style scoped>
.gitee-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* ── Header ── */
.page-header {
  margin-bottom: 2rem;
  text-align: center;
}
.page-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.8rem;
  color: var(--neon-cyan);
  text-shadow: 0 0 12px rgba(0, 245, 255, 0.3);
  margin: 0 0 0.5rem;
  letter-spacing: 2px;
}
.title-icon { font-size: 1.6rem; }
.page-subtitle {
  color: #64748b;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
}

/* ── Search ── */
.search-bar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2rem;
  justify-content: center;
}
.search-input {
  width: 400px;
  padding: 0.75rem 1.25rem;
  background: rgba(8, 12, 32, 0.8);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 8px;
  color: #e2e8f0;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.9rem;
  outline: none;
  transition: all 0.3s;
}
.search-input:focus {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.15);
}
.search-input::placeholder { color: #475569; }

.search-btn {
  padding: 0.75rem 1.5rem;
  background: rgba(0, 245, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.4);
  border-radius: 8px;
  color: var(--neon-cyan);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s;
  letter-spacing: 1px;
}
.search-btn:hover:not(:disabled) {
  background: rgba(0, 245, 255, 0.2);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
}
.search-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Empty / Loading ── */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #94a3b8;
  font-family: 'Share Tech Mono', monospace;
}
.empty-icon { font-size: 3rem; margin-bottom: 1rem; }
.empty-state.small { padding: 2rem 1rem; font-size: 0.85rem; }
.loading-state {
  text-align: center;
  padding: 2rem;
  color: var(--neon-cyan);
  font-family: 'Share Tech Mono', monospace;
}

/* ── Content ── */
.gitee-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  align-items: start;
}

.panel-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1rem;
  color: #94a3b8;
  margin: 0 0 1rem;
  letter-spacing: 1px;
}

/* ── Repo Cards ── */
.repo-list-panel {
  background: rgba(8, 12, 32, 0.5);
  border: 1px solid rgba(0, 245, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
}
.repo-cards {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 600px;
  overflow-y: auto;
}
.repo-card {
  background: rgba(0, 245, 255, 0.03);
  border: 1px solid rgba(0, 245, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.3s;
}
.repo-card:hover {
  border-color: rgba(0, 245, 255, 0.3);
  box-shadow: 0 0 16px rgba(0, 245, 255, 0.05);
}
.repo-card.is-analyzing {
  border-color: rgba(255, 0, 255, 0.5);
  box-shadow: 0 0 16px rgba(255, 0, 255, 0.1);
}
.repo-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
}
.repo-name {
  color: #e2e8f0;
  font-weight: 600;
  font-size: 0.95rem;
}
.repo-lang {
  font-size: 0.65rem;
  padding: 2px 8px;
  background: rgba(0, 245, 255, 0.1);
  border-radius: 4px;
  color: var(--neon-cyan);
}
.repo-desc {
  color: #64748b;
  font-size: 0.75rem;
  margin: 0.4rem 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.repo-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.7rem;
  color: #475569;
  font-family: 'Share Tech Mono', monospace;
  margin: 0.5rem 0;
}
.repo-actions {
  margin-top: 0.5rem;
}
.action-btn {
  width: 100%;
  padding: 0.5rem 1rem;
  background: rgba(0, 245, 255, 0.08);
  border: 1px solid rgba(0, 245, 255, 0.25);
  border-radius: 6px;
  color: var(--neon-cyan);
  cursor: pointer;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
  transition: all 0.3s;
}
.action-btn:hover:not(:disabled) {
  background: rgba(0, 245, 255, 0.15);
  box-shadow: 0 0 12px rgba(0, 245, 255, 0.1);
}
.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── Analysis Panel ── */
.analysis-panel {
  background: rgba(8, 12, 32, 0.5);
  border: 1px solid rgba(255, 0, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  min-height: 200px;
}
.cached-repo {
  border: 1px solid rgba(255, 0, 255, 0.15);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  background: rgba(255, 0, 255, 0.02);
}
.cached-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.cached-name {
  color: var(--neon-cyan);
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.9rem;
}
.remove-btn {
  background: transparent;
  border: 1px solid rgba(255, 0, 0, 0.3);
  border-radius: 4px;
  color: #ef4444;
  cursor: pointer;
  font-size: 0.7rem;
  padding: 4px 8px;
  transition: all 0.3s;
}
.remove-btn:hover {
  background: rgba(255, 0, 0, 0.1);
  border-color: #ef4444;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}
.stat-item {
  text-align: center;
  padding: 0.5rem;
  background: rgba(0, 245, 255, 0.03);
  border-radius: 6px;
}
.stat-val {
  display: block;
  font-size: 1.2rem;
  font-weight: 700;
  color: #e2e8f0;
  font-family: 'Orbitron', sans-serif;
}
.stat-val.add { color: #10b981; }
.stat-val.del { color: #ef4444; }
.stat-label {
  font-size: 0.6rem;
  color: #64748b;
  font-family: 'Share Tech Mono', monospace;
}

.analyze-btn {
  margin-top: 0.5rem;
  border-color: rgba(255, 0, 255, 0.3);
  color: var(--neon-magenta);
}
.analyze-btn:hover:not(:disabled) {
  background: rgba(255, 0, 255, 0.1);
  box-shadow: 0 0 12px rgba(255, 0, 255, 0.1);
}

.analysis-result {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(0, 245, 255, 0.03);
  border-radius: 6px;
}
.analysis-row {
  display: flex;
  justify-content: space-between;
  padding: 0.3rem 0;
  font-size: 0.8rem;
  color: #94a3b8;
  border-bottom: 1px solid rgba(0, 245, 255, 0.05);
}
.alabel { color: #64748b; }
.analysis-langs {
  margin-top: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.lang-tag {
  font-size: 0.6rem;
  padding: 2px 8px;
  background: rgba(0, 245, 255, 0.08);
  border: 1px solid rgba(0, 245, 255, 0.15);
  border-radius: 4px;
  color: #94a3b8;
}

@media (max-width: 768px) {
  .gitee-content { grid-template-columns: 1fr; }
  .search-input { width: 100%; }
  .search-bar { flex-direction: column; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
}
</style>
```

- [ ] **Step 2: Build frontend to verify no compilation errors**

```bash
cd frontend && npx vite build --emptyOutDir 2>&1 | tail -10
```

Expected: "✓ built in X.XXs" (no errors)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/GiteeStats.vue
git commit -m "feat: add GiteeStats page component"
```

---

### Task 8: Integration — Rebuild frontend and verify

- [ ] **Step 1: Rebuild frontend**

```bash
cd frontend && npx vite build --emptyOutDir 2>&1
```

Expected: "✓ built in X.XXs"

- [ ] **Step 2: Restart backend**

```bash
# Kill old process
kill $(lsof -ti :12580) 2>/dev/null; sleep 1
cd backend-py && python3 main.py &
sleep 2
```

- [ ] **Step 3: Test Gitee API endpoint**

```bash
curl -s http://localhost:12580/api/gitee/repos?owner=vuejs | python3 -m json.tool | head -20
```

Expected: JSON response with repo list

- [ ] **Step 4: Verify frontend serves correctly**

```bash
curl -s http://localhost:12580/ | grep -o 'Gitee'
```

Expected: Should match (Gitee nav text is in the HTML via i18n JS, but it's a SPA so the text won't appear in curl output. Instead verify the build succeeded.)

Alternative: Just verify the built dist contains the Gitee chunk:

```bash
ls frontend/dist/assets/ | grep -i 'Gitee' && echo "Gitee chunk found"
```

- [ ] **Step 5: Open in Chrome to verify**

```bash
open -a "Google Chrome" http://localhost:12580
```

- [ ] **Step 6: Commit**

```bash
git add frontend/dist/
git commit -m "build: rebuild frontend with GiteeStats"
```

---

### Task 9: Final — End-to-end verification checklist

- [ ] Navigate to http://localhost:12580
- [ ] Click "Gitee" in the navigation bar
- [ ] Enter a Gitee username (e.g., "vuejs") and click "扫描仓库"
- [ ] Verify the repo list loads
- [ ] Click "深度分析" on a repo
- [ ] Verify the clone and stats appear in the right panel
- [ ] Click "深度分析代码结构" to verify deep analysis
- [ ] Click "移除" to verify removal
