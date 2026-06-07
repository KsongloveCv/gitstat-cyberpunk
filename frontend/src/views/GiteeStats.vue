<template>
  <div class="gitee-page">
    <!-- ── Header ── -->
    <div class="page-header">
      <h2 class="page-title">
        <span class="title-icon">◆</span>
        {{ t('gitee.title') }}
      </h2>
      <p class="page-subtitle">{{ t('gitee.subtitle') }}</p>
      <div class="header-accent"></div>
    </div>

    <!-- ── Search Bar ── -->
    <div class="search-bar">
      <div class="search-input-wrap">
        <span class="search-prefix">gitee.com/</span>
        <input
          v-model="ownerName"
          class="search-input"
          :placeholder="t('gitee.searchPlaceholder')"
          @keyup.enter="scanRepos"
        />
      </div>
      <button
        class="search-btn"
        :disabled="!ownerName.trim() || loading"
        @click="scanRepos"
      >
        <span v-if="!loading" class="btn-content">
          <span class="btn-icon">⚡</span>
          {{ t('gitee.scanRepos') }}
        </span>
        <span v-else class="btn-loading">
          <span class="loading-dot"></span>
          {{ t('gitee.scanning') }}
        </span>
      </button>
    </div>

    <!-- ── Stats Overview Cards ── -->
    <div v-if="hasScanned" class="stats-grid">
      <!-- Skeleton loading -->
      <template v-if="loading">
        <div v-for="i in 4" :key="i" class="stat-card-ph">
          <div class="skeleton-circle stat-ph-icon"></div>
          <div class="skeleton-line w40 stat-ph-value"></div>
          <div class="skeleton-line w60 stat-ph-label"></div>
        </div>
      </template>
      <!-- Real data -->
      <template v-else>
        <StatCard
          :value="repos.length"
          :label="'Gitee Repos'"
          icon="▦"
          color="#00d4ff"
        />
        <StatCard
          :value="totalStars"
          :label="t('gitee.stars')"
          icon="⭐"
          color="#ffd700"
        />
        <StatCard
          :value="cachedRepos.length"
          :label="t('gitee.cachedRepos')"
          icon="💾"
          color="#a78bfa"
        />
        <StatCard
          :value="totalLangCount"
          :label="'Languages'"
          icon="◉"
          color="#00ff88"
        />
      </template>
    </div>

    <!-- ── No data state ── -->
    <div v-if="!hasScanned" class="empty-state">
      <div class="empty-icon">
        <span class="empty-hex">⬡</span>
      </div>
      <p class="empty-text">{{ t('gitee.noData') }}</p>
      <p class="empty-hint">支持 Gitee 用户和组织，如 vuejs、openEuler、dcloudio</p>
    </div>

    <!-- ── Main Content ── -->
    <div v-else class="gitee-content">
      <!-- ── Left: Repo List ── -->
      <div class="repo-list-panel panel-card">
        <div class="panel-header">
          <h3>
            <span class="panel-dot"></span>
            {{ t('gitee.repoList') }}
          </h3>
          <span v-if="repos.length > 0" class="panel-count">{{ repos.length }}</span>
        </div>
        <div class="panel-accent"></div>

        <!-- Loading state -->
        <div v-if="repos.length === 0 && loading" class="panel-loading">
          <div class="loading-spinner"></div>
          <p>{{ t('gitee.loading') }}</p>
        </div>

        <!-- Empty after scan -->
        <div v-else-if="repos.length === 0 && !loading" class="panel-empty">
          没有找到公开仓库
        </div>

        <!-- Repo cards -->
        <div v-else class="repo-cards">
          <div
            v-for="repo in repos"
            :key="repo.id"
            class="repo-card"
            :class="{ 'is-analyzing': analyzingPath === repo.cloneUrl }"
          >
            <!-- Card corners -->
            <div class="repo-corner-tl"></div>
            <div class="repo-corner-br"></div>

            <div class="repo-card-header">
              <a :href="repo.htmlUrl" target="_blank" class="repo-name" :title="repo.fullName">
                {{ repo.fullName }}
              </a>
              <span class="repo-lang" v-if="repo.language">{{ repo.language }}</span>
            </div>
            <p class="repo-desc" v-if="repo.description">{{ repo.description }}</p>
            <div class="repo-meta">
              <span class="meta-item">⭐ {{ repo.stars }}</span>
              <span class="meta-item">⑂ {{ repo.forks }}</span>
              <span class="meta-item">🕐 {{ formatDate(repo.pushedAt) }}</span>
            </div>
            <button
              class="clone-btn"
              :disabled="analyzingPath === repo.cloneUrl"
              @click="cloneAndAnalyze(repo)"
            >
              <span v-if="analyzingPath !== repo.cloneUrl" class="btn-content">
                <span class="btn-icon">⚡</span>
                {{ t('gitee.deepAnalyze') }}
              </span>
              <span v-else class="btn-content">
                <span class="loading-dot"></span>
                {{ t('gitee.analyzing') }}
              </span>
            </button>
          </div>
        </div>
      </div>

      <!-- ── Right: Analysis Panel ── -->
      <div class="analysis-panel panel-card">
        <div class="panel-header">
          <h3>
            <span class="panel-dot mag"></span>
            📊 深度分析结果
          </h3>
          <span v-if="cachedRepos.length > 0" class="panel-count">{{ cachedRepos.length }}</span>
        </div>
        <div class="panel-accent mag"></div>

        <!-- Empty state -->
        <div v-if="cachedRepos.length === 0" class="panel-empty">
          <span class="empty-icon-sm">📦</span>
          <p>{{ t('gitee.cloneFirst') }}</p>
        </div>

        <!-- Cached repos -->
        <div v-for="(cr, idx) in cachedRepos" :key="idx" class="cached-repo">
          <div class="cached-header">
            <span class="cached-name">[Gitee] {{ cr.name }}</span>
            <button class="remove-btn" @click="removeRepo(cr.path, idx)">✕ {{ t('gitee.removeRepo') }}</button>
          </div>

          <!-- Stats row -->
          <div v-if="cr.stats" class="stats-row">
            <div class="mini-stat">
              <span class="mini-val">{{ cr.stats.commitCount || 0 }}</span>
              <span class="mini-label">{{ t('gitee.totalCommits') }}</span>
            </div>
            <div class="mini-stat">
              <span class="mini-val add">+{{ cr.stats.totalAdditions || 0 }}</span>
              <span class="mini-label">{{ t('gitee.totalAdditions') }}</span>
            </div>
            <div class="mini-stat">
              <span class="mini-val del">-{{ cr.stats.totalDeletions || 0 }}</span>
              <span class="mini-label">{{ t('gitee.totalDeletions') }}</span>
            </div>
            <div class="mini-stat">
              <span class="mini-val">{{ cr.stats.contributorCount || 0 }}</span>
              <span class="mini-label">{{ t('gitee.activeAuthors') }}</span>
            </div>
          </div>

          <!-- Analyze button -->
          <button
            v-if="!cr.analyzed"
            class="analyze-btn"
            :disabled="analyzingRepoPath === cr.path"
            @click="runDeepAnalyze(cr)"
          >
            <span v-if="analyzingRepoPath !== cr.path" class="btn-content">
              <span class="btn-icon">🔬</span>
              深度分析代码结构
            </span>
            <span v-else class="btn-content">
              <span class="loading-dot"></span>
              {{ t('gitee.analyzing') }}
            </span>
          </button>

          <!-- Analysis result -->
          <div v-if="cr.analyzed && cr.analysis" class="analysis-result">
            <div class="analysis-grid">
              <div class="analysis-item">
                <span class="a-val">{{ cr.analysis.branchCount }}</span>
                <span class="a-label">分支数</span>
              </div>
              <div class="analysis-item">
                <span class="a-val">{{ cr.analysis.fileCount }}</span>
                <span class="a-label">文件数</span>
              </div>
              <div class="analysis-item">
                <span class="a-val">{{ cr.analysis.totalLines.toLocaleString() }}</span>
                <span class="a-label">总行数</span>
              </div>
            </div>
            <div class="analysis-langs" v-if="cr.analysis.languages?.length">
              <span
                v-for="lang in cr.analysis.languages.slice(0, 6)"
                :key="lang.name"
                class="lang-tag"
              >{{ lang.name }} {{ lang.percent }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useI18n } from '../i18n'
