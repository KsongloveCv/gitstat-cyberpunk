<template>
  <div class="token-heatmap-calendar">
    <div class="heatmap-header">
      <span class="heatmap-title">Token 消耗日历</span>
      <span class="heatmap-subtitle">TOKEN HEATMAP · 365 DAYS</span>
    </div>

    <div class="heatmap-grid">
      <!-- Month labels -->
      <div class="month-labels">
        <span
          v-for="m in monthLabels"
          :key="m.label"
          class="month-label"
          :style="{ marginLeft: m.offset + 'px' }"
        >{{ m.label }}</span>
      </div>

      <!-- Day grid -->
      <div class="heatmap-rows">
        <div
          v-for="(week, wi) in weeks"
          :key="wi"
          class="heatmap-week"
        >
          <div
            v-for="(day, di) in week"
            :key="di"
            class="heatmap-cell"
            :class="{
              'cell-empty': !day,
              'cell-today': day && day.isToday,
              [`cell-level-${day ? day.level : 0}`]: day
            }"
            :style="{ backgroundColor: day ? getCellColor(day.level) : 'transparent' }"
            @mouseenter="hoveredDay = day"
            @mouseleave="hoveredDay = null"
          >
            <!-- Today pulse border -->
            <div v-if="day && day.isToday" class="pulse-border"></div>
          </div>
        </div>
      </div>

      <!-- Week day labels -->
      <div class="weekday-labels">
        <span>Mon</span>
        <span>Wed</span>
        <span>Fri</span>
      </div>
    </div>

    <!-- Hover tooltip -->
    <div
      v-if="hoveredDay && hoveredDay.date"
      class="heatmap-tooltip"
    >
      <div class="tooltip-date">{{ hoveredDay.date }}</div>
      <div class="tooltip-tokens">{{ hoveredDay.tokens }} tokens</div>
    </div>

    <!-- Color legend -->
    <div class="heatmap-legend">
      <span class="legend-label">少</span>
      <div class="legend-cell" style="backgroundColor: getCellColor(0)"></div>
      <div class="legend-cell" style="backgroundColor: getCellColor(1)"></div>
      <div class="legend-cell" style="backgroundColor: getCellColor(2)"></div>
      <div class="legend-cell" style="backgroundColor: getCellColor(3)"></div>
      <div class="legend-cell" style="backgroundColor: getCellColor(4)"></div>
      <span class="legend-label">多</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  heatmapData: {
    type: Array,
    default: () => []
  }
})

const hoveredDay = ref(null)

// Color mapping: 0=dark → 1=cyan → 2=green → 3=gold → 4=magenta
const levelColors = {
  0: 'rgba(20, 30, 50, 0.4)',
  1: 'rgba(0, 245, 255, 0.3)',
  2: 'rgba(0, 255, 136, 0.45)',
  3: 'rgba(255, 215, 0, 0.55)',
  4: 'rgba(255, 0, 255, 0.65)'
}

function getCellColor(level) {
  return levelColors[level] || levelColors[0]
}

// Compute token level from value
function getTokenLevel(tokens) {
  if (!tokens || tokens === 0) return 0
  if (tokens < 5000) return 1
  if (tokens < 20000) return 2
  if (tokens < 50000) return 3
  return 4
}

// Organize data into weeks (7 days per row, 52-53 weeks)
const weeks = computed(() => {
  if (!props.heatmapData.length) return []

  // Sort by date
  const sorted = [...props.heatmapData].sort((a, b) =>
    new Date(a.date) - new Date(b.date)
  )

  // Find first day's weekday offset (0=Sun, 1=Mon...6=Sat)
  const firstDate = new Date(sorted[0].date)
  const firstDayOfWeek = firstDate.getDay()
  // We want Mon=0, so shift
  const offset = (firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1)

  // Build week structure
  const allDays = []
  // Fill empty cells before first day
  for (let i = 0; i < offset; i++) {
    allDays.push(null)
  }
  // Fill actual days
  for (const d of sorted) {
    allDays.push({
      ...d,
      level: getTokenLevel(d.tokens)
    })
  }

  // Split into weeks of 7
  const result = []
  for (let i = 0; i < allDays.length; i += 7) {
    result.push(allDays.slice(i, i + 7))
  }
  return result
})

