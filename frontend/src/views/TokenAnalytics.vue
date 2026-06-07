<template>
  <div class="token-page">
    <!-- 页面标题 -->
    <div class="token-hero">
      <div class="corner-tl"></div>
      <div class="corner-br"></div>
      <div class="hologram-scan"></div>
      <h2 class="token-title glitch-text" data-text="TOKEN ANALYTICS">
        <span class="title-icon">⟐</span> {{ t('token.title') }}
      </h2>
      <p class="token-subtitle">{{ t('token.subtitle') }}</p>
      <div class="hero-glow"></div>
    </div>

    <!-- 时间范围选择 -->
    <div class="token-controls card">
      <div class="control-group">
        <label class="control-label">{{ t('token.timeRange') }}</label>
        <div class="range-buttons">
          <button v-for="r in timeRanges" :key="r.key"
            @click="selectedRange = r.key"
            :class="{ active: selectedRange === r.key }"
          >{{ t(`token.${r.key}`) }}</button>
        </div>
      </div>
      <div class="control-group">
        <label class="control-label">{{ t('token.modelFilter') }}</label>
        <div class="filter-buttons">
          <button @click="selectedModel = 'all'"
            :class="{ active: selectedModel === 'all' }"
          >{{ t('token.allModels') }}</button>
          <button v-for="m in availableModels" :key="m"
            @click="selectedModel = m"
            :class="{ active: selectedModel === m }"
          >{{ m }}</button>
        </div>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="token-loading">
      <div class="loading-bars">
        <span class="loading-bar"></span>
        <span class="loading-bar"></span>
        <span class="loading-bar"></span>
      </div>
      <span class="loading-text">{{ t('token.loading') }}</span>
    </div>

    <!-- 无数据 -->
    <div v-else-if="!tokenData" class="token-empty card">
      <div class="empty-icon">⟐</div>
      <div class="empty-text">{{ t('token.noData') }}</div>
      <div class="empty-hint">{{ t('token.noDataHint') }}</div>
    </div>

    <!-- 有数据 -->
    <template v-else>
      <!-- 概览卡片 -->
      <div class="overview-grid">
        <div class="overview-card card" :style="{ '--card-color': '#00f5ff' }">
          <div class="card-corner-tl"></div><div class="card-corner-br"></div>
          <div class="overview-icon">◈</div>
          <div class="overview-value">{{ formatNum(tokenData.totalInput) }}</div>
          <div class="overview-label">{{ t('token.totalInput') }}</div>
          <div class="overview-unit">tokens</div>
          <div class="overview-glow"></div>
        </div>
        <div class="overview-card card" :style="{ '--card-color': '#ff00ff' }">
          <div class="card-corner-tl"></div><div class="card-corner-br"></div>
          <div class="overview-icon">⟐</div>
          <div class="overview-value">{{ formatNum(tokenData.totalOutput) }}</div>
          <div class="overview-label">{{ t('token.totalOutput') }}</div>
          <div class="overview-unit">tokens</div>
          <div class="overview-glow"></div>
        </div>
        <div class="overview-card card" :style="{ '--card-color': '#00ff88' }">
          <div class="card-corner-tl"></div><div class="card-corner-br"></div>
          <div class="overview-icon">⟡</div>
          <div class="overview-value">{{ formatNum(tokenData.totalTokens) }}</div>
          <div class="overview-label">{{ t('token.totalTokens') }}</div>
          <div class="overview-unit">tokens</div>
          <div class="overview-glow"></div>
        </div>
        <div class="overview-card card" :style="{ '--card-color': '#ffd700' }">
          <div class="card-corner-tl"></div><div class="card-corner-br"></div>
          <div class="overview-icon">$</div>
          <div class="overview-value">${{ formatCost(tokenData.totalCost) }}</div>
          <div class="overview-label">{{ t('token.totalCost') }}</div>
          <div class="overview-unit">{{ t('token.estimated') }}</div>
          <div class="overview-glow"></div>
        </div>
      </div>

      <!-- 模型对比图表 -->
      <div class="chart-section card">
        <div class="section-header">
          <h3>{{ t('token.modelComparison') }}</h3>
          <span class="section-badge">◆</span>
        </div>
        <div ref="modelChartRef" class="chart-container"></div>
      </div>

      <!-- Token趋势图 -->
      <div class="chart-section card">
        <div class="section-header">
          <h3>{{ t('token.tokenTrend') }}</h3>
          <span class="section-badge">◈</span>
        </div>
        <div ref="trendChartRef" class="chart-container"></div>
      </div>

      <!-- 成本占比饼图 + 模型排行表 -->
      <div class="insight-grid">
        <div class="chart-section card">
          <div class="section-header">
            <h3>{{ t('token.costDistribution') }}</h3>
            <span class="section-badge">$</span>
          </div>
          <div ref="costPieRef" class="chart-container chart-small"></div>
        </div>
        <div class="rank-section card">
          <div class="section-header">
            <h3>{{ t('token.modelRank') }}</h3>
            <span class="section-badge">🏆</span>
          </div>
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
                <span class="model-dot" :style="{ background: modelColors[idx % modelColors.length] }"></span>
                {{ m.model }}
              </div>
              <div class="rank-val">{{ formatNum(m.input) }}</div>
              <div class="rank-val">{{ formatNum(m.output) }}</div>
              <div class="rank-val cost">${{ formatCost(m.cost) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入输出比率雷达图 -->
      <div class="chart-section card">
        <div class="section-header">
          <h3>{{ t('token.ioRatio') }}</h3>
          <span class="section-badge">◉</span>
        </div>
        <div ref="ratioChartRef" class="chart-container chart-small"></div>
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

const { t } = useI18n()

const tokenData = ref(null)
const loading = ref(true)
const selectedRange = ref('thisWeek')
const selectedModel = ref('all')
const availableModels = ref([])

const modelChartRef = ref(null)
const trendChartRef = ref(null)
const costPieRef = ref(null)
const ratioChartRef = ref(null)

let modelChart = null
let trendChart = null
let costPie = null
let ratioChart = null

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

async function fetchTokenData() {
  loading.value = true
  try {
    const data = await api.getTokenStats(selectedRange.value, selectedModel.value)
    tokenData.value = data
    availableModels.value = data.availableModels || []
  } catch (err) {
    console.error('Failed to fetch token stats:', err)
    tokenData.value = null
  } finally {
    loading.value = false
  }
}

function initCharts() {
  if (!tokenData.value) return
  nextTick(() => {
    initModelChart()
    initTrendChart()
    initCostPie()
    initRatioChart()
  })
}

function initModelChart() {
  if (!modelChartRef.value) return
  modelChart = echarts.init(modelChartRef.value)
  const d = tokenData.value.modelRank || []

  modelChart.setOption({
    ...CYBERPUNK_CHART_THEME,
    tooltip: { ...CYBERPUNK_CHART_THEME.tooltip, trigger: 'axis' },
    legend: {
      data: [t('token.inputTokens'), t('token.outputTokens')],
      textStyle: { color: '#94a3b8', fontFamily: 'Share Tech Mono' },
      top: 0
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: d.map(m => m.model),
      axisLabel: { color: '#94a3b8', fontSize: 11, rotate: 15 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: v => v >= 1e3 ? (v/1e3)+'K' : v }
    },
    series: [
      {
        name: t('token.inputTokens'),
        type: 'bar',
        data: d.map(m => m.input),
        itemStyle: { color: '#00f5ff', borderRadius: [4,4,0,0] },
        barWidth: '30%'
      },
      {
        name: t('token.outputTokens'),
        type: 'bar',
        data: d.map(m => m.output),
        itemStyle: { color: '#ff00ff', borderRadius: [4,4,0,0] },
        barWidth: '30%'
      }
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
    legend: {
      data: [t('token.inputTokens'), t('token.outputTokens')],
      textStyle: { color: '#94a3b8', fontFamily: 'Share Tech Mono' },
      top: 0
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: d.map(item => item.date),
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: v => v >= 1e3 ? (v/1e3)+'K' : v }
    },
    series: [
      {
        name: t('token.inputTokens'),
        type: 'line',
        data: d.map(item => item.input),
        smooth: true,
        lineStyle: { color: '#00f5ff', width: 2 },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#00f5ff44' }, { offset: 1, color: '#00f5ff05' }] } },
        symbol: 'none'
      },
      {
        name: t('token.outputTokens'),
        type: 'line',
        data: d.map(item => item.output),
        smooth: true,
        lineStyle: { color: '#ff00ff', width: 2 },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#ff00ff44' }, { offset: 1, color: '#ff00ff05' }] } },
        symbol: 'none'
      }
    ]
  })
}

function initCostPie() {
  if (!costPieRef.value) return
  costPie = echarts.init(costPieRef.value)
  const d = tokenData.value.modelRank || []

  costPie.setOption({
    tooltip: { ...CYBERPUNK_CHART_THEME.tooltip, trigger: 'item', formatter: '{b}: ${c} ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '55%'],
      data: d.map((m, i) => ({
        name: m.model,
        value: m.cost,
        itemStyle: { color: modelColors[i % modelColors.length], borderColor: 'rgba(0,245,255,0.3)', borderWidth: 1 }
      })),
      label: {
        color: '#94a3b8',
        fontFamily: 'Share Tech Mono',
        fontSize: 11,
        formatter: '{b}\n${c}'
      },
      labelLine: { lineStyle: { color: '#64748b' } },
      emphasis: {
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,245,255,0.5)' },
        label: { fontSize: 14, fontWeight: 'bold', color: '#00f5ff' }
      }
    }]
  })
}