import * as api from '../api'
import StatCard from '../components/StatCard.vue'

const { t } = useI18n()

const ownerName = ref('')
const loading = ref(false)
const hasScanned = ref(false)
const repos = ref([])
const analyzingPath = ref('')
const analyzingRepoPath = ref('')
const cachedRepos = reactive([])

// Computed overview stats
const totalStars = computed(() => repos.value.reduce((s, r) => s + (r.stars || 0), 0))
const totalLangCount = computed(() => {
  const langs = new Set(repos.value.map(r => r.language).filter(Boolean))
  return langs.size
})

async function scanRepos() {
  const owner = ownerName.value.trim()
  if (!owner) return

  loading.value = true
  hasScanned.value = true
  try {
    repos.value = await api.getGiteeRepos(owner)
  } catch (err) {
    console.error('Scan Gitee repos failed:', err)
    repos.value = []
  } finally {
    loading.value = false
  }
}

async function cloneAndAnalyze(repo) {
  analyzingPath.value = repo.cloneUrl
  try {
    const result = await api.cloneGiteeRepo(
      repo.owner || repo.fullName.split('/')[0],
      repo.name,
      repo.cloneUrl
    )
    const stats = await api.getRepoStats(result.path)
    const commits = stats.recentCommits || []
    const contributors = stats.contributors || []
    const totalAdditions = commits.reduce((sum, c) => sum + (c.additions || 0), 0)
    const totalDeletions = commits.reduce((sum, c) => sum + (c.deletions || 0), 0)

    cachedRepos.push({
      path: result.path,
      name: result.name,
      cloneUrl: repo.cloneUrl,
      analyzed: false,
      analysis: null,
      stats: {
        commitCount: result.commitCount,
        totalAdditions,
        totalDeletions,
        contributorCount: contributors.length,
      },
    })
  } catch (err) {
    console.error('Clone failed:', err)
    alert(`克隆失败: ${err.message}`)
  } finally {
    analyzingPath.value = ''
  }
}

