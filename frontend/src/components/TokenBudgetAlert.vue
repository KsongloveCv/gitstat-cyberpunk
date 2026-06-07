<template>
  <div class="token-budget-alert" :class="{ 'over-budget': budgetData.isOverBudget }">
    <div class="budget-header">
      <span class="budget-title">月度预算管理</span>
      <span class="budget-subtitle">MONTHLY BUDGET CONTROL</span>
      <span v-if="budgetData.isOverBudget" class="budget-warning">⚠ OVER BUDGET</span>
    </div>

    <!-- Budget progress bar -->
    <div class="budget-progress-section">
      <div class="progress-info">
        <span class="progress-spent">
          ¥{{ formatMoney(budgetData.currentSpent) }}
        </span>
        <span class="progress-total">
          / ¥{{ formatMoney(budgetData.monthlyBudget) }}
        </span>
        <span class="progress-percent">{{ budgetData.percentUsed }}%</span>
      </div>

      <div class="progress-bar-track">
        <div
          class="progress-bar-fill"
          :class="{ 'fill-over': budgetData.isOverBudget }"
          :style="{ width: Math.min(budgetData.percentUsed, 100) + '%' }"
        ></div>
        <!-- Over-budget overflow indicator -->
        <div
          v-if="budgetData.isOverBudget"
          class="progress-overflow"
          :style="{ width: (budgetData.percentUsed - 100) + '%' }"
        ></div>
      </div>
    </div>

    <!-- Budget edit -->
    <div class="budget-edit-section">
      <label class="edit-label">设置月度预算 ¥</label>
      <div class="edit-row">
        <input
          v-model="editBudget"
          class="budget-input"
          type="number"
          placeholder="输入预算金额"
          @keyup.enter="saveBudget"
        />
        <button class="budget-save-btn" @click="saveBudget">
          保存
        </button>
      </div>
    </div>

    <!-- Stats row -->
    <div class="budget-stats">
      <div class="stat-item">
        <div class="stat-label">已用比例</div>
        <div class="stat-value" :class="{ 'stat-over': budgetData.isOverBudget }">
          {{ budgetData.percentUsed }}%
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-label">剩余预算</div>
        <div class="stat-value">
          ¥{{ formatMoney(Math.max(0, budgetData.monthlyBudget - budgetData.currentSpent)) }}
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-label">超额金额</div>
        <div class="stat-value stat-over-value">
          ¥{{ formatMoney(Math.max(0, budgetData.currentSpent - budgetData.monthlyBudget)) }}
        </div>
      </div>
    </div>

    <!-- Over budget red flashing overlay -->
    <div v-if="budgetData.isOverBudget" class="flash-overlay"></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  budgetData: {
    type: Object,
    default: () => ({
      monthlyBudget: 100,
      currentSpent: 0,
      percentUsed: 0,
      isOverBudget: false
    })
  }
})

const emit = defineEmits(['updateBudget'])

const editBudget = ref(props.budgetData.monthlyBudget)

function formatMoney(value) {
  if (!value && value !== 0) return '0.00'
  return Number(value).toFixed(2)
}

function saveBudget() {
  const amount = parseFloat(editBudget.value)
  if (amount && amount > 0) {
    emit('updateBudget', amount)
  }
}
</script>

<style scoped>
.token-budget-alert {
  background: rgba(12, 18, 40, 0.7);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 4px;
  padding: 20px;
  position: relative;
  font-family: 'Share Tech Mono', monospace;
  transition: all 0.3s ease;
}

.over-budget {
  border-color: rgba(255, 51, 102, 0.4);
  box-shadow: 0 0 12px rgba(255, 51, 102, 0.2);
}

/* Red flash overlay */
.flash-overlay {
  position: absolute;
  inset: 0;
  border-radius: 4px;
  animation: redFlash 2s ease-in-out infinite;
  pointer-events: none;
}

@keyframes redFlash {
  0%, 100% {
    background: rgba(255, 51, 102, 0);
  }
  50% {
    background: rgba(255, 51, 102, 0.06);
  }
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 16px;
}

