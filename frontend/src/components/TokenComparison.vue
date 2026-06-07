<template>
  <div class="token-comparison">
    <div class="comparison-header">
      <span class="comp-title">时段对比分析</span>
      <span class="comp-subtitle">PERIOD COMPARISON</span>
    </div>

    <div class="comparison-layout">
      <!-- Current Period -->
      <div class="period-column period-current">
        <div class="column-label">当前时段</div>
        <div class="column-label-sub">CURRENT</div>

        <div class="period-card">
          <div class="card-corner-tl"></div>
          <div class="card-corner-br"></div>
          <div class="hologram-scan"></div>

          <div class="metric-row">
            <span class="metric-label">总 Token</span>
            <span class="metric-value">
              {{ formatNumber(comparisonData.currentPeriod?.totalTokens || 0) }}
            </span>
          </div>

          <div class="metric-row">
            <span class="metric-label">总成本</span>
            <span class="metric-value value-cost">
              ¥{{ formatNumber(comparisonData.currentPeriod?.totalCost || 0) }}
            </span>
          </div>

          <div class="metric-row">
            <span class="metric-label">日均 Token</span>
            <span class="metric-value value-daily">
              {{ formatNumber(comparisonData.currentPeriod?.dailyAverage || 0) }}
            </span>
          </div>

          <div class="period-sparkline">
            <svg width="100%" height="40" viewBox="0 0 120 40">
              <polyline
                :points="getSparklinePoints(comparisonData.currentPeriod?.sparkline || [])"
                fill="none"
                stroke="#00f5ff"
                stroke-width="1.5"
                class="sparkline-path"
              />
              <polyline
                :points="getSparklinePoints(comparisonData.currentPeriod?.sparkline || [])"
                fill="none"
                stroke="rgba(0, 245, 255, 0.15)"
                stroke-width="6"
              />
            </svg>
          </div>
        </div>
      </div>

      <!-- Change Arrow Center -->
      <div class="change-center">
        <div
          class="change-arrow"
          :class="{
            'arrow-up': changePercent > 0,
            'arrow-down': changePercent < 0,
            'arrow-neutral': changePercent === 0
          }"
        >
          <div class="arrow-icon">
            <span v-if="changePercent > 0">&#9650;</span>
            <span v-else-if="changePercent < 0">&#9660;</span>
            <span v-else>&#9644;</span>
          </div>
          <div class="change-percent">
            {{ Math.abs(changePercent).toFixed(1) }}%
          </div>
          <div class="change-label">
            {{ changePercent > 0 ? '增长 ↑' : changePercent < 0 ? '下降 ↓' : '持平' }}
          </div>
        </div>
      </div>

      <!-- Previous Period -->
      <div class="period-column period-previous">
        <div class="column-label">上时段</div>
        <div class="column-label-sub">PREVIOUS</div>

        <div class="period-card card-muted">
          <div class="card-corner-tl"></div>
          <div class="card-corner-br"></div>
          <div class="hologram-scan scan-muted"></div>

          <div class="metric-row">
            <span class="metric-label">总 Token</span>
            <span class="metric-value value-muted">
              {{ formatNumber(comparisonData.previousPeriod?.totalTokens || 0) }}
            </span>
          </div>

          <div class="metric-row">
            <span class="metric-label">总成本</span>
            <span class="metric-value value-cost-muted">
              ¥{{ formatNumber(comparisonData.previousPeriod?.totalCost || 0) }}
            </span>
          </div>

          <div class="metric-row">
            <span class="metric-label">日均 Token</span>
            <span class="metric-value value-daily-muted">
              {{ formatNumber(comparisonData.previousPeriod?.dailyAverage || 0) }}
            </span>
          </div>

          <div class="period-sparkline">
            <svg width="100%" height="40" viewBox="0 0 120 40">
              <polyline
                :points="getSparklinePoints(comparisonData.previousPeriod?.sparkline || [])"
                fill="none"
                stroke="rgba(0, 245, 255, 0.4)"
                stroke-width="1.5"
                class="sparkline-path"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  comparisonData: {
    type: Object,
    default: () => ({
      currentPeriod: { totalTokens: 0, totalCost: 0, dailyAverage: 0, sparkline: [] },
      previousPeriod: { totalTokens: 0, totalCost: 0, dailyAverage: 0, sparkline: [] },
      changePercent: 0
    })
  }
})

const changePercent = computed(() => props.comparisonData.changePercent || 0)

function formatNumber(n) {
  if (!n && n !== 0) return '0'
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n.toFixed(0)
}

function getSparklinePoints(data) {
  if (!data || !data.length) return '0,20 120,20'
  const max = Math.max(...data, 1)
  const step = 120 / (data.length - 1 || 1)
  return data.map((v, i) => {
    const x = i * step
    const y = 40 - (v / max) * 36
    return `${x},${y}`
  }).join(' ')
}
</script>

<style scoped>
.token-comparison {
  background: rgba(12, 18, 40, 0.7);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 4px;
  padding: 20px;
  font-family: 'Share Tech Mono', monospace;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 16px;
}

.comp-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  color: #00f5ff;
  letter-spacing: 2px;
}

.comp-subtitle {
  font-size: 11px;
  color: rgba(0, 245, 255, 0.5);
  letter-spacing: 1px;
}

