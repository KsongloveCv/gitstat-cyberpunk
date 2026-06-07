<template>
  <div class="controls-section">
    <div class="controls-inline">
      <div class="control-item">
        <label class="control-label">{{ t('analytics.timeRange') }}</label>
        <div class="time-selector-cyber">
          <div class="quick-options-cyber">
            <button
              v-for="option in timeOptions"
              :key="option.value"
              @click="selectTimeRange(option.value)"
              class="cyber-time-btn"
              :class="{ active: selectedTimeRange === option.value }"
            >
              <span class="btn-glow"></span>
              <span class="btn-text-cyber">{{ option.label }}</span>
            </button>
            <button
              @click.stop="emit('update:showCustomPicker', !showCustomPicker)"
              class="cyber-time-btn custom-btn"
              :class="{ active: selectedTimeRange === 'custom' }"
            >
              <span class="btn-glow"></span>
              <span class="btn-text-cyber">自定义</span>
            </button>
          </div>

          <div v-if="showCustomPicker" class="custom-picker-popup" @click.stop>
            <DatePicker
              :start="customStartDate"
              :end="customEndDate"
              @update:start="onCustomStart"
              @update:end="onCustomEnd"
            />
          </div>
        </div>
      </div>

      <div class="control-item">
        <label class="control-label">{{ t('analytics.repoFilter') }}</label>
        <div class="repo-dropdown">
          <button
            @click.stop="showDropdown = !showDropdown"
            class="repo-dropdown-btn"
            :class="{ active: showDropdown, 'has-selection': selectedRepos.length > 0 }"
          >
            <span class="btn-text">
              {{ selectedRepos.length === 0 ? t('analytics.selectRepo') :
                 selectedRepos.length === repositories.length ? t('analytics.allRepos') :
                 `${selectedRepos.length} ${t('analytics.reposSelected')}` }}
            </span>
            <svg class="dropdown-icon" :class="{ rotated: showDropdown }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>

          <div v-show="showDropdown" class="repo-dropdown-menu">
            <div class="dropdown-header">
              <button @click.stop="toggleAllRepos" class="select-all-btn">
                {{ allReposSelected ? t('analytics.cancelSelectAll') : t('analytics.selectAll') }}
              </button>
              <span class="selected-count">{{ selectedRepos.length }}/{{ repositories.length }}</span>
            </div>
            <div class="dropdown-list">
              <button
                v-for="repo in repositories"
                :key="repo.path"
                @click.stop="toggleRepo(repo.path)"
                class="repo-option"
                :class="{ active: selectedRepos.includes(repo.path) }"
              >
                <div class="option-checkbox">
                  <svg v-if="selectedRepos.includes(repo.path)" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </div>
                <span class="option-text">{{ repo.name }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="control-item">
        <button
          @click="emit('analyze')"
          :disabled="loading || selectedRepos.length === 0"
          class="analyze-btn"
          :class="{ 'can-analyze': selectedRepos.length > 0 }"
        >
          <svg v-if="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
          <div v-else class="btn-spinner"></div>
          <span>{{ loading ? t('analytics.analyzing') : t('analytics.startAnalyze') }}</span>
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from '../i18n'
import DatePicker from './DatePicker.vue'

const { t } = useI18n()

const props = defineProps({
  repositories: Array,
  selectedRepos: Array,
  selectedTimeRange: String,
  showCustomPicker: Boolean,
  customStartDate: String,
  customEndDate: String,
  loading: Boolean
})

const emit = defineEmits([
  'update:selectedRepos',
  'update:selectedTimeRange',
  'update:showCustomPicker',
  'update:customStartDate',
  'update:customEndDate',
  'analyze'
])

const showDropdown = ref(false)

const timeOptions = [
  { label: computed(() => t('analytics.thisWeek')), value: 'week' },
  { label: computed(() => t('analytics.thisMonth')), value: 'month' },
  { label: computed(() => t('analytics.thisYear')), value: 'year' }
]

const allReposSelected = computed(() => {
  return props.repositories.length > 0 &&
    props.selectedRepos.length === props.repositories.length
})

function selectTimeRange(value) {
  emit('update:selectedTimeRange', value)
  emit('update:customStartDate', '')
  emit('update:customEndDate', '')
  emit('update:showCustomPicker', false)
}

function onCustomStart(v) {
  emit('update:customStartDate', v)
  if (props.customEndDate) {
    emit('update:customEndDate', '')
    emit('update:showCustomPicker', false)
  }
}

function onCustomEnd(v) {
  emit('update:customEndDate', v)
  emit('update:selectedTimeRange', 'custom')
  emit('update:showCustomPicker', false)
  emit('analyze')
}

function toggleRepo(repoPath) {
  const idx = props.selectedRepos.indexOf(repoPath)
  if (idx > -1) {
    const next = [...props.selectedRepos]
    next.splice(idx, 1)
    emit('update:selectedRepos', next)
  } else {
    emit('update:selectedRepos', [...props.selectedRepos, repoPath])
  }
}

function toggleAllRepos() {
  if (allReposSelected.value) {
    emit('update:selectedRepos', [])
  } else {
    emit('update:selectedRepos', props.repositories.map(r => r.path))
  }
}

function closeDropdown(e) {
  if (showDropdown.value) {
    const el = e.target.closest('.repo-dropdown')
    if (!el) showDropdown.value = false
  }
}

function closeCustomPicker(e) {
  if (props.showCustomPicker) {
    const picker = e.target.closest('.custom-picker-popup')
    const btn = e.target.closest('.custom-btn')
    if (!picker && !btn) emit('update:showCustomPicker', false)
  }
}

onMounted(() => {
  document.addEventListener('click', closeDropdown)
  document.addEventListener('click', closeCustomPicker)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
  document.removeEventListener('click', closeCustomPicker)
})
</script>

<style scoped>
.controls-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.controls-inline {
  display: flex;
  gap: 1.5rem;
  align-items: flex-end;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-label {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.75rem;
  color: #00f5ff;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-weight: 600;
}

.analyze-btn {
  background: linear-gradient(135deg, #00f5ff 0%, #ff00ff 100%);
  border: none;
  border-radius: 8px;
  padding: 0.6rem 1.5rem;
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  outline: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: 'Orbitron', sans-serif;
  letter-spacing: 1px;
  box-shadow: 0 4px 15px rgba(0, 245, 255, 0.4);
  height: fit-content;
  align-self: flex-end;
  opacity: 0.5;
  cursor: not-allowed;
}

.analyze-btn.can-analyze {
  opacity: 1;
  cursor: pointer;
}

.analyze-btn.can-analyze:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 245, 255, 0.6);
}

.analyze-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.analyze-btn svg {
  width: 18px;
  height: 18px;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.time-selector-cyber {
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.quick-options-cyber {
  display: flex;
  gap: 0.6rem;
}

.cyber-time-btn {
  position: relative;
  background: rgba(10, 14, 39, 0.6);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 4px;
  padding: 0.6rem 1.2rem;
  color: #94a3b8;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  overflow: hidden;
  min-width: 80px;
}

.cyber-time-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.1), transparent);
  transition: left 0.5s ease;
}

