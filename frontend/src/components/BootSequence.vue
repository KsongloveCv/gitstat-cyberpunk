<template>
  <Teleport to="body">
    <div v-if="visible" class="boot-overlay" @click="skip">
      <div class="boot-terminal">
        <!-- Header -->
        <div class="boot-header">
          <span class="boot-dot boot-dot-red"></span>
          <span class="boot-dot boot-dot-yellow"></span>
          <span class="boot-dot boot-dot-green"></span>
          <span class="boot-title">NETRUNNER_OS v2.0.7</span>
        </div>

        <!-- Content -->
        <div class="boot-content" ref="contentRef">
          <div v-for="(line, i) in visibleLines" :key="i" class="boot-line" :class="line.type">
            <span class="boot-prompt" v-if="line.prompt">{{ line.prompt }}</span>
            <span class="boot-text">{{ line.text }}</span>
          </div>
          <span class="boot-cursor" v-if="typing">█</span>
        </div>

        <!-- Skip hint -->
        <div class="boot-skip" v-if="showSkipHint">
          [ PRESS ANY KEY TO SKIP ]
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const emit = defineEmits(['complete'])

const visible = ref(true)
const typing = ref(true)
const showSkipHint = ref(false)
const contentRef = ref(null)

const allLines = [
  { text: '╔══════════════════════════════════════════════════╗', type: 'header' },
  { text: '║   GITSTAT 赛博朋克 · 网络行者版 v2.0           ║', type: 'header' },
  { text: '╚══════════════════════════════════════════════════╝', type: 'header' },
  { text: '', type: 'info' },
  { text: '[系统] 正在初始化神经接口...', prompt: '> ', type: 'info' },
  { text: '[系统] 建立与代码仓库矩阵的安全连接...', prompt: '> ', type: 'info' },
  { text: '[系统] 加载赛博朋克视觉皮层...', prompt: '> ', type: 'info' },
  { text: '[系统] 校准霓虹光谱分析器...', prompt: '> ', type: 'info' },
  { text: '', type: 'info' },
  { text: '[完成] 神经链路已建立', prompt: '  ', type: 'success' },
  { text: '[完成] 仓库扫描器已上线', prompt: '  ', type: 'success' },
  { text: '[完成] 视觉皮层加载完毕 — CRT扫描线 + 数字雨就绪', prompt: '  ', type: 'success' },
  { text: '[完成] 霓虹光谱校准完成', prompt: '  ', type: 'success' },
  { text: '', type: 'info' },
  { text: '所有系统运行正常。', prompt: '  ', type: 'warning' },
  { text: '正在启动 GitStat 仪表盘...', prompt: '  ', type: 'info' },
  { text: '', type: 'info' },
  { text: '██████████████████████████████████████████████████', type: 'progress' },
  { text: '██████████████████████████████████████████████████', type: 'progress' },
  { text: '██████████████████████████████████████████████████', type: 'progress' },
  { text: '就绪。', type: 'success' },
]

const visibleLines = ref([])
let lineIndex = 0
let charIndex = 0
let timerId = null
let completionTimerId = null
let skipHintTimerId = null
let skipped = false

function typeNextChar() {
  if (skipped) return

  if (lineIndex >= allLines.length) {
    typing.value = false
    showSkipHint.value = false
    completionTimerId = setTimeout(() => {
      visible.value = false
      localStorage.setItem('bootShown', '1')
      emit('complete')
    }, 600)
    return
  }

  const currentLine = allLines[lineIndex]

  // Initialize line object if needed
  if (visibleLines.value.length <= lineIndex) {
    visibleLines.value.push({ text: '', type: currentLine.type, prompt: currentLine.prompt || '' })
  }

  const targetText = currentLine.text
  if (charIndex < targetText.length) {
    visibleLines.value[lineIndex].text = targetText.substring(0, charIndex + 1)
    charIndex++

    // Random typing speed for authenticity
    const delay = 10 + Math.random() * 30
    scrollToBottom()
    timerId = setTimeout(typeNextChar, delay)
  } else {
    // Line complete
    lineIndex++
    charIndex = 0
    const lineDelay = currentLine.text === '' ? 50 : 30 + Math.random() * 80
    scrollToBottom()
    timerId = setTimeout(typeNextChar, lineDelay)
  }
}

