<template>
  <canvas ref="canvasRef" class="matrix-canvas"></canvas>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  opacity: { type: Number, default: 0.08 },
  fontSize: { type: Number, default: 14 },
  speed: { type: Number, default: 1.0 },
  color: { type: String, default: '#00f5ff' }
})

const canvasRef = ref(null)
let animationId = null
let drops = []
let columns = 0

const chars = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789'.split('')

function initCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const ctx = canvas.getContext('2d')
  columns = Math.floor(canvas.width / props.fontSize)
  drops = Array(columns).fill(1)
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  const w = canvas.width
  const h = canvas.height

  ctx.fillStyle = `rgba(6, 11, 31, ${0.05 * props.speed})`
  ctx.fillRect(0, 0, w, h)

  ctx.fillStyle = props.color
  ctx.font = `${props.fontSize}px "Share Tech Mono", monospace`

  for (let i = 0; i < drops.length; i++) {
    const char = chars[Math.floor(Math.random() * chars.length)]
    const x = i * props.fontSize
    const y = drops[i] * props.fontSize

    // Leading character brighter
    if (Math.random() > 0.975) {
      ctx.fillStyle = '#ffffff'
    } else {
      ctx.fillStyle = props.color
    }

    ctx.globalAlpha = props.opacity * 3
    ctx.fillText(char, x, y)
    ctx.globalAlpha = 1

    if (y > h && Math.random() > 0.975) {
      drops[i] = 0
    }
    drops[i]++
  }
}

function animate() {
  draw()
  animationId = requestAnimationFrame(animate)
}

function handleResize() {
  initCanvas()
}

onMounted(() => {
  initCanvas()
  animate()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.matrix-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}
</style>
