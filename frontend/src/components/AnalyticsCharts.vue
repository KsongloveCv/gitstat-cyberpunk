<template>
  <div class="charts-grid">
    <ChartContainer
      :title="commitTrendTitle"
      :subtitle="t('analytics.commitTrendSub')"
      :option="commitTrendOption"
      :loading="loading"
      class="chart-card primary"
    />
    <ChartContainer
      :title="codeChangeTitle"
      :subtitle="t('analytics.codeChangeSub')"
      :option="codeChangeOption"
      :loading="loading"
      class="chart-card secondary"
    />
    <ChartContainer
      title="开发者贡献榜"
      subtitle="Top 10 按提交数排序"
      :option="authorRankOption"
      :loading="loading"
      class="chart-card tertiary"
    />
    <ChartContainer
      title="提交时间热力图"
      subtitle="星期 × 小时维度"
      :option="heatmapOption"
      :loading="loading"
      class="chart-card quaternary"
    />
    <ChartContainer
      title="仓库活跃度对比"
      subtitle="多维度雷达分析"
      :option="repoComparisonOption"
      :loading="loading"
      class="chart-card quinary"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../i18n'
import echarts from '../utils/echarts'
import ChartContainer from './ChartContainer.vue'

const { t } = useI18n()

const props = defineProps({
  loading: Boolean,
  dailyStats: Array,
  periodStats: Array,
  currentGranularity: String,
  selectedRepos: Array,
  authorRank: Array,
  activityHeatmap: Array,
  repoComparison: Array
})

function formatPeriodLabel(period, granularity) {
  if (granularity === 'week') {
    const match = period.match(/-W(\d+)/)
    return match ? `第${match[1]}周` : period
  }
  if (granularity === 'month') {
    return period.slice(5) + '月'
  }
  if (granularity === 'year') {
    return period + '年'
  }
  return period
}

function adjustColor(color, amount) {
  const num = parseInt(color.replace('#', ''), 16)
  const r = Math.min(255, Math.max(0, (num >> 16) + amount))
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + amount))
  const b = Math.min(255, Math.max(0, (num & 0x0000FF) + amount))
  return `#${(0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1)}`
}

const activeStats = computed(() => {
  return props.currentGranularity === 'day' ? props.dailyStats : props.periodStats
})

const filteredStats = computed(() => {
  const source = activeStats.value
  return props.selectedRepos.length === 0
    ? source
    : source.filter(stat => props.selectedRepos.includes(stat.repoPath))
})

const processedStats = computed(() => {
  const data = filteredStats.value
  const dateSet = new Set()
  const authorMap = new Map()

  data.forEach(repo => {
    repo.authors?.forEach(author => {
      author.dailyData?.forEach(day => dateSet.add(day.date))
      if (!authorMap.has(author.email)) {
        authorMap.set(author.email, {
          name: author.author,
          email: author.email,
          isMe: author.isMe
        })
      }
    })
  })

  return {
    dates: Array.from(dateSet).sort(),
    authors: Array.from(authorMap.values())
  }
})

const granularityPrefix = computed(() => {
  switch (props.currentGranularity) {
    case 'week': return t('analytics.weekly')
    case 'month': return t('analytics.monthly')
    case 'year': return t('analytics.yearly')
    default: return t('analytics.daily')
  }
})

const commitTrendTitle = computed(() => granularityPrefix.value + t('analytics.commitTrend'))
const codeChangeTitle = computed(() => granularityPrefix.value + t('analytics.codeChange'))

const commitTrendOption = computed(() => {
  const { dates, authors } = processedStats.value

  if (dates.length === 0 || authors.length === 0) {
    return {
      title: {
        text: t('analytics.noData'),
        left: 'center',
        top: 'center',
        textStyle: { color: '#64748b', fontSize: 16 }
      }
    }
  }

  const colors = ['#00f5ff', '#ff00ff', '#ffd700', '#00ff88', '#ff6b6b', '#a78bfa']
  const series = authors.map((author, idx) => {
    const data = dates.map(date => {
      let commits = 0
      filteredStats.value.forEach(repo => {
        const authorStat = repo.authors?.find(a => a.email === author.email)
        if (authorStat && authorStat.dailyData) {
          const dayData = authorStat.dailyData.find(d => d.date === date)
          if (dayData) commits += dayData.commits
        }
      })
      return commits
    })

    return {
      name: author.name,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: {
        width: 3,
        color: colors[idx % colors.length]
      },
      itemStyle: {
        color: colors[idx % colors.length],
        borderWidth: 2,
        borderColor: '#fff'
      },
      areaStyle: {
        opacity: 0.1,
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: colors[idx % colors.length] },
          { offset: 1, color: 'rgba(0,0,0,0)' }
        ])
      },
      data
    }
  })

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 14, 39, 0.95)',
      borderColor: '#00f5ff',
      textStyle: { color: '#fff' },
      axisPointer: {
        type: 'cross',
        lineStyle: { color: '#00f5ff', opacity: 0.5 }
      }
    },
    legend: {
      data: authors.map(a => a.name),
      textStyle: { color: '#94a3b8' },
      top: 10
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: {
        color: '#94a3b8',
        formatter: (value) => formatPeriodLabel(value, props.currentGranularity)
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#94a3b8' },
      splitLine: {
        lineStyle: {
          color: '#1e293b',
          type: 'dashed'
        }
      }
    },
    series
  }
})

