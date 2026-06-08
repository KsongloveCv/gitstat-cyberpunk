# GitStat 功能扩展提案

**日期:** 2026-06-08 | **当前端点数:** 36 API + 6 页面

---

## 一、代码智能（3 项）

### 1. 🔥 文件热点分析（Code Churn）
**是什么:** 统计哪些文件变更最频繁，识别代码库中的"热点"区域（bug 高发区）。

**实现:**
- 后端: 解析 `git log --numstat` 输出，按文件路径聚合新增/删除行数
- 前端: 新增热力图组件，Top 20 高频变更文件列表
- API: `GET /api/stats/file-churn?days=30`

**价值:** 识别需要重构的模块，指导 code review 重点。

### 2. ⏰ 提交时段分析
**是什么:** 展示团队的编码时间规律 — 几点最活跃、周几提交最多。

**实现:**
- 后端: 从 commit date 提取 hour + weekday，按 24h×7d 矩阵聚合
- 前端: ECharts 热力图日历（复用 CalendarView 组件），像 GitHub 贡献图
- API: `GET /api/stats/commit-heatmap?email=`

**价值:** 了解团队节奏，安排 code review 和协作时间。

### 3. 📏 提交质量评分
**是什么:** 自动评估提交信息质量：是否遵循 Conventional Commits 规范、消息长度、是否包含描述。

**实现:**
- 后端: 检查提交信息格式（`feat:`/`fix:`/`chore:` 等前缀），统计比例
- 前端: 仪表盘卡片显示"规范提交占比"
- API: `GET /api/stats/commit-quality`

**价值:** 提升团队提交规范意识。

---

## 二、协作洞察（3 项）

### 4. 👥 贡献者网络图
**是什么:** 可视化谁和谁在同一个文件上协作 — 共同修改同一文件的人形成连接。

**实现:**
- 后端: 按文件聚合作者，生成共现矩阵
- 前端: ECharts 力导向图或关系图
- API: `GET /api/stats/collaboration-network`

**价值:** 发现隐形的协作关系，帮助新人找到 mentor。

### 5. 🚌 知识孤岛检测（Bus Factor）
**是什么:** 找出只有一个人修改过的文件 — 如果那个人离开，没人能接手。

**实现:**
- 后端: 统计每个文件的唯一作者数，标出"唯一作者文件"
- 前端: 警示卡片 + 文件列表
- API: `GET /api/stats/bus-factor`

**价值:** 识别团队风险点，安排知识分享。

### 6. 📬 周报自动生成
**是什么:** 一键生成团队周报："本周 X 位成员共提交 Y 次，净增 Z 行代码，最活跃仓库是..." 

**实现:**
- 后端: 聚合本周全部数据，生成 Markdown 模板
- API: `GET /api/report/weekly?format=markdown`

**价值:** 节省写周报的时间。

---

## 三、告警与自动化（3 项）

### 7. 🛎 异常提交告警
**是什么:** 单次提交超过阈值（如 1000 行）时标记警告。

**实现:**
- 后端: 扫描新提交，标记超大 commit
- 前端: Dashboard 顶部 banner 提示
- API: `GET /api/alerts/large-commits?threshold=1000`

### 8. 📅 长期未更新提醒
**是什么:** 仓库超过 N 天无提交时提醒。

**实现:**
- 后端: 检查每个仓库的 `lastCommitTime`
- 前端: 设置页面配置阈值
- API: `GET /api/alerts/inactive-repos?days=7`

### 9. 🔗 Webhook 推送
**是什么:** 每日/每周自动推送统计摘要到 Slack/钉钉/企业微信。

**实现:**
- 后端: 定时任务生成摘要，POST 到 webhook URL
- 前端: 设置页面配置 webhook URL
- API: `POST /api/settings/webhook`

---

## 四、平台扩展（3 项）

### 10. 🐙 GitHub 仓库统计
**是什么:** 对标 GiteeStats，新增 GitHubStats 页面，支持 GitHub 用户/组织仓库浏览。

**实现:**
- 后端: GitHub API v3 代理（`/api/github/repos?owner=`），复用 gitee.py 模式
- 前端: GitHubStats.vue 页面

### 11. 🔌 GitLab 支持
**是什么:** 支持自建 GitLab 实例的仓库统计。

**实现:**
- 后端: GitLab API v4 代理，支持自定义 base URL
- 前端: GitLabStats.vue 页面（可选标签页或独立页面）

### 12. ⌨ CLI 快速查询
**是什么:** 终端直接查询统计数据，无需打开浏览器。

**实现:**
- 新增 `gitstat` CLI 命令：
  ```bash
  gitstat --today          # 今日统计
  gitstat --week           # 本周统计
  gitstat --author 宋康    # 我的统计
  gitstat --top-files      # 热点文件
  ```
- 独立 Python 脚本，调用现有 API

---

## 五、用户体验（3 项）

### 13. 📱 PWA 离线支持
**是什么:** 浏览器缓存前端资源，离线也能查看已加载的数据。

**实现:**
- `vite-plugin-pwa` + `manifest.json` + Service Worker

### 14. 🌐 国际化补全
**是什么:** 当前仅中英文，补全日文、韩文，覆盖更多开发者。

**实现:**
- i18n.js 新增 `ja`、`ko` 语言包

### 15. 🎛 可定制仪表盘
**是什么:** 用户可拖拽排列仪表盘卡片顺序，显示/隐藏指定模块。

**实现:**
- 前端: 使用 `vue-draggable` 组件
- localStorage 持久化布局配置

---

## 📊 优先级矩阵

| 排名 | 功能 | 难度 | 价值 | 建议 |
|------|------|------|------|------|
| 🥇 | #2 提交时段分析 | ⭐ | 🔥🔥🔥 | **立即开始** |
| 🥇 | #1 文件热点分析 | ⭐⭐ | 🔥🔥🔥 | **立即开始** |
| 🥈 | #6 周报自动生成 | ⭐ | 🔥🔥🔥 | 本周可完成 |
| 🥈 | #3 提交质量评分 | ⭐ | 🔥🔥 | 本周可完成 |
| 🥈 | #7 异常提交告警 | ⭐ | 🔥🔥 | 本周可完成 |
| 🥉 | #4 贡献者网络图 | ⭐⭐ | 🔥🔥 | 下周 |
| 🥉 | #5 知识孤岛检测 | ⭐ | 🔥🔥 | 下周 |
| 🥉 | #12 CLI 快速查询 | ⭐⭐ | 🔥🔥 | 下周 |
| 🥉 | #10 GitHub 支持 | ⭐⭐⭐ | 🔥🔥🔥 | 本月 |
| 🥉 | #13 PWA | ⭐ | 🔥 | 本月 |

---

**总计: 15 项新功能提案，预计 4-6 周开发周期。**
