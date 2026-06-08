<template>
  <div class="weather-card card" :class="{ loading: weatherLoading }">
    <!-- Skeleton -->
    <div v-if="weatherLoading" class="weather-skeleton">
      <div class="skeleton-row">
        <div class="skeleton-circle"></div>
        <div class="skeleton-lines">
          <div class="skeleton-bar w60"></div>
          <div class="skeleton-bar w40"></div>
        </div>
      </div>
      <div class="forecast-skeleton">
        <div class="skeleton-mini" v-for="i in 7" :key="i"></div>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="weatherError" class="weather-error">
      <span class="error-icon">!</span>
      <span>{{ t('weather.unavailable') }}</span>
    </div>

    <!-- Loaded state -->
    <div v-else-if="weatherCurrent" class="weather-content">
      <!-- Current weather -->
      <div class="current-section">
        <div class="current-left">
          <div class="weather-icon-box">
            <span class="weather-emoji">{{ getWeatherEmoji(weatherCurrent.icon) }}</span>
          </div>
          <div class="current-info">
            <div class="temp-main">
              <span class="temp-value">{{ weatherCurrent.temperature }}</span>
              <span class="temp-unit">{{ t('weather.unitC') }}</span>
            </div>
            <div class="weather-desc">{{ locale === 'zh' ? weatherCurrent.descriptionZh : weatherCurrent.descriptionEn }}</div>
          </div>
        </div>
        <div class="current-right">
          <div class="location-row">
            <span class="location-pin">📍</span>
            <span class="location-name">{{ weatherCurrent.locationName }}</span>
            <span class="location-tz">{{ weatherCurrent.timezone }}</span>
          </div>
          <div class="weather-date">{{ todayDate }}</div>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">{{ t('weather.feelsLike') }}</span>
              <span class="detail-value">{{ weatherCurrent.apparentTemperature }}{{ t('weather.unitC') }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">{{ t('weather.humidity') }}</span>
              <span class="detail-value">{{ weatherCurrent.humidity }}{{ t('weather.unitPercent') }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">{{ t('weather.wind') }}</span>
              <span class="detail-value">{{ weatherCurrent.windSpeed }}{{ t('weather.unitKmh') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 7-day forecast -->
      <div class="forecast-section" v-if="weatherForecast.length">
        <div class="forecast-header">{{ t('weather.forecast') }}</div>
        <div class="forecast-strip">
          <div
            class="forecast-day"
            v-for="(day, idx) in weatherForecast"
            :key="day.date"
            :class="{ today: idx === 0 }"
          >
            <div class="day-name">{{ getDayName(day.date, idx) }}</div>
            <div class="day-icon">{{ getWeatherEmoji(day.icon) }}</div>
            <div class="day-desc">{{ locale === 'zh' ? day.descriptionZh : day.descriptionEn }}</div>
            <div class="day-temps">
              <span class="temp-max">{{ day.temperatureMax }}°</span>
              <span class="temp-sep">/</span>
              <span class="temp-min">{{ day.temperatureMin }}°</span>
            </div>
            <div class="day-precip" v-if="day.precipitation > 0">
              {{ day.precipitation }}{{ t('weather.unitMm') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../i18n'
import { weatherState } from '../stores/weather'
import { WEATHER_EMOJI_MAP } from '../utils/constants'

const { t, locale } = useI18n()

const weatherCurrent = computed(() => weatherState.current)
const weatherForecast = computed(() => weatherState.forecast)
const weatherLoading = computed(() => weatherState.loading)
const weatherError = computed(() => weatherState.error && !weatherCurrent.value)

const todayDate = computed(() => {
  const d = new Date()
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${days[d.getDay()]}`
})

function getWeatherEmoji(icon) {
  return WEATHER_EMOJI_MAP[icon] || WEATHER_EMOJI_MAP.unknown
}

function getDayName(dateStr, idx) {
  if (idx === 0) return t('weather.today')
  const date = new Date(dateStr)
  const dayIdx = date.getDay()
  return t('weather.daysOfWeek')[dayIdx]
}
</script>

<style scoped>
.weather-card {
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.weather-card.loading {
  min-height: 180px;
}

/* Skeleton */
.weather-skeleton {
  padding: 1.5rem;
}

.skeleton-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.skeleton-circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.1), rgba(120, 0, 255, 0.1));
  animation: skeletonPulse 1.5s ease-in-out infinite;
}

.skeleton-lines {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-bar {
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.1), rgba(120, 0, 255, 0.1));
  animation: skeletonPulse 1.5s ease-in-out infinite;
}

.skeleton-bar.w60 { width: 60%; }
.skeleton-bar.w40 { width: 40%; }

.forecast-skeleton {
  display: flex;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.skeleton-mini {
  flex: 1;
  height: 80px;
  border-radius: 6px;
  background: linear-gradient(135deg, rgba(0, 245, 255, 0.05), rgba(120, 0, 255, 0.05));
  animation: skeletonPulse 1.5s ease-in-out infinite;
}

@keyframes skeletonPulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* Error */
.weather-error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  color: #ff4757;
  font-family: 'Rajdhani', sans-serif;
}

.error-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid #ff4757;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

/* Content */
.weather-content {
  padding: 1.5rem;
}

.current-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
}

.current-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.weather-icon-box {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: rgba(0, 245, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.15);
}

.weather-icon-box:hover {
  background: rgba(0, 245, 255, 0.2);
  box-shadow: 0 0 25px rgba(0, 245, 255, 0.3);
}

.weather-emoji {
  font-size: 2rem;
  line-height: 1;
}

.current-info {
  display: flex;
  flex-direction: column;
}

.temp-main {
  display: flex;
  align-items: baseline;
}

.temp-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--neon-cyan, #00f5ff);
  letter-spacing: 2px;
  line-height: 1;
}

.temp-unit {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  color: #a0aec0;
  margin-left: 0.25rem;
}

.weather-desc {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.95rem;
  color: #e0e6ff;
  margin-top: 0.25rem;
  letter-spacing: 1px;
}

.current-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.location-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.3rem;
}
.location-pin { font-size: 0.9rem; }
.location-name {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.85rem;
  color: #e2e8f0;
  letter-spacing: 1px;
  font-weight: 600;
}
.location-tz {
  font-size: 0.55rem;
  color: #475569;
  font-family: 'Share Tech Mono', monospace;
  background: rgba(0, 245, 255, 0.06);
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(0, 245, 255, 0.1);
}
.weather-date {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.7rem;
  color: #64748b;
  margin-bottom: 0.6rem;
  letter-spacing: 0.5px;
}

.detail-grid {
  display: flex;
  gap: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
}

.detail-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.7rem;
  color: #a0aec0;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.detail-value {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.85rem;
  color: var(--neon-cyan, #00f5ff);
}

/* Forecast */
.forecast-section {
  margin-top: 1.5rem;
  border-top: 1px solid rgba(0, 245, 255, 0.15);
  padding-top: 1rem;
}

.forecast-header {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.75rem;
  color: #a0aec0;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
}

.forecast-strip {
  display: flex;
  gap: 0.5rem;
}

.forecast-day {
  flex: 1;
  min-width: 0;
  text-align: center;
  padding: 0.5rem 0.25rem;
  border-radius: 8px;
  background: rgba(0, 245, 255, 0.03);
  border: 1px solid rgba(0, 245, 255, 0.1);
  transition: all 0.3s;
  cursor: default;
}

.forecast-day:hover {
  background: rgba(0, 245, 255, 0.08);
  border-color: rgba(0, 245, 255, 0.3);
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.15);
}

.forecast-day.today {
  background: rgba(0, 245, 255, 0.1);
  border-color: rgba(0, 245, 255, 0.4);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
}

.day-name {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.65rem;
  color: var(--neon-cyan, #00f5ff);
  letter-spacing: 1px;
  margin-bottom: 0.25rem;
}

.day-icon {
  font-size: 1.2rem;
  line-height: 1;
  margin-bottom: 0.15rem;
}

.day-desc {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.65rem;
  color: #a0aec0;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.day-temps {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.75rem;
}

.temp-max {
  color: #ff6b6b;
}

.temp-sep {
  color: #a0aec0;
  margin: 0 0.1rem;
}

.temp-min {
  color: #4ecdc4;
}

.day-precip {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.6rem;
  color: #00d4ff;
  margin-top: 0.15rem;
}

@media (max-width: 640px) {
  .current-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .current-right {
    align-items: flex-start;
  }

  .detail-grid {
    gap: 0.75rem;
  }

  .forecast-strip {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .forecast-day {
    min-width: 70px;
    flex: none;
  }
}
</style>