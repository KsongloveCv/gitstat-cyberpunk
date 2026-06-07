<template>
  <div class="analytics">
    <div class="header-section">
      <div class="title-row">
        <div>
          <h2 class="page-title">数据分析中心</h2>
          <p class="subtitle">实时监控 · 多维度洞察</p>
        </div>
        <AnalyticsControls
          :repositories="repositories"
          :selectedRepos="selectedRepos"
          :selectedTimeRange="selectedTimeRange"
          :showCustomPicker="showCustomPicker"
          :customStartDate="customStartDate"
          :customEndDate="customEndDate"
          :loading="loading"
          @update:selectedRepos="selectedRepos = $event"
          @update:selectedTimeRange="selectedTimeRange = $event"
          @update:showCustomPicker="showCustomPicker = $event"
          @update:customStartDate="customStartDate = $event"
          @update:customEndDate="customEndDate = $event"
          @analyze="loadData"
        />
      </div>
      <div class="view-toggle-bar">
        <div class="view-toggle-inner">
          <button
            @click="viewMode = 'chart'"
            class="view-toggle-btn"
            :class="{ active: viewMode === 'chart' }"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toggle-icon">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
            <span>{{ t('calendar.chartView') }}</span>
          </button>
          <button
            @click="viewMode = 'calendar'"
            class="view-toggle-btn"
            :class="{ active: viewMode === 'calendar' }"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="toggle-icon">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            <span>{{ t('calendar.calendarView') }}</span>
          </button>
        </div>
      </div>
    </div>

    <OverviewCards
      :overviewStats="overviewStats"
      :loadedTimeRange="loadedTimeRange"
      :expandedSection="expandedSection"
      :customStartDate="customStartDate"
      :customEndDate="customEndDate"
      @toggle-section="toggleSection"
    />

    <AnalyticsPanels
      :expandedSection="expandedSection"
      :overviewStats="overviewStats"
      :loadedTimeRange="loadedTimeRange"
      :repoComparison="repoComparison"
      :authorRank="authorRank"
      @toggle-section="toggleSection"
    />

    <AnalyticsCharts
      v-if="viewMode === 'chart'"
      :loading="loading"
      :dailyStats="dailyStats"
      :periodStats="periodStats"
      :currentGranularity="currentGranularity"
      :selectedRepos="selectedRepos"
      :authorRank="authorRank"
      :activityHeatmap="activityHeatmap"
      :repoComparison="repoComparison"
    />

    <CalendarView
      v-else
      :viewType="calendarViewType"
      :dailyStats="dailyStats"
      :periodStats="periodStats"
      :startDate="currentStartDate"
      :endDate="currentEndDate"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { getDailyStats, getWeeklyStats, getMonthlyStats, getYearlyStats, getRepositories, getOverviewStats, getAuthorRank, getActivityHeatmap, getRepoComparison } from '../api'
import AnalyticsControls from '../components/AnalyticsControls.vue'
import OverviewCards from '../components/OverviewCards.vue'
import AnalyticsPanels from '../components/AnalyticsPanels.vue'
import AnalyticsCharts from '../components/AnalyticsCharts.vue'
import CalendarView from '../components/CalendarView.vue'
import { useI18n } from '../i18n'

const { t } = useI18n()
const loading = ref(false)
const overviewStats = ref(null)
const selectedTimeRange = ref('week')
const customStartDate = ref('')
const customEndDate = ref('')
const showCustomPicker = ref(false)
const selectedRepos = ref([])
const repositories = ref([])
const dailyStats = ref([])
const periodStats = ref([])
const currentGranularity = ref('day')
const authorRank = ref([])
const activityHeatmap = ref([])
const repoComparison = ref([])
const expandedSection = ref(null)
const viewMode = ref('chart')
const currentStartDate = ref('')
const currentEndDate = ref('')
const loadedTimeRange = ref('')

