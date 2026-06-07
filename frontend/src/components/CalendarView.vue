<template>
  <div class="calendar-area">
    <!-- ====== WEEK VIEW ====== -->
    <div v-if="viewType === 'week'" class="cal-week-view card">
      <div class="cal-header">
        <span class="cal-title">{{ weekRangeLabel }}</span>
      </div>
      <div v-if="weekData.length === 0" class="cal-empty">{{ t('analytics.noData') }}</div>
      <div v-else class="cal-table-wrapper">
        <table class="cal-table">
          <thead>
            <tr>
              <th class="row-header th-dev">{{ t('analytics.developer') }}</th>
              <th v-for="day in weekDays" :key="day.date" class="col-header">
                <div class="day-name">{{ day.name }}</div>
                <div class="day-date">{{ day.dateShort }}</div>
              </th>
              <th class="col-header total-col">{{ t('calendar.total') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="author in weekData" :key="author.email"
              @click="toggleExpandAuthor(author.email)"
              class="author-row"
              :class="{ expanded: expandedAuthor === author.email }"
            >
              <td class="row-header cell-author">
                <div class="author-label">
                  <span class="author-name">{{ author.author }}</span>
                  <span v-if="author.isMe" class="me-badge">{{ t('dashboard.me') }}</span>
                </div>
                <div class="author-email">{{ author.email }}</div>
              </td>
              <td v-for="day in weekDays" :key="day.date"
                class="data-cell"
                :class="{ 'has-data': !!author.days[day.date] }"
                :style="{ backgroundColor: cellBg(author.days[day.date]?.commits || 0, maxCommits) }"
              >
                <div class="cell-commits">{{ author.days[day.date]?.commits ?? '-' }}</div>
                <div v-if="author.days[day.date]" class="cell-changes">
                  <span class="add">+{{ author.days[day.date].additions }}</span>
                  <span class="del">-{{ author.days[day.date].deletions }}</span>
                </div>
              </td>
              <td class="data-cell total-cell">
                <div class="cell-commits">{{ author.total.commits }}</div>
                <div class="cell-changes">
                  <span class="add">+{{ author.total.additions }}</span>
                  <span class="del">-{{ author.total.deletions }}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ====== MONTH VIEW ====== -->
    <div v-if="viewType === 'month'" class="cal-month-view card">
      <div class="cal-header">
        <span class="cal-title">{{ monthYearLabel }}</span>
      </div>
      <div v-if="monthGrid.length === 0" class="cal-empty">{{ t('analytics.noData') }}</div>
      <template v-else>
        <div class="cal-grid-wrapper">
          <table class="cal-grid">
            <thead>
              <tr>
                <th v-for="d in dayNames" :key="d" class="grid-day-header"
                  :class="{ 'weekend-header': d === dayNames[5] || d === dayNames[6] }">{{ d }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(week, wi) in monthGrid" :key="wi">
                <td v-for="(cell, ci) in week" :key="ci"
                  class="cal-cell"
                  :class="{
                    'is-today': cell?.isToday,
                    'has-data': !!cell?.data,
                    'weekend-cell': ci >= 5
                  }"
                  :style="cell ? { backgroundColor: cellBg(cell.data?.commits || 0, monthMaxCommits) } : {}"
                  @click="cell && selectDate(cell)"
                >
                  <div v-if="cell" class="cell-inner">
                    <div class="cell-day" :class="{ 'today-text': cell.isToday }">{{ cell.day }}</div>
                    <div v-if="cell.data" class="cell-count">{{ cell.data.commits }}</div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="selectedCell" class="detail-panel expand-panel">
          <div class="detail-hero">
            <div class="hero-date">{{ formattedDate }}</div>
            <div class="hero-stats">
              <div class="hero-commits">
                <span class="hero-number">{{ selectedCell.data?.commits || 0 }}</span>
                <span class="hero-label">{{ t('calendar.commitsUnit') }}</span>
              </div>
              <div v-if="selectedCell.data" class="hero-changes">
                <span class="hero-add">+{{ selectedCell.data.additions }}</span>
                <span class="hero-del">-{{ selectedCell.data.deletions }}</span>
                <span class="hero-net" :class="netChange >= 0 ? 'pos' : 'neg'">
                  {{ netChange >= 0 ? '+' : '' }}{{ netChange }}
                </span>
              </div>
            </div>
          </div>
          <div class="detail-divider"></div>
          <table v-if="dateDetail && dateDetail.length > 0" class="detail-table">
            <thead>
              <tr>
                <th>{{ t('analytics.repoName') }}</th>
                <th>{{ t('analytics.developer') }}</th>
                <th class="num-col">{{ t('dashboard.commits') }}</th>
                <th class="num-col">{{ t('analytics.additions') }}</th>
                <th class="num-col">{{ t('analytics.deletions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in dateDetail" :key="idx" :style="{ animationDelay: idx * 0.04 + 's' }">
                <td class="cell-repo">{{ item.repoName }}</td>
                <td class="cell-author">{{ item.author }}</td>
                <td class="num-col">{{ item.commits }}</td>
                <td class="num-col cell-additions">+{{ item.additions }}</td>
                <td class="num-col cell-deletions">-{{ item.deletions }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="detail-empty">
            <span class="empty-icon">⌧</span>
            {{ t('calendar.noDetail') }}
          </div>
        </div>
      </template>
    </div>

    <!-- ====== YEAR VIEW ====== -->
    <div v-if="viewType === 'year'" class="cal-year-view card">
      <div class="cal-header">
        <span class="cal-title">{{ yearLabel }}</span>
      </div>
      <div v-if="yearData.length === 0" class="cal-empty">{{ t('analytics.noData') }}</div>
      <div v-else class="year-grid">
        <div v-for="month in yearData" :key="month.month"
          class="year-month-card"
          :class="{ 'future-month': month.isFuture, 'selected': selectedMonth?.key === month.key }"
          :style="{ '--bg-alpha': month.commits ? (0.05 + Math.min(month.commits / yearMaxCommits, 1) * 0.55).toFixed(2) : '0' }"
          @click="!month.isFuture && (selectedMonth = selectedMonth?.key === month.key ? null : month)"
        >
          <div class="ym-header">{{ month.name }}</div>
          <div class="ym-commits">{{ month.commits }}</div>
          <div class="ym-changes">
            <span class="ym-add">+{{ month.additions }}</span>
            <span class="ym-del">-{{ month.deletions }}</span>
            <span class="ym-net">{{ (month.additions || 0) - (month.deletions || 0) >= 0 ? '+' : '' }}{{ (month.additions || 0) - (month.deletions || 0) }}</span>
          </div>
        </div>
      </div>
      <div v-if="selectedMonth" class="detail-panel expand-panel">
        <div class="detail-hero">
          <div class="hero-date">{{ selectedMonth.name }} {{ startDate?.slice(0, 4) }}</div>
          <div class="hero-stats">
            <div class="hero-commits">
              <span class="hero-number">{{ selectedMonth.commits }}</span>
              <span class="hero-label">{{ t('calendar.commitsUnit') }}</span>
            </div>
            <div class="hero-changes">
              <span class="hero-add">+{{ selectedMonth.additions }}</span>
              <span class="hero-del">-{{ selectedMonth.deletions }}</span>
              <span class="hero-net" :class="(selectedMonth.additions - selectedMonth.deletions) >= 0 ? 'pos' : 'neg'">
                {{ (selectedMonth.additions - selectedMonth.deletions) >= 0 ? '+' : '' }}{{ selectedMonth.additions - selectedMonth.deletions }}
              </span>
            </div>
          </div>
        </div>
        <div class="detail-divider"></div>
        <table v-if="monthDetail.length > 0" class="detail-table">
          <thead>
            <tr>
              <th>{{ t('analytics.repoName') }}</th>
              <th>{{ t('analytics.developer') }}</th>
              <th class="num-col">{{ t('dashboard.commits') }}</th>
              <th class="num-col">{{ t('analytics.additions') }}</th>
              <th class="num-col">{{ t('analytics.deletions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in monthDetail" :key="idx" :style="{ animationDelay: idx * 0.04 + 's' }">
              <td class="cell-repo">{{ item.repoName }}</td>
              <td class="cell-author">{{ item.author }}</td>
              <td class="num-col">{{ item.commits }}</td>
              <td class="num-col cell-additions">+{{ item.additions }}</td>
              <td class="num-col cell-deletions">-{{ item.deletions }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="detail-empty">
          <span class="empty-icon">⌧</span>
          {{ t('calendar.noDetail') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from '../i18n'

const props = defineProps({
  viewType: { type: String, required: true },
  dailyStats: { type: Array, default: () => [] },
  periodStats: { type: Array, default: () => [] },
  startDate: { type: String, default: '' },
  endDate: { type: String, default: '' }
})

const { t, locale } = useI18n()

const expandedAuthor = ref(null)
const selectedCell = ref(null)
const selectedMonth = ref(null)

function toggleExpandAuthor(email) {
  expandedAuthor.value = expandedAuthor.value === email ? null : email
}

// ====== Helpers ======

const dayNames = computed(() => {
  return locale.value === 'zh'
    ? ['一', '二', '三', '四', '五', '六', '日']
    : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
})

const monthNames = computed(() => {
  if (locale.value === 'zh') {
    return ['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月']
  }
  return ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
})

function pad(n) {
  return String(n).padStart(2, '0')
}

function cellBg(commits, maxC) {
  if (!commits || !maxC) return 'transparent'
  const intensity = Math.min(commits / maxC, 1)
  const alpha = 0.05 + intensity * 0.55
  return `rgba(160, 100, 200, ${alpha.toFixed(2)})`
}

function isToday(dateStr) {
  const d = new Date()
  const today = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`
  return dateStr === today
}

// ====== WEEK VIEW ======

const weekDays = computed(() => {
  if (!props.startDate) return []
  const start = new Date(props.startDate + 'T00:00:00')
  const dow = start.getDay() || 7
  const monday = new Date(start)
  monday.setDate(start.getDate() - dow + 1)
  const days = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    const y = d.getFullYear()
    const mo = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const dateStr = `${y}-${mo}-${day}`
    const name = dayNames.value[i]
    const dateShort = `${d.getMonth()+1}/${d.getDate()}`
    days.push({ date: dateStr, name, dateShort })
  }
  return days
})

const weekRangeLabel = computed(() => {
  if (weekDays.value.length === 0) return ''
  const first = weekDays.value[0]
  const last = weekDays.value[weekDays.value.length - 1]
  return `${first.date} ~ ${last.date}`
})

const weekData = computed(() => {
  const authorMap = new Map()
  const daySet = new Set(weekDays.value.map(d => d.date))

  for (const repo of props.dailyStats) {
    for (const author of repo.authors) {
      if (!authorMap.has(author.email)) {
        authorMap.set(author.email, {
          author: author.author,
          email: author.email,
          isMe: author.isMe,
          days: {},
          total: { commits: 0, additions: 0, deletions: 0 }
        })
      }
      const entry = authorMap.get(author.email)
      for (const day of author.dailyData) {
        if (daySet.has(day.date)) {
          if (!entry.days[day.date]) {
            entry.days[day.date] = { commits: 0, additions: 0, deletions: 0 }
          }
          entry.days[day.date].commits += day.commits
          entry.days[day.date].additions += day.additions
          entry.days[day.date].deletions += day.deletions
          entry.total.commits += day.commits
          entry.total.additions += day.additions
          entry.total.deletions += day.deletions
        }
      }
    }
  }
  return Array.from(authorMap.values()).sort((a, b) => b.total.commits - a.total.commits)
})

const maxCommits = computed(() => {
  let m = 0
  for (const author of weekData.value) {
    for (const day of Object.values(author.days)) {
      if (day.commits > m) m = day.commits
    }
  }
  return m
})

// ====== MONTH VIEW ======

const monthYearLabel = computed(() => {
  if (!props.startDate) return ''
  const d = new Date(props.startDate + 'T00:00:00')
  const y = d.getFullYear()
  const m = d.getMonth() + 1
  return locale.value === 'zh' ? `${y}年${m}月` : `${monthNames.value[m-1]} ${y}`
})

const monthGrid = computed(() => {
  if (!props.startDate) return []
  const d = new Date(props.startDate + 'T00:00:00')
  const year = d.getFullYear()
  const month = d.getMonth()

  // Build date→data map
  const dateMap = new Map()
  for (const repo of props.dailyStats) {
    for (const author of repo.authors) {
      for (const day of author.dailyData) {
        if (!dateMap.has(day.date)) {
          dateMap.set(day.date, { commits: 0, additions: 0, deletions: 0 })
        }
        const data = dateMap.get(day.date)
        data.commits += day.commits
        data.additions += day.additions
        data.deletions += day.deletions
      }
    }
  }

  const firstDay = new Date(year, month, 1)
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  let startCol = firstDay.getDay() - 1
  if (startCol < 0) startCol = 6

  const grid = []
  let week = []
  for (let i = 0; i < startCol; i++) week.push(null)
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${pad(month+1)}-${pad(day)}`
    const data = dateMap.get(dateStr) || null
    week.push({ day, dateStr, data, isToday: isToday(dateStr) })
    if (week.length === 7) {
      grid.push(week)
      week = []
    }
  }
  if (week.length > 0) {
    while (week.length < 7) week.push(null)
    grid.push(week)
  }
  return grid
})

const monthMaxCommits = computed(() => {
  let m = 0
  for (const week of monthGrid.value) {
    for (const cell of week) {
      if (cell?.data?.commits > m) m = cell.data.commits
    }
  }
  return m
})

function selectDate(cell) {
  selectedCell.value = selectedCell.value?.dateStr === cell.dateStr ? null : cell
}

const dateDetail = computed(() => {
  if (!selectedCell.value) return null
  const dateStr = selectedCell.value.dateStr
  const items = []
  for (const repo of props.dailyStats) {
    for (const author of repo.authors) {
      for (const day of author.dailyData) {
        if (day.date === dateStr && day.commits > 0) {
          items.push({
            repoName: repo.repoName,
            author: author.author,
            commits: day.commits,
            additions: day.additions,
            deletions: day.deletions
          })
        }
      }
    }
  }
  return items.sort((a, b) => b.commits - a.commits)
})

// ====== Detail Helpers ======

const formattedDate = computed(() => {
  if (!selectedCell.value) return ''
  const d = new Date(selectedCell.value.dateStr + 'T00:00:00')
  if (locale.value === 'zh') {
    const wd = ['日', '一', '二', '三', '四', '五', '六']
    return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日 周${wd[d.getDay()]}`
  }
  const ms = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  const wd = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
  return `${wd[d.getDay()]}, ${ms[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`
})

const netChange = computed(() => {
  if (!selectedCell.value?.data) return 0
  return selectedCell.value.data.additions - selectedCell.value.data.deletions
})

// ====== YEAR VIEW ======

const yearLabel = computed(() => {
  if (!props.startDate) return ''
  return props.startDate.slice(0, 4) + (locale.value === 'zh' ? '年' : '')
})

const yearData = computed(() => {
  if (!props.startDate) return []
  const year = parseInt(props.startDate.slice(0, 4))
  const now = new Date()
  const currentMonth = now.getMonth() + 1
  const currentYear = now.getFullYear()

  const monthMap = new Map()
  for (let m = 1; m <= 12; m++) {
    const key = `${year}-${pad(m)}`
    monthMap.set(key, { month: m, key, commits: 0, additions: 0, deletions: 0 })
  }

  for (const repo of props.periodStats) {
    for (const author of repo.authors) {
      for (const period of author.dailyData) {
        if (monthMap.has(period.date)) {
          const data = monthMap.get(period.date)
          data.commits += period.commits
          data.additions += period.additions
          data.deletions += period.deletions
        }
      }
    }
  }

  let maxC = 0
  const result = []
  for (let m = 1; m <= 12; m++) {
    const key = `${year}-${pad(m)}`
    const data = monthMap.get(key)
    data.isFuture = (year > currentYear) || (year === currentYear && m > currentMonth)
    data.name = monthNames.value[m - 1]
    if (data.commits > maxC) maxC = data.commits
    result.push(data)
  }

  result.forEach(d => d.maxCommits = maxC)
  return result
})

const yearMaxCommits = computed(() => {
  let m = 0
  for (const month of yearData.value) {
    if (month.commits > m) m = month.commits
  }
  return m
})

const monthDetail = computed(() => {
  if (!selectedMonth.value) return []
  const key = selectedMonth.value.key
  const items = []
  for (const repo of props.periodStats) {
    for (const author of repo.authors) {
      for (const period of author.dailyData) {
        if (period.date === key && period.commits > 0) {
          items.push({
            repoName: repo.repoName,
            author: author.author,
            commits: period.commits,
            additions: period.additions,
            deletions: period.deletions
          })
        }
      }
    }
  }
  return items.sort((a, b) => b.commits - a.commits)
})
</script>

<style scoped>
.calendar-area {
  animation: slideDown 0.3s ease;
}

.cal-week-view.card,
.cal-month-view.card,
.cal-year-view.card {
  position: relative;
}
.cal-week-view.card::after,
.cal-month-view.card::after,
.cal-year-view.card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 12%;
  right: 12%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00f5ff, #ff00ff, transparent);
  border-radius: 2px;
  opacity: 0.45;
  pointer-events: none;
}

/* ====== Shared Header ====== */
.cal-header {
  margin-bottom: 1.25rem;
}
.cal-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1rem;
  color: #00f5ff;
  letter-spacing: 2px;
}

.cal-empty {
  text-align: center;
  padding: 3rem 0;
  color: #64748b;
  font-size: 0.95rem;
  letter-spacing: 1px;
}

/* ====== Week View Table ====== */
.cal-table-wrapper {
  overflow-x: auto;
}
.cal-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.9rem;
}
.cal-table thead th {
  text-align: center;
  padding: 0.5rem 0.4rem;
  border-bottom: 1px solid rgba(160, 100, 200, 0.15);
  vertical-align: bottom;
}
.cal-table .row-header {
  text-align: center;
  padding: 0.5rem 0.3rem;
  min-width: 64px;
  color: #64748b;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.75rem;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.col-header {
  min-width: 64px;
}
.day-name {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.72rem;
  color: #00f5ff;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.day-date {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 2px;
}
.total-col {
  min-width: 80px;
}
.total-col .day-name {
  color: #ffd700;
}

/* table body */
.data-cell {
  text-align: center;
  padding: 0.6rem 0.3rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.08);
  transition: all 0.2s ease;
  cursor: default;
}
.data-cell.has-data {
  cursor: pointer;
}
.data-cell:hover {
  filter: brightness(1.3);
  border-color: rgba(160, 100, 200, 0.3);
}
.cell-commits {
  font-size: 1.05rem;
  font-weight: 700;
  color: #e2e8f0;
}
.cell-changes {
  font-size: 0.65rem;
  margin-top: 2px;
  display: flex;
  gap: 4px;
  justify-content: center;
}
.cell-changes .add { color: #00ff88; }
.cell-changes .del { color: #ff6b6b; }

.total-cell {
  border-left: 1px solid rgba(160, 100, 200, 0.25);
}
.total-cell .cell-commits {
  color: #ffd700;
  font-size: 1.15rem;
}

.author-row {
  cursor: pointer;
  transition: background 0.2s;
}
.author-row:hover {
  background: rgba(160, 100, 200, 0.05);
}
.author-row.expanded {
  background: rgba(160, 100, 200, 0.08);
}
.cell-author {
  text-align: center;
  padding: 0.35rem 0.15rem !important;
  line-height: 1.2;
}
.author-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
}
.author-name {
  font-family: 'Rajdhani', sans-serif;
  color: #00f5ff;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: none;
  letter-spacing: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.author-email {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.6rem;
  color: #64748b;
  text-transform: none !important;
  letter-spacing: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
  margin-top: 1px;
}
.me-badge {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.6rem;
  padding: 1px 5px;
  border: 1px solid #ffd700;
  border-radius: 3px;
  color: #ffd700;
  letter-spacing: 0.5px;
}

/* ====== Month View Grid ====== */
.cal-grid-wrapper {
  overflow-x: auto;
}
.cal-grid {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
.cal-grid thead th {
  text-align: center;
  padding: 0.5rem 0.3rem;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.75rem;
  color: #94a3b8;
  letter-spacing: 1px;
  text-transform: uppercase;
  border-bottom: 1px solid rgba(160, 100, 200, 0.15);
}
.weekend-header {
  color: #64748b;
  opacity: 0.6;
}

.cal-cell {
  position: relative;
  text-align: center;
  vertical-align: top;
  padding: 4px;
  border: 1px solid rgba(148, 163, 184, 0.06);
  transition: all 0.2s ease;
  cursor: default;
  height: 72px;
  width: 14.28%;
}
.cal-cell.has-data {
  cursor: pointer;
}
.cal-cell:hover {
  border-color: rgba(160, 100, 200, 0.4);
  filter: brightness(1.25);
  z-index: 1;
}
.weekend-cell {
  background: rgba(148, 163, 184, 0.03);
}

.cell-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 2px;
}
.cell-day {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  color: #94a3b8;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}
.cell-day.today-text {
  background: rgba(160, 100, 200, 0.8);
  color: #0a0e27;
  font-weight: 700;
  box-shadow: 0 0 12px rgba(160, 100, 200, 0.5);
}
.cell-count {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.85rem;
  font-weight: 700;
  color: #e2e8f0;
  line-height: 1;
}

/* detail panel */
.detail-panel {
  margin-top: 1rem;
  animation: slideDown 0.25s ease;
  text-align: center;
}

.detail-hero {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  padding: 0.25rem 0;
}

.hero-date {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.3rem;
  font-weight: 700;
  background: linear-gradient(135deg, #e2e8f0, #a064c8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 1px;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.hero-commits {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.hero-number {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #00f5ff;
}

.hero-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.8rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.hero-changes {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.9rem;
}

.hero-add { color: #00ff88; }
.hero-del { color: #ff6b6b; }

.hero-net {
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.7rem;
  font-weight: 600;
}
.hero-net.pos {
  background: rgba(0, 255, 136, 0.1);
  color: #00ff88;
  border: 1px solid rgba(0, 255, 136, 0.2);
}
.hero-net.neg {
  background: rgba(255, 107, 107, 0.1);
  color: #ff6b6b;
  border: 1px solid rgba(255, 107, 107, 0.2);
}

.detail-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(160, 100, 200, 0.3), transparent);
  margin: 0.75rem 0;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.85rem;
}

.detail-table th {
  padding: 0.4rem 0.6rem;
  color: #64748b;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.65rem;
  letter-spacing: 1px;
  text-transform: uppercase;
  border-bottom: 1px solid rgba(160, 100, 200, 0.15);
}

.detail-table th.num-col,
.detail-table td.num-col {
  text-align: right;
}

.detail-table td {
  padding: 0.4rem 0.6rem;
  color: #e2e8f0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.06);
}

.detail-table tbody tr {
  animation: rowFadeIn 0.3s ease both;
}

.detail-table tbody tr:hover {
  background: rgba(160, 100, 200, 0.05);
}

.detail-table .cell-repo {
  color: #94a3b8;
}

.detail-table .cell-author {
  color: #00f5ff;
  font-weight: 600;
}

.detail-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #64748b;
  font-size: 0.85rem;
  padding: 1.5rem 0;
  font-family: 'Rajdhani', sans-serif;
}

.detail-empty .empty-icon {
  font-size: 1.1rem;
  opacity: 0.4;
}

@keyframes rowFadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ====== Year View Grid ====== */
.year-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}
.year-month-card {
  position: relative;
  background: rgba(10, 14, 39, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 12px;
  padding: 1.25rem 1rem;
  text-align: center;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.year-month-card:hover:not(.future-month) {
  border-color: rgba(0, 245, 255, 0.5);
  box-shadow: 0 8px 32px rgba(0, 245, 255, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transform: translateY(-3px);
}
.year-month-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 15%;
  right: 15%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00f5ff, #ff00ff, transparent);
  border-radius: 2px;
  opacity: 0.4;
  transition: all 0.4s ease;
  pointer-events: none;
}
.year-month-card:hover::before {
  left: 5%;
  right: 5%;
  opacity: 0.8;
}
.year-month-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(160, 100, 200, calc(var(--bg-alpha, 0)));
  pointer-events: none;
  transition: opacity 0.3s ease;
}
.year-month-card.selected {
  border-color: #00f5ff;
  box-shadow: 0 0 25px rgba(0, 245, 255, 0.3), inset 0 0 20px rgba(0, 245, 255, 0.05);
}
.year-month-card.selected::before {
  left: 5%;
  right: 5%;
  opacity: 1;
}
.year-month-card.future-month {
  opacity: 0.3;
  cursor: not-allowed;
  filter: grayscale(0.5);
}
.ym-header {
  position: relative;
  z-index: 1;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.7rem;
  font-weight: 500;
  color: #94a3b8;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 0.35rem;
}
.ym-commits {
  position: relative;
  z-index: 1;
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #e2e8f0;
  line-height: 1.15;
  margin-bottom: 0.4rem;
}
.ym-changes {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.65rem;
  font-weight: 600;
}
.ym-changes .ym-add { color: #00ff88; }
.ym-changes .ym-del { color: #ff6b6b; }
.ym-changes .ym-net { color: #64748b; }

/* responsive */
@media (max-width: 900px) {
  .year-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
@media (max-width: 600px) {
  .year-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .cal-table .row-header {
    min-width: 50px;
    font-size: 0.6rem;
  }
  .th-dev {
    min-width: 65px;
  }
  .col-header {
    min-width: 44px;
  }
  .cell-author {
    padding: 0.2rem 0.2rem !important;
    max-width: 45px;
  }
  .author-name {
    font-size: 0.65rem;
    max-width: 38px;
  }
  .author-email {
    font-size: 0.45rem;
    max-width: 38px;
  }
  .cal-cell {
    height: 60px;
    padding: 2px;
  }
  .cell-day {
    width: 22px;
    height: 22px;
    font-size: 0.75rem;
  }
  .cell-count {
    font-size: 0.7rem;
  }
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