async function runDeepAnalyze(cr) {
  analyzingRepoPath.value = cr.path
  try {
    const analysis = await api.analyzeGiteeRepo(cr.path)
    cr.analyzed = true
    cr.analysis = analysis
  } catch (err) {
    console.error('Analyze failed:', err)
  } finally {
    analyzingRepoPath.value = ''
  }
}

async function removeRepo(path, idx) {
  try {
    await api.removeGiteeRepo(path)
    cachedRepos.splice(idx, 1)
  } catch (err) {
    console.error('Remove failed:', err)
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now - d
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 30) return `${days} 天前`
  if (days < 365) return `${Math.floor(days / 30)} 个月前`
  return `${Math.floor(days / 365)} 年前`
}
</script>

<style scoped>
.gitee-page {
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Header ── */
.page-header {
  margin-bottom: 2rem;
  text-align: center;
  position: relative;
}
.page-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.8rem;
  color: var(--neon-cyan);
  text-shadow: 0 0 12px rgba(0, 245, 255, 0.3);
  margin: 0 0 0.5rem;
  letter-spacing: 2px;
}
.title-icon { font-size: 1.6rem; }
.page-subtitle {
  color: #64748b;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
  margin: 0;
}
.header-accent {
  width: 80px;
  height: 2px;
  margin: 1rem auto 0;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-magenta));
  box-shadow: 0 0 8px var(--neon-cyan), 0 0 16px var(--neon-magenta);
}

