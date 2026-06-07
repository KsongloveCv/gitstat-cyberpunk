<template>
  <div class="streak-section card" :style="streakStyle">
    <!-- 装饰角标 -->
    <div class="corner-tl"></div>
    <div class="corner-br"></div>
    <!-- 全息扫描线 -->
    <div class="hologram-scan"></div>

    <div class="streak-header">
      <h3>{{ t('streak.title') }} <span class="streak-badge">⚡</span></h3>
      <span class="streak-period">{{ weekRange }}</span>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="streak-loading">
      <div class="streak-loading-bar">
        <span class="streak-loading-dot"></span>
        <span class="streak-loading-dot"></span>
        <span class="streak-loading-dot"></span>
      </div>
      <span class="streak-loading-text">{{ t('streak.calculating') }}</span>
    </div>

    <!-- 无数据 -->
    <div v-else-if="!streakData" class="streak-empty">
      <span class="streak-empty-icon">◈</span>
      <span>{{ t('streak.noData') }}</span>
    </div>

    <!-- 有数据 -->
    <template v-else>
      <div class="streak-stats">
        <!-- 当前连续 -->
        <div class="streak-stat-item current-streak">
          <div class="streak-fire" :class="{ 'fire-active': streakData.current > 0 }">
            🔥
          </div>
          <div class="streak-stat-value" :data-text="String(streakData.current)">
            {{ streakData.current }}
          </div>
          <div class="streak-stat-label">{{ t('streak.currentStreak') }}</div>
          <div class="streak-stat-sub">{{ t('streak.days') }}</div>
        </div>
        <!-- 最长连续 -->
        <div class="streak-stat-item longest-streak">
          <div class="streak-medal">🏆</div>
          <div class="streak-stat-value" :data-text="String(streakData.longest)">
            {{ streakData.longest }}
          </div>
          <div class="streak-stat-label">{{ t('streak.longestStreak') }}</div>
          <div class="streak-stat-sub">{{ t('streak.days') }}</div>
        </div>
        <!-- 本周活跃天数 -->
        <div class="streak-stat-item weekly-active">
          <div class="streak-pulse">◆</div>
          <div class="streak-stat-value" :data-text="String(streakData.weeklyActiveDays)">
            {{ streakData.weeklyActiveDays }}/7
          </div>
          <div class="streak-stat-label">{{ t('streak.weeklyActive') }}</div>
          <div class="streak-stat-sub">{{ t('streak.days') }}</div>
        </div>
      </div>

      <!-- 连续天数可视化 - 贡献热力条 -->
      <div class="streak-heatmap">
        <div class="heatmap-label">{{ t('streak.last30Days') }}</div>
        <div class="heatmap-grid">
          <div
            v-for="(day, idx) in streakData.last30Days"
            :key="idx"
            class="heatmap-cell"
            :class="{ 'heatmap-active': day.commits > 0, 'heatmap-today': day.isToday }"
            :style="{ '--cell-color': getCellColor(day.commits), '--cell-opacity': getCellOpacity(day.commits) }"
            @mouseenter="hoveredDay = day"
            @mouseleave="hoveredDay = null"
          >
            <div class="heatmap-inner"></div>
          </div>
        </div>
        <!-- 悬浮提示 -->
        <div v-if="hoveredDay" class="heatmap-tooltip">
          <span class="tooltip-date">{{ hoveredDay.date }}</span>
          <span class="tooltip-commits">{{ hoveredDay.commits }} {{ t('streak.commits') }}</span>
        </div>
      </div>

      <!-- 连续贡献进度条 -->
      <div class="streak-progress" v-if="streakData.current > 0">
        <div class="progress-label">{{ t('streak.keepGoing') }}</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          <div class="progress-glow"></div>
        </div>
        <div class="progress-target">{{ streakData.longest }} {{ t('streak.days') }}</div>
      </div>
    </template>

    <!-- 底部发光条 -->
    <div class="streak-glow-bar"></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from '../i18n'
import { state } from '../stores/data'
import * as api from '../api'

const { t } = useI18n()
const streakData = ref(null)
const loading = ref(true)
const hoveredDay = ref(null)

// 获取本周日期范围文字
const weekRange = computed(() => {
  const now = new Date()
  const start = new Date(now)
  start.setDate(now.getDate() - now.getDay())
  const end = new Date(start)
  end.setDate(start.getDate() + 6)
  return `${start.getMonth()+1}/${start.getDate()} - ${end.getMonth()+1}/${end.getDate()}`
})

// 当前连续天数占比最长连续的进度
const progressPercent = computed(() => {
  if (!streakData.value || streakData.value.longest === 0) return 0
  return Math.min(100, (streakData.value.current / streakData.value.longest) * 100)
})

// 赛博朋克配色
const streakStyle = computed(() => ({
  '--accent': streakData.value?.current > 0 ? '#ff6b35' : '#00d4ff',
  '--accent-glow': streakData.value?.current > 0 ? '#ff6b3566' : '#00d4ff66'
}))

