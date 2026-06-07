// Cyberpunk Neon Chart Color Palette
export const CHART_COLORS = [
  '#00f5ff', // neon cyan
  '#ff00ff', // neon magenta
  '#00ff88', // neon green
  '#ffd700', // neon yellow
  '#ff3366', // neon red
  '#a78bfa', // neon purple
  '#ff8c00', // neon orange
  '#00e5ff', // light cyan
]

export const STAT_COLORS = {
  commits: '#00f5ff',
  additions: '#00ff88',
  deletions: '#ff00ff',
  authors: '#ffd700',
  repos: '#a78bfa',
  weekly: '#ff3366'
}

// ECharts dark cyberpunk theme defaults
export const WEATHER_EMOJI_MAP = {
  clear: '☀️',
  'mostly-clear': '🌤️',
  'partly-cloudy': '⛅',
  overcast: '☁️',
  fog: '🌫️',
  drizzle: '🌦️',
  rain: '🌧️',
  snow: '❄️',
  thunderstorm: '⛈️',
  unknown: '🌡️',
}

export const CYBERPUNK_CHART_THEME = {
  tooltip: {
    backgroundColor: 'rgba(8, 12, 32, 0.95)',
    borderColor: 'rgba(0, 245, 255, 0.4)',
    borderWidth: 1,
    textStyle: { color: '#e0e6ff', fontSize: 12, fontFamily: 'Rajdhani, sans-serif' },
    extraCssText: 'box-shadow: 0 0 20px rgba(0, 245, 255, 0.2), 0 0 40px rgba(0, 0, 0, 0.5); border-radius: 8px;'
  },
  grid: {
    borderColor: 'rgba(0, 245, 255, 0.1)'
  },
  xAxis: {
    axisLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.3)' } },
    axisLabel: { color: '#94a3b8', fontSize: 11 },
    splitLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.06)', type: 'dashed' } }
  },
  yAxis: {
    axisLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.3)' } },
    axisLabel: { color: '#94a3b8', fontSize: 11 },
    splitLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.08)', type: 'dashed' } }
  }
}
