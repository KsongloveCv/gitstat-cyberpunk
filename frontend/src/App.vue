<template>
  <div class="app">
    <!-- Matrix Rain Background -->
    <MatrixRain :opacity="matrixOpacity" />

    <!-- Boot Sequence -->
    <Teleport to="body">
      <BootSequence v-if="showBoot" @complete="showBoot = false" />
    </Teleport>

    <!-- Header -->
    <header class="header">
      <div class="header-scanline"></div>
      <div class="header-left">
        <div class="logo-container">
          <h1 class="logo glitch-text" data-text="GITSTAT" @click="cycleTheme">
            GITSTAT
          </h1>
          <div class="logo-glow"></div>
          <div class="logo-subtitle">// NETRUNNER EDITION</div>
        </div>
        <div class="header-meta" v-if="version || scanPath">
          <svg class="git-icon" viewBox="0 0 78 78" width="14" height="14">
            <path fill="currentColor" transform="translate(10 10) rotate(-45 29 29)" d="M5,58c-2.76142,0 -5,-2.23858 -5,-5v-48c0,-2.76142 2.23858,-5 5,-5h33v12.54404c-2.06553,0.94801 -3.5,3.03446 -3.5,5.45596c0,0.73514 0.13221,1.43941 0.37415,2.09031l-15.28384,15.28384c-0.6509,-0.24194 -1.35517,-0.37415 -2.09031,-0.37415c-3.31371,0 -6,2.68629 -6,6c0,3.31371 2.68629,6 6,6c3.31371,0 6,-2.68629 6,-6c0,-0.73514 -0.13221,-1.43941 -0.37415,-2.09031l14.87415,-14.87415l0,11.50851c-2.06553,0.94801 -3.5,3.03446 -3.5,5.45596c0,3.31371 2.68629,6 6,6c3.31371,0 6,-2.68629 6,-6c0,-2.42149 -1.43447,-4.50795 -3.5,-5.45596l0,-12.08808c2.06553,-0.94801 3.5,-3.03446 3.5,-5.45596c0,-2.42149 -1.43447,-4.50795 -3.5,-5.45596l0,-12.54404h10c2.76142,0 5,2.23858 5,5v48c0,2.76142 -2.23858,5 -5,5z"/>
          </svg>
          <span class="meta-version">{{ version || 'dev' }}</span>
          <span class="meta-sep">│</span>
          <span class="meta-path" :title="scanPath">{{ scanPath || '—' }}</span>
        </div>
      </div>
      <nav>
        <a @click="setView('dashboard')" :class="{ active: currentView === 'dashboard' }">
          <span class="nav-icon">◈</span>
          {{ t('nav.dashboard') }}
        </a>
        <a @click="setView('analytics')" :class="{ active: currentView === 'analytics' }">
          <span class="nav-icon">◉</span>
          {{ t('nav.analytics') }}
        </a>
        <a @click="setView('tokens')" :class="{ active: currentView === 'tokens' }">
          <span class="nav-icon">⟐</span>
          {{ t('nav.tokens') }}
        </a>
        <a @click="setView('repos')" :class="{ active: currentView === 'repos' }">
          <span class="nav-icon">▤</span>
          {{ t('nav.repos') }}
        </a>
        <a @click="setView('gitee')" :class="{ active: currentView === 'gitee' }">
          <span class="nav-icon">◆</span>
          {{ t('nav.gitee') }}
        </a>
        <a @click="setView('settings')" :class="{ active: currentView === 'settings' }">
          <span class="nav-icon">⚙</span>
          {{ t('nav.settings') }}
        </a>
        <!-- Matrix toggle -->
        <button @click="toggleMatrix" class="matrix-toggle" :class="{ active: matrixEnabled }" title="Toggle Matrix Rain">
          <span class="toggle-icon">{{ matrixEnabled ? '≋' : '≋' }}</span>
        </button>
        <button @click="toggleLanguage" class="lang-switcher" :title="locale === 'zh' ? 'Switch to English' : '切换到中文'">
          <span class="lang-icon">{{ locale === 'zh' ? '中' : 'EN' }}</span>
        </button>
        <a href="https://github.com/wsyqn6/gitstat" target="_blank" rel="noopener" class="github-link" :title="t('nav.github')">
          <svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
        </a>
      </nav>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <KeepAlive>
        <component :is="currentComponent" />
      </KeepAlive>
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <div class="footer-scanline"></div>
      <span>GITSTAT NETRUNNER EDITION</span>
      <span class="footer-sep">//</span>
      <span>"THE STREET FINDS ITS OWN USES FOR THINGS"</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, defineAsyncComponent, onMounted } from 'vue'
import { useI18n } from './i18n'
import * as api from './api'
import { loadScanPath } from './stores/data'
import MatrixRain from './components/MatrixRain.vue'
import BootSequence from './components/BootSequence.vue'