function initRatioChart() {
  if (!ratioChartRef.value) return
  ratioChart = echarts.init(ratioChartRef.value)
  const d = tokenData.value.modelRank || []

  // 雷达图：每个模型的input/output/total/cost四个维度
  const indicators = [
    { name: t('token.inputTokens'), max: Math.max(...d.map(m => m.input), 1) },
    { name: t('token.outputTokens'), max: Math.max(...d.map(m => m.output), 1) },
    { name: t('token.totalTokens'), max: Math.max(...d.map(m => m.input+m.output), 1) },
    { name: t('token.cost'), max: Math.max(...d.map(m => m.cost * 1000), 1) }  // 放大cost以便可视化
  ]

  ratioChart.setOption({
    tooltip: { ...CYBERPUNK_CHART_THEME.tooltip },
    legend: {
      data: d.slice(0, 5).map(m => m.model),
      textStyle: { color: '#94a3b8', fontFamily: 'Share Tech Mono' },
      top: 0
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      axisName: { color: '#94a3b8', fontFamily: 'Share Tech Mono', fontSize: 11 },
      splitArea: { areaStyle: { color: ['rgba(0,245,255,0.02)', 'rgba(0,245,255,0.05)'] } },
      splitLine: { lineStyle: { color: 'rgba(0,245,255,0.1)' } },
      axisLine: { lineStyle: { color: 'rgba(0,245,255,0.2)' } }
    },
    series: [{
      type: 'radar',
      data: d.slice(0, 5).map((m, i) => ({
        name: m.model,
        value: [m.input, m.output, m.input+m.output, m.cost*1000],
        lineStyle: { color: modelColors[i % modelColors.length], width: 2 },
        areaStyle: { color: modelColors[i % modelColors.length] + '33' },
        symbol: 'circle',
        symbolSize: 4,
        itemStyle: { color: modelColors[i % modelColors.length] }
      }))
    }]
  })
}

