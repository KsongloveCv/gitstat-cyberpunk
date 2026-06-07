<template>
  <div class="dashboard">
    <!-- 天气卡片 -->
    <WeatherCard />

    <!-- 今日统计概览 -->
      <div v-if="sectionLoading.stats" class="stats-grid">
        <div v-for="i in 6" :key="i" class="stat-card-ph">
          <div class="skeleton-circle stat-ph-icon"></div>
          <div class="skeleton-line w40 stat-ph-value"></div>
          <div class="skeleton-line w60 stat-ph-label"></div>
        </div>
      </div>
      <div v-else-if="state.overviewStats" class="stats-grid">
        <StatCard 
          :value="todayCommits" 
          :label="t('dashboard.todayCommits')"
          icon="◈"
          color="#00d4ff"
        />
        <StatCard 
          :value="todayAdditions" 
          :label="t('dashboard.todayAdditions')"
          icon="↑"
          color="#00ff88"
        />
        <StatCard 
          :value="todayDeletions" 
          :label="t('dashboard.todayDeletions')"
          icon="↓"
          color="#ff6b9d"
        />
        <StatCard 
          :value="state.overviewStats.activeAuthors" 
          :label="t('dashboard.activeAuthors')"
          icon="◉"
          color="#ffd700"
        />
        <StatCard 
          :value="state.overviewStats.repositoryCount" 
          :label="t('dashboard.repositoryCount')"
          icon="▦"
          color="#a78bfa"
        />
        <StatCard 
          :value="weeklyTotal" 
          :label="t('dashboard.weeklyTotal')"
          icon="⟡"
          color="#f472b6"
        />
      </div>
      
      <!-- 连续贡献天数 -->
      <StreakCard />
      
      <!-- 本周趋势 + 作者排行榜 -->
      <div class="insight-grid">
        <div class="insight-card card">
          <div class="insight-header">
            <h3>{{ t('dashboard.weeklyTrend') }} <span class="range-hint">{{ weekRange }}</span></h3>
          </div>
          <div v-if="sectionLoading.trend" class="skeleton-chart-area">
            <div class="skeleton-line w80"></div>
            <div class="skeleton-line w60"></div>
            <div class="skeleton-line w90"></div>
            <div class="skeleton-line w40"></div>
            <div class="skeleton-line w70"></div>
            <div class="skeleton-line w50"></div>
          </div>
          <div v-else-if="state.repoDailyTrend.length === 0" class="insight-empty">{{ t('analytics.noData') }}</div>
          <template v-else>
            <div ref="trendChartRef" class="trend-chart"></div>
            <div v-if="state.repoDailyTrend.length > 1" class="chart-legend">
              <span v-for="(repo, i) in state.repoDailyTrend" :key="repo.repoName" class="legend-item">
                <span class="legend-dot" :style="{ background: repoColors[i] }"></span>
                {{ repo.repoName }}
              </span>
            </div>
          </template>
        </div>
        <div class="insight-card card">
          <div class="insight-header">
            <h3>{{ t('dashboard.authorRank') }} <span class="range-hint">{{ weekRange }}</span></h3>
          </div>
          <div v-if="sectionLoading.rank" class="skeleton-rank">
            <div class="skeleton-rank-row" v-for="i in 5" :key="i">
              <div class="skeleton-circle"></div>
              <div class="skeleton-line w60"></div>
              <div class="skeleton-line w20"></div>
            </div>
          </div>
          <template v-else-if="authorRankWithRepos.length > 0">
            <div class="rank-list">
              <template v-for="(author, index) in authorRankWithRepos.slice(0, 5)" :key="author.email">
                <div class="rank-row rank-row-compact">
                  <div class="rank-num" :class="{ gold: index === 0, silver: index === 1, bronze: index === 2 }">
                    {{ index + 1 }}
                  </div>
                  <div class="rank-info">
                    <span class="rank-name">{{ author.author }}</span>
                    <span v-if="author.isMe" class="me-badge-small">{{ t('dashboard.me') }}</span>
                  </div>
                  <div class="rank-stats">
                    <span class="rank-commits">{{ author.commits }}</span>
                  </div>
                </div>
                <div class="rank-repo-dist">
                  <span v-for="r in author.repos" :key="r.name" class="repo-tag" :style="{ borderColor: r.color, color: r.color }">
                    {{ r.name }} {{ r.commits }}
                  </span>
                </div>
              </template>
            </div>
          </template>
          <div v-else class="insight-empty">{{ t('analytics.noData') }}</div>
        </div>
      </div>

      <div ref="section2Ref">
        <!-- 仓库活跃度对比 -->
        <div class="comparison-section">
          <div class="section-header">
            <h3>{{ t('dashboard.repoComparison') }} <span class="range-hint">{{ weekRange }}</span></h3>
          </div>
          <div v-if="sectionLoading.below" class="comparison-table card">
            <div v-for="i in 3" :key="i" class="cmp-row">
              <div class="skeleton-line w40"></div>
              <div class="skeleton-line w15"></div>
              <div class="skeleton-line w15"></div>
              <div class="skeleton-line w15"></div>
              <div class="skeleton-line w15"></div>
              <div class="skeleton-line w15"></div>
            </div>
          </div>
          <div v-else-if="state.repoComparison.length > 0" class="comparison-table card">
            <div class="cmp-header">
              <div class="cmp-col-name">{{ t('dashboard.repo') }}</div>
              <div class="cmp-col-num">{{ t('dashboard.commits') }}</div>
              <div class="cmp-col-num">{{ t('analytics.additions') }}</div>
              <div class="cmp-col-num">{{ t('analytics.deletions') }}</div>
              <div class="cmp-col-num">{{ t('dashboard.activeDays') }}</div>
              <div class="cmp-col-num">{{ t('dashboard.dailyAvg') }}</div>
            </div>
            <div v-for="repo in state.repoComparison" :key="repo.repoPath" class="cmp-row">
              <div class="cmp-col-name">{{ repo.repoName }}</div>
              <div class="cmp-col-num">{{ repo.commits }}</div>
              <div class="cmp-col-num additions">+{{ repo.additions }}</div>
              <div class="cmp-col-num deletions">-{{ repo.deletions }}</div>
              <div class="cmp-col-num">{{ repo.activeDays }}</div>
              <div class="cmp-col-num">{{ repo.avgCommitsPerDay }}</div>
            </div>
          </div>
        </div>

        <!-- 分仓库分人统计 -->
        <div class="daily-stats-section">
          <div class="section-header">
            <h3>{{ t('dashboard.todayDetails') }}</h3>
          </div>
          
          <div v-if="sectionLoading.below" class="skeleton-daily">
            <div v-for="i in 2" :key="i" class="repo-daily-card card">
              <div class="repo-daily-header">
                <div class="skeleton-line w50"></div>
                <div class="skeleton-line w30" style="margin-top:8px"></div>
              </div>
              <div class="authors-table">
                <div v-for="j in 2" :key="j" class="table-row">
                  <div class="skeleton-line w35"></div>
                  <div class="skeleton-line w15"></div>
                  <div class="skeleton-line w25"></div>
                </div>
              </div>
            </div>
          </div>
          <template v-else-if="state.dailyStats && state.dailyStats.length > 0">
            <div v-for="repo in state.dailyStats" :key="repo.repoPath" class="repo-daily-card card">
              <div class="repo-daily-header">
                <div class="repo-info">
                  <h4>{{ repo.repoName }}</h4>
                  <div class="repo-meta">
                    <span class="branch-badge">{{ repo.currentBranch }}</span>
                    <span class="last-commit">{{ t('dashboard.lastCommit') }}: {{ repo.lastCommitTime }}</span>
                  </div>
                </div>
              </div>
              
              <div class="authors-table">
                <div class="table-header">
                  <div class="col-author">{{ t('dashboard.author') }}</div>
                  <div class="col-commits">{{ t('dashboard.commits') }}</div>
                  <div class="col-changes">{{ t('dashboard.changes') }}</div>
                </div>
                <div 
                  v-for="author in repo.authors" 
                  :key="author.email" 
                  class="table-row"
                >
                  <div class="col-author">
                    <span class="author-name">{{ author.author }}</span>
                    <span v-if="author.isMe" class="me-badge" :title="t('dashboard.me')">{{ t('dashboard.me') }}</span>
                  </div>
                  <div class="col-commits">{{ author.commits }}</div>
                  <div class="col-changes">
                    <span class="additions">+{{ author.additions }}</span>
                    <span class="deletions">-{{ author.deletions }}</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from '../i18n'