.comparison-layout {
  display: flex;
  gap: 16px;
  align-items: center;
}

.period-column {
  flex: 1;
}

.column-label {
  font-family: 'Orbitron', sans-serif;
  font-size: 13px;
  color: #00f5ff;
  letter-spacing: 1px;
  margin-bottom: 2px;
}

.column-label-sub {
  font-size: 10px;
  color: rgba(0, 245, 255, 0.4);
  letter-spacing: 1px;
  margin-bottom: 12px;
}

.period-previous .column-label {
  color: rgba(0, 245, 255, 0.5);
}

.period-card {
  background: rgba(8, 14, 36, 0.8);
  border: 1px solid rgba(0, 245, 255, 0.25);
  border-radius: 4px;
  padding: 16px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.period-card:hover {
  box-shadow: 0 0 16px rgba(0, 245, 255, 0.25);
  border-color: rgba(0, 245, 255, 0.4);
}

.card-muted {
  border-color: rgba(0, 245, 255, 0.12);
}

.card-muted:hover {
  box-shadow: 0 0 10px rgba(0, 245, 255, 0.15);
  border-color: rgba(0, 245, 255, 0.25);
}

/* Corner decorations */
.card-corner-tl {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 12px;
  height: 12px;
  border-top: 2px solid #00f5ff;
  border-left: 2px solid #00f5ff;
}

.card-muted .card-corner-tl {
  border-top-color: rgba(0, 245, 255, 0.3);
  border-left-color: rgba(0, 245, 255, 0.3);
}

.card-corner-br {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 12px;
  height: 12px;
  border-bottom: 2px solid #00f5ff;
  border-right: 2px solid #00f5ff;
}

.card-muted .card-corner-br {
  border-bottom-color: rgba(0, 245, 255, 0.3);
  border-right-color: rgba(0, 245, 255, 0.3);
}

/* Hologram scan */
.hologram-scan {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
  background: linear-gradient(
    transparent 0%,
    rgba(0, 245, 255, 0.03) 50%,
    transparent 100%
  );
  animation: holoScan 4s ease-in-out infinite;
  pointer-events: none;
}

.scan-muted {
  background: linear-gradient(
    transparent 0%,
    rgba(0, 245, 255, 0.015) 50%,
    transparent 100%
  );
}

@keyframes holoScan {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}

/* Metric rows */
.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid rgba(0, 245, 255, 0.06);
}

.metric-row:last-of-type {
  border-bottom: none;
}

.metric-label {
  font-size: 12px;
  color: rgba(0, 245, 255, 0.5);
}

.metric-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  color: #00f5ff;
}

.value-cost {
  color: #ffd700;
}

.value-daily {
  color: #00ff88;
}

.value-muted {
  color: rgba(0, 245, 255, 0.4);
}

.value-cost-muted {
  color: rgba(255, 215, 0, 0.4);
}

.value-daily-muted {
  color: rgba(0, 255, 136, 0.4);
}

/* Sparkline */
.period-sparkline {
  margin-top: 8px;
}

.sparkline-path {
  animation: sparkDraw 1s ease-out forwards;
}

@keyframes sparkDraw {
  from { stroke-dasharray: 200; stroke-dashoffset: 200; }
  to { stroke-dasharray: 200; stroke-dashoffset: 0; }
}

/* Change center */
.change-center {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 80px;
}

.change-arrow {
  text-align: center;
  padding: 12px;
  border-radius: 4px;
  background: rgba(8, 14, 36, 0.6);
  border: 1px solid rgba(0, 245, 255, 0.15);
  transition: all 0.3s ease;
}

.arrow-up {
  border-color: rgba(255, 51, 102, 0.3);
  background: rgba(255, 51, 102, 0.05);
  animation: arrowUpPulse 2s ease-in-out infinite;
}

.arrow-down {
  border-color: rgba(0, 255, 136, 0.3);
  background: rgba(0, 255, 136, 0.05);
}

.arrow-neutral {
  border-color: rgba(0, 245, 255, 0.15);
}

@keyframes arrowUpPulse {
  0%, 100% { box-shadow: 0 0 4px rgba(255, 51, 102, 0.1); }
  50% { box-shadow: 0 0 12px rgba(255, 51, 102, 0.3); }
}

.arrow-icon {
  font-size: 20px;
  margin-bottom: 4px;
}

.arrow-up .arrow-icon {
  color: #ff3366;
}

.arrow-down .arrow-icon {
  color: #00ff88;
}

.arrow-neutral .arrow-icon {
  color: rgba(0, 245, 255, 0.5);
}

.change-percent {
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  letter-spacing: 1px;
  margin-bottom: 2px;
}

.arrow-up .change-percent {
  color: #ff3366;
}

.arrow-down .change-percent {
  color: #00ff88;
}

.arrow-neutral .change-percent {
  color: rgba(0, 245, 255, 0.5);
}

.change-label {
  font-size: 11px;
  letter-spacing: 1px;
}

.arrow-up .change-label {
  color: rgba(255, 51, 102, 0.6);
}

.arrow-down .change-label {
  color: rgba(0, 255, 136, 0.6);
}

.arrow-neutral .change-label {
  color: rgba(0, 245, 255, 0.4);
}
</style>