<template>
  <div class="gitee-page">
    <!-- Header -->
    <div class="page-header">
      <h2 class="page-title">
        <span class="title-icon">◆</span>
        {{ t('gitee.title') }}
      </h2>
      <p class="page-subtitle">{{ t('gitee.subtitle') }}</p>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <input
        v-model="ownerName"
        class="search-input"
        :placeholder="t('gitee.searchPlaceholder')"
        @keyup.enter="scanRepos"
      />
      <button
        class="search-btn"
        :disabled="!ownerName.trim() || loading"
        @click="scanRepos"
      >
        <span v-if="!loading">{{ t('gitee.scanRepos') }}</span>
        <span v-else class="btn-loading">⚡ {{ t('gitee.scanning') }}</span>
      </button>
    </div>

    <!-- No data state -->
    <div v-if="!hasScanned" class="empty-state">
      <div class="empty-icon">🔍</div>
      <p>{{ t('gitee.noData') }}</p>
    </div>

    <!-- Main content -->
    <div v-else class="gitee-content">
      <!-- Repo List -->
      <div class="repo-list-panel">
        <h3 class="panel-title">{{ t('gitee.repoList') }}</h3>
        <div v-if="repos.length === 0 && loading" class="loading-state">
          {{ t('gitee.loading') }}
        </div>
        <div v-else-if="repos.length === 0" class="empty-state small">
          没有找到公开仓库
        </div>
        <div v-else class="repo-cards">
          <div
            v-for="repo in repos"
            :key="repo.id"
            class="repo-card"
            :class="{ 'is-analyzing': analyzingPath === repo.cloneUrl }"
          >
            <div class="repo-card-header">
              <span class="repo-name">{{ repo.fullName }}</span>
              <span class="repo-lang" v-if="repo.language">{{ repo.language }}</span>
            </div>
            <p class="repo-desc" v-if="repo.description">{{ repo.description }}</p>
            <div class="repo-meta">
              <span>⭐ {{ repo.stars }}</span>
              <span>🕐 {{ formatDate(repo.pushedAt) }}</span>
            </div>
            <div class="repo-actions">
              <button
                class="action-btn clone-btn"
                :disabled="analyzingPath === repo.cloneUrl"
                @click="cloneAndAnalyze(repo)"
              >
                <span v-if="analyzingPath !== repo.cloneUrl">{{ t('gitee.deepAnalyze') }}</span>
                <span v-else>⚡ {{ t('gitee.analyzing') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Analysis Results Panel -->
      <div class="analysis-panel">
        <h3 class="panel-title">📊 深度分析结果</h3>
        <div v-if="cachedRepos.length === 0" class="empty-state small">
          <p>{{ t('gitee.cloneFirst') }}</p>
        </div>

        <div v-for="(cr, idx) in cachedRepos" :key="idx" class="cached-repo">
          <div class="cached-header">
            <span class="cached-name">[Gitee] {{ cr.name }}</span>
            <button class="remove-btn" @click="removeRepo(cr.path, idx)">✕ {{ t('gitee.removeRepo') }}</button>
          </div>

          <!-- Overview stats -->
          <div v-if="cr.stats" class="stats-row">
            <div class="stat-item">
              <span class="stat-val">{{ cr.stats.commitCount || 0 }}</span>
              <span class="stat-label">{{ t('gitee.totalCommits') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-val add">+{{ cr.stats.totalAdditions || 0 }}</span>
              <span class="stat-label">{{ t('gitee.totalAdditions') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-val del">-{{ cr.stats.totalDeletions || 0 }}</span>
              <span class="stat-label">{{ t('gitee.totalDeletions') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-val">{{ cr.stats.contributorCount || 0 }}</span>
              <span class="stat-label">{{ t('gitee.activeAuthors') }}</span>
            </div>
          </div>

          <!-- Analyze button -->
          <button
            v-if="!cr.analyzed"
            class="action-btn analyze-btn"
            :disabled="analyzingRepoPath === cr.path"
            @click="runDeepAnalyze(cr)"
          >
            <span v-if="analyzingRepoPath !== cr.path">🔬 深度分析代码结构</span>
            <span v-else>⚡ {{ t('gitee.analyzing') }}</span>
          </button>

          <!-- Analysis result -->
          <div v-if="cr.analyzed && cr.analysis" class="analysis-result">
            <div class="analysis-row">
              <span class="alabel">分支数</span>
              <span>{{ cr.analysis.branchCount }}</span>
            </div>
            <div class="analysis-row">
              <span class="alabel">文件数</span>
              <span>{{ cr.analysis.fileCount }}</span>
            </div>
            <div class="analysis-row">
              <span class="alabel">总行数</span>
              <span>{{ cr.analysis.totalLines.toLocaleString() }}</span>
            </div>
            <div class="analysis-langs" v-if="cr.analysis.languages?.length">
              <span
                v-for="lang in cr.analysis.languages.slice(0, 5)"
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
import { ref, reactive } from 'vue'
import { useI18n } from '../i18n'
import * as api from '../api'

const { t } = useI18n()

const ownerName = ref('')
const loading = ref(false)
const hasScanned = ref(false)
const repos = ref([])
const analyzingPath = ref('')
const analyzingRepoPath = ref('')
const cachedRepos = reactive([])

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
    const result = await api.cloneGiteeRepo(repo.owner || repo.fullName.split('/')[0], repo.name, repo.cloneUrl)
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
}

/* ── Header ── */
.page-header {
  margin-bottom: 2rem;
  text-align: center;
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
}

/* ── Search ── */
.search-bar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2rem;
  justify-content: center;
}
.search-input {
  width: 400px;
  padding: 0.75rem 1.25rem;
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
}
.search-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Empty / Loading ── */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #94a3b8;
  font-family: 'Share Tech Mono', monospace;
}
.empty-icon { font-size: 3rem; margin-bottom: 1rem; }
.empty-state.small { padding: 2rem 1rem; font-size: 0.85rem; }
.loading-state {
  text-align: center;
  padding: 2rem;
  color: var(--neon-cyan);
  font-family: 'Share Tech Mono', monospace;
}

/* ── Content ── */
.gitee-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  align-items: start;
}

.panel-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1rem;
  color: #94a3b8;
  margin: 0 0 1rem;
  letter-spacing: 1px;
}

/* ── Repo Cards ── */
.repo-list-panel {
  background: rgba(8, 12, 32, 0.5);
  border: 1px solid rgba(0, 245, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
}
.repo-cards {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 600px;
  overflow-y: auto;
}
.repo-card {
  background: rgba(0, 245, 255, 0.03);
  border: 1px solid rgba(0, 245, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.3s;
}
.repo-card:hover {
  border-color: rgba(0, 245, 255, 0.3);
  box-shadow: 0 0 16px rgba(0, 245, 255, 0.05);
}
.repo-card.is-analyzing {
  border-color: rgba(255, 0, 255, 0.5);
  box-shadow: 0 0 16px rgba(255, 0, 255, 0.1);
}
.repo-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
}
.repo-name {
  color: #e2e8f0;
  font-weight: 600;
  font-size: 0.95rem;
}
.repo-lang {
  font-size: 0.65rem;
  padding: 2px 8px;
  background: rgba(0, 245, 255, 0.1);
  border-radius: 4px;
  color: var(--neon-cyan);
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
}
.repo-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.7rem;
  color: #475569;
  font-family: 'Share Tech Mono', monospace;
  margin: 0.5rem 0;
}
.repo-actions {
  margin-top: 0.5rem;
}
.action-btn {
  width: 100%;
  padding: 0.5rem 1rem;
  background: rgba(0, 245, 255, 0.08);
  border: 1px solid rgba(0, 245, 255, 0.25);
  border-radius: 6px;
  color: var(--neon-cyan);
  cursor: pointer;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
  transition: all 0.3s;
}
.action-btn:hover:not(:disabled) {
  background: rgba(0, 245, 255, 0.15);
  box-shadow: 0 0 12px rgba(0, 245, 255, 0.1);
}
.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── Analysis Panel ── */
.analysis-panel {
  background: rgba(8, 12, 32, 0.5);
  border: 1px solid rgba(255, 0, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  min-height: 200px;
}
.cached-repo {
  border: 1px solid rgba(255, 0, 255, 0.15);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  background: rgba(255, 0, 255, 0.02);
}
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
  border: 1px solid rgba(255, 0, 0, 0.3);
  border-radius: 4px;
  color: #ef4444;
  cursor: pointer;
  font-size: 0.7rem;
  padding: 4px 8px;
  transition: all 0.3s;
}
.remove-btn:hover {
  background: rgba(255, 0, 0, 0.1);
  border-color: #ef4444;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}
.stat-item {
  text-align: center;
  padding: 0.5rem;
  background: rgba(0, 245, 255, 0.03);
  border-radius: 6px;
}
.stat-val {
  display: block;
  font-size: 1.2rem;
  font-weight: 700;
  color: #e2e8f0;
  font-family: 'Orbitron', sans-serif;
}
.stat-val.add { color: #10b981; }
.stat-val.del { color: #ef4444; }
.stat-label {
  font-size: 0.6rem;
  color: #64748b;
  font-family: 'Share Tech Mono', monospace;
}

.analyze-btn {
  margin-top: 0.5rem;
  border-color: rgba(255, 0, 255, 0.3);
  color: var(--neon-magenta);
}
.analyze-btn:hover:not(:disabled) {
  background: rgba(255, 0, 255, 0.1);
  box-shadow: 0 0 12px rgba(255, 0, 255, 0.1);
}

.analysis-result {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(0, 245, 255, 0.03);
  border-radius: 6px;
}
.analysis-row {
  display: flex;
  justify-content: space-between;
  padding: 0.3rem 0;
  font-size: 0.8rem;
  color: #94a3b8;
  border-bottom: 1px solid rgba(0, 245, 255, 0.05);
}
.alabel { color: #64748b; }
.analysis-langs {
  margin-top: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.lang-tag {
  font-size: 0.6rem;
  padding: 2px 8px;
  background: rgba(0, 245, 255, 0.08);
  border: 1px solid rgba(0, 245, 255, 0.15);
  border-radius: 4px;
  color: #94a3b8;
}

@media (max-width: 768px) {
  .gitee-content { grid-template-columns: 1fr; }
  .search-input { width: 100%; }
  .search-bar { flex-direction: column; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
}
</style>