import { state, fetchOverviewStats, fetchRepoDailyTrend, fetchAuthorRank, loadDashboardS2, fetchWeather } from '../stores/data'
import StatCard from '../components/StatCard.vue'
import StreakCard from '../components/StreakCard.vue'
import WeatherCard from '../components/WeatherCard.vue'
import echarts from '../utils/echarts'
import { CHART_COLORS } from '../utils/constants'

const { t } = useI18n()

const sectionLoading = reactive({
  stats: true,
  trend: true,
  rank: true,
  below: true
})

function getWeekRange() {
  const now = new Date()
  const dow = now.getDay()
  const diff = dow === 0 ? 6 : dow - 1
  const monday = new Date(now)
  monday.setDate(now.getDate() - diff)
  const fmt = (d) => `${d.getMonth() + 1}/${d.getDate()}`
  return `${fmt(monday)} - ${fmt(now)}`
}
const weekRange = getWeekRange()

const trendChartRef = ref(null)
const section2Ref = ref(null)
let trendChart = null
let observer = null

const todayCommits = computed(() => state.overviewStats?.totalCommits ?? 0)
const todayAdditions = computed(() => state.overviewStats?.totalAdditions ?? 0)
const todayDeletions = computed(() => state.overviewStats?.totalDeletions ?? 0)

