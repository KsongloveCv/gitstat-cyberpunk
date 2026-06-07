<template>
  <div class="token-efficiency-cards">
    <div class="efficiency-header">
      <span class="eff-title">模型效率指标</span>
      <span class="eff-subtitle">MODEL EFFICIENCY METRICS</span>
    </div>

    <div class="cards-row">
      <!-- Card 1: Average Output/Input Ratio -->
      <div class="eff-card">
        <div class="card-corner-tl"></div>
        <div class="card-corner-br"></div>
        <div class="hologram-scan"></div>
        <div class="card-icon">&#8644;</div>
        <div class="card-label">平均输出/输入比率</div>
        <div class="card-value">AVG RATIO</div>
        <div class="card-number">{{ formatNumber(efficiencyData.averageRatio) }}x</div>
        <div class="card-glow-bar">
          <div
            class="glow-fill"
            :style="{ width: getBarWidth(efficiencyData.averageRatio, maxRatio) + '%' }"
          ></div>
        </div>
      </div>

      <!-- Card 2: Best Value Model (Gold Highlight) -->
      <div class="eff-card card-best">
        <div class="card-corner-tl"></div>
        <div class="card-corner-br"></div>
        <div class="hologram-scan hologram-gold"></div>
        <div class="card-icon trophy">&#9733;</div>
        <div class="card-label">最佳性价比模型</div>
        <div class="card-value">BEST VALUE</div>
        <div class="card-number card-number-gold">{{ efficiencyData.bestValueModel || '—' }}</div>
        <div class="card-meta">
          {{ formatNumber(efficiencyData.bestValuePerDollar) }} tokens/$
        </div>
        <div class="card-glow-bar bar-gold">
          <div
            class="glow-fill fill-gold"
            :style="{ width: getBarWidth(efficiencyData.bestValuePerDollar, maxPerDollar) + '%' }"
          ></div>
        </div>
      </div>

      <!-- Card 3: Average Tokens per Dollar -->
      <div class="eff-card">
        <div class="card-corner-tl"></div>
        <div class="card-corner-br"></div>
        <div class="hologram-scan"></div>
        <div class="card-icon">&#36;</div>
        <div class="card-label">每美元平均 Token 产出</div>
        <div class="card-value">TOKENS / $</div>
        <div class="card-number">{{ formatNumber(efficiencyData.averageRatio ? efficiencyData.bestValuePerDollar * 0.85 : 0) }} t/$</div>
        <div class="card-glow-bar">
          <div
            class="glow-fill"
            :style="{ width: '75%' }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Per-model breakdown -->
    <div v-if="efficiencyData.modelsEfficiency && efficiencyData.modelsEfficiency.length" class="models-breakdown">
      <div class="breakdown-title">各模型效率对比</div>
      <div class="breakdown-list">
        <div
          v-for="(m, i) in efficiencyData.modelsEfficiency"
          :key="i"
          class="breakdown-row"
          :class="{ 'row-best': m.model === efficiencyData.bestValueModel }"
        >
          <span class="bd-model">{{ m.model }}</span>
          <div class="bd-bar-track">
            <div
              class="bd-bar"
              :class="{ 'bd-bar-best': m.model === efficiencyData.bestValueModel }"
              :style="{ width: getBarWidth(m.perDollar, maxPerDollar) + '%' }"
            ></div>
          </div>
          <span class="bd-value">{{ formatNumber(m.perDollar) }} t/$</span>
          <span class="bd-ratio">{{ formatNumber(m.ratio) }}x</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  efficiencyData: {
    type: Object,
    default: () => ({
      averageRatio: 0,
      bestValueModel: '',
      bestValuePerDollar: 0,
      modelsEfficiency: []
    })
  }
})

const maxRatio = computed(() => {
  if (!props.efficiencyData.modelsEfficiency?.length) return 5
  return Math.max(...props.efficiencyData.modelsEfficiency.map(m => m.ratio), 5)
})

const maxPerDollar = computed(() => {
  if (!props.efficiencyData.modelsEfficiency?.length) return 10000
  return Math.max(...props.efficiencyData.modelsEfficiency.map(m => m.perDollar), 10000)
})

function formatNumber(n) {
  if (!n || typeof n !== 'number') return '0'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n.toFixed(2)
}

function getBarWidth(value, max) {
  if (!max) return 0
  return Math.min((value / max) * 100, 100)
}
</script>

<style scoped>
.token-efficiency-cards {
  background: rgba(12, 18, 40, 0.7);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 4px;
  padding: 20px;
  font-family: 'Share Tech Mono', monospace;
}