function handleResize() {
  modelChart?.resize()
  trendChart?.resize()
  costPie?.resize()
  ratioChart?.resize()
}

watch([selectedRange, selectedModel], () => {
  fetchTokenData()
})

watch(tokenData, () => {
  // 清除旧图表
  modelChart?.dispose(); trendChart?.dispose(); costPie?.dispose(); ratioChart?.dispose()
  modelChart = null; trendChart = null; costPie = null; ratioChart = null
  initCharts()
})

onMounted(() => {
  fetchTokenData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  modelChart?.dispose(); trendChart?.dispose(); costPie?.dispose(); ratioChart?.dispose()
})
</script>

<style scoped>
.token-page {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
}

/* ── Hero ── */
.token-hero {
  background: rgba(12, 18, 40, 0.7);
  backdrop-filter: blur(24px);
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid rgba(0,245,255,0.2);
  text-align: center;
  position: relative;
  overflow: hidden;
  margin-bottom: 1.5rem;
}
.corner-tl { position:absolute;top:0;left:0;width:20px;height:20px;border-top:2px solid var(--card-color,#00f5ff);border-left:2px solid var(--card-color,#00f5ff);border-radius:12px 0 4px 0;opacity:.5;z-index:2;box-shadow:0 0 6px var(--card-color,#00f5ff) }
.corner-br { position:absolute;bottom:0;right:0;width:20px;height:20px;border-bottom:2px solid var(--card-color,#00f5ff);border-right:2px solid var(--card-color,#00f5ff);border-radius:0 4px 0 12px;opacity:.5;z-index:2;box-shadow:0 0 6px var(--card-color,#00f5ff) }
.hologram-scan { position:absolute;top:-100%;left:0;width:100%;height:30%;background:linear-gradient(180deg,transparent,rgba(255,255,255,0.04),transparent);z-index:1;animation:hScan 4s ease-in-out infinite;pointer-events:none }
@keyframes hScan { 0%{top:-30%} 100%{top:130%} }

.token-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  font-weight: 900;
  background: linear-gradient(135deg, #00f5ff, #7800ff, #ff00ff);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 3px;
  margin-bottom: 0.5rem;
  position: relative; z-index: 1;
}
.title-icon { filter: drop-shadow(0 0 8px #00f5ff); animation: iconPulse 2s ease-in-out infinite; }
@keyframes iconPulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.1)} }

.token-subtitle {
  font-family: 'Share Tech Mono', monospace;
  color: #94a3b8;
  font-size: 0.85rem;
  letter-spacing: 1px;
  position: relative; z-index: 1;
}
.hero-glow {
  position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  width:200%;height:200%;background:radial-gradient(circle,rgba(0,245,255,0.15)0%,transparent 70%);
  filter:blur(30px);opacity:.4;animation:heroPulse 3s ease-in-out infinite;pointer-events:none
}
@keyframes heroPulse { 0%,100%{opacity:.3;transform:translate(-50%,-50%)scale(1)} 50%{opacity:.6;transform:translate(-50%,-50%)scale(1.1)} }

/* ── Controls ── */
.token-controls {
  display: flex; gap: 1.5rem; align-items: center;
  padding: 1rem 1.5rem; margin-bottom: 1.5rem;
  background: rgba(12,18,40,0.7); border-radius: 12px;
  border: 1px solid rgba(0,245,255,0.15);
}
.control-group { display: flex; align-items: center; gap: 0.75rem; }
.control-label {
  font-family: 'Share Tech Mono', monospace;
  color: #94a3b8; font-size: 0.75rem;
  letter-spacing: 1px; white-space: nowrap;
}
.range-buttons, .filter-buttons { display: flex; gap: 0.5rem; }
.range-buttons button, .filter-buttons button {
  background: rgba(0,245,255,0.05);
  border: 1px solid rgba(0,245,255,0.15);
  color: #64748b; padding: 0.35rem 0.8rem;
  border-radius: 6px; font-family: 'Share Tech Mono', monospace;
  font-size: 0.7rem; cursor: pointer;
  transition: all 0.3s; letter-spacing: 1px;
}
.range-buttons button:hover, .filter-buttons button:hover {
  border-color: #00f5ff; color: #94a3b8;
  box-shadow: 0 0 8px rgba(0,245,255,0.15);
}
.range-buttons button.active, .filter-buttons button.active {
  background: rgba(0,245,255,0.15);
  border-color: #00f5ff; color: #00f5ff;
  box-shadow: 0 0 12px rgba(0,245,255,0.25);
  text-shadow: 0 0 6px #00f5ff;
}

/* ── Overview Grid ── */
.overview-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 1rem; margin-bottom: 1.5rem;
}
.overview-card {
  background: rgba(12,18,40,0.7); backdrop-filter: blur(24px);
  padding: 1.5rem; border-radius: 12px;
  border: 1px solid rgba(0,245,255,0.2);
  text-align: center; position: relative;
  overflow: hidden; transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
}
.card-corner-tl { position:absolute;top:0;left:0;width:16px;height:16px;border-top:2px solid var(--card-color);border-left:2px solid var(--card-color);border-radius:12px 0 4px 0;opacity:.5;z-index:2 }
.card-corner-br { position:absolute;bottom:0;right:0;width:16px;height:16px;border-bottom:2px solid var(--card-color);border-right:2px solid var(--card-color);border-radius:0 4px 0 12px;opacity:.5;z-index:2 }
.overview-card:hover { transform:translateY(-4px);border-color:var(--card-color);box-shadow:0 16px 48px rgba(0,0,0,0.5),0 0 40px var(--card-color)66 }
.overview-icon { font-size:1.8rem;margin-bottom:0.5rem;color:var(--card-color);filter:drop-shadow(0 0 8px var(--card-color));animation:iconPulse 3s ease-in-out infinite }
.overview-value {
  font-family:'Orbitron',sans-serif;font-size:1.8rem;font-weight:900;
  background:linear-gradient(180deg,var(--card-color),#fff);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;margin-bottom:0.25rem;
}
.overview-label { font-family:'Share Tech Mono',monospace;color:#94a3b8;font-size:.7rem;letter-spacing:2px;text-transform:uppercase }
.overview-unit { font-family:'Share Tech Mono',monospace;color:#475569;font-size:.65rem }
.overview-glow { position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:50%;height:2px;background:linear-gradient(90deg,transparent,var(--card-color),transparent);box-shadow:0 0 10px var(--card-color);transition:all .3s }
.overview-card:hover .overview-glow { width:80% }

/* ── Chart Section ── */
.chart-section {
  background:rgba(12,18,40,0.7);backdrop-filter:blur(24px);
  padding:1.5rem;border-radius:12px;
  border:1px solid rgba(0,245,255,0.15);
  margin-bottom:1.5rem;
}
.section-header { display:flex;align-items:center;gap:0.5rem;margin-bottom:1rem }
.section-header h3 { font-family:'Orbitron',sans-serif;font-size:.85rem;color:#e2e8f0;letter-spacing:2px }
.section-badge { color:#00f5ff;font-size:.9rem;filter:drop-shadow(0 0 4px #00f5ff) }
.chart-container { height:300px;width:100% }
.chart-small { height:250px }

/* ── Insight Grid ── */
.insight-grid { display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem }

/* ── Rank Table ── */
.rank-section {
  background:rgba(12,18,40,0.7);backdrop-filter:blur(24px);
  padding:1.5rem;border-radius:12px;
  border:1px solid rgba(0,245,255,0.15);
}
.rank-table { width:100% }
.rank-header { display:flex;padding:.5rem 0;border-bottom:1px solid rgba(0,245,255,0.15);font-family:'Share Tech Mono',monospace;color:#64748b;font-size:.7rem;letter-spacing:1px }
.rank-row { display:flex;padding:.6rem 0;border-bottom:1px solid rgba(0,245,255,0.05);transition:all .3s }
.rank-row:hover { background:rgba(0,245,255,0.05);border-bottom-color:rgba(0,245,255,0.1) }
.rank-col-num { width:12%;text-align:center }
.rank-col-name { width:36%; }
.rank-header .rank-col-num { text-align:center }
.rank-num { width:12%;font-family:'Orbitron',sans-serif;font-weight:700;text-align:center;font-size:.8rem }
.rank-num.gold { color:#ffd700;text-shadow:0 0 8px #ffd700 }
.rank-num.silver { color:#c0c0c0;text-shadow:0 0 6px #c0c0c0 }
.rank-num.bronze { color:#cd7f32;text-shadow:0 0 6px #cd7f32 }
.rank-name { width:36%;font-family:'Share Tech Mono',monospace;color:#e2e8f0;font-size:.8rem;display:flex;align-items:center;gap:.5rem }
.model-dot { width:8px;height:8px;border-radius:50%;display:inline-block }
.rank-val { width:12%;text-align:center;font-family:'Share Tech Mono',monospace;color:#94a3b8;font-size:.8rem }
.rank-val.cost { color:#ffd700 }

/* ── Loading ── */
.token-loading { display:flex;align-items:center;gap:1rem;justify-content:center;padding:4rem }
.loading-bars { display:flex;gap:6px }
.loading-bar { width:8px;height:20px;background:#00f5ff;border-radius:2px;animation:barPulse 1.2s ease-in-out infinite }
.loading-bar:nth-child(2) { animation-delay:.2s }
.loading-bar:nth-child(3) { animation-delay:.4s }
@keyframes barPulse { 0%,100%{transform:scaleY(0.4);opacity:.3} 50%{transform:scaleY(1);opacity:1} }
.loading-text { font-family:'Share Tech Mono',monospace;color:#94a3b8;font-size:.8rem;letter-spacing:1px }

/* ── Empty ── */
.token-empty { text-align:center;padding:4rem }
.empty-icon { font-size:3rem;color:#00f5ff;opacity:.2;filter:drop-shadow(0 0 4px #00f5ff) }
.empty-text { font-family:'Orbitron',sans-serif;color:#64748b;font-size:1rem;margin-top:1rem }
.empty-hint { font-family:'Share Tech Mono',monospace;color:#475569;font-size:.75rem;margin-top:.5rem }

@media (max-width:768px) {
  .overview-grid { grid-template-columns:1fr 1fr }
  .insight-grid { grid-template-columns:1fr }
  .token-controls { flex-direction:column }
}
</style>