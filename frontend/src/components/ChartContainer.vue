<template>
  <div class="chart-container card">
    <div class="chart-header">
      <div class="title-section">
        <h3>{{ title }}</h3>
        <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
      </div>
      <div class="header-accent"></div>
    </div>
    <div v-show="loading" class="chart-loading">
      <div class="loading-spinner"></div>
      <p>{{ $t ? $t('analytics.loading', 'LOADING') : 'LOADING' }}...</p>
    </div>
    <div v-show="!loading" ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import echarts from '../utils/echarts'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  option: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})

const chartRef = ref(null)
let chartInstance = null

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  if (!props.loading && chartRef.value) {
    await nextTick()
    if (!chartInstance) {
      chartInstance = echarts.init(chartRef.value)
    }
    if (props.option) {
      chartInstance.setOption(props.option, true)
      chartInstance.resize()
    }
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})

watch(() => props.loading, async (newVal) => {
  if (!newVal && chartRef.value) {
    await nextTick()
    if (!chartInstance) {
      chartInstance = echarts.init(chartRef.value)
    }
    if (props.option) {
      chartInstance.setOption(props.option, true)
      chartInstance.resize()
    }
  }
})

watch(() => props.option, (newVal) => {
  if (newVal && chartInstance) {
    chartInstance.setOption(newVal, true)
    nextTick(() => {
      chartInstance?.resize()
    })
  }
})

function handleResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}
</script>

<style scoped>
.chart-container {
  margin-bottom: 2rem;
  position: relative;
}

.chart-header {
  position: relative;
  margin-bottom: 1.5rem;
}

.title-section {
  display: flex;
  align-items: baseline;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.chart-header h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.3rem;
  color: var(--neon-cyan);
  letter-spacing: 2px;
  text-transform: uppercase;
  margin: 0;
  text-shadow: 0 0 10px var(--neon-cyan), 0 0 20px rgba(0, 245, 255, 0.3);
}

.header-accent {
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-magenta));
  box-shadow: 0 0 8px var(--neon-cyan), 0 0 16px var(--neon-magenta);
}

.subtitle {
  font-size: 0.85rem;
  color: #64748b;
  letter-spacing: 1px;
  margin: 0;
  font-family: 'Share Tech Mono', monospace;
}

.chart-loading {
  height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: #64748b;
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 2px;
  font-size: 0.8rem;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 2px solid rgba(0, 245, 255, 0.08);
  border-top-color: var(--neon-cyan);
  border-right-color: var(--neon-magenta);
  border-radius: 50%;
  animation: cyberspin 1s linear infinite;
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.3), 0 0 40px rgba(255, 0, 255, 0.15);
}

@keyframes cyberspin {
  to { transform: rotate(360deg); }
}

.chart {
  height: 400px;
  width: 100%;
}
</style>
