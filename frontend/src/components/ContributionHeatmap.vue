<template>
  <div class="contribution-heatmap card">
    <div class="corner-tl"></div>
    <div class="corner-br"></div>

    <div class="heatmap-header">
      <div class="heatmap-title-row">
        <span class="total-count">{{ totalContributions }}</span>
        <span class="total-label">{{ totalLabelText }}</span>
      </div>
      <span class="heatmap-subtitle">{{ t('contribution.subtitle') }}</span>
    </div>

    <div v-if="loading" class="heatmap-loading">{{ t('contribution.loading') }}</div>
    <div v-else-if="!cells.length" class="heatmap-empty">{{ t('contribution.noData') }}</div>

    <template v-else>
      <div class="heatmap-scroll">
        <div class="month-row">
          <span
            v-for="m in monthLabels"
            :key="m.key"
            class="month-label"
            :style="{ left: m.left + 'px' }"
          >{{ m.label }}</span>
        </div>

        <div class="grid-wrap">
          <div class="weekday-labels">
            <span>{{ t('contribution.mon') }}</span>
            <span>{{ t('contribution.wed') }}</span>
            <span>{{ t('contribution.fri') }}</span>
          </div>

          <div class="week-columns">
            <div v-for="(week, wi) in weekColumns" :key="wi" class="week-column">
              <div
                v-for="(day, di) in week"
                :key="di"
                class="heatmap-cell"
                :class="{
                  'cell-empty': !day,
                  'cell-today': day?.isToday,
                  [`cell-level-${day ? day.level : 0}`]: day
                }"
                :style="{ backgroundColor: day ? cellColor(day.level) : 'transparent' }"
                @mouseenter="onCellEnter(day, $event)"
                @mouseleave="hoveredDay = null"
              >
                <div v-if="day?.isToday" class="pulse-border"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="hoveredDay?.date"
        class="heatmap-tooltip"
        :style="tooltipStyle"
      >
        <div class="tooltip-date">{{ formatTooltipDate(hoveredDay.date) }}</div>
        <div class="tooltip-commits">
          {{ hoveredDay.commits }} {{ t('contribution.commitsUnit') }}
        </div>
      </div>

      <div class="heatmap-legend">
        <span class="legend-label">{{ t('contribution.less') }}</span>
        <div
          v-for="level in 5"
          :key="level"
          class="legend-cell"
          :style="{ backgroundColor: cellColor(level - 1) }"
        ></div>
        <span class="legend-label">{{ t('contribution.more') }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from '../i18n'
import * as api from '../api'

const { t, locale } = useI18n()

const loading = ref(true)
const cells = ref([])
const totalContributions = ref(0)
const calendarDays = ref(365)
const hoveredDay = ref(null)
const tooltipStyle = ref({})

const totalLabelText = computed(() => {
  if (locale.value === 'zh') {
    return `次提交 · 最近 ${calendarDays.value} 天`
  }
  return `contributions in the last ${calendarDays.value} days`
})

const levelColors = [
  'rgba(30, 40, 55, 0.55)',
  'rgba(0, 245, 255, 0.22)',
  'rgba(0, 255, 136, 0.38)',
  'rgba(0, 255, 136, 0.62)',
  'rgba(255, 0, 255, 0.72)',
]

function cellColor(level) {
  return levelColors[level] || levelColors[0]
}

function commitLevel(commits) {
  if (!commits) return 0
  if (commits === 1) return 1
  if (commits <= 3) return 2
  if (commits <= 6) return 3
  return 4
}

const cellSize = 13
const cellGap = 3
const weekWidth = cellSize + cellGap

const weekColumns = computed(() => {
  if (!cells.value.length) return []

  const byDate = Object.fromEntries(cells.value.map(c => [c.date, c]))
  const first = new Date(cells.value[0].date)
  const last = new Date(cells.value[cells.value.length - 1].date)

  const gridStart = new Date(first)
  const mondayOffset = (gridStart.getDay() + 6) % 7
  gridStart.setDate(gridStart.getDate() - mondayOffset)

  const weeks = []
  const cur = new Date(gridStart)
  while (cur <= last || weeks.length === 0) {
    const week = []
    for (let i = 0; i < 7; i++) {
      const ds = formatDateLocal(cur)
      const inRange = cur >= first && cur <= last
      if (inRange && byDate[ds]) {
        const item = byDate[ds]
        week.push({ ...item, level: commitLevel(item.commits) })
      } else {
        week.push(null)
      }
      cur.setDate(cur.getDate() + 1)
    }
    weeks.push(week)
    if (cur > last && cur.getDay() === 1) break
  }
  return weeks
})

const monthLabels = computed(() => {
  if (!cells.value.length) return []
  const months = locale.value === 'zh'
    ? ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

  const labels = []
  let lastMonth = -1
  weekColumns.value.forEach((week, wi) => {
    const day = week.find(d => d?.date)
    if (!day) return
    const m = new Date(day.date).getMonth()
    if (m !== lastMonth) {
      labels.push({ key: `${m}-${wi}`, label: months[m], left: wi * weekWidth })
      lastMonth = m
    }
  })
  return labels
})

function formatDateLocal(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function onCellEnter(day, event) {
  hoveredDay.value = day
  if (event?.target) {
    const rect = event.target.getBoundingClientRect()
    tooltipStyle.value = {
      left: `${rect.left + rect.width / 2}px`,
      top: `${rect.top}px`,
    }
  }
}

function formatTooltipDate(dateStr) {
  const d = new Date(dateStr + 'T12:00:00')
  if (locale.value === 'zh') {
    return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
  }
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

async function loadCalendar() {
  loading.value = true
  try {
    const data = await api.getContributionCalendar()
    cells.value = data.cells || []
    totalContributions.value = data.totalContributions || 0
    calendarDays.value = data.days || 365
  } catch (e) {
    console.error('Failed to load contribution calendar:', e)
    cells.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadCalendar)
</script>

<style scoped>
.contribution-heatmap {
  position: relative;
  padding: 1.25rem 1.25rem 1rem 2.5rem;
  margin-bottom: 1.25rem;
  overflow: hidden;
}

.corner-tl, .corner-br {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 1px solid rgba(0, 245, 255, 0.45);
  pointer-events: none;
}
.corner-tl { top: 8px; left: 8px; border-right: none; border-bottom: none; }
.corner-br { bottom: 8px; right: 8px; border-left: none; border-top: none; }

.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.heatmap-title-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.total-count {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.35rem;
  color: #00ff88;
  text-shadow: 0 0 12px rgba(0, 255, 136, 0.45);
}

.total-label {
  font-size: 0.85rem;
  color: var(--text-secondary, rgba(200, 220, 255, 0.75));
}

.heatmap-subtitle {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.7rem;
  color: rgba(0, 245, 255, 0.45);
  letter-spacing: 0.08em;
}

.heatmap-loading,
.heatmap-empty {
  padding: 2rem;
  text-align: center;
  color: var(--text-secondary, rgba(200, 220, 255, 0.6));
  font-size: 0.9rem;
}

.heatmap-scroll {
  overflow-x: auto;
  padding-bottom: 0.25rem;
}

.month-row {
  position: relative;
  height: 18px;
  margin-left: 0;
  margin-bottom: 4px;
}

.month-label {
  position: absolute;
  top: 0;
  font-size: 10px;
  color: rgba(0, 245, 255, 0.55);
  white-space: nowrap;
}

.grid-wrap {
  display: flex;
  align-items: flex-start;
  position: relative;
}

.weekday-labels {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: calc(7 * 13px + 6 * 3px);
  margin-right: 8px;
  margin-top: 2px;
  font-size: 10px;
  color: rgba(0, 245, 255, 0.45);
  line-height: 1;
  position: absolute;
  left: -28px;
  top: 0;
}
.weekday-labels span:nth-child(2) { margin-top: 14px; }
.weekday-labels span:nth-child(3) { margin-top: 14px; }

.week-columns {
  display: flex;
  gap: 3px;
}

.week-column {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.heatmap-cell {
  width: 13px;
  height: 13px;
  border-radius: 2px;
  position: relative;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  border: 1px solid rgba(0, 245, 255, 0.06);
}

.heatmap-cell:hover:not(.cell-empty) {
  transform: scale(1.35);
  z-index: 5;
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.55);
}

.cell-empty {
  cursor: default;
  border-color: transparent;
}

.cell-today {
  outline: 1px solid rgba(0, 245, 255, 0.8);
}

.pulse-border {
  position: absolute;
  inset: -2px;
  border: 1px solid #00f5ff;
  border-radius: 3px;
  animation: cellPulse 1.8s ease-in-out infinite;
  pointer-events: none;
}

@keyframes cellPulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 4px rgba(0, 245, 255, 0.35); }
  50% { opacity: 0.35; box-shadow: 0 0 10px rgba(0, 245, 255, 0.75); }
}

.heatmap-tooltip {
  position: fixed;
  background: rgba(8, 14, 32, 0.96);
  border: 1px solid rgba(0, 255, 136, 0.35);
  border-radius: 4px;
  padding: 8px 12px;
  z-index: 200;
  pointer-events: none;
  box-shadow: 0 0 16px rgba(0, 255, 136, 0.2);
  transform: translate(-50%, -120%);
}

.tooltip-date {
  font-size: 11px;
  color: rgba(0, 245, 255, 0.65);
  margin-bottom: 4px;
}

.tooltip-commits {
  font-family: 'Orbitron', sans-serif;
  font-size: 13px;
  color: #00ff88;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  margin-top: 12px;
}

.legend-label {
  font-size: 10px;
  color: rgba(0, 245, 255, 0.45);
}

.legend-cell {
  width: 13px;
  height: 13px;
  border-radius: 2px;
  border: 1px solid rgba(0, 245, 255, 0.08);
}
</style>
