<template>
  <Teleport to="body">
    <div v-if="visible" class="confirm-overlay" @click.self="onCancel">
      <div class="confirm-dialog" role="alertdialog" aria-modal="true">
        <div class="confirm-header">
          <h3>{{ title }}</h3>
        </div>
        <p class="confirm-body">{{ message }}</p>
        <div class="confirm-actions">
          <button class="btn-cancel" @click="onCancel" ref="cancelBtn">{{ cancelText }}</button>
          <button class="btn-confirm" @click="onConfirm" ref="confirmBtn">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '确认操作' },
  message: { type: String, default: '确定要执行此操作吗？' },
  confirmText: { type: String, default: '确定' },
  cancelText: { type: String, default: '取消' },
})

const emit = defineEmits(['confirm', 'cancel', 'update:visible'])
const confirmBtn = ref(null)
const cancelBtn = ref(null)

watch(() => props.visible, async (v) => {
  if (v) await nextTick(); cancelBtn.value?.focus()
})

function onConfirm() { emit('confirm'); emit('update:visible', false) }
function onCancel() { emit('cancel'); emit('update:visible', false) }
</script>

<style scoped>
.confirm-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  animation: fadeIn 0.2s ease-out;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.confirm-dialog {
  background: rgba(12, 18, 40, 0.95);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 12px; padding: 1.5rem;
  max-width: 420px; width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 30px rgba(0,245,255,0.1);
}
.confirm-header h3 {
  font-family: 'Orbitron', sans-serif; font-size: 1rem;
  color: var(--neon-cyan); margin: 0;
  text-shadow: 0 0 8px rgba(0,245,255,0.3);
}
.confirm-body {
  color: #94a3b8; margin: 1rem 0; font-size: 0.9rem; line-height: 1.5;
}
.confirm-actions { display: flex; gap: 0.75rem; justify-content: flex-end; }
.btn-cancel, .btn-confirm {
  padding: 0.5rem 1.25rem; border-radius: 6px; cursor: pointer;
  font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; transition: all 0.3s;
}
.btn-cancel {
  background: transparent; border: 1px solid rgba(148,163,184,0.3); color: #94a3b8;
}
.btn-cancel:hover { background: rgba(148,163,184,0.1); }
.btn-confirm {
  background: rgba(0,245,255,0.1); border: 1px solid rgba(0,245,255,0.4); color: var(--neon-cyan);
}
.btn-confirm:hover {
  background: rgba(0,245,255,0.2); box-shadow: 0 0 16px rgba(0,245,255,0.2);
}
</style>
