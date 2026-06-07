const API_BASE = import.meta.env.VITE_API_BASE || '/api'

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
  if (repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }
  
  const url = `${API_BASE}/stats/overview?${params.toString()}`
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error('Failed to fetch stats')
  }
  
  return response.json()
}

export async function getRepositories() {
  const response = await fetch(`${API_BASE}/repositories`)
  
  if (!response.ok) {
    throw new Error('Failed to fetch repositories')
  }
  
  return response.json()
}

export async function exportData() {
  const response = await fetch(`${API_BASE}/export/json`)
  
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
  if (repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }
  
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
  
  if (repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }
  
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

  if (repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }

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

  if (repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }

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

  if (repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }

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
  
  if (repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }
  
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
  
  if (repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }
  
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