function toLocalDateStr(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const toggleSection = (section) => {
  expandedSection.value = expandedSection.value === section ? null : section
}

const calendarViewType = computed(() => {
  if (!currentStartDate.value || !currentEndDate.value) return 'week'
  if (selectedTimeRange.value === 'year') return 'year'
  if (selectedTimeRange.value === 'month' || selectedTimeRange.value === 'lastMonth') return 'month'
  if (selectedTimeRange.value === 'week' || selectedTimeRange.value === 'lastWeek' || selectedTimeRange.value === 'today') return 'week'
  const days = Math.round((new Date(currentEndDate.value) - new Date(currentStartDate.value)) / (1000 * 60 * 60 * 24))
  if (days <= 7) return 'week'
  if (days <= 31) return 'month'
  return 'year'
})

watch(viewMode, (newMode) => {
  if (!currentStartDate.value || loading.value) return
  if (newMode === 'calendar' && currentGranularity.value !== 'day') {
    loadData()
  }
})

const loadData = async () => {
  if (selectedRepos.value.length === 0) return

  loading.value = true
  try {
    let startDate, endDate
    const now = new Date()

    switch (selectedTimeRange.value) {
      case 'today':
        startDate = toLocalDateStr(now)
        endDate = toLocalDateStr(now)
        break
      case 'week':
        const currentDay = now.getDay() || 7
        const monday = new Date(now)
        monday.setDate(now.getDate() - currentDay + 1)
        startDate = toLocalDateStr(monday)
        endDate = toLocalDateStr(now)
        break
      case 'lastWeek':
        const lastWeekMonday = new Date(now)
        lastWeekMonday.setDate(now.getDate() - (now.getDay() || 7) - 6)
        const lastWeekSunday = new Date(lastWeekMonday)
        lastWeekSunday.setDate(lastWeekMonday.getDate() + 6)
        startDate = toLocalDateStr(lastWeekMonday)
        endDate = toLocalDateStr(lastWeekSunday)
        break
      case 'month':
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
        startDate = toLocalDateStr(firstDay)
        endDate = toLocalDateStr(now)
        break
      case 'lastMonth':
        const firstDayLast = new Date(now.getFullYear(), now.getMonth() - 1, 1)
        const lastDayLast = new Date(now.getFullYear(), now.getMonth(), 0)
        startDate = toLocalDateStr(firstDayLast)
        endDate = toLocalDateStr(lastDayLast)
        break
      case 'year':
        const firstDayOfYear = new Date(now.getFullYear(), 0, 1)
        startDate = toLocalDateStr(firstDayOfYear)
        endDate = toLocalDateStr(now)
        break
      case 'custom':
        startDate = customStartDate.value
        endDate = customEndDate.value
        break
      default:
        startDate = null
        endDate = null
    }

    currentStartDate.value = startDate
    currentEndDate.value = endDate

    let granularity = 'day'
    let statsPromise
    const tr = selectedTimeRange.value

    if (tr === 'today' || tr === 'week' || tr === 'lastWeek') {
      granularity = 'day'
      statsPromise = getDailyStats(null, tr === 'custom' ? '' : tr, selectedRepos.value, startDate, endDate)
    } else if (tr === 'month' || tr === 'lastMonth') {
      if (viewMode.value === 'calendar') {
        granularity = 'day'
        statsPromise = getDailyStats(null, tr, selectedRepos.value, startDate, endDate)
      } else {
        granularity = 'week'
        statsPromise = getWeeklyStats(null, tr, selectedRepos.value, startDate, endDate)
      }
    } else if (tr === 'year') {
      granularity = 'month'
      statsPromise = getMonthlyStats(null, tr, selectedRepos.value, startDate, endDate)
    } else {
      const days = Math.round((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24))
      if (days <= 31) {
        granularity = 'day'
        statsPromise = getDailyStats(null, '', selectedRepos.value, startDate, endDate)
      } else if (days <= 180 && viewMode.value !== 'calendar') {
        granularity = 'week'
        statsPromise = getWeeklyStats(null, '', selectedRepos.value, startDate, endDate)
      } else {
        granularity = 'month'
        statsPromise = getMonthlyStats(null, '', selectedRepos.value, startDate, endDate)
      }
    }
    currentGranularity.value = granularity

    const [overview, stats, authors, heatmap, comparison] = await Promise.all([
      getOverviewStats(startDate, endDate, selectedRepos.value),
      statsPromise,
      getAuthorRank(selectedRepos.value, startDate, endDate),
      getActivityHeatmap(selectedRepos.value, startDate, endDate),
      getRepoComparison(selectedRepos.value, startDate, endDate)
    ])
    overviewStats.value = overview

    if (granularity === 'day') {
      dailyStats.value = stats || []
      periodStats.value = []
    } else {
      periodStats.value = stats || []
      dailyStats.value = []
    }
    authorRank.value = authors || []
    activityHeatmap.value = heatmap || []
    repoComparison.value = comparison || []

    await nextTick()
    loadedTimeRange.value = selectedTimeRange.value
    loading.value = false
  } catch (error) {
    console.error('Failed to load analytics data:', error)
    loading.value = false
  }
}

onMounted(async () => {
  try {
    repositories.value = await getRepositories()
  } catch (error) {
    console.error('加载仓库失败:', error)
  }
})
</script>

<style scoped>
.analytics {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

.header-section {
  margin-bottom: 1.5rem;
  position: relative;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.page-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #00f5ff 0%, #ff00ff 50%, #ffd700 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin: 0 0 0.25rem 0;
  filter: drop-shadow(0 0 15px rgba(0, 245, 255, 0.3));
}

.subtitle {
  font-size: 0.85rem;
  color: #64748b;
  letter-spacing: 4px;
  text-transform: uppercase;
  margin: 0;
}

.view-toggle-bar {
  text-align: center;
  margin-top: 0.75rem;
}

.view-toggle-inner {
  display: inline-flex;
  background: rgba(10, 14, 39, 0.6);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 8px;
  padding: 3px;
  gap: 2px;
}

.view-toggle-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0.5rem 1.2rem;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #64748b;
  font-size: 0.8rem;
  font-family: 'Orbitron', sans-serif;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
}

.view-toggle-btn:hover {
  color: #94a3b8;
}

.view-toggle-btn.active {
  background: rgba(0, 245, 255, 0.15);
  color: #00f5ff;
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
}

.toggle-icon {
  width: 16px;
  height: 16px;
}

@media (max-width: 1200px) {
  .title-row {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 768px) {
  .analytics {
    padding: 1rem;
  }

  .page-title {
    font-size: 1.5rem;
  }
}
</style>