const codeChangeOption = computed(() => {
  const { dates, authors } = processedStats.value

  if (dates.length === 0 || authors.length === 0) {
    return {
      title: {
        text: t('analytics.noData'),
        left: 'center',
        top: 'center',
        textStyle: { color: '#64748b', fontSize: 16 }
      }
    }
  }

  const colors = ['#00f5ff', '#ff00ff', '#ffd700', '#00ff88', '#ff6b6b', '#a78bfa']
  const series = []

  authors.forEach((author, idx) => {
    const baseColor = colors[idx % colors.length]

    const netData = dates.map(date => {
      let additions = 0
      let deletions = 0
      filteredStats.value.forEach(repo => {
        const authorStat = repo.authors?.find(a => a.email === author.email)
        if (authorStat && authorStat.dailyData) {
          const dayData = authorStat.dailyData.find(d => d.date === date)
          if (dayData) {
            additions += dayData.additions
            deletions += dayData.deletions
          }
        }
      })
      return { additions, deletions }
    })

    series.push({
      name: author.name,
      type: 'bar',
      stack: 'total',
      barWidth: '40%',
      emphasis: { focus: 'series' },
      data: netData.map(item => item.additions),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: baseColor },
          { offset: 1, color: adjustColor(baseColor, -30) }
        ]),
        borderRadius: [4, 4, 0, 0]
      }
    })

    series.push({
      name: `${author.name} - 删除`,
      type: 'bar',
      stack: 'total',
      barWidth: '40%',
      emphasis: { focus: 'series' },
      data: netData.map(item => -item.deletions),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: adjustColor(baseColor, -60) },
          { offset: 1, color: adjustColor(baseColor, -90) }
        ]),
        borderRadius: [0, 0, 4, 4]
      }
    })
  })

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 14, 39, 0.95)',
      borderColor: '#00f5ff',
      textStyle: { color: '#fff' },
      axisPointer: {
        type: 'shadow',
        shadowStyle: { color: 'rgba(0, 245, 255, 0.1)' }
      },
      formatter: (params) => {
        let result = `<div style="font-weight:bold;margin-bottom:5px">${params[0].axisValue}</div>`
        params.forEach(param => {
          const value = Math.abs(param.value)
          const type = param.value >= 0 ? '新增' : '删除'
          result += `<div>${param.seriesName}: <span style="color:${param.color}">${value}</span> (${type})</div>`
        })
        return result
      }
    },
    legend: {
      data: series.map(s => s.name),
      textStyle: { color: '#94a3b8' },
      top: 10,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: {
        color: '#94a3b8',
        formatter: (value) => formatPeriodLabel(value, props.currentGranularity)
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: {
        color: '#94a3b8',
        formatter: (value) => Math.abs(value)
      },
      splitLine: {
        lineStyle: {
          color: '#1e293b',
          type: 'dashed'
        }
      }
    },
    series
  }
})

const authorRankOption = computed(() => {
  if (!props.authorRank || props.authorRank.length === 0) {
    return {
      title: {
        text: t('analytics.noData'),
        left: 'center',
        top: 'center',
        textStyle: { color: '#64748b', fontSize: 16 }
      }
    }
  }

  const topAuthors = props.authorRank.slice(0, 10)
  const colors = ['#00f5ff', '#ff00ff', '#ffd700', '#00ff88', '#ff6b6b', '#a78bfa']

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 14, 39, 0.95)',
      borderColor: '#00f5ff',
      textStyle: { color: '#fff' },
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const item = params[0]
        const author = topAuthors[item.dataIndex]
        return `
          <div style="font-weight:bold;margin-bottom:5px">${author.author}</div>
          <div>提交数: ${author.commits}</div>
          <div>新增: <span style="color:#00ff88">${author.additions}</span></div>
          <div>删除: <span style="color:#ff6b6b">${author.deletions}</span></div>
          <div>净变化: ${author.netChange > 0 ? '+' : ''}${author.netChange}</div>
        `
      }
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#94a3b8' },
      splitLine: {
        lineStyle: {
          color: '#1e293b',
          type: 'dashed'
        }
      }
    },
    yAxis: {
      type: 'category',
      data: topAuthors.map(a => a.author),
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8' },
      inverse: true
    },
    series: [{
      type: 'bar',
      data: topAuthors.map((a, idx) => ({
        value: a.commits,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: colors[idx % colors.length] },
            { offset: 1, color: adjustColor(colors[idx % colors.length], -40) }
          ]),
          borderRadius: [0, 4, 4, 0]
        }
      })),
      barWidth: '60%'
    }]
  }
})