/* ── Search ── */
.search-bar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2rem;
  justify-content: center;
}
.search-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.search-prefix {
  position: absolute;
  left: 1rem;
  color: #475569;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.85rem;
  z-index: 1;
  pointer-events: none;
}
.search-input {
  width: 380px;
  padding: 0.75rem 1.25rem 0.75rem 7.5rem;
  background: rgba(8, 12, 32, 0.8);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 8px;
  color: #e2e8f0;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.9rem;
  outline: none;
  transition: all 0.3s;
}
.search-input:focus {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.15);
}
.search-input::placeholder { color: #475569; }

.search-btn {
  padding: 0.75rem 1.5rem;
  background: rgba(0, 245, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.4);
  border-radius: 8px;
  color: var(--neon-cyan);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s;
  letter-spacing: 1px;
}
.search-btn:hover:not(:disabled) {
  background: rgba(0, 245, 255, 0.2);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
  transform: translateY(-1px);
}
.search-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-content { display: flex; align-items: center; gap: 0.4rem; justify-content: center; }
.btn-icon { font-size: 1rem; }

/* Loading dot animation */
.loading-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--neon-cyan);
  display: inline-block;
  animation: dotPulse 0.8s ease-in-out infinite;
  box-shadow: 0 0 8px var(--neon-cyan);
}
@keyframes dotPulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}
.btn-loading { display: flex; align-items: center; gap: 0.5rem; }

/* ── Stat Cards Grid ── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}
@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Skeleton placeholders (matching Dashboard) */
.stat-card-ph {
  background: rgba(12, 18, 40, 0.7);
  backdrop-filter: blur(24px);
  padding: 1.75rem 1.5rem;
  border-radius: 12px;
  text-align: center;
  border: 1px solid rgba(0, 245, 255, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.stat-ph-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-bottom: 0.5rem;
}
.stat-ph-value {
  height: 40px;
  width: 50%;
  border-radius: 8px;
}
.stat-ph-label {
  height: 14px;
  width: 60%;
  border-radius: 4px;
}
.w40 { width: 40%; }
.w50 { width: 50%; }
.w60 { width: 60%; }

.skeleton-circle {
  background: linear-gradient(90deg, rgba(0,245,255,0.06) 25%, rgba(0,245,255,0.12) 50%, rgba(0,245,255,0.06) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 50%;
}
.skeleton-line {
  background: linear-gradient(90deg, rgba(0,245,255,0.06) 25%, rgba(0,245,255,0.12) 50%, rgba(0,245,255,0.06) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Empty State ── */
.empty-state {
  text-align: center;
  padding: 6rem 2rem;
}
.empty-hex {
  font-size: 5rem;
  display: inline-block;
  color: rgba(0, 245, 255, 0.15);
  animation: hexRotate 8s linear infinite;
  filter: drop-shadow(0 0 20px rgba(0, 245, 255, 0.1));
}
@keyframes hexRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.empty-text {
  color: #94a3b8;
  font-family: 'Share Tech Mono', monospace;
  font-size: 1rem;
  margin: 1.5rem 0 0.5rem;
}
.empty-hint {
  color: #475569;
  font-size: 0.75rem;
}

/* ── Content Grid ── */
.gitee-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  align-items: start;
}
@media (max-width: 768px) {
  .gitee-content { grid-template-columns: 1fr; }
}

/* ── Panel Card ── */
.panel-card {
  background: rgba(12, 18, 40, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 245, 255, 0.15);
  border-radius: 12px;
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.panel-header h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1rem;
  color: #94a3b8;
  margin: 0;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.panel-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--neon-cyan);
  box-shadow: 0 0 8px var(--neon-cyan);
  display: inline-block;
}
.panel-dot.mag {
  background: var(--neon-magenta);
  box-shadow: 0 0 8px var(--neon-magenta);
}
.panel-count {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.8rem;
  color: var(--neon-cyan);
  background: rgba(0, 245, 255, 0.08);
  padding: 2px 10px;
  border-radius: 12px;
  border: 1px solid rgba(0, 245, 255, 0.2);
}
.panel-accent {
  height: 1px;
  background: linear-gradient(90deg, var(--neon-cyan), transparent);
  margin-bottom: 1rem;
  opacity: 0.4;
}
.panel-accent.mag {
  background: linear-gradient(90deg, var(--neon-magenta), transparent);
}
.panel-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: #64748b;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.85rem;
}
.empty-icon-sm { font-size: 2rem; display: block; margin-bottom: 0.5rem; }

.panel-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem 1rem;
  color: var(--neon-cyan);
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
}
.loading-spinner {
  width: 40px; height: 40px;
  border: 2px solid rgba(0, 245, 255, 0.08);
  border-top-color: var(--neon-cyan);
  border-right-color: var(--neon-magenta);
  border-radius: 50%;
  animation: cyberspin 1s linear infinite;
  box-shadow: 0 0 16px rgba(0, 245, 255, 0.2);
}
@keyframes cyberspin {
  to { transform: rotate(360deg); }
}