const Dashboard = defineAsyncComponent(() => import('./views/Dashboard.vue'))
const Analytics = defineAsyncComponent(() => import('./views/Analytics.vue'))
const TokenAnalytics = defineAsyncComponent(() => import('./views/TokenAnalytics.vue'))
const RepoSection = defineAsyncComponent(() => import('./views/RepoSection.vue'))
const Settings = defineAsyncComponent(() => import('./views/Settings.vue'))
const GiteeStats = defineAsyncComponent(() => import('./views/GiteeStats.vue'))

const componentMap = { dashboard: Dashboard, analytics: Analytics, tokens: TokenAnalytics, repos: RepoSection, gitee: GiteeStats, settings: Settings }

const { t, locale, setLocale } = useI18n()
const currentView = ref(localStorage.getItem('currentView') || 'gitee')
const currentComponent = computed(() => componentMap[currentView.value])
const scanPath = ref('')
const version = ref('')
const matrixEnabled = ref(localStorage.getItem('matrixRain') !== 'off')
const showBoot = ref(!localStorage.getItem('bootShown'))

const matrixOpacity = computed(() => matrixEnabled.value ? 0.07 : 0)

function cycleTheme() {
  const themes = ['default', 'amber', 'green']
  const current = localStorage.getItem('neonTheme') || 'default'
  const idx = themes.indexOf(current)
  const next = themes[(idx + 1) % themes.length]
  localStorage.setItem('neonTheme', next)
  applyTheme(next)
}

function applyTheme(name) {
  const root = document.documentElement
  const themes = {
    default: { '--neon-cyan': '#00f5ff', '--neon-magenta': '#ff00ff' },
    amber:   { '--neon-cyan': '#ffb800', '--neon-magenta': '#ff6600' },
    green:   { '--neon-cyan': '#00ff88', '--neon-magenta': '#00ffcc' },
  }
  const t = themes[name] || themes.default
  Object.entries(t).forEach(([k, v]) => root.style.setProperty(k, v))
}

function toggleMatrix() {
  matrixEnabled.value = !matrixEnabled.value
  localStorage.setItem('matrixRain', matrixEnabled.value ? 'on' : 'off')
}

onMounted(async () => {
  // Apply saved theme
  const theme = localStorage.getItem('neonTheme') || 'default'
  applyTheme(theme)

  try {
    const info = await api.getScanPath()
    scanPath.value = info.path
    version.value = info.version
  } catch (err) {
    console.error('Failed to load scan info:', err)
    try {
      await loadScanPath()
      const info = await api.getScanPath()
      scanPath.value = info.path
      version.value = info.version
    } catch {}
  }
})

function setView(view) {
  currentView.value = view
  localStorage.setItem('currentView', view)
}

function toggleLanguage() {
  setLocale(locale.value === 'zh' ? 'en' : 'zh')
}
</script>

<!-- Global design tokens -->
<style>
:root {
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --text-dim: #475569;
  --border-dim: rgba(0, 245, 255, 0.1);
  --border-strong: rgba(0, 245, 255, 0.3);
  --bg-panel: rgba(12, 18, 40, 0.7);
  --bg-card: rgba(0, 245, 255, 0.03);
  --bg-hover: rgba(0, 245, 255, 0.05);
  --accent-green: #00ff88;
  --accent-gold: #ffd700;
  --accent-red: #ef4444;
  --accent-purple: #a78bfa;
  --font-mono: 'Share Tech Mono', monospace;
  --font-display: 'Orbitron', sans-serif;
}

/* Unified cyberpunk scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(0, 245, 255, 0.15);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 245, 255, 0.3);
}
::-webkit-scrollbar-corner { background: transparent; }
</style>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* ══════════════════════════════════════════════════════════════
   HEADER
   ══════════════════════════════════════════════════════════════ */
.header {
  background: rgba(8, 12, 32, 0.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  padding: 1.25rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0, 245, 255, 0.2);
  box-shadow:
    0 4px 32px rgba(0, 0, 0, 0.4),
    0 -1px 0 rgba(0, 245, 255, 0.08) inset;
  position: relative;
  z-index: 100;
}

/* Header scanline */
.header-scanline {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    var(--neon-cyan),
    var(--neon-magenta),
    var(--neon-cyan),
    transparent
  );
  opacity: 0.8;
  box-shadow: 0 0 10px rgba(0, 245, 255, 0.5), 0 0 20px rgba(255, 0, 255, 0.3);
  animation: headerScanlinePulse 3s ease-in-out infinite;
}

@keyframes headerScanlinePulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.header-left {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.logo-container {
  position: relative;
}

.logo {
  margin: 0;
  font-family: 'Orbitron', sans-serif;
  font-weight: 900;
  font-size: 2rem;
  background: linear-gradient(135deg, var(--neon-cyan) 0%, #7800ff 50%, var(--neon-green) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 4px;
  position: relative;
  z-index: 1;
  cursor: pointer;
  user-select: none;
  transition: filter 0.3s;
}

.logo:hover {
  filter: brightness(1.3);
  animation: glitchText1 0.2s ease-in-out;
}

/* Glitch layers */
.logo::before,
.logo::after {
  content: 'GITSTAT';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--neon-cyan) 0%, #7800ff 50%, var(--neon-green) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  opacity: 0;
  z-index: -1;
}

.logo:hover::before {
  color: var(--neon-cyan);
  animation: glitchText1 0.15s infinite;
  opacity: 0.8;
  z-index: -1;
}

.logo:hover::after {
  color: var(--neon-magenta);
  animation: glitchText2 0.2s infinite;
  opacity: 0.8;
  z-index: -2;
}

.logo-subtitle {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.55rem;
  color: #64748b;
  letter-spacing: 3px;
  margin-top: 2px;
}

.logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 160%;
  height: 160%;
  background: radial-gradient(circle, rgba(0, 245, 255, 0.25) 0%, transparent 70%);
  filter: blur(24px);
  animation: logoPulse 3s ease-in-out infinite;
  pointer-events: none;
}

