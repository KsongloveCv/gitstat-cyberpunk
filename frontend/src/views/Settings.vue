<template>
  <div class="settings">
    <h2 class="page-title">{{ t('settings.title') }}</h2>
    
    <!-- 扫描路径配置 -->
    <div class="card settings-card">
      <div class="card-header">
        <h3>{{ t('settings.scanConfig') }}</h3>
      </div>
      <div class="scan-config-section">
        <div class="form-group">
          <label>{{ t('settings.directoryPath') }}</label>
          <div class="input-row">
            <input v-model="scanPath" :placeholder="t('settings.pathPlaceholder')" />
            <button @click="handleScan" :disabled="scanning" class="btn scan-btn">
              <span v-if="!scanning">{{ t('settings.startScan') }}</span>
              <span v-else class="loading-text">
                <span class="spinner"></span>
                {{ t('settings.scanning') }}
              </span>
            </button>
          </div>
        </div>
        <p v-if="scanError" class="error-msg">{{ scanError }}</p>
        <p v-if="scanSuccess" class="success-msg">{{ scanSuccess }}</p>
      </div>
    </div>
    
    <div class="card settings-card">
      <div class="card-header">
        <h3>{{ t('settings.dataManagement') }}</h3>
      </div>
      <button @click="handleExport" class="btn export-btn">
        <span class="btn-icon">↓</span>
        {{ t('settings.exportData') }}
      </button>
    </div>
    
    <div class="card settings-card">
      <div class="card-header">
        <h3>{{ t('settings.about') }}</h3>
      </div>
      <div class="about-content">
        <div class="logo-text">GITSTAT</div>
        <p class="version">{{ version }} - {{ t('settings.platformName') }}</p>
        <div class="tech-stack">
          <div class="tech-item">
            <span class="tech-icon">⚡</span>
            <span>Go 1.26</span>
          </div>
          <div class="tech-item">
            <span class="tech-icon">◈</span>
            <span>Vue 3</span>
          </div>
          <div class="tech-item">
            <span class="tech-icon">◉</span>
            <span>ECharts</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from '../i18n'
import { performScan, state, loadScanPath } from '../stores/data'
import * as api from '../api'

const { t } = useI18n()
const scanPath = computed({
  get: () => state.scanPath,
  set: (v) => { state.scanPath = v }
})
const scanning = ref(false)
const scanError = ref('')
const scanSuccess = ref('')
const version = ref('v0.1.0')

onMounted(async () => {
  try {
    const scanInfo = await api.getScanPath()
    version.value = scanInfo.version || 'dev'
  } catch (err) {
    console.error('Failed to fetch version:', err)
  }
  await loadScanPath()
})

async function handleScan() {
  scanning.value = true
  scanError.value = ''
  scanSuccess.value = ''
  
  try {
    await performScan(scanPath.value, '1d')
    scanSuccess.value = t('settings.scanSuccess')
    setTimeout(() => scanSuccess.value = '', 3000)
  } catch (err) {
    scanError.value = err.message
  } finally {
    scanning.value = false
  }
}

async function handleExport() {
  try {
    const blob = await api.exportData()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'gitstat-data.json'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    alert('导出失败: ' + err.message)
  }
}
</script>

<style scoped>
.settings {
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 2rem;
  color: #00d4ff;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #00d4ff, #7800ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.settings-card {
  margin-bottom: 2rem;
}

.scan-config-section {
  padding: 1rem 0;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.75rem;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.85rem;
  color: #a0aec0;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.input-row {
  display: flex;
  gap: 1rem;
}

.input-row input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 8px;
  background: rgba(10, 14, 39, 0.6);
  color: #e0e6ff;
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  transition: all 0.3s;
}

.input-row input:focus {
  outline: none;
  border-color: #00d4ff;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
  background: rgba(10, 14, 39, 0.8);
}

.scan-btn {
  min-width: 140px;
  position: relative;
}

.error-msg,
.success-msg {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  font-family: 'Rajdhani', sans-serif;
}

.error-msg {
  color: #ff4757;
  background: rgba(255, 71, 87, 0.1);
  border: 1px solid rgba(255, 71, 87, 0.3);
}

.success-msg {
  color: #00ff88;
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.card-header {
  position: relative;
  margin-bottom: 1.5rem;
}

.card-header h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.3rem;
  color: #00d4ff;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin: 0;
}

.export-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
}

.btn-icon {
  font-size: 1.2rem;
}

.about-content {
  text-align: center;
  padding: 2rem 0;
}

.logo-text {
  font-family: 'Orbitron', sans-serif;
  font-size: 2.5rem;
  font-weight: 900;
  background: linear-gradient(135deg, #00d4ff 0%, #7800ff 50%, #00ff88 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 4px;
  margin-bottom: 1rem;
}

.version {
  color: #a0aec0;
  font-size: 1rem;
  margin-bottom: 2rem;
}

.tech-stack {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.tech-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 8px;
  transition: all 0.3s;
}

.tech-item:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: #00d4ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
}

.tech-icon {
  font-size: 1.2rem;
}
</style>
