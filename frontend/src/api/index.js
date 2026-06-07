const API_BASE = import.meta.env.VITE_API_BASE || '/api'

// Helper: append repo filter params (skip when 'all' or empty)
function appendRepoParams(params, repos) {
  if (repos && repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }
  return params
}

export async function setScanPath(path) {
  const response = await fetch(`${API_BASE}/scan/path`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  })
  
  if (!response.ok) {
    throw new Error('Set path failed')
  }
  
  return response.json()
}

export async function getScanPath() {
  const response = await fetch(`${API_BASE}/scan/path`)
  
  if (!response.ok) {
    throw new Error('Failed to fetch scan path')
  }
  
  const data = await response.json()
  return {
    path: data.data?.path || '',
    version: data.data?.version || ''
  }
}

export async function getOverviewStats(startDate = null, endDate = null, repos = []) {
  const params = new URLSearchParams()
  if (startDate) params.append('startDate', startDate)
  if (endDate) params.append('endDate', endDate)
  
  // repos为空或包含'all'时不传repo参数（后端返回所有仓库）
  appendRepoParams(params, repos)
  
  const url = `${API_BASE}/stats/overview?${params.toString()}`
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error('Failed to fetch stats')
  }
  
  return response.json()
}

export async function getRepositories(includeCommits = false) {
  const params = includeCommits ? '?includeCommits=true' : ''
  const response = await fetch(`${API_BASE}/repositories${params}`)
  
  if (!response.ok) {
    throw new Error('Failed to fetch repositories')
  }
  
  const data = await response.json()
  return data.data ?? data
}

export async function getUserIdentity() {
  const response = await fetch(`${API_BASE}/user/identity`)
  if (!response.ok) throw new Error('Failed to fetch user identity')
  const data = await response.json()
  return data.data
}

export async function refreshScan() {
  const response = await fetch(`${API_BASE}/scan/refresh`, { method: 'POST' })
  if (!response.ok) throw new Error('Refresh failed')
  return response.json()
}

export async function exportData(includeCommits = true) {
  const response = await fetch(`${API_BASE}/export/json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ includeCommits }),
  })
  
  if (!response.ok) {
    throw new Error('Export failed')
  }
  
  return response.blob()
}

export async function getDailyStats(email, timeRange = 'week', repos = [], startDate = null, endDate = null) {
  const params = new URLSearchParams()
  if (email) params.append('email', email)
  if (timeRange) params.append('range', timeRange)
  if (startDate) params.append('startDate', startDate)
  if (endDate) params.append('endDate', endDate)
  
  // repos为空或包含'all'时不传repo参数（后端返回所有仓库）
  appendRepoParams(params, repos)
  
  const url = `${API_BASE}/stats/daily?${params.toString()}`
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error('Failed to fetch daily stats')
  }
  
  return response.json()
}

export async function getAuthorRank(repos = [], startDate = null, endDate = null, timeRange = 'week') {
  const params = new URLSearchParams()
  if (startDate) params.append('startDate', startDate)
  if (endDate) params.append('endDate', endDate)
  if (timeRange) params.append('range', timeRange)
  
  appendRepoParams(params, repos)
  
  const url = `${API_BASE}/stats/authors?${params.toString()}`
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error('Failed to fetch author rank')
  }
  
  return response.json()
}

export async function getWeeklyStats(email, timeRange = 'week', repos = [], startDate = null, endDate = null) {
  const params = new URLSearchParams()
  if (email) params.append('email', email)
  if (timeRange) params.append('range', timeRange)
  if (startDate) params.append('startDate', startDate)
  if (endDate) params.append('endDate', endDate)

  appendRepoParams(params, repos)

  const url = `${API_BASE}/stats/weekly?${params.toString()}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch weekly stats')
  }

  return response.json()
}

export async function getMonthlyStats(email, timeRange = 'month', repos = [], startDate = null, endDate = null) {
  const params = new URLSearchParams()
  if (email) params.append('email', email)
  if (timeRange) params.append('range', timeRange)
  if (startDate) params.append('startDate', startDate)
  if (endDate) params.append('endDate', endDate)

  appendRepoParams(params, repos)

  const url = `${API_BASE}/stats/monthly?${params.toString()}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch monthly stats')
  }

  return response.json()
}

export async function getYearlyStats(email, timeRange = 'year', repos = [], startDate = null, endDate = null) {
  const params = new URLSearchParams()
  if (email) params.append('email', email)
  if (timeRange) params.append('range', timeRange)
  if (startDate) params.append('startDate', startDate)
  if (endDate) params.append('endDate', endDate)

  appendRepoParams(params, repos)

  const url = `${API_BASE}/stats/yearly?${params.toString()}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch yearly stats')
  }

  return response.json()
}