/* ── Repo Cards ── */
.repo-cards {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 600px;
  overflow-y: auto;
  padding-right: 4px;
}
.repo-cards::-webkit-scrollbar { width: 4px; }
.repo-cards::-webkit-scrollbar-track { background: transparent; }
.repo-cards::-webkit-scrollbar-thumb {
  background: rgba(0, 245, 255, 0.15);
  border-radius: 2px;
}

.repo-card {
  background: rgba(0, 245, 255, 0.02);
  border: 1px solid rgba(0, 245, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}
.repo-card::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 8px;
  background: radial-gradient(ellipse at 0% 0%, var(--neon-cyan) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.4s;
  z-index: 0;
}
.repo-card:hover {
  border-color: rgba(0, 245, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 24px rgba(0, 245, 255, 0.05);
}
.repo-card:hover::before { opacity: 0.04; }
.repo-card.is-analyzing {
  border-color: rgba(255, 0, 255, 0.5);
  box-shadow: 0 0 20px rgba(255, 0, 255, 0.08);
}

/* Card corners */
.repo-corner-tl {
  position: absolute; top: 0; left: 0;
  width: 12px; height: 12px;
  border-top: 1px solid rgba(0, 245, 255, 0.3);
  border-left: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 4px 0 2px 0;
  opacity: 0;
  z-index: 2;
  transition: opacity 0.3s;
}
.repo-corner-br {
  position: absolute; bottom: 0; right: 0;
  width: 12px; height: 12px;
  border-bottom: 1px solid rgba(0, 245, 255, 0.3);
  border-right: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 0 2px 0 4px;
  opacity: 0;
  z-index: 2;
  transition: opacity 0.3s;
}
.repo-card:hover .repo-corner-tl,
.repo-card:hover .repo-corner-br { opacity: 1; }

.repo-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
  position: relative;
  z-index: 1;
}
.repo-name {
  color: #e2e8f0;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  transition: color 0.3s;
}
.repo-name:hover { color: var(--neon-cyan); }
.repo-lang {
  font-size: 0.6rem;
  padding: 2px 8px;
  background: rgba(0, 245, 255, 0.08);
  border: 1px solid rgba(0, 245, 255, 0.15);
  border-radius: 4px;
  color: var(--neon-cyan);
  font-family: 'Share Tech Mono', monospace;
}
.repo-desc {
  color: #64748b;
  font-size: 0.75rem;
  margin: 0.4rem 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  position: relative;
  z-index: 1;
}
.repo-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.7rem;
  color: #475569;
  font-family: 'Share Tech Mono', monospace;
  margin: 0.5rem 0;
  position: relative;
  z-index: 1;
}
.meta-item { display: flex; align-items: center; gap: 0.2rem; }

