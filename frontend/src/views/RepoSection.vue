<template>
  <div class="repo-page">
    <div v-if="state.reposInfo.length === 0" class="empty-state card">
      <span class="empty-icon">▤</span>
      <p>{{ t('repo.empty') }}</p>
    </div>

    <template v-else>
      <div v-if="state.reposInfo.length > 1" class="tabs">
        <button
          v-for="repo in state.reposInfo"
          :key="repo.path"
          :class="['tab', { active: activePath === repo.path }]"
          @click="switchRepo(repo.path)"
        >
          {{ repo.name }}
        </button>
      </div>

      <div class="content">
        <div v-if="loading" class="loading-state">
          <span class="spinner large"></span>
          <p>{{ t('repo.loading') }}</p>
        </div>

        <template v-else-if="detail">
          <div class="title-row">
            <h2 class="repo-title">{{ detail.name }}</h2>
            <span class="repo-path">{{ detail.path }}</span>
          </div>

          <div class="card-row fast-row">
            <div class="info-card">
              <span class="info-icon" style="color:#00d4ff">⑂</span>
              <span class="info-value">{{ detail.currentBranch }}</span>
              <span class="info-label">{{ t('repo.currentBranch') }}</span>
            </div>
            <div class="info-card clickable" :class="{ expanded: expandedBranch }" @click="toggleBranch">
              <span class="info-icon" style="color:#a78bfa">⑂</span>
              <span class="info-value">{{ detail.branchCount }}</span>
              <span class="info-label">{{ t('repo.branchCount') }} <span class="expand-icon">{{ expandedBranch ? '▼' : '▶' }}</span></span>
            </div>
            <div class="info-card">
              <span class="info-icon" style="color:#fbbf24">◈</span>
              <span class="info-value">{{ formatDate(detail.earliestDate) }}</span>
              <span class="info-label">{{ t('repo.createDate') }}</span>
            </div>
            <div class="info-card">
              <span class="info-icon" style="color:#f472b6">◉</span>
              <span class="info-value">{{ formatTimeAgo(detail.lastCommitTime) }}</span>
              <span class="info-label">{{ t('repo.lastCommit') }} · {{ timeSpan }}</span>
            </div>
          </div>

          <div v-if="expandedBranch" class="expand-panel card">
            <h4>{{ t('repo.branchList') }}</h4>
            <div v-if="detail.analysis && detail.analysis.branches" class="branch-tags">
              <span
                v-for="b in detail.analysis.branches"
                :key="b"
                class="branch-tag"
                :class="{ current: b.includes('(current)') }"
              >{{ b }}</span>
            </div>
            <p v-else class="expand-hint">{{ t('repo.analyzeToSee') }}</p>
          </div>

          <div v-if="!statsLoaded" class="stats-cta card" @click="loadStats">
            <div class="stats-cta-content">
              <span class="stats-cta-icon">▦</span>
              <div>
                <h4>{{ t('repo.statsTitle') }}</h4>
                <p>{{ t('repo.statsDesc') }}</p>
              </div>
              <button class="btn" :disabled="loadingStats" @click.stop="loadStats">
                <span v-if="loadingStats" class="spinner"></span>
                {{ loadingStats ? t('repo.statsLoading') : t('repo.statsBtn') }}
              </button>
            </div>
          </div>

          <template v-if="statsLoaded">
            <div class="card-row stats-row">
              <div class="info-card dim" :class="{ 'has-data': hasCommits }">
                <span class="info-value">{{ hasCommits ? totalCommitCount : '--' }}</span>
                <span class="info-label">{{ t('repo.commits') }}</span>
              </div>
              <div class="info-card clickable dim" :class="{ expanded: expandedContributor, 'has-data': hasCommits }" @click="toggleContributor">
                <span class="info-value">{{ hasCommits ? detail.contributors.length : '--' }}</span>
                <span class="info-label">{{ t('repo.contributors') }} <span class="expand-icon">{{ expandedContributor ? '▼' : '▶' }}</span></span>
              </div>
              <div class="info-card dim" :class="{ 'has-data': detail.repoSize > 0 }">
                <span class="info-value">{{ detail.repoSize > 0 ? formatBytes(detail.repoSize) : '--' }}</span>
                <span class="info-label">{{ t('repo.diskSize') }}</span>
              </div>
              <div class="info-card dim" :class="{ 'has-data': detail.earliestCommitAuthor }">
                <span class="info-value">{{ detail.earliestCommitAuthor || '--' }}</span>
                <span class="info-label">{{ t('repo.creator') }}</span>
              </div>
              <div class="info-card dim" :class="{ 'has-data': detail.analysis }">
                <span class="info-value">{{ mainLangName }}</span>
                <span class="info-label">{{ t('repo.mainLang') }}</span>
              </div>
            </div>

            <div v-if="expandedContributor" class="expand-panel card">
              <h4>{{ t('repo.contributors') }}</h4>
              <div class="contrib-table">
                <div class="contrib-header">
                  <span>{{ t('repo.author') }}</span>
                  <span>{{ t('repo.commits') }}</span>
                  <span class="add">{{ t('repo.additions') }}</span>
                  <span class="del">{{ t('repo.deletions') }}</span>
                  <span>{{ t('repo.lastCommit') }}</span>
                </div>
                <div v-for="ct in detail.contributors" :key="ct.email" class="contrib-row">
                  <span class="contrib-name">{{ ct.author }}</span>
                  <span>{{ ct.commitCount }}</span>
                  <span class="add">+{{ ct.additions }}</span>
                  <span class="del">-{{ ct.deletions }}</span>
                  <span class="contrib-time">{{ ct.lastCommitDate?.slice(0, 10) }}</span>
                </div>
              </div>
            </div>
          </template>

          <div class="section-group">
            <div class="section card">
              <h3 class="section-title">{{ t('repo.langDistribution') }}</h3>
              <div v-if="analysisLoading" class="section-loading">
                <span class="spinner"></span>
                <span>{{ t('repo.analyzing') }}</span>
              </div>
              <div v-else-if="detail.analysis" class="lang-body">
                <div ref="langChartRef" id="lang-chart-el" class="lang-chart"></div>
                <div class="lang-table">
                  <div class="lang-header">
                    <span>{{ t('repo.lang') }}</span>
                    <span>{{ t('repo.files') }}</span>
                    <span>{{ t('repo.lines') }}</span>
                    <span>{{ t('repo.percent') }}</span>
                  </div>
                  <div v-for="lang in detail.analysis.languages" :key="lang.name" class="lang-row">
                    <span class="lang-name">{{ lang.name }}</span>
                    <span>{{ lang.fileCount }}</span>
                    <span>{{ formatNumber(lang.lines) }}</span>
                      <span class="lang-pct">
                        <span class="pct-track"><span class="pct-bar" :style="{ width: lang.percentage + '%' }"></span></span>
                        <span class="pct-text">{{ lang.percentage.toFixed(1) }}%</span>
                    </span>
                  </div>
                  <div class="lang-total">
                    <span>{{ t('repo.total') }}</span>
                    <span>{{ detail.analysis.fileCount }}</span>
                    <span>{{ formatNumber(detail.analysis.totalLines) }}</span>
                    <span>100%</span>
                  </div>
                </div>
              </div>
              <div v-else class="analyze-cta">
                <span class="analyze-icon">🔍</span>
                <h4>{{ t('repo.analyzeTitle') }}</h4>
                <p class="analyze-desc">{{ t('repo.analyzeDesc') }}</p>
                <button class="btn" :disabled="state.analyzing" @click="doAnalyze">
                  <span v-if="state.analyzing" class="spinner"></span>
                  {{ state.analyzing ? t('repo.analyzing') : t('repo.analyzeBtn') }}
                </button>
              </div>
            </div>

            <template v-if="statsLoaded">
              <div v-if="detail.recentCommits && detail.recentCommits.length > 0" class="section card">
                <h3 class="section-title">{{ t('repo.recentCommits') }}</h3>
                <div class="commit-list">
                  <div v-for="c in detail.recentCommits" :key="c.hash" class="commit-item">
                    <div class="commit-main" @click="toggleCommit(c.hash)">
                      <span class="commit-hash">{{ c.hash.slice(0, 7) }}</span>
                      <span class="commit-msg">{{ c.message.split('\n')[0] }}</span>
                      <span class="commit-author">{{ c.author }}</span>
                      <span class="commit-time">{{ formatTimeAgo(c.date) }}</span>
                      <span class="commit-changes">
                        <span v-if="c.additions > 0" class="add">+{{ c.additions }}</span>
                        <span v-if="c.deletions > 0" class="del">-{{ c.deletions }}</span>
                      </span>
                    </div>
                    <div v-if="expandedCommit === c.hash" class="commit-body">
                      <pre>{{ c.message }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from '../i18n'
import { state, fetchReposInfo, fetchRepoInfo, fetchRepoStats, triggerAnalyze } from '../stores/data'
import echarts from '../utils/echarts'

const { t } = useI18n()

const activePath = ref(localStorage.getItem('activeRepoPath') || '')
const loading = ref(false)
const detail = ref(null)
const statsLoaded = ref(false)
const loadingStats = ref(false)
const expandedBranch = ref(false)
const expandedContributor = ref(false)
const expandedCommit = ref(null)
const analysisLoading = ref(false)
const langChartRef = ref(null)
let langChart = null

const totalCommitCount = computed(() =>
  detail.value?.contributors?.reduce((s, c) => s + c.commitCount, 0) || 0
)

const hasCommits = computed(() =>
  detail.value?.contributors && detail.value.contributors.length > 0
)

const mainLangName = computed(() => {
  if (!detail.value?.analysis?.languages?.length) return '--'
  const top = detail.value.analysis.languages[0]
  return `${top.name} ${top.percentage.toFixed(0)}%`
})

const timeSpan = computed(() => {
  if (!detail.value?.earliestDate || !detail.value?.lastCommitTime) return ''
  const d1 = new Date(detail.value.earliestDate)
  const d2 = new Date(detail.value.lastCommitTime)
  const ms = d2 - d1
  if (ms <= 0) return ''
  const days = Math.round(ms / 86400000)
  if (days < 30) return days + t('repo.dayUnit')
  if (days < 365) return Math.round(days / 30) + t('repo.monthUnit')
  const y = Math.floor(days / 365)
  const m = Math.round((days % 365) / 30)
  return y + t('repo.yearUnit') + (m ? m + t('repo.monthUnit') : '')
})

function formatDate(s) {
  if (!s) return '-'
  return s.slice(0, 10)
}

function formatTimeAgo(s) {
  if (!s) return '-'
  const d = new Date(s)
  const now = Date.now()
  const diff = (now - d.getTime()) / 1000
  if (diff < 60) return Math.round(diff) + 's'
  if (diff < 3600) return Math.round(diff / 60) + 'm'
  if (diff < 86400) return Math.round(diff / 3600) + 'h'
  if (diff < 2592000) return Math.round(diff / 86400) + 'd'
  return s.slice(0, 10)
}

function formatBytes(n) {
  if (!n) return '0B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let v = n
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++ }
  return v.toFixed(i > 0 ? 1 : 0) + units[i]
}