export async function getActivityHeatmap(repos = [], startDate = null, endDate = null) {
  const params = new URLSearchParams()
  if (startDate) params.append('startDate', startDate)
  if (endDate) params.append('endDate', endDate)
  
  appendRepoParams(params, repos)
  
  const url = `${API_BASE}/stats/activity-heatmap?${params.toString()}`
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error('Failed to fetch activity heatmap')
  }
  
  return response.json()
}

export async function getRepoComparison(repos = [], startDate = null, endDate = null, timeRange = 'week') {
  const params = new URLSearchParams()
  if (startDate) params.append('startDate', startDate)
  if (endDate) params.append('endDate', endDate)
  if (timeRange) params.append('range', timeRange)
  
  appendRepoParams(params, repos)
  
  const url = `${API_BASE}/stats/repo-comparison?${params.toString()}`
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error('Failed to fetch repo comparison')
  }
  
  return response.json()
}

export async function getReposList() {
  const response = await fetch(`${API_BASE}/repos/list`)

  if (!response.ok) {
    throw new Error('Failed to fetch repos list')
  }

  return response.json()
}

export async function getRepoInfo(path) {
  const params = new URLSearchParams({ path })
  const response = await fetch(`${API_BASE}/repos/info?${params}`)

  if (!response.ok) {
    throw new Error('Failed to fetch repo info')
  }

  return response.json()
}

export async function getRepoStats(path) {
  const params = new URLSearchParams({ path })
  const response = await fetch(`${API_BASE}/repos/stats?${params}`)

  if (!response.ok) {
    throw new Error('Failed to fetch repo stats')
  }

  return response.json()
}

export async function analyzeRepo(path) {
  const response = await fetch(`${API_BASE}/repos/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  })

  if (!response.ok) {
    throw new Error('Failed to analyze repo')
  }

  return response.json()
}

export async function getVersion() {
  const response = await fetch(`${API_BASE}/version`)
  
  if (!response.ok) {
    throw new Error('Failed to fetch version')
  }
  
  const data = await response.json()
  return data.version
}

export async function searchCommits(q = '', limit = 50, offset = 0) {
  const params = new URLSearchParams({ q, limit, offset })
  const response = await fetch(`${API_BASE}/stats/commits/search?${params}`)
  if (!response.ok) throw new Error('Search failed')
  const data = await response.json()
  return data.data
}

export async function getStatsSummary(range = 'week') {
  const response = await fetch(`${API_BASE}/stats/summary?range=${range}`)
  if (!response.ok) throw new Error('Failed to fetch summary')
  const data = await response.json()
  return data.data
}

export async function getTokenStats(range = 'thisWeek', model = 'all') {
  const params = new URLSearchParams({ range })
  if (model && model !== 'all') {
    params.set('model', model)
  }
  const url = `${API_BASE}/stats/tokens?${params.toString()}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch token stats')
  }

  const data = await response.json()
  return data.data
}

export async function getTokenBudget() {
  const url = `${API_BASE}/stats/tokens/budget`
  const response = await fetch(url)
  if (!response.ok) throw new Error('Failed to fetch token budget')
  const data = await response.json()
  return data
}

export async function setTokenBudget(monthlyBudget) {
  const url = `${API_BASE}/stats/tokens/budget`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ monthlyBudget })
  })
  if (!response.ok) throw new Error('Failed to set token budget')
  const data = await response.json()
  return data
}

export async function getStreakStats(repos = []) {
  const params = new URLSearchParams()

  appendRepoParams(params, repos)

  const url = `${API_BASE}/stats/streak?${params.toString()}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch streak stats')
  }

  const data = await response.json()
  return data.data
}

export async function getWeatherCurrent(lat, lon) {
  const params = new URLSearchParams({ lat, lon })
  const response = await fetch(`${API_BASE}/weather/current?${params}`)

  if (!response.ok) {
    throw new Error('Failed to fetch current weather')
  }

  const data = await response.json()
  return data.data
}

export async function getWeatherForecast(lat, lon, days = 7) {
  const params = new URLSearchParams({ lat, lon, days })
  const response = await fetch(`${API_BASE}/weather/forecast?${params}`)

  if (!response.ok) {
    throw new Error('Failed to fetch weather forecast')
  }

  const data = await response.json()
  return data.data
}

export async function getCommitList(range = 'today', repos = [], startDate = null, endDate = null, limit = 50) {
  const params = new URLSearchParams()
  if (range) params.append('range', range)
  if (startDate) params.append('startDate', startDate)
  if (endDate) params.append('endDate', endDate)
  if (limit) params.append('limit', limit)

  appendRepoParams(params, repos)

  const url = `${API_BASE}/stats/commit-list?${params.toString()}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to fetch commit list')
  }

  return response.json()
}

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
