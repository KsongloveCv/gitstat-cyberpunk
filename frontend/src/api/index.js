const API_BASE = import.meta.env.VITE_API_BASE || '/api'

// ━━━ Generic API helpers ━━━

function appendRepoParams(params, repos) {
  if (repos && repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }
  return params
}

async function apiGet(path, queryParams = {}) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(queryParams)) {
    if (value === null || value === undefined || value === '' || value === false) continue
    if (Array.isArray(value)) {
      if (value.includes('all')) continue  // 'all' means no filter, skip
      value.forEach(v => params.append(key, v))
    } else {
      params.append(key, value)
    }
  }
  const qs = params.toString()
  const url = qs ? `${API_BASE}${path}?${qs}` : `${API_BASE}${path}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  return response.json()
}

async function apiPost(path, body = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: `API error: ${response.status}` }))
    throw new Error(err.detail || `API error: ${response.status}`)
  }
  return response.json()
}

// ━━━ Scan & Config ━━━

export async function setScanPath(path) {
  return apiPost('/scan/path', { path })
}

export async function getScanPath() {
  const data = await apiGet('/scan/path')
  return { path: data.data?.path || '', version: data.data?.version || '' }
}

export async function refreshScan() {
  return apiPost('/scan/refresh')
}

export async function getVersion() {
  const data = await apiGet('/version')
  return data.version
}

// ━━━ Repositories ━━━

export async function getRepositories(includeCommits = false) {
  const data = await apiGet('/repositories', { includeCommits })
  return data.data ?? data
}

export async function getUserIdentity() {
  const data = await apiGet('/user/identity')
  return data.data
}

export async function getReposList() {
  return apiGet('/repos/list')
}

export async function getRepoInfo(path) {
  const data = await apiGet('/repos/info', { path })
  return data
}

export async function getRepoStats(path) {
  const data = await apiGet('/repos/stats', { path })
  return data
}

export async function analyzeRepo(path) {
  return apiPost('/repos/analyze', { path })
}

// ━━━ Stats ━━━

export async function getOverviewStats(startDate = null, endDate = null, repos = []) {
  return apiGet('/stats/overview', { startDate, endDate, repo: repos })
}

export async function getDailyStats(email, timeRange = 'week', repos = [], startDate = null, endDate = null) {
  return apiGet('/stats/daily', { email, range: timeRange, startDate, endDate, repo: repos })
}

export async function getWeeklyStats(email, timeRange = 'week', repos = [], startDate = null, endDate = null) {
  return apiGet('/stats/weekly', { email, range: timeRange, startDate, endDate, repo: repos })
}

export async function getMonthlyStats(email, timeRange = 'month', repos = [], startDate = null, endDate = null) {
  return apiGet('/stats/monthly', { email, range: timeRange, startDate, endDate, repo: repos })
}

export async function getYearlyStats(email, timeRange = 'year', repos = [], startDate = null, endDate = null) {
  return apiGet('/stats/yearly', { email, range: timeRange, startDate, endDate, repo: repos })
}

export async function getAuthorRank(repos = [], startDate = null, endDate = null, timeRange = 'week') {
  return apiGet('/stats/authors', { startDate, endDate, range: timeRange, repo: repos })
}

export async function getActivityHeatmap(repos = [], startDate = null, endDate = null) {
  return apiGet('/stats/activity-heatmap', { startDate, endDate, repo: repos })
}

export async function getRepoComparison(repos = [], startDate = null, endDate = null, timeRange = 'week') {
  return apiGet('/stats/repo-comparison', { startDate, endDate, range: timeRange, repo: repos })
}

export async function getCommitList(range = 'today', repos = [], startDate = null, endDate = null, limit = 50) {
  return apiGet('/stats/commit-list', { range, startDate, endDate, limit, repo: repos })
}

export async function searchCommits(q = '', limit = 50, offset = 0) {
  const data = await apiGet('/stats/commits/search', { q, limit, offset })
  return data.data
}

export async function getStatsSummary(range = 'week') {
  const data = await apiGet('/stats/summary', { range })
  return data.data
}

// ━━━ Streak ━━━

export async function getStreakStats(repos = []) {
  const data = await apiGet('/stats/streak', { repo: repos })
  return data.data
}

export async function getContributionCalendar(repos = [], days = 365) {
  const data = await apiGet('/stats/contribution-calendar', { repo: repos, days })
  return data.data
}

// ━━━ Token Analytics ━━━

export async function getTokenStats(range = 'thisWeek', model = 'all') {
  const data = await apiGet('/stats/tokens', { range, model: model !== 'all' ? model : null })
  return { data: data.data, source: data.source || 'logs' }
}

export async function getTokenBudget() {
  return apiGet('/stats/tokens/budget')
}

export async function setTokenBudget(monthlyBudget) {
  return apiPost('/stats/tokens/budget', { monthlyBudget })
}

// ━━━ Weather ━━━

export async function getWeatherCurrent(lat, lon) {
  const data = await apiGet('/weather/current', { lat, lon })
  return data.data
}

export async function getWeatherForecast(lat, lon, days = 7) {
  const data = await apiGet('/weather/forecast', { lat, lon, days })
  return data.data
}

// ━━━ Export ━━━

export async function exportData(includeCommits = true) {
  const response = await fetch(`${API_BASE}/export/json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ includeCommits }),
  })
  if (!response.ok) throw new Error('Export failed')
  return response.blob()
}

// ━━━ Gitee ━━━

export async function getGiteeRepos(owner, page = 1, perPage = 30) {
  const data = await apiGet('/gitee/repos', { owner, page, perPage })
  return data.data || []
}

export async function getGiteeRepoInfo(owner, repo) {
  const data = await apiGet('/gitee/repos/info', { owner, repo })
  return data.data
}

export async function cloneGiteeRepo(owner, repo, cloneUrl) {
  const data = await apiPost('/gitee/repos/clone', { owner, repo, cloneUrl })
  return data.data
}

export async function analyzeGiteeRepo(path) {
  return apiPost('/gitee/repos/analyze', { path })
}

export async function removeGiteeRepo(path) {
  return apiPost('/gitee/repos/remove', { path })
}