const weeklyTotal = computed(() =>
  state.repoDailyTrend.reduce((sum, repo) =>
    sum + repo.data.reduce((s, d) => s + d.commits, 0), 0)
)

const repoColors = computed(() =>
  state.repoDailyTrend.map((_, i) => CHART_COLORS[i % CHART_COLORS.length])
)

const authorRankWithRepos = computed(() => {
  if (state.authorRank.length === 0) return []
  const repoOf = {}
  for (const repo of state.repoDailyTrend) {
    for (const author of repo.authors || []) {
      if (!repoOf[author.email]) repoOf[author.email] = []
      const total = author.dailyData ? author.dailyData.reduce((s, d) => s + d.commits, 0) : 0
      repoOf[author.email].push({ name: repo.repoName, commits: total, color: CHART_COLORS[state.repoDailyTrend.indexOf(repo) % CHART_COLORS.length] })
    }
  }
  return state.authorRank.map(a => ({
    ...a,
    repos: (repoOf[a.email] || []).filter(r => r.commits > 0)
  }))
})

function renderTrendChart() {
  if (!trendChartRef.value || state.repoDailyTrend.length === 0) return

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  const allDates = [...new Set(state.repoDailyTrend.flatMap(r => r.data.map(d => d.date)))].sort()
  const labels = allDates.map(d => d.slice(5))

  const series = state.repoDailyTrend.map((repo, i) => {
    const dateMap = Object.fromEntries(repo.data.map(d => [d.date, d.commits]))
    return {
      name: repo.repoName,
      type: 'line',
      stack: 'total',
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 1.5, color: CHART_COLORS[i % CHART_COLORS.length] },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: CHART_COLORS[i % CHART_COLORS.length] + '60' },
          { offset: 1, color: CHART_COLORS[i % CHART_COLORS.length] + '05' }
        ])
      },
      itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
      data: allDates.map(d => dateMap[d] || 0)
    }
  })

  trendChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 14, 39, 0.9)',
      borderColor: 'rgba(0, 212, 255, 0.3)',
      textStyle: { color: '#e0e6ff', fontSize: 12 }
    },
    legend: { show: false },
    grid: { left: 40, right: 16, top: 16, bottom: 24 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.2)' } },
      axisLabel: { color: '#a0aec0', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.08)', type: 'dashed' } },
      axisLabel: { color: '#a0aec0', fontSize: 11 }
    },
    series
  })
}