const heatmapOption = computed(() => {
  if (!props.activityHeatmap || props.activityHeatmap.length === 0) {
    return {
      title: {
        text: t('analytics.noData'),
        left: 'center',
        top: 'center',
        textStyle: { color: '#64748b', fontSize: 16 }
      }
    }
  }

  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

  const data = props.activityHeatmap.map(item => [
    item.dayOfWeek,
    item.hour,
    item.commitCount
  ])

  const maxCount = Math.max(...data.map(d => d[2]))

  return {
    tooltip: {
      backgroundColor: 'rgba(10, 14, 39, 0.95)',
      borderColor: '#00f5ff',
      textStyle: { color: '#fff' },
      formatter: (params) => {
        return `<div>${days[params.value[0]]} ${hours[params.value[1]]}</div><div>提交数: ${params.value[2]}</div>`
      }
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: days,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8' },
      splitArea: { show: true, areaStyle: { color: 'rgba(30, 41, 59, 0.3)' } }
    },
    yAxis: {
      type: 'category',
      data: hours,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8' },
      splitArea: { show: true, areaStyle: { color: 'rgba(30, 41, 59, 0.3)' } }
    },
    visualMap: {
      min: 0,
      max: maxCount,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: [
          'rgba(0, 245, 255, 0.1)',
          'rgba(0, 245, 255, 0.4)',
          'rgba(0, 245, 255, 0.7)',
          '#00f5ff'
        ]
      },
      textStyle: { color: '#94a3b8' }
    },
    series: [{
      type: 'heatmap',
      data: data,
      label: { show: false },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 245, 255, 0.5)'
        }
      }
    }]
  }
})

const repoComparisonOption = computed(() => {
  if (!props.repoComparison || props.repoComparison.length === 0) {
    return {
      title: {
        text: t('analytics.noData'),
        left: 'center',
        top: 'center',
        textStyle: { color: '#64748b', fontSize: 16 }
      }
    }
  }

  const repos = props.repoComparison.slice(0, 5)
  const colors = ['#00f5ff', '#ff00ff', '#ffd700', '#00ff88', '#ff6b6b']

  const maxCommits = Math.max(...repos.map(r => r.commits))
  const maxAdditions = Math.max(...repos.map(r => r.additions))
  const maxAuthors = Math.max(...repos.map(r => r.authors))
  const maxActiveDays = Math.max(...repos.map(r => r.activeDays))

  return {
    tooltip: {
      backgroundColor: 'rgba(10, 14, 39, 0.95)',
      borderColor: '#00f5ff',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: repos.map(r => r.repoName),
      textStyle: { color: '#94a3b8' },
      top: 10
    },
    radar: {
      indicator: [
        { name: '提交数', max: 100 },
        { name: '代码量', max: 100 },
        { name: '作者数', max: 100 },
        { name: '活跃天数', max: 100 },
        { name: '日均提交', max: 100 }
      ],
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#94a3b8' },
      splitLine: {
        lineStyle: { color: 'rgba(0, 245, 255, 0.2)' }
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(0, 245, 255, 0.05)', 'rgba(0, 245, 255, 0.1)']
        }
      }
    },
    series: [{
      type: 'radar',
      data: repos.map((repo, idx) => {
        const avgCommitsPerDayNormalized = repo.avgCommitsPerDay > 10 ? 100 : (repo.avgCommitsPerDay / 10) * 100
        return {
          value: [
            (repo.commits / maxCommits) * 100,
            (repo.additions / maxAdditions) * 100,
            (repo.authors / maxAuthors) * 100,
            (repo.activeDays / maxActiveDays) * 100,
            avgCommitsPerDayNormalized
          ],
          name: repo.repoName,
          lineStyle: { color: colors[idx % colors.length], width: 2 },
          itemStyle: { color: colors[idx % colors.length] },
          areaStyle: { opacity: 0.2, color: colors[idx % colors.length] }
        }
      })
    }]
  }
})
</script>

<style scoped>
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
}

.chart-card {
  min-height: 450px;
  height: 450px;
}

@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