function formatNumber(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

function toggleBranch() {
  expandedBranch.value = !expandedBranch.value
}

function toggleContributor() {
  expandedContributor.value = !expandedContributor.value
}

function toggleCommit(hash) {
  expandedCommit.value = expandedCommit.value === hash ? null : hash
}

async function loadDetail(path) {
  loading.value = true
  statsLoaded.value = false
  expandedBranch.value = false
  expandedContributor.value = false
  expandedCommit.value = null
  langChart = null
  try {
    const info = await fetchRepoInfo(path)
    detail.value = { contributors: [], recentCommits: [], repoSize: 0, earliestDate: '', earliestCommitAuthor: '', ...info }
  } catch (err) {
    console.error('Failed to load info:', err)
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  if (!activePath.value || loadingStats.value) return
  loadingStats.value = true
  try {
    const stats = await fetchRepoStats(activePath.value)
    detail.value = { ...detail.value, ...stats }
    statsLoaded.value = true
    await nextTick()
    renderChart()
  } catch (err) {
    console.error('Failed to load stats:', err)
  } finally {
    loadingStats.value = false
  }
}

function switchRepo(path) {
  activePath.value = path
  localStorage.setItem('activeRepoPath', path)
  loadDetail(path)
}

async function doAnalyze() {
  analysisLoading.value = true
  try {
    const result = await triggerAnalyze(activePath.value)
    detail.value.analysis = result
  } catch (err) {
    console.error('Analysis failed:', err)
  } finally {
    analysisLoading.value = false
    await nextTick()
    renderChart()
  }
}

const LANG_COLORS = {
  Rust: '#dea584', Go: '#00add8', Python: '#3572a5',
  JavaScript: '#f1e05a', TypeScript: '#3178c6',
  'React (JSX)': '#61dafb', 'React (TSX)': '#61dafb',
  Vue: '#41b883', Java: '#b07219', Kotlin: '#a97bff',
  C: '#555555', 'C++': '#f34b7d', 'C#': '#178600',
  Ruby: '#701516', PHP: '#4f5d95', Swift: '#ffac45',
  Dart: '#00b4ab', CSS: '#563d7c', SCSS: '#c6538c',
  HTML: '#e34c26', Shell: '#89e051', Dockerfile: '#384d54',
  SQL: '#e38c00', Markdown: '#083fa1', YAML: '#cb171e',
  TOML: '#9c4221', JSON: '#292929', Lua: '#000080',
  Scala: '#c22d40', Zig: '#ec915c', Default: '#a0aec0'
}

function getLangColor(name) {
  return LANG_COLORS[name] || LANG_COLORS.Default
}

function renderChart() {
  const el = document.getElementById('lang-chart-el')
  if (!el || !detail.value?.analysis) return
  try {
    if (!langChart) langChart = echarts.init(el)
    const data = detail.value.analysis.languages.map(l => ({
      name: l.name,
      value: l.lines || 1
    }))
    langChart.setOption({
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(10, 14, 39, 0.9)',
        borderColor: 'rgba(0, 212, 255, 0.3)',
        textStyle: { color: '#e0e6ff', fontSize: 12 },
        formatter: p => `${p.name}: ${p.percent}% (${formatNumber(p.value)} lines)`
      },
      series: [{
        type: 'pie',
        radius: ['30%', '65%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 4, borderColor: 'rgba(10,14,39,0.8)', borderWidth: 2 },
        label: {
          show: true, color: '#e0e6ff', fontFamily: 'Rajdhani', fontSize: 12,
          formatter: p => `${p.name}\n${p.percent}%`
        },
        labelLine: { lineStyle: { color: 'rgba(0,212,255,0.3)' } },
        data: data.map(d => ({ ...d, itemStyle: { color: getLangColor(d.name) } }))
      }]
    })
    langChart.resize()
  } catch (e) {
    console.error('[Chart] render error:', e)
  }
}

function handleResize() {
  if (langChart) langChart.resize()
}

function init() {
  fetchReposInfo().then(() => {
    if (state.reposInfo.length > 0) {
      const saved = activePath.value
      const exists = state.reposInfo.some(r => r.path === saved)
      activePath.value = exists ? saved : state.reposInfo[0].path
      localStorage.setItem('activeRepoPath', activePath.value)
      loadDetail(activePath.value)
    }
  })
  window.addEventListener('resize', handleResize)
}

watch(() => detail.value?.analysis, val => {
  if (val) nextTick(renderChart)
})

onMounted(init)

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  langChart?.dispose()
  langChart = null
})
</script>

