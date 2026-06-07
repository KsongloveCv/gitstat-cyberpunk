# GitStat 项目优化报告

**日期:** 2026-06-07 | **分支:** feature/gitee-stats

---

## 🔴 高优先级

### 1. 零测试覆盖
整个项目没有任何测试文件（`.test.*` / `.spec.*`）。

**影响:** 每次改动都可能引入回归 bug，CSS 语法错误（如 Dashboard.vue 的孤立 `}`）直到构建才暴露。

**建议:**
- 后端：用 `pytest` 覆盖 `git_exec`, `parse_git_log`, `gitee_list_repos`, `aggregate_overview` 等核心函数
- 前端：用 `vitest` 覆盖 `formatDate`, `i18n`, API 函数

### 2. 后端单文件巨石（2117 行）
`backend-py/main.py` 包含所有逻辑 — API 路由、数据聚合、Token 统计、天气代理、Gitee 代理、Git 操作、Streak 计算等。

**影响:** 难以维护、测试、审查。每次改一个功能都要触碰 2000+ 行文件。

**建议拆分:**
```
backend-py/
├── main.py          # FastAPI app + 路由注册（~100 行）
├── config.py        # VERSION, 常量
├── git_utils.py     # git_exec, parse_git_log, run_git_log
├── store.py         # Store 类
├── scanner.py       # discover_repos, analyze_repo_deep
├── aggregator.py    # aggregate_* 系列函数
├── gitee.py         # Gitee API + clone + 路由
├── weather.py       # Open-Meteo 代理
├── token_stats.py   # Token 消耗解析与统计
├── streak.py        # 连续贡献计算
└── routes.py        # 所有 @app 路由
```

### 3. 前端 API 层严重代码重复
`api/index.js` 中同一个过滤模式重复 10 次：
```javascript
if (repos.length > 0 && !repos.includes('all')) {
  repos.forEach(repo => params.append('repo', repo))
}
```

**建议:** 提取为通用函数：
```javascript
function appendRepoParams(params, repos) {
  if (repos.length > 0 && !repos.includes('all')) {
    repos.forEach(repo => params.append('repo', repo))
  }
  return params
}
```

---

## 🟡 中优先级

### 4. 静默异常吞没（7 处）
```python
except Exception:   # ← 没有任何日志
    return ""
```
在 `git_exec`、`gitee_api`、weather 等函数中，异常被完全吞没，排查问题极困难。

**建议:** 至少加 `print(f"Warning: {e}", file=sys.stderr)` 或引入 `logging`。

### 5. echarts 整包加载（631KB）
前端加载整个 echarts 库，但仪表盘只用了折线图。

**建议:** 按需引入：
```javascript
// 当前
import echarts from '../utils/echarts'
// 改为
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])
```
预计可减少 ~400KB 的 JS 体积。

### 6. 无缓存机制
每次请求都重新执行 `git log`（开销很大的子进程调用），完全没有任何缓存。

**建议:**
- `run_git_log` 结果加 TTL 缓存（5 分钟）
- `analyze_repo_deep` 结果持久化到磁盘
- 静态数据（语言映射、天气 WMO code 表）内存常驻即可

### 7. CSS 颜色/样式重复
Dashboard.vue、GiteeStats.vue 中大量颜色硬编码：
- `#64748b` 出现 8 次
- `#a0aec0` 出现 8 次
- `#00d4ff` 出现 6 次

**建议:** 统一用 CSS 变量（已有 `--neon-cyan`、`--neon-magenta`），扩展更多语义变量：
```css
--text-primary: #e2e8f0;
--text-secondary: #94a3b8;
--text-muted: #64748b;
--border-dim: rgba(0, 245, 255, 0.1);
--bg-panel: rgba(12, 18, 40, 0.7);
```

---

## 🟢 低优先级

### 8. Gitee 页面缺少分页
API 支持 `page`/`perPage` 参数，但前端未使用。对于有数百个仓库的组织，一次加载体验差。

**建议:** 加简单的"加载更多"或分页控件。

### 9. Gitee API 无认证支持
仅支持公开仓库访问，速率限制 5000/小时。无法查看私有仓库。

**建议:** 支持可选的 Personal Access Token 配置。

### 10. 深度分析重复执行无防护
同一个仓库可以多次点击"深度分析"，但 clone 步骤会重复执行。`analyze_repo_deep` 结果已缓存但 clone 检查逻辑可以改进。

### 11. 前端状态管理混合
`stores/data.js` 混合了仪表盘数据、仓库信息、天气状态等。没有按功能域分离。

**建议:** 按域拆分 store：
```
stores/
├── dashboard.js   # dashboard 相关状态
├── repos.js       # 仓库信息
├── gitee.js       # Gitee 相关
└── weather.js     # 天气
```

### 12. 组件缺少 Props 验证
Vue 组件未使用 `defineProps` 的 `validator` 和 `required` 标记，类型安全性依赖人工检查。

---

## 📊 汇总

| # | 问题 | 影响范围 | 优先级 |
|---|------|---------|--------|
| 1 | 零测试 | 全局 | 🔴 高 |
| 2 | 后端单文件巨石 | 后端 | 🔴 高 |
| 3 | API 层代码重复 | 前端 | 🔴 高 |
| 4 | 静默异常吞没 | 后端 | 🟡 中 |
| 5 | echarts 全量加载 | 前端性能 | 🟡 中 |
| 6 | 无缓存机制 | 后端性能 | 🟡 中 |
| 7 | CSS 颜色重复 | 前端 | 🟡 中 |
| 8 | Gitee 无分页 | 功能 | 🟢 低 |
| 9 | 无认证支持 | 功能 | 🟢 低 |
| 10 | 分析重复执行 | 功能 | 🟢 低 |
| 11 | Store 混合 | 前端架构 | 🟢 低 |
| 12 | Props 验证缺失 | 前端质量 | 🟢 低 |