watch(() => state.repoDailyTrend, () => {
  nextTick(() => renderTrendChart())
})

function handleResize() {
  if (trendChart) trendChart.resize()
}

onMounted(async () => {
  // Load weather data with geolocation
  try {
    const pos = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        timeout: 5000,
        maximumAge: 300000
      })
    })
    fetchWeather(pos.coords.latitude, pos.coords.longitude)
  } catch {
    // Fallback to Shanghai coordinates
    fetchWeather(31.23, 121.47)
  }

  await Promise.all([
    fetchOverviewStats().then(() => { sectionLoading.stats = false }),
    fetchRepoDailyTrend().then(() => { sectionLoading.trend = false }),
    fetchAuthorRank().then(() => { sectionLoading.rank = false })
  ])
  nextTick(() => renderTrendChart())

  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting && sectionLoading.below) {
        loadDashboardS2().then(() => { sectionLoading.below = false })
        observer.disconnect()
      }
    },
    { rootMargin: '200px' }
  )
  if (section2Ref.value) {
    observer.observe(section2Ref.value)
  }

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  trendChart = null
  if (observer) observer.disconnect()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.header-actions {
  margin-bottom: 2rem;
  display: flex;
  justify-content: flex-end;
}

.switch-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-icon {
  font-size: 1.2rem;
  transition: transform 0.3s;
}

.switch-btn:hover .btn-icon {
  transform: rotate(180deg);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-bottom: 3rem;
}

.daily-stats-section {
  margin-top: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.range-hint {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.75rem;
  color: #4a5568;
  letter-spacing: 0;
  text-transform: none;
  font-weight: 400;
}

.section-header h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  color: var(--neon-cyan);
  letter-spacing: 2px;
  text-transform: uppercase;
  margin: 0;
  text-shadow: 0 0 10px var(--neon-cyan), 0 0 20px rgba(0, 245, 255, 0.3);
}

.repo-daily-card {
  margin-bottom: 2rem;
  padding: 0;
  overflow: hidden;
}

.repo-daily-header {
  padding: 1.5rem 2rem;
  background: rgba(0, 212, 255, 0.05);
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
}

.repo-daily-header h4 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.2rem;
  color: var(--neon-cyan);
  margin: 0 0 0.75rem 0;
  letter-spacing: 1px;
  text-shadow: 0 0 8px var(--neon-cyan);
}

.repo-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.branch-badge {
  background: rgba(0, 255, 136, 0.15);
  border: 1px solid rgba(0, 255, 136, 0.4);
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  color: #00ff88;
  font-weight: 600;
  font-family: 'Rajdhani', monospace;
}

.last-commit {
  font-size: 0.85rem;
  color: #a0aec0;
  font-family: 'Rajdhani', monospace;
}

.authors-table {
  padding: 1rem 0;
}

.table-header,
.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr;
  padding: 1rem 2rem;
  align-items: center;
}

.table-header {
  background: rgba(0, 212, 255, 0.05);
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.8rem;
  color: #a0aec0;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.table-row {
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
  transition: all 0.3s;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: rgba(0, 212, 255, 0.05);
}

