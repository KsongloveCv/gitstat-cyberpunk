<template>
  <div>
    <!-- 活跃作者展开面板 -->
    <div v-if="expandedSection === 'authors' && overviewStats?.authors" class="expand-panel">
      <div class="expand-panel-header">{{ timePeriodPrefix }}活跃作者 · 共 {{ overviewStats.authors.length }} 人</div>
      <table class="expand-table">
        <thead>
          <tr>
            <th>作者</th>
            <th>提交数</th>
            <th>新增</th>
            <th>删除</th>
            <th>净变更</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="author in overviewStats.authors" :key="author.email">
            <td class="cell-author">{{ author.author }}</td>
            <td>{{ author.commits }}</td>
            <td class="cell-additions">+{{ author.additions }}</td>
            <td class="cell-deletions">-{{ author.deletions }}</td>
            <td :class="author.netChange >= 0 ? 'cell-additions' : 'cell-deletions'">{{ author.netChange >= 0 ? '+' : '' }}{{ author.netChange }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 洞察卡片 -->
    <div v-if="insights.length > 0" class="insights-grid">
      <div
        v-for="(insight, idx) in insights"
        :key="idx"
        class="insight-card"
        :class="{ clickable: insight.clickable, expanded: insight.clickable && expandedSection === insight.section }"
        @click="insight.clickable && emit('toggle-section', insight.section)"
      >
        <div class="insight-icon" v-html="insight.iconSvg"></div>
        <div class="insight-content">
          <div class="insight-title">{{ insight.title }}</div>
          <div class="insight-value">{{ insight.value }}</div>
          <div class="insight-desc">{{ insight.description }}</div>
        </div>
      </div>
    </div>

    <!-- 活跃仓库展开面板 -->
    <div v-if="expandedSection === 'repos' && repoComparison.length > 0" class="expand-panel">
      <div class="expand-panel-header">{{ timePeriodPrefix }}活跃仓库 · 共 {{ repoComparison.filter(r => r.commits > 0).length }} 个</div>
      <table class="expand-table">
        <thead>
          <tr>
            <th>仓库名</th>
            <th>提交数</th>
            <th>作者数</th>
            <th>新增行数</th>
            <th>活跃天数</th>
            <th>日均提交</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="repo in repoComparison" :key="repo.repoPath">
            <td class="cell-author">{{ repo.repoName }}</td>
            <td>{{ repo.commits }}</td>
            <td>{{ repo.authors }}</td>
            <td class="cell-additions">+{{ repo.additions }}</td>
            <td>{{ repo.activeDays }}</td>
            <td>{{ repo.avgCommitsPerDay }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../i18n'

const { t } = useI18n()

const props = defineProps({
  expandedSection: String,
  overviewStats: Object,
  loadedTimeRange: String,
  repoComparison: Array,
  authorRank: Array
})

defineEmits(['toggle-section'])

const timePeriodPrefix = computed(() => {
  switch (props.loadedTimeRange) {
    case 'week': return t('analytics.thisWeek')
    case 'lastWeek': return t('analytics.lastWeek')
    case 'month': return t('analytics.thisMonth')
    case 'lastMonth': return t('analytics.lastMonth')
    case 'year': return t('analytics.thisYear')
    case 'custom': return t('analytics.customPeriod')
    default: return ''
  }
})

const insights = computed(() => {
  const result = []
  const prefix = timePeriodPrefix.value

  if (props.authorRank && props.authorRank.length > 0) {
    const topAuthor = props.authorRank[0]
    result.push({
      iconSvg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
      title: `${prefix}之星`,
      value: topAuthor.author,
      description: `${topAuthor.commits} 次提交 · ${topAuthor.additions} 行新增`
    })
  }

  if (props.overviewStats && props.overviewStats.totalCommits > 0) {
    const avgSize = Math.round((props.overviewStats.totalAdditions + props.overviewStats.totalDeletions) / props.overviewStats.totalCommits)
    result.push({
      iconSvg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>`,
      title: '平均提交规模',
      value: `${avgSize} 行`,
      description: `${prefix}每次提交平均变更 ${avgSize} 行`
    })
  }

  if (props.overviewStats) {
    const netChange = props.overviewStats.totalAdditions - props.overviewStats.totalDeletions
    result.push({
      iconSvg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>`,
      title: '代码净增长',
      value: `${netChange > 0 ? '+' : ''}${netChange}`,
      description: `${prefix}代码净增 ${netChange} 行`
    })
  }

  if (props.repoComparison && props.repoComparison.length > 0) {
    const activeRepos = props.repoComparison.filter(r => r.commits > 0).length
    result.push({
      iconSvg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`,
      title: '活跃仓库',
      value: `${activeRepos} 个`,
      description: `${prefix}${activeRepos} 个仓库有提交活动`,
      clickable: true,
      section: 'repos'
    })
  }

  return result
})
</script>

<style scoped>
.expand-panel {
  background: rgba(10, 14, 39, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  padding: 1.25rem;
  margin-top: 1rem;
  animation: slideDown 0.25s ease;
  overflow-x: auto;
}

.expand-panel-header {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.8rem;
  color: #00f5ff;
  letter-spacing: 1px;
  margin-bottom: 1rem;
  opacity: 0.9;
}

.expand-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.9rem;
}

.expand-table th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  color: #64748b;
  font-weight: 600;
  font-size: 0.8rem;
  letter-spacing: 1px;
  text-transform: uppercase;
  border-bottom: 1px solid rgba(0, 245, 255, 0.15);
}

.expand-table td {
  padding: 0.5rem 0.75rem;
  color: #e2e8f0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.expand-table tbody tr:hover {
  background: rgba(0, 245, 255, 0.05);
}

.expand-table .cell-author {
  color: #00f5ff;
  font-weight: 600;
}

.expand-table .cell-additions {
  color: #00ff88;
}

.expand-table .cell-deletions {
  color: #ff6b6b;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.insight-card {
  background: rgba(10, 14, 39, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s;
  min-height: 100px;
}

.insight-card:hover {
  border-color: rgba(0, 212, 255, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 212, 255, 0.15);
}

.insight-card.clickable {
  cursor: pointer;
}

.insight-card.clickable:hover {
  border-color: rgba(0, 212, 255, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 212, 255, 0.15);
}

.insight-card.clickable.expanded {
  border-color: #00f5ff;
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.3), inset 0 0 20px rgba(0, 245, 255, 0.05);
}

.insight-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00f5ff;
  filter: drop-shadow(0 0 6px rgba(0, 245, 255, 0.4));
}

.insight-icon svg {
  width: 24px;
  height: 24px;
}

.insight-content {
  flex: 1;
}

.insight-title {
  font-size: 0.85rem;
  color: #64748b;
  letter-spacing: 1px;
  margin-bottom: 0.25rem;
}

.insight-value {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #00d4ff, #7800ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.25rem;
}

.insight-desc {
  font-size: 0.8rem;
  color: #94a3b8;
}
</style>