<style scoped>
.repo-page {
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn 0.5s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Empty */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}
.empty-icon { font-size: 4rem; color: #00d4ff; margin-bottom: 1rem; opacity: 0.5; }
.empty-state p { color: #64748b; font-size: 1.1rem; font-family: 'Rajdhani', sans-serif; letter-spacing: 1px; }

/* Tabs */
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}
.tab {
  flex-shrink: 0;
  padding: 0.6rem 1.4rem;
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  background: rgba(20, 25, 50, 0.4);
  color: #a0aec0;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.85rem;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s;
}
.tab:hover { border-color: rgba(0, 212, 255, 0.5); color: #00d4ff; }
.tab.active {
  background: rgba(0, 212, 255, 0.1);
  border-color: #00d4ff;
  color: #00d4ff;
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}
.loading-state p { font-family: 'Orbitron', sans-serif; color: #00d4ff; letter-spacing: 1px; margin-top: 1rem; }

/* Title */
.title-row {
  display: flex;
  align-items: baseline;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.repo-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.8rem;
  margin: 0;
  background: linear-gradient(135deg, #00d4ff, #00ff88);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.repo-path { font-family: 'Rajdhani', monospace; color: #64748b; font-size: 0.9rem; }

/* Spinner */
.spinner {
  display: inline-block;
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  vertical-align: middle;
}
.spinner.large { width: 32px; height: 32px; border-width: 3px; border-color: rgba(0,212,255,0.2); border-top-color: #00d4ff; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Card rows */
.card-row {
  display: grid;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}
.fast-row { grid-template-columns: repeat(4, 1fr); }
.stats-row { grid-template-columns: repeat(5, 1fr); }

.info-card {
  background: rgba(20, 25, 50, 0.6);
  backdrop-filter: blur(20px);
  padding: 1.5rem 1rem;
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.15);
  text-align: center;
  transition: all 0.3s;
}
.info-card.dim { border-color: rgba(0, 212, 255, 0.08); }
.info-card.dim.has-data { border-color: rgba(0, 212, 255, 0.15); }
.info-card.clickable { cursor: pointer; }
.info-card.clickable:hover, .info-card.expanded {
  border-color: rgba(0, 212, 255, 0.4);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
  transform: translateY(-2px);
}

.info-icon { display: block; font-size: 1.8rem; margin-bottom: 0.5rem; }
.info-value {
  display: block;
  font-family: 'Orbitron', sans-serif;
  font-size: 1.3rem;
  font-weight: 700;
  color: #e0e6ff;
  margin-bottom: 0.3rem;
}
.dim .info-value { color: #4a5568; }
.dim.has-data .info-value { color: #e0e6ff; }
.info-label {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.65rem;
  color: #a0aec0;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.expand-icon { font-size: 0.5rem; margin-left: 0.2rem; vertical-align: middle; }

/* Expand panel */
.expand-panel {
  margin-bottom: 1.5rem;
  padding: 1.5rem;
}
.expand-panel h4 {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.9rem;
  color: #00d4ff;
  letter-spacing: 1px;
  margin: 0 0 1rem 0;
}
.expand-hint { color: #64748b; font-family: 'Rajdhani', sans-serif; font-size: 0.9rem; }

/* Branch tags */
.branch-tags { display: flex; flex-wrap: wrap; gap: 0.6rem; }
.branch-tag {
  padding: 0.3rem 0.8rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-family: 'Rajdhani', monospace;
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.2);
  color: #a0aec0;
}
.branch-tag.current {
  background: rgba(0, 255, 136, 0.12);
  border-color: rgba(0, 255, 136, 0.4);
  color: #00ff88;
  font-weight: 600;
}

/* Contributor table */
.contrib-table { width: 100%; }
.contrib-header, .contrib-row {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 1fr 1.5fr;
  padding: 0.6rem 0.5rem;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.85rem;
}
.contrib-header {
  background: rgba(0, 212, 255, 0.05);
  border-bottom: 1px solid rgba(0, 212, 255, 0.15);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.7rem;
  color: #a0aec0;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.contrib-row { border-bottom: 1px solid rgba(0, 212, 255, 0.06); color: #e0e6ff; }
.contrib-name { font-weight: 600; }
.contrib-time { font-family: 'Rajdhani', monospace; color: #64748b; font-size: 0.8rem; }
.add { color: #00ff88; }
.del { color: #ff6b6b; }

/* Section group */
.section-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}
.section { padding: 1.5rem; }
.section-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.95rem;
  color: #00d4ff;
  letter-spacing: 1px;
  margin: 0 0 1rem 0;
}
.section-loading { text-align: center; padding: 2rem; color: #00d4ff; font-family: 'Rajdhani', sans-serif; }

/* Language */
.lang-body { display: grid; grid-template-columns: 1fr 1.2fr; gap: 1.5rem; align-items: start; }
.lang-chart { height: 250px; min-height: 250px; width: 100%; }
.lang-header, .lang-row, .lang-total {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr 1fr 1.5fr;
  padding: 0.5rem 0.5rem;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.85rem;
}
.lang-header {
  background: rgba(0, 212, 255, 0.05);
  border-bottom: 1px solid rgba(0, 212, 255, 0.15);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.7rem;
  color: #a0aec0;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.lang-row { border-bottom: 1px solid rgba(0, 212, 255, 0.06); color: #e0e6ff; }
.lang-row:hover { background: rgba(0, 212, 255, 0.03); }
.lang-name { font-weight: 600; color: #e0e6ff; }
.lang-pct { display: flex; align-items: center; gap: 0.3rem; font-family: 'Orbitron', sans-serif; font-size: 0.75rem; color: #00d4ff; }
.pct-track { flex: 1; height: 8px; background: rgba(0,0,0,0.15); border-radius: 4px; overflow: hidden; min-width: 4px; }
.pct-bar { display: block; height: 8px; border-radius: 4px; background: linear-gradient(90deg, #00d4ff, #7800ff); }
.pct-text { flex-shrink: 0; font-family: 'Rajdhani', 'Orbitron', monospace; }
.lang-total {
  border-top: 1px solid rgba(0, 212, 255, 0.3);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.8rem;
  color: #00d4ff;
  font-weight: 700;
  padding-top: 0.6rem;
}
.lang-total span { text-align: center; }
.lang-total span:first-child { text-align: left; }

/* Stats CTA */
.stats-cta {
  cursor: pointer;
  margin-bottom: 1.5rem;
  padding: 1.5rem;
  transition: all 0.3s;
}
.stats-cta:hover {
  border-color: rgba(0, 212, 255, 0.4);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
}
.stats-cta-content {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.stats-cta-icon {
  font-size: 2.5rem;
  color: #00d4ff;
  opacity: 0.6;
  flex-shrink: 0;
}
.stats-cta-content div { flex: 1; }
.stats-cta-content h4 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1rem;
  color: #00d4ff;
  letter-spacing: 1px;
  margin: 0 0 0.3rem 0;
}
.stats-cta-content p {
  color: #64748b;
  font-size: 0.85rem;
  margin: 0;
  font-family: 'Rajdhani', sans-serif;
}

/* Analyze CTA */
.analyze-cta { text-align: center; padding: 2rem 1rem; }
.analyze-icon { font-size: 2.5rem; display: block; margin-bottom: 0.8rem; }
.analyze-cta h4 { font-family: 'Orbitron', sans-serif; font-size: 1.1rem; color: #00d4ff; letter-spacing: 1px; margin-bottom: 0.4rem; }
.analyze-desc { color: #64748b; font-size: 0.9rem; margin-bottom: 1rem; font-family: 'Rajdhani', sans-serif; }

/* Commits */
.commit-list { width: 100%; }
.commit-main {
  display: grid;
  grid-template-columns: 1fr 2.5fr 1fr 1fr 1.2fr;
  padding: 0.55rem 0.5rem;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #e0e6ff;
  border-bottom: 1px solid rgba(0, 212, 255, 0.06);
  cursor: pointer;
  transition: background 0.2s;
}
.commit-main:hover { background: rgba(0, 212, 255, 0.03); }
.commit-hash { font-family: 'Rajdhani', monospace; color: #a0aec0; }
.commit-msg { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.commit-author { font-size: 0.8rem; }
.commit-time { font-family: 'Rajdhani', monospace; color: #64748b; font-size: 0.8rem; }
.commit-changes { text-align: right; }
.commit-changes .add { margin-right: 0.3rem; }
.commit-body pre {
  margin: 0; padding: 0.6rem 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  font-family: 'Rajdhani', monospace;
  font-size: 0.8rem;
  color: #a0aec0;
  border-bottom: 1px solid rgba(0, 212, 255, 0.06);
  white-space: pre-wrap;
}
</style>