.cyber-time-btn:hover::before {
  left: 100%;
}

.cyber-time-btn:hover {
  border-color: rgba(0, 245, 255, 0.5);
  color: #e2e8f0;
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.2), inset 0 0 20px rgba(0, 245, 255, 0.05);
  transform: translateY(-2px);
}

.cyber-time-btn.active {
  background: rgba(0, 245, 255, 0.15);
  border-color: #00f5ff;
  color: #00f5ff;
  box-shadow:
    0 0 30px rgba(0, 245, 255, 0.4),
    inset 0 0 30px rgba(0, 245, 255, 0.1),
    0 0 60px rgba(0, 245, 255, 0.2);
  text-shadow: 0 0 10px rgba(0, 245, 255, 0.8);
}

.cyber-time-btn.active .btn-glow {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #00f5ff, #ff00ff, #00f5ff);
  border-radius: 4px;
  opacity: 0.3;
  filter: blur(8px);
  animation: glow-pulse 2s ease-in-out infinite;
  z-index: -1;
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.btn-text-cyber {
  position: relative;
  z-index: 1;
}

.cyber-time-btn.custom-btn {
  min-width: 70px;
  font-size: 0.78rem;
  padding: 0.6rem 0.8rem;
}

.custom-picker-popup {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  margin-top: 0.5rem;
  padding: 0.25rem;
  animation: slideDown 0.2s ease;
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

.repo-dropdown {
  position: relative;
}

.repo-dropdown-btn {
  background: rgba(10, 14, 39, 0.8);
  border: 2px solid rgba(0, 245, 255, 0.3);
  border-radius: 8px;
  padding: 0.6rem 1rem;
  color: #e2e8f0;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  outline: none;
  min-width: 180px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  font-family: 'Rajdhani', sans-serif;
}

.repo-dropdown-btn:hover {
  border-color: #00f5ff;
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.3);
}

.repo-dropdown-btn.active {
  border-color: #00f5ff;
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.5);
}

.btn-text {
  flex: 1;
  text-align: left;
}

.dropdown-icon {
  width: 16px;
  height: 16px;
  transition: transform 0.3s ease;
  color: #00f5ff;
}

.dropdown-icon.rotated {
  transform: rotate(180deg);
}

.repo-dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: rgba(10, 14, 39, 0.98);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(0, 245, 255, 0.3);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 30px rgba(0, 245, 255, 0.2);
  z-index: 1000;
  overflow: hidden;
  animation: dropdownSlide 0.2s ease;
}

@keyframes dropdownSlide {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 245, 255, 0.1);
  background: rgba(0, 245, 255, 0.05);
}

.select-all-btn {
  background: transparent;
  border: 1px solid rgba(0, 245, 255, 0.4);
  border-radius: 6px;
  padding: 0.35rem 0.75rem;
  color: #00f5ff;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Rajdhani', sans-serif;
}

.select-all-btn:hover {
  background: rgba(0, 245, 255, 0.1);
  border-color: #00f5ff;
}

.selected-count {
  font-size: 0.8rem;
  color: #64748b;
  font-family: 'Orbitron', sans-serif;
}

.dropdown-list {
  max-height: 300px;
  overflow-y: auto;
  padding: 0.5rem;
}

.dropdown-list::-webkit-scrollbar {
  width: 6px;
}

.dropdown-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

.dropdown-list::-webkit-scrollbar-thumb {
  background: rgba(0, 245, 255, 0.3);
  border-radius: 3px;
}

.dropdown-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 245, 255, 0.5);
}

.repo-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #94a3b8;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  font-family: 'Rajdhani', sans-serif;
}

.repo-option:hover {
  background: rgba(0, 245, 255, 0.1);
  color: #e2e8f0;
}

.repo-option.active {
  background: rgba(0, 245, 255, 0.15);
  color: #00f5ff;
}

.option-checkbox {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(148, 163, 184, 0.4);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.repo-option.active .option-checkbox {
  border-color: #00f5ff;
  background: rgba(0, 245, 255, 0.2);
}

.option-checkbox svg {
  width: 12px;
  height: 12px;
  color: #00f5ff;
}

.option-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}


</style>