.col-author {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.author-name {
  font-weight: 600;
  color: #e0e6ff;
}

.me-badge {
  background: rgba(0, 212, 255, 0.15);
  border: 1px solid rgba(0, 212, 255, 0.4);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  color: #00d4ff;
  font-family: 'Orbitron', sans-serif;
  letter-spacing: 1px;
  cursor: help;
}

.col-commits {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--neon-cyan);
  text-align: center;
  text-shadow: 0 0 6px var(--neon-cyan);
}

.col-changes {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.additions {
  color: #00ff88;
  font-weight: 600;
}

.deletions {
  color: #ff6b9d;
  font-weight: 600;
}

.insight-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 3rem;
}

.insight-card {
  padding: 1.5rem;
}

.insight-header h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.1rem;
  color: var(--neon-cyan);
  letter-spacing: 2px;
  margin: 0 0 1rem 0;
  text-shadow: 0 0 8px var(--neon-cyan);
}

.trend-chart {
  height: 220px;
  width: 100%;
}

.insight-empty {
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  letter-spacing: 1px;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.rank-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  transition: all 0.3s;
  border-bottom: 1px solid rgba(0, 212, 255, 0.08);
}

.rank-row:last-child {
  border-bottom: none;
}

.rank-row:hover {
  background: rgba(0, 212, 255, 0.05);
}

.rank-num {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.8rem;
  font-weight: 700;
  background: rgba(0, 212, 255, 0.1);
  color: #a0aec0;
  flex-shrink: 0;
}

.rank-num.gold {
  background: rgba(255, 215, 0, 0.2);
  color: #ffd700;
  box-shadow: 0 0 12px rgba(255, 215, 0, 0.3);
}

.rank-num.silver {
  background: rgba(192, 192, 192, 0.15);
  color: #c0c0c0;
}

.rank-num.bronze {
  background: rgba(205, 127, 50, 0.15);
  color: #cd7f32;
}