.budget-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  color: #00f5ff;
  letter-spacing: 2px;
}

.budget-subtitle {
  font-size: 11px;
  color: rgba(0, 245, 255, 0.5);
  letter-spacing: 1px;
}

.budget-warning {
  font-family: 'Orbitron', sans-serif;
  font-size: 12px;
  color: #ff3366;
  animation: warningPulse 1.5s ease-in-out infinite;
}

@keyframes warningPulse {
  0%, 100% { opacity: 1; text-shadow: 0 0 4px rgba(255, 51, 102, 0.3); }
  50% { opacity: 0.5; text-shadow: 0 0 12px rgba(255, 51, 102, 0.8); }
}

/* Progress bar */
.budget-progress-section {
  margin-bottom: 16px;
}

.progress-info {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.progress-spent {
  font-family: 'Orbitron', sans-serif;
  font-size: 18px;
  color: #00f5ff;
}

.progress-total {
  font-size: 14px;
  color: rgba(0, 245, 255, 0.5);
}

.progress-percent {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  color: rgba(0, 255, 136, 0.8);
  margin-left: 8px;
}

.over-budget .progress-percent {
  color: #ff3366;
}

.progress-bar-track {
  height: 8px;
  background: rgba(0, 245, 255, 0.08);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(0, 245, 255, 0.5), rgba(0, 255, 136, 0.7));
  border-radius: 4px;
  transition: width 0.5s ease;
  box-shadow: 0 0 6px rgba(0, 245, 255, 0.3);
}

.fill-over {
  background: linear-gradient(90deg, rgba(0, 245, 255, 0.3), rgba(255, 51, 102, 0.6));
  box-shadow: 0 0 6px rgba(255, 51, 102, 0.4);
  animation: barFlashRed 1s ease-in-out infinite;
}

@keyframes barFlashRed {
  0%, 100% { box-shadow: 0 0 6px rgba(255, 51, 102, 0.3); }
  50% { box-shadow: 0 0 16px rgba(255, 51, 102, 0.7); }
}

.progress-overflow {
  position: absolute;
  right: 0;
  top: 0;
  height: 100%;
  background: rgba(255, 51, 102, 0.5);
  border-radius: 4px;
  animation: overflowPulse 1s ease-in-out infinite;
}

@keyframes overflowPulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* Budget edit */
.budget-edit-section {
  margin-bottom: 16px;
}

.edit-label {
  font-size: 11px;
  color: rgba(0, 245, 255, 0.5);
  margin-bottom: 6px;
  display: block;
}

.edit-row {
  display: flex;
  gap: 8px;
}

.budget-input {
  flex: 1;
  background: rgba(8, 14, 36, 0.8);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 2px;
  padding: 8px 12px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 14px;
  color: #00f5ff;
  outline: none;
  transition: all 0.2s ease;
}

.budget-input:focus {
  border-color: rgba(0, 245, 255, 0.6);
  box-shadow: 0 0 8px rgba(0, 245, 255, 0.2);
}

.budget-input::placeholder {
  color: rgba(0, 245, 255, 0.3);
}

.budget-save-btn {
  background: rgba(0, 245, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.4);
  border-radius: 2px;
  padding: 8px 16px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px;
  color: #00f5ff;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 1px;
}

.budget-save-btn:hover {
  background: rgba(0, 245, 255, 0.2);
  box-shadow: 0 0 8px rgba(0, 245, 255, 0.3);
}

.budget-save-btn:active {
  background: rgba(0, 245, 255, 0.3);
}

/* Stats */
.budget-stats {
  display: flex;
  gap: 16px;
  border-top: 1px solid rgba(0, 245, 255, 0.1);
  padding-top: 12px;
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-label {
  font-size: 11px;
  color: rgba(0, 245, 255, 0.5);
  margin-bottom: 4px;
}

.stat-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  color: #00ff88;
}

.stat-over {
  color: #ff3366;
}

.stat-over-value {
  color: #ff3366;
}
</style>