// Month labels positioned along the grid
const monthLabels = computed(() => {
  if (!props.heatmapData.length) return []

  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
  const labels = []
  const seenMonths = new Set()
  const cellSize = 14
  const gap = 3

  for (const d of props.heatmapData) {
    const date = new Date(d.date)
    const month = date.getMonth()
    if (!seenMonths.has(month)) {
      seenMonths.add(month)
      // Calculate week index for this month
      const weekIdx = Math.floor(seenMonths.size - 1)
      labels.push({
        label: months[month],
        offset: weekIdx * (cellSize + gap)
      })
    }
  }
  return labels
})
</script>

<style scoped>
.token-heatmap-calendar {
  background: rgba(12, 18, 40, 0.7);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 4px;
  padding: 20px;
  position: relative;
  font-family: 'Share Tech Mono', monospace;
}

.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 16px;
}

.heatmap-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  color: #00f5ff;
  letter-spacing: 2px;
}

.heatmap-subtitle {
  font-size: 11px;
  color: rgba(0, 245, 255, 0.5);
  letter-spacing: 1px;
}

.heatmap-grid {
  overflow-x: auto;
  position: relative;
}

.month-labels {
  display: flex;
  margin-bottom: 4px;
  height: 16px;
  position: relative;
}

.month-label {
  font-size: 10px;
  color: rgba(0, 245, 255, 0.6);
  position: absolute;
}

.heatmap-rows {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.heatmap-week {
  display: flex;
  gap: 3px;
}

.heatmap-cell {
  width: 14px;
  height: 14px;
  border-radius: 2px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
}

.heatmap-cell:hover {
  transform: scale(1.4);
  z-index: 10;
  box-shadow: 0 0 8px rgba(0, 245, 255, 0.6);
}

.cell-empty {
  cursor: default;
  opacity: 0;
}

.cell-empty:hover {
  transform: none;
  box-shadow: none;
}

.cell-today {
  border: 1px solid #00f5ff;
}

/* Pulse animation for today */
.pulse-border {
  position: absolute;
  inset: -2px;
  border: 2px solid #00f5ff;
  border-radius: 4px;
  animation: cellPulse 1.5s ease-in-out infinite;
  pointer-events: none;
}

@keyframes cellPulse {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 4px rgba(0, 245, 255, 0.4);
  }
  50% {
    opacity: 0.3;
    box-shadow: 0 0 12px rgba(0, 245, 255, 0.8);
  }
}

.weekday-labels {
  display: flex;
  flex-direction: column;
  gap: 17px;
  position: absolute;
  left: -32px;
  top: 22px;
  font-size: 10px;
  color: rgba(0, 245, 255, 0.5);
}

.heatmap-tooltip {
  position: fixed;
  background: rgba(12, 18, 40, 0.95);
  border: 1px solid rgba(0, 245, 255, 0.4);
  border-radius: 4px;
  padding: 8px 12px;
  z-index: 100;
  pointer-events: none;
  box-shadow: 0 0 12px rgba(0, 245, 255, 0.3);
}

.tooltip-date {
  font-size: 12px;
  color: rgba(0, 245, 255, 0.7);
  margin-bottom: 4px;
}

.tooltip-tokens {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  color: #00f5ff;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  justify-content: flex-end;
}

.legend-label {
  font-size: 10px;
  color: rgba(0, 245, 255, 0.5);
}

.legend-cell {
  width: 14px;
  height: 14px;
  border-radius: 2px;
  border: 1px solid rgba(0, 245, 255, 0.1);
}
</style>