.rank-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.rank-name {
  font-weight: 600;
  color: #e0e6ff;
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.me-badge-small {
  background: rgba(0, 212, 255, 0.15);
  border: 1px solid rgba(0, 212, 255, 0.4);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.6rem;
  font-weight: 700;
  color: #00d4ff;
  font-family: 'Orbitron', sans-serif;
  letter-spacing: 1px;
  flex-shrink: 0;
}

.rank-stats {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
}

.rank-commits {
  font-family: 'Orbitron', sans-serif;
  font-size: 1rem;
  font-weight: 700;
  color: #00d4ff;
}

.rank-changes {
  font-family: 'Rajdhani', monospace;
  font-size: 0.9rem;
  font-weight: 600;
}

.rank-changes.positive {
  color: #00ff88;
}

.rank-changes.negative {
  color: #ff6b9d;
}

.rank-row-compact {
  padding-bottom: 0.25rem;
}

.rank-repo-dist {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
  padding: 0 1rem 0.6rem 3rem;
  margin-top: -0.25rem;
}

.repo-tag {
  font-size: 0.7rem;
  font-family: 'Rajdhani', monospace;
  padding: 0.1rem 0.5rem;
  border-radius: 8px;
  border: 1px solid;
  background: rgba(0, 0, 0, 0.2);
  font-weight: 600;
}

.chart-legend {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 0.75rem 0 0 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: #a0aec0;
  font-family: 'Rajdhani', sans-serif;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.comparison-section {
  margin-bottom: 3rem;
}

.comparison-table {
  overflow: hidden;
}

.cmp-header,
.cmp-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr;
  padding: 1rem 2rem;
  align-items: center;
}

.cmp-header {
  background: rgba(0, 212, 255, 0.05);
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.8rem;
  color: #a0aec0;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.cmp-row {
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
  transition: all 0.3s;
}

.cmp-row:last-child {
  border-bottom: none;
}

.cmp-row:hover {
  background: rgba(0, 212, 255, 0.05);
}

.cmp-col-name {
  font-weight: 600;
  color: #e0e6ff;
}

.cmp-col-num {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.95rem;
  font-weight: 700;
  color: #00d4ff;
  text-align: center;
}

.cmp-col-num.additions {
  color: #00ff88;
}

.cmp-col-num.deletions {
  color: #ff6b9d;
}

.skeleton-line {
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(90deg, rgba(0,212,255,0.06) 25%, rgba(0,212,255,0.15) 50%, rgba(0,212,255,0.06) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.skeleton-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(90deg, rgba(0,212,255,0.06) 25%, rgba(0,212,255,0.15) 50%, rgba(0,212,255,0.06) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  flex-shrink: 0;
}

.skeleton-chart-area {
  height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  padding: 20px 10px;
}

.skeleton-chart-area .skeleton-line {
  height: 10px;
}

.skeleton-rank {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 0;
}

.skeleton-rank-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.skeleton-rank-row .skeleton-line {
  height: 14px;
}

.skeleton-rank-row .skeleton-line.w60 {
  flex: 1;
}

.skeleton-daily {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.skeleton-daily .repo-daily-header .skeleton-line {
  height: 18px;
}

.skeleton-daily .authors-table .table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr;
  padding: 1rem 2rem;
  align-items: center;
}

.comparison-section .cmp-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr;
  padding: 1rem 2rem;
  align-items: center;
}

.comparison-section .cmp-row .skeleton-line {
  height: 14px;
}

/* Commit list styles */
.commit-list {
  overflow: hidden;
}

.commit-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 2rem;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
  transition: all 0.3s;
}

.commit-row:last-child {
  border-bottom: none;
}

.commit-row:hover {
  background: rgba(0, 212, 255, 0.05);
}

.commit-left {
  flex-shrink: 0;
}

.commit-hash {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.75rem;
  color: var(--neon-magenta, #ff00ff);
  background: rgba(255, 0, 255, 0.1);
  border: 1px solid rgba(255, 0, 255, 0.3);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  letter-spacing: 1px;
}

.commit-info {
  min-width: 0;
}

.commit-message {
  font-weight: 600;
  color: #e0e6ff;
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 500px;
}

.commit-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.8rem;
}

.commit-author {
  color: #a0aec0;
}

.commit-repo {
  background: rgba(0, 245, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.3);
  padding: 0.15rem 0.5rem;
  border-radius: 8px;
  color: #00f5ff;
  font-size: 0.75rem;
}

.commit-time {
  color: #64748b;
}

.commit-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
  min-width: 120px;
}

.change-stats {
  display: flex;
  gap: 0.5rem;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.85rem;
}

.change-additions {
  color: #00ff88;
  font-weight: 600;
}

.change-deletions {
  color: #ff6b9d;
  font-weight: 600;
}

.change-bar {
  display: flex;
  height: 8px;
  width: 80px;
  border-radius: 4px;
  background: rgba(0, 212, 255, 0.1);
  overflow: hidden;
}

.change-bar-add {
  background: #00ff88;
  height: 100%;
  border-radius: 4px 0 0 4px;
}

.change-bar-del {
  background: #ff6b9d;
  height: 100%;
  border-radius: 0 4px 4px 0;
}

.commit-row-skeleton {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 2rem;
}

.skeleton-bar-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.no-commits-hint {
  text-align: center;
  padding: 3rem 2rem;
  color: #64748b;
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  letter-spacing: 1px;
}

.stat-ph-skeleton {
  background: rgba(20, 25, 50, 0.6);
  backdrop-filter: blur(20px);
  padding: 2rem;
  border-radius: 16px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.stat-ph-icon {
  width: 40px;
  height: 40px;
  margin-bottom: 0.5rem;
}

.stat-ph-value {
  height: 40px;
}

.stat-ph-label {
  height: 14px;
}

.w15 { width: 15%; }
.w20 { width: 20%; }
.w25 { width: 25%; }
.w30 { width: 30%; }
.w35 { width: 35%; }
.w40 { width: 40%; }
.w50 { width: 50%; }
.w60 { width: 60%; }
.w70 { width: 70%; }
.w80 { width: 80%; }
.w90 { width: 90%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