// 热力格子颜色映射
function getCellColor(commits) {
  if (commits === 0) return 'rgba(0, 245, 255, 0.06)'
  if (commits <= 2) return '#00f5ff'
  if (commits <= 5) return '#00ff88'
  if (commits <= 10) return '#ffd700'
  return '#ff6b35'
}

function getCellOpacity(commits) {
  if (commits === 0) return 0.1
  if (commits <= 2) return 0.4
  if (commits <= 5) return 0.6
  if (commits <= 10) return 0.8
  return 1
}

async function fetchStreak() {
  loading.value = true
  try {
    const data = await api.getStreakStats(['all'])
    streakData.value = data
  } catch (err) {
    console.error('Failed to fetch streak data:', err)
    streakData.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStreak()
})

// 当overviewStats变化时刷新（扫描新目录等）
watch(() => state.overviewStats, () => {
  if (state.overviewStats) fetchStreak()
})
</script>

<style scoped>
.streak-section {
  background: rgba(12, 18, 40, 0.7);
  backdrop-filter: blur(24px);
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid rgba(0, 245, 255, 0.2);
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.streak-section:hover {
  border-color: var(--accent);
  box-shadow: 0 0 40px var(--accent-glow), 0 0 80px var(--accent-glow);
}

/* 装饰角标 */
.corner-tl {
  position: absolute; top: 0; left: 0;
  width: 20px; height: 20px;
  border-top: 2px solid var(--accent);
  border-left: 2px solid var(--accent);
  border-radius: 12px 0 4px 0;
  opacity: 0.5; z-index: 2;
  box-shadow: 0 0 6px var(--accent);
  transition: all 0.3s;
}
.corner-br {
  position: absolute; bottom: 0; right: 0;
  width: 20px; height: 20px;
  border-bottom: 2px solid var(--accent);
  border-right: 2px solid var(--accent);
  border-radius: 0 4px 0 12px;
  opacity: 0.5; z-index: 2;
  box-shadow: 0 0 6px var(--accent);
  transition: all 0.3s;
}
.streak-section:hover .corner-tl,
.streak-section:hover .corner-br {
  opacity: 1;
  box-shadow: 0 0 12px var(--accent), 0 0 24px var(--accent-glow);
}

/* 全息扫描线 */
.hologram-scan {
  position: absolute; top: -100%; left: 0;
  width: 100%; height: 30%;
  background: linear-gradient(180deg, transparent, rgba(255,255,255,0.04), transparent);
  z-index: 1; animation: hologramScan 4s ease-in-out infinite;
  pointer-events: none;
}
@keyframes hologramScan { 0% { top: -30%; } 100% { top: 130%; } }

.streak-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 1rem;
}
.streak-header h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.9rem; letter-spacing: 2px;
  color: #e2e8f0;
}
.streak-badge {
  color: #ff6b35;
  filter: drop-shadow(0 0 6px #ff6b35);
  animation: badgePulse 2s ease-in-out infinite;
}
@keyframes badgePulse { 0%,100% { opacity: 1; } 50% { opacity: 0.7; } }

.streak-period {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.75rem; color: #94a3b8;
  letter-spacing: 1px;
}

/* 统计数字 */
.streak-stats {
  display: flex; gap: 1rem; justify-content: center;
  margin-bottom: 1rem;
}
.streak-stat-item {
  text-align: center; padding: 0.75rem;
  background: rgba(0, 245, 255, 0.05);
  border-radius: 10px; border: 1px solid rgba(0, 245, 255, 0.1);
  min-width: 100px; transition: all 0.3s;
}
.streak-stat-item:hover {
  border-color: var(--accent);
  box-shadow: 0 0 20px var(--accent-glow);
  transform: translateY(-2px);
}

.streak-fire, .streak-medal, .streak-pulse {
  font-size: 1.5rem; margin-bottom: 0.5rem;
  transition: all 0.3s;
}
.streak-fire.fire-active {
  filter: drop-shadow(0 0 12px #ff6b35) drop-shadow(0 0 24px #ff6b3566);
  animation: fireFlicker 1.5s ease-in-out infinite;
}
@keyframes fireFlicker { 0%,100% { transform: scale(1); } 50% { transform: scale(1.15); } }

.streak-medal { filter: drop-shadow(0 0 8px #ffd700); }
.streak-pulse { color: var(--accent); animation: pulseDot 2s ease-in-out infinite; }
@keyframes pulseDot { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }

.streak-stat-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 2rem; font-weight: 900;
  background: linear-gradient(180deg, var(--accent) 0%, #fff 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; transition: all 0.3s;
}
.streak-stat-item:hover .streak-stat-value {
  animation: valueGlitch 0.3s ease-in-out;
}
@keyframes valueGlitch {
  0% { transform: translate(0); }
  20% { transform: translate(-3px, 1px); }
  40% { transform: translate(3px, -1px); }
  60% { transform: translate(-2px, -1px); }
  80% { transform: translate(2px, 1px); }
  100% { transform: translate(0); }
}

.streak-stat-label {
  font-family: 'Share Tech Mono', monospace;
  color: #94a3b8; font-size: 0.7rem;
  letter-spacing: 1.5px; text-transform: uppercase;
}
.streak-stat-sub {
  font-family: 'Share Tech Mono', monospace;
  color: #64748b; font-size: 0.65rem;
}

/* 热力图 */
.streak-heatmap { margin-bottom: 0.75rem; }
.heatmap-label {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.7rem; color: #94a3b8;
  margin-bottom: 0.5rem; letter-spacing: 1px;
}
.heatmap-grid {
  display: flex; gap: 3px; flex-wrap: wrap;
  justify-content: center;
}
.heatmap-cell {
  width: 12px; height: 12px;
  border-radius: 2px; position: relative;
  transition: all 0.2s; cursor: pointer;
}
.heatmap-inner {
  width: 100%; height: 100%;
  border-radius: 2px;
  background: var(--cell-color);
  opacity: var(--cell-opacity);
  transition: all 0.2s;
}
.heatmap-cell:hover .heatmap-inner {
  opacity: 1;
  box-shadow: 0 0 6px var(--cell-color), 0 0 12px var(--cell-color);
  transform: scale(1.3);
}
.heatmap-cell.heatmap-today .heatmap-inner {
  border: 1px solid var(--accent);
  box-shadow: 0 0 8px var(--accent);
}
.heatmap-cell.heatmap-today::after {
  content: ''; position: absolute;
  inset: -2px; border-radius: 3px;
  border: 1px solid var(--accent);
  animation: todayPulse 2s ease-in-out infinite;
}
@keyframes todayPulse { 0%,100% { opacity: 0.3; } 50% { opacity: 0.8; } }

.heatmap-tooltip {
  position: absolute; bottom: 100%; left: 50%;
  transform: translateX(-50%); z-index: 10;
  background: rgba(8, 12, 32, 0.95);
  border: 1px solid var(--accent);
  border-radius: 6px; padding: 6px 10px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.7rem; color: #e2e8f0;
  display: flex; gap: 8px;
  box-shadow: 0 0 16px var(--accent-glow);
  pointer-events: none;
  white-space: nowrap;
}

/* 进度条 */
.streak-progress { margin-top: 0.75rem; }
.progress-label {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.7rem; color: #94a3b8;
  letter-spacing: 1px; margin-bottom: 0.5rem;
}
.progress-bar {
  height: 4px; background: rgba(0, 245, 255, 0.1);
  border-radius: 2px; position: relative; overflow: hidden;
}
.progress-fill {
  height: 100%; border-radius: 2px;
  background: linear-gradient(90deg, var(--accent), #ffd700);
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 10px var(--accent);
}
.progress-glow {
  position: absolute; top: 0; right: 0;
  width: 20px; height: 100%;
  background: radial-gradient(circle at right, var(--accent), transparent);
  opacity: 0.5; animation: progressGlow 2s ease-in-out infinite;
}
@keyframes progressGlow { 0%,100% { opacity: 0.3; } 50% { opacity: 0.8; } }

.progress-target {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.65rem; color: #64748b;
  margin-top: 0.25rem; text-align: right;
}

/* 底部发光条 */
.streak-glow-bar {
  position: absolute; bottom: 0; left: 50%;
  transform: translateX(-50%);
  width: 50%; height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  box-shadow: 0 0 10px var(--accent);
  transition: all 0.3s;
}
.streak-section:hover .streak-glow-bar {
  width: 80%;
  box-shadow: 0 0 16px var(--accent), 0 0 32px var(--accent-glow);
}

/* 加载状态 */
.streak-loading {
  display: flex; align-items: center; gap: 0.75rem;
  justify-content: center; padding: 2rem;
}
.streak-loading-bar { display: flex; gap: 4px; }
.streak-loading-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent);
  animation: loadingDot 1.4s ease-in-out infinite;
}
.streak-loading-dot:nth-child(2) { animation-delay: 0.2s; }
.streak-loading-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes loadingDot { 0%,100% { opacity: 0.2; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.2); } }
.streak-loading-text {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem; color: #94a3b8;
  letter-spacing: 1px;
}

/* 空状态 */
.streak-empty {
  display: flex; align-items: center; gap: 0.75rem;
  justify-content: center; padding: 2rem;
  color: #64748b;
}
.streak-empty-icon {
  color: var(--accent); opacity: 0.3;
  filter: drop-shadow(0 0 4px var(--accent-glow));
}

@media (max-width: 640px) {
  .streak-stats { flex-direction: column; }
  .streak-stat-item { min-width: auto; }
}
</style>