.efficiency-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 16px;
}

.eff-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  color: #00f5ff;
  letter-spacing: 2px;
}

.eff-subtitle {
  font-size: 11px;
  color: rgba(0, 245, 255, 0.5);
  letter-spacing: 1px;
}

.cards-row {
  display: flex;
  gap: 16px;
}

.eff-card {
  flex: 1;
  background: rgba(8, 14, 36, 0.8);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 4px;
  padding: 16px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.eff-card:hover {
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.3), 0 0 40px rgba(0, 245, 255, 0.1);
  border-color: rgba(0, 245, 255, 0.5);
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

.card-corner-br {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 12px;
  height: 12px;
  border-bottom: 2px solid #00f5ff;
  border-right: 2px solid #00f5ff;
}

/* Hologram scan line */
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

.hologram-gold {
  background: linear-gradient(
    transparent 0%,
    rgba(255, 215, 0, 0.05) 50%,
    transparent 100%
  );
}

@keyframes holoScan {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}

.card-icon {
  font-size: 24px;
  color: rgba(0, 245, 255, 0.7);
  margin-bottom: 8px;
}

.card-icon.trophy {
  color: #ffd700;
  animation: trophyGlow 2s ease-in-out infinite;
}

@keyframes trophyGlow {
  0%, 100% { text-shadow: 0 0 4px rgba(255, 215, 0, 0.3); }
  50% { text-shadow: 0 0 12px rgba(255, 215, 0, 0.8); }
}

.card-label {
  font-size: 11px;
  color: rgba(0, 245, 255, 0.6);
  margin-bottom: 4px;
}

.card-value {
  font-size: 10px;
  color: rgba(0, 245, 255, 0.4);
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.card-number {
  font-family: 'Orbitron', sans-serif;
  font-size: 20px;
  color: #00f5ff;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.card-number-gold {
  color: #ffd700;
}

.card-meta {
  font-size: 12px;
  color: rgba(255, 215, 0, 0.7);
  margin-bottom: 8px;
}

/* Glow bar */
.card-glow-bar {
  height: 4px;
  background: rgba(0, 245, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.bar-gold {
  background: rgba(255, 215, 0, 0.1);
}

.glow-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(0, 245, 255, 0.6), rgba(0, 255, 136, 0.8));
  border-radius: 2px;
  transition: width 0.6s ease;
  box-shadow: 0 0 6px rgba(0, 245, 255, 0.4);
}

.fill-gold {
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.6), rgba(255, 215, 0, 0.9));
  box-shadow: 0 0 6px rgba(255, 215, 0, 0.4);
}

/* Best card special */
.card-best {
  border-color: rgba(255, 215, 0, 0.3);
}

.card-best:hover {
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.3), 0 0 40px rgba(255, 215, 0, 0.1);
  border-color: rgba(255, 215, 0, 0.5);
}

.card-best .card-corner-tl {
  border-top-color: #ffd700;
  border-left-color: #ffd700;
}

.card-best .card-corner-br {
  border-bottom-color: #ffd700;
  border-right-color: #ffd700;
}

/* Models breakdown */
.models-breakdown {
  margin-top: 16px;
  border-top: 1px solid rgba(0, 245, 255, 0.15);
  padding-top: 12px;
}

.breakdown-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 12px;
  color: rgba(0, 245, 255, 0.7);
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.breakdown-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.breakdown-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 2px;
  transition: all 0.2s ease;
}

.breakdown-row:hover {
  background: rgba(0, 245, 255, 0.05);
}

.row-best {
  background: rgba(255, 215, 0, 0.08);
}

.bd-model {
  font-size: 12px;
  color: rgba(0, 245, 255, 0.8);
  min-width: 120px;
}

.bd-bar-track {
  flex: 1;
  height: 3px;
  background: rgba(0, 245, 255, 0.08);
  border-radius: 1px;
  overflow: hidden;
}

.bd-bar {
  height: 100%;
  background: linear-gradient(90deg, rgba(0, 245, 255, 0.4), rgba(0, 255, 136, 0.6));
  border-radius: 1px;
  transition: width 0.4s ease;
}

.bd-bar-best {
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.4), rgba(255, 215, 0, 0.8));
}

.bd-value {
  font-size: 12px;
  color: rgba(0, 245, 255, 0.7);
  min-width: 70px;
}

.bd-ratio {
  font-size: 12px;
  color: rgba(0, 255, 136, 0.6);
  min-width: 50px;
}

.row-best .bd-model {
  color: #ffd700;
}
</style>