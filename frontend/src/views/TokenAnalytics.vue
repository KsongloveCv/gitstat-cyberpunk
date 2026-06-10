<template>
  <div class="token-page">
    <!-- Hero 标题 -->
    <div class="token-hero">
      <div class="corner-tl"></div><div class="corner-br"></div>
      <div class="hologram-scan"></div>
      <h2 class="token-title glitch-text" data-text="TOKEN ANALYTICS">
        <span class="title-icon">⟐</span> {{ t('token.title') }}
      </h2>
      <p class="token-subtitle">{{ t('token.subtitle') }}</p>
      <div class="hero-glow"></div>
    </div>

    <!-- 控制面板 -->
    <div class="token-controls card">
      <div class="control-group">
        <label class="control-label">{{ t('token.timeRange') }}</label>
        <div class="range-buttons">
          <button v-for="r in timeRanges" :key="r.key" @click="selectedRange = r.key"
            :class="{ active: selectedRange === r.key }">{{ t(`token.${r.key}`) }}</button>
        </div>
      </div>
      <div class="control-group">
        <label class="control-label">{{ t('token.modelFilter') }}</label>
        <div class="filter-buttons">
          <button @click="selectedModel = 'all'" :class="{ active: selectedModel === 'all' }">{{ t('token.allModels') }}</button>
          <button v-for="m in availableModels" :key="m" @click="selectedModel = m"
            :class="{ active: selectedModel === m }">{{ m }}</button>
        </div>
      </div>
      <!-- 数据导出 -->
      <div class="export-group" v-if="tokenData">
        <button class="export-btn" @click="exportCSV">⬇ CSV</button>
        <button class="export-btn" @click="exportJSON">⬇ JSON</button>
      </div>
    </div>

    <!-- 演示数据提示 -->
    <div v-if="dataSource === 'demo'" class="demo-banner card">
      ⚠ {{ t('token.demoNotice') }}
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="token-loading">
      <div class="loading-bars"><span class="loading-bar"></span><span class="loading-bar"></span><span class="loading-bar"></span></div>
      <span class="loading-text">{{ t('token.loading') }}</span>
    </div>

    <!-- 无数据 -->
    <div v-else-if="!tokenData" class="token-empty card">
      <div class="empty-icon">⟐</div>
      <div class="empty-text">{{ t('token.noData') }}</div>
    </div>

    <!-- 有数据 -->
    <template v-else>
      <!-- 预算管理 -->
      <TokenBudgetAlert :budget-data="budgetData" @update-budget="handleBudgetUpdate" />

      <!-- 概览卡片 (带动画计数器) -->
      <div class="overview-grid">
        <div v-for="(card, idx) in overviewCards" :key="idx" class="overview-card card"
          :style="{ '--card-color': card.color }" :class="{ pulse: pulseCards }">
          <div class="card-corner-tl"></div><div class="card-corner-br"></div>
          <div class="crt-overlay"></div>
          <div class="overview-icon">{{ card.icon }}</div>
          <div class="overview-value glitch-hover" :data-text="animatedValues[idx]">{{ animatedValues[idx] }}</div>
          <div class="overview-label">{{ card.label }}</div>
          <!-- Sparkline -->
          <svg v-if="card.sparkline" class="sparkline" viewBox="0 0 80 24">
            <polyline :points="card.sparkline" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.6"/>
          </svg>
          <div class="overview-glow"></div>
        </div>
      </div>

      <!-- 时段对比 -->
      <TokenComparison :comparison-data="comparisonMapped" />

      <!-- 效率指标 -->
      <TokenEfficiencyCards :efficiency-data="efficiencyMapped" />

      <!-- 模型对比柱状图 -->
      <div class="chart-section card">
        <div class="crt-overlay"></div>
        <div class="section-header"><h3>{{ t('token.modelComparison') }}</h3><span class="section-badge">◆</span></div>
        <div ref="modelChartRef" class="chart-container"></div>
      </div>

      <!-- Token趋势折线图 -->
      <div class="chart-section card">
        <div class="crt-overlay"></div>
        <div class="section-header"><h3>{{ t('token.tokenTrend') }}</h3><span class="section-badge">◈</span></div>
        <div ref="trendChartRef" class="chart-container"></div>
      </div>

      <!-- 热力日历图 -->
      <TokenHeatmapCalendar :heatmap-data="tokenData.heatmapData || []" />

      <!-- 成本占比饼图 + 模型排行表 -->
      <div class="insight-grid">
        <div class="chart-section card">
          <div class="crt-overlay"></div>
          <div class="section-header"><h3>{{ t('token.costDistribution') }}</h3><span class="section-badge">$</span></div>
          <div ref="costPieRef" class="chart-container chart-small"></div>
        </div>
        <div class="rank-section card">
          <div class="section-header"><h3>{{ t('token.modelRank') }}</h3><span class="section-badge">🏆</span></div>
          <div class="rank-table">
            <div class="rank-header">
              <div class="rank-col-num">#</div>
              <div class="rank-col-name">{{ t('token.model') }}</div>
              <div class="rank-col-num">{{ t('token.inputTokens') }}</div>
              <div class="rank-col-num">{{ t('token.outputTokens') }}</div>
              <div class="rank-col-num">{{ t('token.cost') }}</div>
            </div>
            <div v-for="(m, idx) in tokenData.modelRank" :key="m.model" class="rank-row">
              <div class="rank-num" :class="{ gold: idx===0, silver: idx===1, bronze: idx===2 }">{{ idx+1 }}</div>
              <div class="rank-name">
                <span class="model-dot" :style="{ background: modelColors[idx % modelColors.length] }"></span>{{ m.model }}
              </div>
              <div class="rank-val">{{ formatNum(m.input) }}</div>
              <div class="rank-val">{{ formatNum(m.output) }}</div>
              <div class="rank-val cost">${{ formatCost(m.cost) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 对话Top10排行 -->
      <div class="chart-section card" v-if="tokenData.topSessions && tokenData.topSessions.length">
        <div class="section-header"><h3>{{ t('token.topSessions') }}</h3><span class="section-badge">⚡</span></div>
        <div class="session-table">
          <div class="session-header">
            <div class="session-col">#</div>
            <div class="session-col">{{ t('token.model') }}</div>
            <div class="session-col">{{ t('token.inputTokens') }}</div>
            <div class="session-col">{{ t('token.outputTokens') }}</div>
            <div class="session-col">{{ t('token.cost') }}</div>
            <div class="session-col">{{ t('token.date') }}</div>
          </div>
          <div v-for="(s, idx) in tokenData.topSessions" :key="s.sessionId" class="session-row">
            <div class="session-num" :class="{ gold: idx===0, silver: idx===1, bronze: idx===2 }">{{ idx+1 }}</div>
            <div class="session-val">{{ s.model }}</div>
            <div class="session-val">{{ formatNum(s.input) }}</div>
            <div class="session-val">{{ formatNum(s.output) }}</div>
            <div class="session-val cost">${{ formatCost(s.cost) }}</div>
            <div class="session-val date">{{ s.date }}</div>
          </div>
        </div>
      </div>

      <!-- 模型偏好图 -->
      <div class="chart-section card" v-if="tokenData.modelSessions">
        <div class="crt-overlay"></div>
        <div class="section-header"><h3>{{ t('token.modelPreference') }}</h3><span class="section-badge">◈</span></div>
        <div ref="preferenceChartRef" class="chart-container chart-small"></div>
      </div>

      <!-- IO比率雷达图 -->
      <div class="chart-section card">
        <div class="crt-overlay"></div>
        <div class="section-header"><h3>{{ t('token.ioRatio') }}</h3><span class="section-badge">◉</span></div>
        <div ref="ratioChartRef" class="chart-container chart-small"></div>
      </div>

      <!-- 成本预测 -->
      <div class="prediction-card card" v-if="tokenData.costPrediction">
        <div class="card-corner-tl"></div><div class="card-corner-br"></div>
        <div class="prediction-icon">🔮</div>
        <div class="prediction-content">
          <div class="prediction-title">{{ t('token.costPrediction') }}</div>
          <div class="prediction-row">
            <span class="prediction-label">{{ t('token.monthlyEstimate') }}</span>
            <span class="prediction-value">${{ formatCost(tokenData.costPrediction.monthlyEstimate) }}</span>
          </div>
          <div class="prediction-row">
            <span class="prediction-label">{{ t('token.dailyAvg') }}</span>
            <span class="prediction-value">${{ formatCost(tokenData.costPrediction.dailyAvg) }}</span>
          </div>
          <div class="prediction-row">
            <span class="prediction-label">{{ t('token.trendDirection') }}</span>
            <span class="prediction-value trend-{{ tokenData.costPrediction.trendDirection }}">
              {{ trendIcon(tokenData.costPrediction.trendDirection) }}
              {{ t(`token.trend_${tokenData.costPrediction.trendDirection}`) }}
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from '../i18n'
import * as api from '../api'
import echarts from '../utils/echarts'
import { CHART_COLORS, CYBERPUNK_CHART_THEME } from '../utils/constants'
import TokenBudgetAlert from '../components/TokenBudgetAlert.vue'
import TokenComparison from '../components/TokenComparison.vue'
import TokenEfficiencyCards from '../components/TokenEfficiencyCards.vue'
import TokenHeatmapCalendar from '../components/TokenHeatmapCalendar.vue'

const { t } = useI18n()

const tokenData = ref(null)
const dataSource = ref('logs')
const budgetData = ref({ monthlyBudget: 100, currentSpent: 0, percentUsed: 0, isOverBudget: false })
const loading = ref(true)
const selectedRange = ref('thisWeek')
const selectedModel = ref('all')
const availableModels = ref([])
const pulseCards = ref(false)

const animatedValues = ref(['0', '0', '0', '0'])
const targetValues = ref([0, 0, 0, 0])

const modelChartRef = ref(null)
const trendChartRef = ref(null)
const costPieRef = ref(null)
const ratioChartRef = ref(null)
const preferenceChartRef = ref(null)

let modelChart = null, trendChart = null, costPie = null, ratioChart = null, preferenceChart = null
let animFrameId = null

const modelColors = CHART_COLORS
const timeRanges = [
  { key: 'thisWeek' }, { key: 'lastWeek' },
  { key: 'thisMonth' }, { key: 'lastMonth' },
  { key: 'thisYear' }, { key: 'customPeriod' }
]

function formatNum(n) {
  if (!n) return '0'
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M'
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K'
  return n.toFixed(0)
}

function formatCost(n) {
  if (!n) return '0.00'
  if (n >= 1000) return n.toFixed(0)
  if (n >= 1) return n.toFixed(2)
  return n.toFixed(4)
}

function trendIcon(dir) {
  if (dir === 'up') return '↑'
  if (dir === 'down') return '↓'
  return '→'
}

// 概览卡片配置
const overviewCards = computed(() => {
  const d = tokenData.value
  if (!d) return []
  const sparkData = (d.trend || []).slice(-7)
  const makeSparkline = (key) => {
    if (sparkData.length < 2) return null
    const vals = sparkData.map(s => s[key] || 0)
    const max = Math.max(...vals, 1)
    const min = Math.min(...vals, 0)
    const range = max - min || 1
    return vals.map((v, i) => `${(i * 80 / (vals.length - 1)).toFixed(1)},${24 - ((v - min) / range) * 20}`).join(' ')
  }
  return [
    { icon: '◈', color: '#00f5ff', label: t('token.totalInput'), key: 'totalInput', unit: 'tokens', sparkline: makeSparkline('input') },
    { icon: '⟐', color: '#ff00ff', label: t('token.totalOutput'), key: 'totalOutput', unit: 'tokens', sparkline: makeSparkline('output') },
    { icon: '⟡', color: '#00ff88', label: t('token.totalTokens'), key: 'totalTokens', unit: 'tokens', sparkline: null },
    { icon: '$', color: '#ffd700', label: t('token.totalCost'), key: 'totalCost', unit: t('token.estimated'), sparkline: makeSparkline('cost') },
  ]
})

// 映射数据给子组件
const comparisonMapped = computed(() => {
  const pc = tokenData.value?.periodComparison
  if (!pc) return {}
  return {
    changePercent: pc.changePercent,
    currentPeriod: { totalTokens: pc.currentPeriod?.total ?? 0, totalCost: pc.currentPeriod?.cost ?? 0 },
    previousPeriod: { totalTokens: pc.previousPeriod?.total ?? 0, totalCost: pc.previousPeriod?.cost ?? 0 },
  }
})

const efficiencyMapped = computed(() => {
  const eff = tokenData.value?.efficiency
  if (!eff) return {}
  return {
    averageRatio: eff?.averageRatio ?? 0,
    bestValueModel: eff?.bestValueModel ?? '',
    bestValuePerDollar: eff?.bestValuePerDollar ?? 0,
    modelsEfficiency: eff?.modelsEfficiency ?? [],
  }
})

// 数字动画计数器
function animateNumbers() {
  const start = Date.now()
  const duration = 2000
  const from = [0, 0, 0, 0]
  const to = targetValues.value
  function tick() {
    const elapsed = Date.now() - start
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3) // easeOutCubic
    animatedValues.value = overviewCards.value.map((card, i) => {
      const val = from[i] + (to[i] - from[i]) * eased
      if (card.key === 'totalCost') return '$' + formatCost(val)
      return formatNum(Math.round(val))
    })
    if (progress < 1) animFrameId = requestAnimationFrame(tick)
  }
  animFrameId = requestAnimationFrame(tick)
}

async function fetchBudget() {
  try { budgetData.value = await api.getTokenBudget() } catch (e) { console.error(e) }
}

async function handleBudgetUpdate(amount) {
  await api.setTokenBudget(amount)
  await fetchBudget()
}

async function fetchTokenData() {
  loading.value = true
  try {
    const data = await api.getTokenStats(selectedRange.value, selectedModel.value)
    tokenData.value = data
    // 从data推断source（无真实数据时后端会加source字段）
    dataSource.value = data.source || 'logs'
    availableModels.value = data.availableModels || []
    // 设置目标值并启动动画
    targetValues.value = [data.totalInput || 0, data.totalOutput || 0, data.totalTokens || 0, data.totalCost || 0]
    if (animFrameId) cancelAnimationFrame(animFrameId)
    animateNumbers()
    // 脉冲效果
    pulseCards.value = true
    setTimeout(() => pulseCards.value = false, 800)
    await fetchBudget()
  } catch (err) {
    console.error(err); tokenData.value = null
  } finally { loading.value = false }
}

function initCharts() {
  if (!tokenData.value) return
  nextTick(() => { initModelChart(); initTrendChart(); initCostPie(); initRatioChart(); initPreferenceChart() })
}

function initModelChart() {
  if (!modelChartRef.value) return
  modelChart = echarts.init(modelChartRef.value)
  const d = tokenData.value.modelRank || []
  modelChart.setOption({
    ...CYBERPUNK_CHART_THEME,
    tooltip: { ...CYBERPUNK_CHART_THEME.tooltip, trigger: 'axis' },
    legend: { data: [t('token.inputTokens'), t('token.outputTokens')], textStyle: { color: '#94a3b8', fontFamily: 'Share Tech Mono' }, top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: d.map(m => m.model), axisLabel: { color: '#94a3b8', fontSize: 11, rotate: 15 } },
    yAxis: { type: 'value', axisLabel: { formatter: v => v >= 1e3 ? (v/1e3)+'K' : v } },
    series: [
      { name: t('token.inputTokens'), type: 'bar', data: d.map(m => m.input), itemStyle: { color: '#00f5ff', borderRadius: [4,4,0,0] }, barWidth: '30%' },
      { name: t('token.outputTokens'), type: 'bar', data: d.map(m => m.output), itemStyle: { color: '#ff00ff', borderRadius: [4,4,0,0] }, barWidth: '30%' }
    ]
  })
}

function initTrendChart() {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)
  const d = tokenData.value.trend || []
  trendChart.setOption({
    ...CYBERPUNK_CHART_THEME,
    tooltip: { ...CYBERPUNK_CHART_THEME.tooltip, trigger: 'axis' },
    legend: { data: [t('token.inputTokens'), t('token.outputTokens'), t('token.cost')], textStyle: { color: '#94a3b8', fontFamily: 'Share Tech Mono' }, top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: d.map(item => item.date), boundaryGap: false },
    yAxis: [{ type: 'value', axisLabel: { formatter: v => v >= 1e3 ? (v/1e3)+'K' : v } }, { type: 'value', axisLabel: { formatter: v => '$'+v }, splitLine: { show: false } }],
    series: [
      { name: t('token.inputTokens'), type: 'line', data: d.map(i => i.input), smooth: true, lineStyle: { color: '#00f5ff', width: 2 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#00f5ff44' }, { offset: 1, color: '#00f5ff05' }] } }, symbol: 'none', yAxisIndex: 0 },
      { name: t('token.outputTokens'), type: 'line', data: d.map(i => i.output), smooth: true, lineStyle: { color: '#ff00ff', width: 2 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#ff00ff44' }, { offset: 1, color: '#ff00ff05' }] } }, symbol: 'none', yAxisIndex: 0 },
      { name: t('token.cost'), type: 'line', data: d.map(i => i.cost), smooth: true, lineStyle: { color: '#ffd700', width: 2 }, symbol: 'none', yAxisIndex: 1 }
    ]
  })
}

function initCostPie() {
  if (!costPieRef.value) return
  costPie = echarts.init(costPieRef.value)
  const d = tokenData.value.modelRank || []
  costPie.setOption({
    tooltip: { ...CYBERPUNK_CHART_THEME.tooltip, trigger: 'item', formatter: '{b}: ${c} ({d}%)' },
    series: [{ type: 'pie', radius: ['35%', '65%'], center: ['50%', '55%'],
      data: d.map((m, i) => ({ name: m.model, value: m.cost, itemStyle: { color: modelColors[i % modelColors.length], borderColor: 'rgba(0,245,255,0.3)', borderWidth: 1 } })),
      label: { color: '#94a3b8', fontFamily: 'Share Tech Mono', fontSize: 11, formatter: '{b}\n${c}' },
      labelLine: { lineStyle: { color: '#64748b' } },
      emphasis: { itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,245,255,0.5)' }, label: { fontSize: 14, fontWeight: 'bold', color: '#00f5ff' } }
    }]
  })
}

function initRatioChart() {
  if (!ratioChartRef.value) return
  ratioChart = echarts.init(ratioChartRef.value)
  const d = tokenData.value.modelRank || []
  const indicators = [
    { name: t('token.inputTokens'), max: Math.max(...d.map(m => m.input), 1) },
    { name: t('token.outputTokens'), max: Math.max(...d.map(m => m.output), 1) },
    { name: t('token.totalTokens'), max: Math.max(...d.map(m => m.input+m.output), 1) },
    { name: t('token.cost'), max: Math.max(...d.map(m => m.cost * 1000), 1) }
  ]
  ratioChart.setOption({
    tooltip: CYBERPUNK_CHART_THEME.tooltip,
    legend: { data: d.slice(0,5).map(m => m.model), textStyle: { color: '#94a3b8', fontFamily: 'Share Tech Mono' }, top: 0 },
    radar: { indicator: indicators, shape: 'polygon', axisName: { color: '#94a3b8', fontFamily: 'Share Tech Mono', fontSize: 11 }, splitArea: { areaStyle: { color: ['rgba(0,245,255,0.02)','rgba(0,245,255,0.05)'] } }, splitLine: { lineStyle: { color: 'rgba(0,245,255,0.1)' } }, axisLine: { lineStyle: { color: 'rgba(0,245,255,0.2)' } } },
    series: [{ type: 'radar', data: d.slice(0,5).map((m,i) => ({ name: m.model, value: [m.input, m.output, m.input+m.output, m.cost*1000], lineStyle: { color: modelColors[i%modelColors.length], width: 2 }, areaStyle: { color: modelColors[i%modelColors.length]+'33' }, symbol: 'circle', symbolSize: 4, itemStyle: { color: modelColors[i%modelColors.length] } })) }]
  })
}

function initPreferenceChart() {
  if (!preferenceChartRef.value) return
  const sessions = tokenData.value.modelSessions || {}
  preferenceChart = echarts.init(preferenceChartRef.value)
  const data = Object.entries(sessions).map(([model, count]) => ({ name: model, value: count }))
  preferenceChart.setOption({
    tooltip: { ...CYBERPUNK_CHART_THEME.tooltip, trigger: 'item', formatter: '{b}: {c}次 ({d}%)' },
    series: [{ type: 'pie', radius: ['30%', '60%'], center: ['50%', '55%'],
      data: data.map((d, i) => ({ ...d, itemStyle: { color: modelColors[i % modelColors.length] } })),
      label: { color: '#94a3b8', fontFamily: 'Share Tech Mono', fontSize: 11, formatter: '{b}\n{c}次' },
      emphasis: { label: { fontSize: 14, color: '#00f5ff' } }
    }]
  })
}

// 数据导出
function exportCSV() {
  const d = tokenData.value
  if (!d) return
  const rows = ['日期,模型,输入Token,输出Token,成本']
  d.trend?.forEach(t => { rows.push(`${t.date},合计,${t.input},${t.output},${t.cost || 0}`) })
  d.modelRank?.forEach(m => { rows.push(`—,${m.model},${m.input},${m.output},${m.cost}`) })
  const blob = new Blob([rows.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = `token-stats-${selectedRange.value}.csv`; a.click()
  URL.revokeObjectURL(url)
}

function exportJSON() {
  const d = tokenData.value
  if (!d) return
  const blob = new Blob([JSON.stringify(d, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = `token-stats-${selectedRange.value}.json`; a.click()
  URL.revokeObjectURL(url)
}

function handleResize() {
  modelChart?.resize(); trendChart?.resize(); costPie?.resize(); ratioChart?.resize(); preferenceChart?.resize()
}

watch([selectedRange, selectedModel], () => fetchTokenData())

watch(tokenData, () => {
  modelChart?.dispose(); trendChart?.dispose(); costPie?.dispose(); ratioChart?.dispose(); preferenceChart?.dispose()
  modelChart = null; trendChart = null; costPie = null; ratioChart = null; preferenceChart = null
  initCharts()
})

onMounted(() => { fetchTokenData(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); modelChart?.dispose(); trendChart?.dispose(); costPie?.dispose(); ratioChart?.dispose(); preferenceChart?.dispose(); if (animFrameId) cancelAnimationFrame(animFrameId) })
</script>

<style scoped>
.token-page { max-width: 1200px; margin: 0 auto; position: relative; }

/* ── Hero ── */
.token-hero { background:rgba(12,18,40,0.7);backdrop-filter:blur(24px);padding:2rem;border-radius:12px;border:1px solid rgba(0,245,255,0.2);text-align:center;position:relative;overflow:hidden;margin-bottom:1.5rem }
.corner-tl{position:absolute;top:0;left:0;width:20px;height:20px;border-top:2px solid var(--card-color,#00f5ff);border-left:2px solid var(--card-color,#00f5ff);border-radius:12px 0 4px 0;opacity:.5;z-index:2;box-shadow:0 0 6px var(--card-color,#00f5ff)}
.corner-br{position:absolute;bottom:0;right:0;width:20px;height:20px;border-bottom:2px solid var(--card-color,#00f5ff);border-right:2px solid var(--card-color,#00f5ff);border-radius:0 4px 0 12px;opacity:.5;z-index:2;box-shadow:0 0 6px var(--card-color,#00f5ff)}
.hologram-scan{position:absolute;top:-100%;left:0;width:100%;height:30%;background:linear-gradient(180deg,transparent,rgba(255,255,255,0.04),transparent);z-index:1;animation:hScan 4s ease-in-out infinite;pointer-events:none}
@keyframes hScan{0%{top:-30%}100%{top:130%}}

.token-title{font-family:'Orbitron',sans-serif;font-size:1.5rem;font-weight:900;background:linear-gradient(135deg,#00f5ff,#7800ff,#ff00ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:3px;margin-bottom:.5rem;position:relative;z-index:1}
.title-icon{filter:drop-shadow(0 0 8px #00f5ff);animation:iconPulse 2s ease-in-out infinite}
@keyframes iconPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.1)}}
.token-subtitle{font-family:'Share Tech Mono',monospace;color:#94a3b8;font-size:.85rem;letter-spacing:1px;position:relative;z-index:1}
.hero-glow{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:200%;height:200%;background:radial-gradient(circle,rgba(0,245,255,0.15)0%,transparent 70%);filter:blur(30px);opacity:.4;animation:heroPulse 3s ease-in-out infinite;pointer-events:none}
@keyframes heroPulse{0%,100%{opacity:.3;transform:translate(-50%,-50%)scale(1)}50%{opacity:.6;transform:translate(-50%,-50%)scale(1.1)}}

/* ── Controls ── */
.token-controls{display:flex;gap:1.5rem;align-items:center;padding:1rem 1.5rem;margin-bottom:1.5rem;background:rgba(12,18,40,0.7);border-radius:12px;border:1px solid rgba(0,245,255,0.15)}
.control-group{display:flex;align-items:center;gap:.75rem}
.control-label{font-family:'Share Tech Mono',monospace;color:#94a3b8;font-size:.75rem;letter-spacing:1px;white-space:nowrap}
.range-buttons,.filter-buttons{display:flex;gap:.5rem}
.range-buttons button,.filter-buttons button{background:rgba(0,245,255,0.05);border:1px solid rgba(0,245,255,0.15);color:#64748b;padding:.35rem .8rem;border-radius:6px;font-family:'Share Tech Mono',monospace;font-size:.7rem;cursor:pointer;transition:all .3s;letter-spacing:1px}
.range-buttons button:hover,.filter-buttons button:hover{border-color:#00f5ff;color:#94a3b8;box-shadow:0 0 8px rgba(0,245,255,0.15)}
.range-buttons button.active,.filter-buttons button.active{background:rgba(0,245,255,0.15);border-color:#00f5ff;color:#00f5ff;box-shadow:0 0 12px rgba(0,245,255,0.25);text-shadow:0 0 6px #00f5ff}

/* ── Export ── */
.export-group{display:flex;gap:.5rem;margin-left:auto}
.export-btn{background:rgba(0,245,255,0.05);border:1px solid rgba(0,245,255,0.15);color:#64748b;padding:.35rem .8rem;border-radius:6px;font-family:'Share Tech Mono',monospace;font-size:.7rem;cursor:pointer;transition:all .3s}
.export-btn:hover{border-color:#00f5ff;color:#00f5ff;box-shadow:0 0 8px rgba(0,245,255,0.2)}

/* ── Demo Banner ── */
.demo-banner{margin-bottom:1rem;padding:.75rem 1rem;border:1px solid rgba(255,184,0,0.4);color:#ffb800;font-size:.85rem;text-align:center}

/* ── Overview Grid ── */
.overview-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem}
.overview-card{background:rgba(12,18,40,0.7);backdrop-filter:blur(24px);padding:1.5rem;border-radius:12px;border:1px solid rgba(0,245,255,0.2);text-align:center;position:relative;overflow:hidden;transition:all .4s cubic-bezier(0.4,0,0.2,1)}
.card-corner-tl{position:absolute;top:0;left:0;width:16px;height:16px;border-top:2px solid var(--card-color);border-left:2px solid var(--card-color);border-radius:12px 0 4px 0;opacity:.5;z-index:2}
.card-corner-br{position:absolute;bottom:0;right:0;width:16px;height:16px;border-bottom:2px solid var(--card-color);border-right:2px solid var(--card-color);border-radius:0 4px 0 12px;opacity:.5;z-index:2}
.overview-card:hover{transform:translateY(-4px);border-color:var(--card-color);box-shadow:0 16px 48px rgba(0,0,0,0.5),0 0 40px var(--card-color)66}
.overview-icon{font-size:1.8rem;margin-bottom:.5rem;color:var(--card-color);filter:drop-shadow(0 0 8px var(--card-color));animation:iconPulse 3s ease-in-out infinite}
.overview-value{font-family:'Orbitron',sans-serif;font-size:1.8rem;font-weight:900;background:linear-gradient(180deg,var(--card-color),#fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:.25rem}
.overview-label{font-family:'Share Tech Mono',monospace;color:#94a3b8;font-size:.7rem;letter-spacing:2px;text-transform:uppercase}
.overview-glow{position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:50%;height:2px;background:linear-gradient(90deg,transparent,var(--card-color),transparent);box-shadow:0 0 10px var(--card-color);transition:all .3s}
.overview-card:hover .overview-glow{width:80%}

/* ── Sparkline ── */
.sparkline{width:80px;height:24px;display:block;margin:.25rem auto 0;color:var(--card-color);opacity:.7}

/* ── CRT Overlay ── */
.crt-overlay{position:absolute;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,245,255,0.03) 2px,rgba(0,245,255,0.03) 4px);pointer-events:none;z-index:1;animation:crtScan 8s linear infinite}
@keyframes crtScan{0%{background-position:0 0}100%{background-position:0 100px}}

/* ── Glitch Hover ── */
.glitch-hover{cursor:default}
.glitch-hover:hover{animation:glitch .3s ease-in-out}
@keyframes glitch{0%{transform:translate(0)}20%{transform:translate(-2px,1px);filter:hue-rotate(90deg)}40%{transform:translate(2px,-1px);filter:hue-rotate(-90deg)}60%{transform:translate(-1px,2px) skewX(2deg)}80%{transform:translate(1px,-2px) skewX(-2deg)}100%{transform:translate(0);filter:none}}

/* ── Pulse ── */
.overview-card.pulse{animation:neonPulse .8s ease-out}
@keyframes neonPulse{0%{border-color:var(--card-color);box-shadow:0 0 30px var(--card-color)}50%{border-color:transparent;box-shadow:none}100%{border-color:rgba(0,245,255,0.2);box-shadow:none}}

/* ── Chart Section ── */
.chart-section{background:rgba(12,18,40,0.7);backdrop-filter:blur(24px);padding:1.5rem;border-radius:12px;border:1px solid rgba(0,245,255,0.15);margin-bottom:1.5rem;position:relative}
.section-header{display:flex;align-items:center;gap:.5rem;margin-bottom:1rem}
.section-header h3{font-family:'Orbitron',sans-serif;font-size:.85rem;color:#e2e8f0;letter-spacing:2px}
.section-badge{color:#00f5ff;font-size:.9rem;filter:drop-shadow(0 0 4px #00f5ff)}
.chart-container{height:300px;width:100%}
.chart-small{height:250px}

/* ── Insight Grid ── */
.insight-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem}

/* ── Rank Table ── */
.rank-section{background:rgba(12,18,40,0.7);backdrop-filter:blur(24px);padding:1.5rem;border-radius:12px;border:1px solid rgba(0,245,255,0.15)}
.rank-table{width:100%}
.rank-header{display:flex;padding:.5rem 0;border-bottom:1px solid rgba(0,245,255,0.15);font-family:'Share Tech Mono',monospace;color:#64748b;font-size:.7rem;letter-spacing:1px}
.rank-row{display:flex;padding:.6rem 0;border-bottom:1px solid rgba(0,245,255,0.05);transition:all .3s}
.rank-row:hover{background:rgba(0,245,255,0.05);border-bottom-color:rgba(0,245,255,0.1)}
.rank-col-num{width:12%;text-align:center}
.rank-col-name{width:36%}
.rank-num{width:12%;font-family:'Orbitron',sans-serif;font-weight:700;text-align:center;font-size:.8rem}
.rank-num.gold{color:#ffd700;text-shadow:0 0 8px #ffd700}
.rank-num.silver{color:#c0c0c0;text-shadow:0 0 6px #c0c0c0}
.rank-num.bronze{color:#cd7f32;text-shadow:0 0 6px #cd7f32}
.rank-name{width:36%;font-family:'Share Tech Mono',monospace;color:#e2e8f0;font-size:.8rem;display:flex;align-items:center;gap:.5rem}
.model-dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.rank-val{width:12%;text-align:center;font-family:'Share Tech Mono',monospace;color:#94a3b8;font-size:.8rem}
.rank-val.cost{color:#ffd700}

/* ── Session Table ── */
.session-table{width:100%}
.session-header{display:flex;padding:.5rem 0;border-bottom:1px solid rgba(0,245,255,0.15);font-family:'Share Tech Mono',monospace;color:#64748b;font-size:.7rem;letter-spacing:1px}
.session-row{display:flex;padding:.6rem 0;border-bottom:1px solid rgba(0,245,255,0.05);transition:all .3s}
.session-row:hover{background:rgba(0,245,255,0.05)}
.session-col{width:16%;text-align:center;font-family:'Share Tech Mono',monospace;font-size:.7rem;color:#64748b}
.session-num{width:8%;font-family:'Orbitron',sans-serif;font-weight:700;text-align:center;font-size:.8rem}
.session-num.gold{color:#ffd700;text-shadow:0 0 8px #ffd700}
.session-num.silver{color:#c0c0c0;text-shadow:0 0 6px #c0c0c0}
.session-num.bronze{color:#cd7f32;text-shadow:0 0 6px #cd7f32}
.session-val{width:16%;text-align:center;font-family:'Share Tech Mono',monospace;color:#94a3b8;font-size:.8rem}
.session-val.cost{color:#ffd700}
.session-val.date{color:#64748b;font-size:.7rem}

/* ── Prediction Card ── */
.prediction-card{background:rgba(12,18,40,0.7);backdrop-filter:blur(24px);padding:1.5rem;border-radius:12px;border:1px solid rgba(0,245,255,0.15);margin-bottom:1.5rem;text-align:center;position:relative;overflow:hidden}
.prediction-icon{font-size:2rem;color:#ff00ff;margin-bottom:.5rem;animation:iconPulse 3s ease-in-out infinite}
.prediction-title{font-family:'Orbitron',sans-serif;font-size:.85rem;color:#e2e8f0;letter-spacing:2px;margin-bottom:1rem}
.prediction-content{position:relative;z-index:2}
.prediction-row{display:flex;justify-content:center;gap:.5rem;margin-bottom:.5rem}
.prediction-label{font-family:'Share Tech Mono',monospace;color:#94a3b8;font-size:.7rem;letter-spacing:1px}
.prediction-value{font-family:'Orbitron',sans-serif;font-size:1.1rem;font-weight:700;color:#00f5ff}
.trend-up{color:#ff3366;text-shadow:0 0 8px #ff3366}
.trend-down{color:#00ff88;text-shadow:0 0 8px #00ff88}
.trend-stable{color:#ffd700;text-shadow:0 0 8px #ffd700}

/* ── Loading ── */
.token-loading{display:flex;align-items:center;gap:1rem;justify-content:center;padding:4rem}
.loading-bars{display:flex;gap:6px}
.loading-bar{width:8px;height:20px;background:#00f5ff;border-radius:2px;animation:barPulse 1.2s ease-in-out infinite}
.loading-bar:nth-child(2){animation-delay:.2s}
.loading-bar:nth-child(3){animation-delay:.4s}
@keyframes barPulse{0%,100%{transform:scaleY(.4);opacity:.3}50%{transform:scaleY(1);opacity:1}}
.loading-text{font-family:'Share Tech Mono',monospace;color:#94a3b8;font-size:.8rem;letter-spacing:1px}

/* ── Empty ── */
.token-empty{text-align:center;padding:4rem}
.empty-icon{font-size:3rem;color:#00f5ff;opacity:.2;filter:drop-shadow(0 0 4px #00f5ff)}
.empty-text{font-family:'Orbitron',sans-serif;color:#64748b;font-size:1rem;margin-top:1rem}

@media (max-width:768px) {
  .overview-grid{grid-template-columns:1fr 1fr}
  .insight-grid{grid-template-columns:1fr}
  .token-controls{flex-direction:column}
  .export-group{margin-left:0}
}
</style>