@keyframes logoPulse {
  0%, 100% { opacity: 0.4; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 0.7; transform: translate(-50%, -50%) scale(1.15); }
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.6rem;
  font-family: 'Share Tech Mono', monospace;
  color: #475569;
  margin-top: 0.1rem;
  max-width: 360px;
}

.git-icon { color: #f05033; flex-shrink: 0; }
.meta-version { color: #94a3b8; white-space: nowrap; }
.meta-sep { color: rgba(148, 163, 184, 0.25); }
.meta-path { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }

/* ══════════════════════════════════════════════════════════════
   NAVIGATION
   ══════════════════════════════════════════════════════════════ */
.header nav {
  display: flex;
  align-items: center;
}

.header nav a {
  color: #94a3b8;
  text-decoration: none;
  margin-left: 1.5rem;
  cursor: pointer;
  font-family: 'Orbitron', sans-serif;
  font-weight: 500;
  font-size: 0.8rem;
  letter-spacing: 1px;
  transition: all 0.3s;
  position: relative;
  padding: 0.5rem 0;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.nav-icon {
  font-size: 1.1rem;
  transition: all 0.3s;
}

.header nav a:hover {
  color: var(--neon-cyan);
  text-shadow: 0 0 8px var(--neon-cyan);
}

.header nav a:hover .nav-icon {
  transform: rotate(180deg);
  filter: drop-shadow(0 0 4px var(--neon-cyan));
}

.header nav a.active {
  color: var(--neon-cyan);
  font-weight: 700;
  text-shadow: 0 0 8px var(--neon-cyan);
}

.header nav a.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-magenta));
  box-shadow: 0 0 10px var(--neon-cyan), 0 0 20px var(--neon-magenta);
  animation: navSlideIn 0.3s ease-out;
}

@keyframes navSlideIn {
  from { width: 0; opacity: 0; }
  to { width: 100%; opacity: 1; }
}

/* Matrix Toggle */
.matrix-toggle {
  margin-left: 1rem;
  background: transparent;
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 6px;
  padding: 0.35rem 0.6rem;
  cursor: pointer;
  transition: all 0.3s;
  color: #475569;
  display: inline-flex;
  align-items: center;
}

.matrix-toggle.active {
  background: rgba(0, 245, 255, 0.1);
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
  box-shadow: 0 0 10px rgba(0, 245, 255, 0.2);
}

.matrix-toggle:hover {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 12px rgba(0, 245, 255, 0.2);
}

.toggle-icon {
  font-size: 0.9rem;
}

.lang-switcher {
  margin-left: 0.75rem;
  background: rgba(0, 245, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 6px;
  padding: 0.4rem 0.8rem;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.75rem;
  color: var(--neon-cyan);
  letter-spacing: 1px;
}

.lang-switcher:hover {
  background: rgba(0, 245, 255, 0.2);
  border-color: var(--neon-cyan);
  box-shadow: 0 0 16px rgba(0, 245, 255, 0.3);
  transform: translateY(-1px);
}

.lang-icon { font-weight: 700; }

.github-link {
  margin-left: 0.5rem;
  border: none;
  border-radius: 6px;
  padding: 0.4rem 0.5rem;
  cursor: pointer;
  transition: all 0.3s;
  color: #475569;
  display: inline-flex;
  align-items: center;
  text-decoration: none;
}

.github-link:hover {
  color: var(--neon-cyan);
  background: rgba(0, 245, 255, 0.1);
  box-shadow: 0 0 12px rgba(0, 245, 255, 0.2);
  transform: translateY(-1px);
}

/* ══════════════════════════════════════════════════════════════
   MAIN CONTENT
   ══════════════════════════════════════════════════════════════ */
.main-content {
  flex: 1;
  padding: 2rem;
  position: relative;
  z-index: 1;
}

/* ══════════════════════════════════════════════════════════════
   FOOTER
   ══════════════════════════════════════════════════════════════ */
.app-footer {
  padding: 1rem 2rem;
  text-align: center;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.6rem;
  color: #334155;
  letter-spacing: 2px;
  border-top: 1px solid rgba(0, 245, 255, 0.08);
  position: relative;
  z-index: 1;
}

.footer-scanline {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent);
  opacity: 0.3;
}

.footer-sep {
  margin: 0 0.5rem;
  color: #1e293b;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .header nav a {
    margin-left: 0.75rem;
    font-size: 0.7rem;
  }

  .main-content {
    padding: 1rem;
  }
}
</style>
