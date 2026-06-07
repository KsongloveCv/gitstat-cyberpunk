<template>
  <div class="stat-card" :style="cardStyle">
    <!-- Corner decorations -->
    <div class="corner-tl"></div>
    <div class="corner-br"></div>
    <!-- Hologram scan line -->
    <div class="hologram-scan"></div>
    <!-- Content -->
    <div class="stat-icon">{{ icon }}</div>
    <div class="stat-value" :data-text="String(value)">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
    <div class="stat-glow"></div>
    <!-- Data lines decoration -->
    <div class="data-lines">
      <span></span><span></span><span></span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: [Number, String], required: true },
  label: { type: String, required: true },
  icon: { type: String, default: '◈' },
  color: { type: String, default: '#00d4ff' }
})

const cardStyle = computed(() => ({
  '--accent-color': props.color,
  '--accent-glow': props.color + '66'
}))
</script>

<style scoped>
.stat-card {
  background: rgba(12, 18, 40, 0.7);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  padding: 1.75rem 1.5rem;
  border-radius: 12px;
  text-align: center;
  border: 1px solid rgba(0, 245, 255, 0.2);
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;
}

/* Background glow */
.stat-card::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 12px;
  background: radial-gradient(
    ellipse at 50% 0%,
    var(--accent-color) 0%,
    transparent 70%
  );
  opacity: 0;
  transition: opacity 0.4s;
  z-index: 0;
}

/* Corner neon accents — Top Left */
.corner-tl {
  position: absolute;
  top: 0;
  left: 0;
  width: 20px;
  height: 20px;
  border-top: 2px solid var(--accent-color);
  border-left: 2px solid var(--accent-color);
  border-radius: 12px 0 4px 0;
  opacity: 0.5;
  z-index: 2;
  box-shadow: 0 0 6px var(--accent-color);
  transition: all 0.3s;
}

/* Corner neon accents — Bottom Right */
.corner-br {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 20px;
  height: 20px;
  border-bottom: 2px solid var(--accent-color);
  border-right: 2px solid var(--accent-color);
  border-radius: 0 4px 0 12px;
  opacity: 0.5;
  z-index: 2;
  box-shadow: 0 0 6px var(--accent-color);
  transition: all 0.3s;
}

/* Hologram scan line */
.hologram-scan {
  position: absolute;
  top: -100%;
  left: 0;
  width: 100%;
  height: 30%;
  background: linear-gradient(
    180deg,
    transparent,
    rgba(255, 255, 255, 0.04),
    transparent
  );
  z-index: 1;
  animation: hologramScan 4s ease-in-out infinite;
  pointer-events: none;
}

@keyframes hologramScan {
  0% { top: -30%; }
  100% { top: 130%; }
}

/* Hover effects */
.stat-card:hover {
  transform: translateY(-6px);
  border-color: var(--accent-color);
  box-shadow:
    0 16px 48px rgba(0, 0, 0, 0.5),
    0 0 40px var(--accent-glow),
    0 0 80px var(--accent-glow);
}

.stat-card:hover::before {
  opacity: 0.12;
}

.stat-card:hover .corner-tl,
.stat-card:hover .corner-br {
  opacity: 1;
  box-shadow: 0 0 12px var(--accent-color), 0 0 24px var(--accent-glow);
}

/* Icon */
.stat-icon {
  font-size: 2.2rem;
  margin-bottom: 0.75rem;
  color: var(--accent-color);
  filter: drop-shadow(0 0 8px var(--accent-color)) drop-shadow(0 0 16px var(--accent-glow));
  animation: iconFloat 3s ease-in-out infinite;
  position: relative;
  z-index: 1;
}

.stat-card:nth-child(2) .stat-icon { animation-delay: 0.5s; }
.stat-card:nth-child(3) .stat-icon { animation-delay: 1s; }
.stat-card:nth-child(4) .stat-icon { animation-delay: 1.5s; }
.stat-card:nth-child(5) .stat-icon { animation-delay: 2s; }
.stat-card:nth-child(6) .stat-icon { animation-delay: 2.5s; }

@keyframes iconFloat {
  0%, 100% { transform: translateY(0) scale(1); }
  25% { transform: translateY(-4px) scale(1.05); }
  75% { transform: translateY(2px) scale(0.97); }
}

/* Value with glitch hover */
.stat-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 2.5rem;
  font-weight: 900;
  background: linear-gradient(180deg, var(--accent-color) 0%, #ffffff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
  position: relative;
  z-index: 1;
  transition: all 0.3s;
}

.stat-card:hover .stat-value {
  text-shadow: 0 0 10px var(--accent-glow);
  animation: valueGlitch 0.3s ease-in-out;
}

@keyframes valueGlitch {
  0% { transform: translate(0); }
  20% { transform: translate(-3px, 1px); }
  40% { transform: translate(3px, -1px); }
  60% { transform: translate(-2px, -1px); }
  80% { transform: translate(2px, 1px); }
  100% { transform: translate(0); }
}

/* Label */
.stat-label {
  font-family: 'Share Tech Mono', monospace;
  color: #94a3b8;
  font-size: 0.75rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  position: relative;
  z-index: 1;
}

/* Bottom glow bar */
.stat-glow {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 50%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent-color), transparent);
  box-shadow: 0 0 10px var(--accent-color), 0 0 20px var(--accent-glow);
  transition: all 0.3s;
}

.stat-card:hover .stat-glow {
  width: 80%;
  box-shadow: 0 0 16px var(--accent-color), 0 0 32px var(--accent-glow);
}

/* Data line decorations */
.data-lines {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 3px;
  opacity: 0.2;
  z-index: 0;
}

.data-lines span {
  display: block;
  width: 20px;
  height: 1px;
  background: var(--accent-color);
  transition: all 0.3s;
}

.stat-card:hover .data-lines {
  opacity: 0.6;
}

.stat-card:hover .data-lines span:nth-child(1) { width: 30px; }
.stat-card:hover .data-lines span:nth-child(2) { width: 22px; }
.stat-card:hover .data-lines span:nth-child(3) { width: 28px; }
</style>
