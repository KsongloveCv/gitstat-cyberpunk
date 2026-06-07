/** Weather state and actions. */
import { reactive } from 'vue'
import * as api from '../api'

export const weatherState = reactive({
  current: null,
  forecast: [],
  loading: false,
  coords: null,
  error: null,
})

export async function fetchWeather(lat, lon) {
  weatherState.loading = true
  weatherState.error = null
  try {
    const [current, forecast] = await Promise.all([
      api.getWeatherCurrent(lat, lon),
      api.getWeatherForecast(lat, lon, 7)
    ])
    weatherState.current = current
    weatherState.forecast = forecast
    weatherState.coords = { lat, lon }
  } catch (err) {
    weatherState.error = err.message
    console.error('Failed to fetch weather:', err)
  } finally {
    weatherState.loading = false
  }
}