.clone-btn {
  width: 100%;
  padding: 0.5rem 1rem;
  background: rgba(0, 245, 255, 0.06);
  border: 1px solid rgba(0, 245, 255, 0.2);
  border-radius: 6px;
  color: var(--neon-cyan);
  cursor: pointer;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
  transition: all 0.3s;
  position: relative;
  z-index: 1;
}
.clone-btn:hover:not(:disabled) {
  background: rgba(0, 245, 255, 0.12);
  box-shadow: 0 0 12px rgba(0, 245, 255, 0.1);
  border-color: var(--neon-cyan);
}
.clone-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── Analysis Panel ── */
.cached-repo {
  border: 1px solid rgba(255, 0, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  background: rgba(255, 0, 255, 0.02);
  transition: border-color 0.3s;
}
.cached-repo:hover { border-color: rgba(255, 0, 255, 0.2); }
.cached-repo:last-child { margin-bottom: 0; }

.cached-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.cached-name {
  color: var(--neon-cyan);
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.9rem;
}
.remove-btn {
  background: transparent;
  border: 1px solid rgba(255, 0, 0, 0.2);
  border-radius: 4px;
  color: #ef4444;
  cursor: pointer;
  font-size: 0.65rem;
  padding: 3px 8px;
  transition: all 0.3s;
  font-family: 'Share Tech Mono', monospace;
}
.remove-btn:hover {
  background: rgba(255, 0, 0, 0.1);
  border-color: #ef4444;
}

/* Mini stat row */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}
.mini-stat {
  text-align: center;
  padding: 0.6rem 0.4rem;
  background: rgba(0, 245, 255, 0.03);
  border: 1px solid rgba(0, 245, 255, 0.06);
  border-radius: 6px;
  transition: all 0.3s;
}
.mini-stat:hover {
  border-color: rgba(0, 245, 255, 0.2);
  background: rgba(0, 245, 255, 0.05);
}
.mini-val {
  display: block;
  font-size: 1.1rem;
  font-weight: 700;
  color: #e2e8f0;
  font-family: 'Orbitron', sans-serif;
}
.mini-val.add { color: #10b981; text-shadow: 0 0 6px rgba(16, 185, 129, 0.3); }
.mini-val.del { color: #ef4444; text-shadow: 0 0 6px rgba(239, 68, 68, 0.3); }
.mini-label {
  font-size: 0.6rem;
  color: #64748b;
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 0.5px;
}

/* Analyze button */
.analyze-btn {
  width: 100%;
  margin-top: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 0, 255, 0.04);
  border: 1px solid rgba(255, 0, 255, 0.2);
  border-radius: 6px;
  color: var(--neon-magenta);
  cursor: pointer;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
  transition: all 0.3s;
}
.analyze-btn:hover:not(:disabled) {
  background: rgba(255, 0, 255, 0.1);
  box-shadow: 0 0 16px rgba(255, 0, 255, 0.12);
  border-color: var(--neon-magenta);
}
.analyze-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Analysis result */
.analysis-result {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(0, 245, 255, 0.02);
  border: 1px solid rgba(0, 245, 255, 0.06);
  border-radius: 6px;
  animation: fadeIn 0.3s ease-out;
}
.analysis-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.analysis-item {
  text-align: center;
  padding: 0.4rem;
}
.a-val {
  display: block;
  font-size: 1.1rem;
  font-weight: 700;
  color: #e2e8f0;
  font-family: 'Orbitron', sans-serif;
}
.a-label {
  font-size: 0.6rem;
  color: #64748b;
  font-family: 'Share Tech Mono', monospace;
}
.analysis-langs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.lang-tag {
  font-size: 0.6rem;
  padding: 2px 8px;
  background: rgba(0, 245, 255, 0.06);
  border: 1px solid rgba(0, 245, 255, 0.12);
  border-radius: 4px;
  color: #94a3b8;
  font-family: 'Share Tech Mono', monospace;
}
</style>
