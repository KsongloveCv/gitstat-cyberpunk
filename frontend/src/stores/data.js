import { reactive } from 'vue'
import * as api from '../api'

export const state = reactive({
  overviewStats: null,
  dailyStats: [],
  repoDailyTrend: [],
  repoComparison: [],
  authorRank: [],
  scanPath: '',
  loading: false,
  error: null,
  reposInfo: [],
  analyzing: false,
  analyzeCache: {},
  repoInfoCache: {},
  repoStatsCache: {},
  commitList: []
})

export async function performScan(path, timeRange) {
  state.loading = true
  state.error = null
  
  try {
    await api.setScanPath(path)
    const [overview, daily] = await Promise.all([
      api.getOverviewStats(null, null, ['all']),
      api.getDailyStats('', 'today', ['all'])
    ])
    state.overviewStats = overview
    state.dailyStats = daily
  } catch (err) {
    state.error = err.message
  } finally {
    state.loading = false
  }
}

export async function fetchOverviewStats() {
  try {
    state.overviewStats = await api.getOverviewStats(null, null, ['all'])
  } catch (err) {
    console.error('Failed to fetch overview stats:', err)
  }
}

export async function fetchDailyStatsToday() {
  try {
    state.dailyStats = await api.getDailyStats('', 'today', ['all'])
  } catch (err) {
    console.error('Failed to fetch daily stats:', err)
  }
}

export async function loadDashboardS1() {
  await Promise.all([
    fetchOverviewStats(),
    fetchRepoDailyTrend(),
    fetchAuthorRank()
  ])
}

export async function loadDashboardS2() {
  await Promise.all([
    fetchRepoComparison(),
    fetchDailyStatsToday()
  ])
}

export async function fetchRepoDailyTrend() {
  try {
    const daily = await api.getDailyStats('', 'week', ['all'])
    const result = []
    for (const repo of daily) {
      const dateMap = {}
      for (const author of repo.authors) {
        for (const day of (author.dailyData || [])) {
          if (!dateMap[day.date]) dateMap[day.date] = 0
          dateMap[day.date] += day.commits
        }
      }
      const sorted = Object.entries(dateMap)
        .map(([date, commits]) => ({ date, commits }))
        .sort((a, b) => a.date.localeCompare(b.date))
      if (sorted.length > 0) {
        result.push({ repoName: repo.repoName, data: sorted, authors: repo.authors })
      }
    }
    state.repoDailyTrend = result
  } catch (err) {
    console.error('Failed to fetch repo daily trend:', err)
  }
}

export async function fetchRepoComparison() {
  try {
    state.repoComparison = await api.getRepoComparison(['all'], null, null, 'week')
  } catch (err) {
    console.error('Failed to fetch repo comparison:', err)
  }
}

export async function fetchAuthorRank() {
  try {
    state.authorRank = await api.getAuthorRank(['all'], null, null, 'week')
  } catch (err) {
    console.error('Failed to fetch author rank:', err)
  }
}

export async function fetchReposInfo() {
  try {
    state.reposInfo = await api.getReposList()
  } catch (err) {
    console.error('Failed to fetch repos info:', err)
  }
}

export async function fetchRepoInfo(path) {
  if (state.repoInfoCache[path]) {
    return state.repoInfoCache[path]
  }
  try {
    const result = await api.getRepoInfo(path)
    state.repoInfoCache[path] = result
    return result
  } catch (err) {
    console.error('Failed to fetch repo info:', err)
    throw err
  }
}

export async function fetchRepoStats(path) {
  if (state.repoStatsCache[path]) {
    return state.repoStatsCache[path]
  }
  try {
    const result = await api.getRepoStats(path)
    state.repoStatsCache[path] = result
    return result
  } catch (err) {
    console.error('Failed to fetch repo stats:', err)
    throw err
  }
}

export async function triggerAnalyze(path) {
  if (state.analyzeCache[path]) {
    return state.analyzeCache[path]
  }
  state.analyzing = true
  try {
    const result = await api.analyzeRepo(path)
    state.analyzeCache[path] = result
    return result
  } catch (err) {
    console.error('Failed to analyze repo:', err)
    throw err
  } finally {
    state.analyzing = false
  }
}

export async function loadScanPath() {
  try {
    const info = await api.getScanPath()
    state.scanPath = info.path
  } catch (err) {
    console.error('Failed to load scan path:', err)
  }
}

export async function fetchCommitList(range = 'today', repos = []) {
  try {
    state.commitList = await api.getCommitList(range, repos)
  } catch (err) {
    console.error('Failed to fetch commit list:', err)
  }
}