function scrollToBottom() {
  if (contentRef.value) {
    contentRef.value.scrollTop = contentRef.value.scrollHeight
  }
}

function skip() {
  if (skipped) return
  skipped = true
  typing.value = false
  showSkipHint.value = false
  if (timerId) clearTimeout(timerId)
  if (completionTimerId) clearTimeout(completionTimerId)

  // Show all lines immediately
  visibleLines.value = allLines.map(l => ({
    text: l.text,
    type: l.type,
    prompt: l.prompt || ''
  }))

  completionTimerId = setTimeout(() => {
    visible.value = false
    localStorage.setItem('bootShown', '1')
    emit('complete')
  }, 400)
}

function onKeydown() {
  skip()
}

onMounted(() => {
  timerId = setTimeout(typeNextChar, 200)
  skipHintTimerId = setTimeout(() => { showSkipHint.value = true }, 1500)
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  if (timerId) clearTimeout(timerId)
  if (completionTimerId) clearTimeout(completionTimerId)
  if (skipHintTimerId) clearTimeout(skipHintTimerId)
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.boot-overlay {
  position: fixed;
  inset: 0;
  background: #050a18;
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Share Tech Mono', monospace;
  cursor: pointer;
  animation: bootFadeOut 0.5s ease-out 1s forwards;
}

.boot-terminal {
  width: min(700px, 90vw);
  background: rgba(8, 12, 32, 0.95);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 8px;
  overflow: hidden;
  box-shadow:
    0 0 40px rgba(0, 245, 255, 0.15),
    0 0 80px rgba(255, 0, 255, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  position: relative;
}

.boot-terminal::after {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.06) 2px,
    rgba(0, 0, 0, 0.06) 4px
  );
  pointer-events: none;
  z-index: 2;
}

.boot-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(0, 245, 255, 0.1);
}

.boot-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.boot-dot-red { background: #ff5f57; box-shadow: 0 0 6px #ff5f57; }
.boot-dot-yellow { background: #ffbd2e; box-shadow: 0 0 6px #ffbd2e; }
.boot-dot-green { background: #28ca41; box-shadow: 0 0 6px #28ca41; }

.boot-title {
  margin-left: auto;
  color: #475569;
  font-size: 0.65rem;
  letter-spacing: 2px;
}

.boot-content {
  padding: 1.5rem;
  max-height: 55vh;
  overflow-y: auto;
  font-size: 0.8rem;
  line-height: 1.6;
  position: relative;
  z-index: 1;
}

.boot-line {
  white-space: pre-wrap;
  word-break: break-all;
}

.boot-line.header {
  color: var(--neon-cyan);
  font-weight: bold;
}

.boot-line.info {
  color: #94a3b8;
}

.boot-line.success {
  color: var(--neon-green);
}

.boot-line.warning {
  color: var(--neon-yellow);
}

.boot-line.error {
  color: var(--neon-red);
}

.boot-line.progress {
  color: var(--neon-magenta);
  letter-spacing: 1px;
}

.boot-prompt {
  color: var(--neon-cyan);
  opacity: 0.7;
}

.boot-text {
  color: inherit;
}

.boot-cursor {
  color: var(--neon-cyan);
  animation: cursorBlink 0.6s step-end infinite;
  font-weight: bold;
}

@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.boot-skip {
  text-align: center;
  padding: 0.75rem;
  color: #334155;
  font-size: 0.65rem;
  letter-spacing: 2px;
  animation: skipPulse 2s ease-in-out infinite;
  position: relative;
  z-index: 1;
}

@keyframes skipPulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

@keyframes bootFadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}
</style>
