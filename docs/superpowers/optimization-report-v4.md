# GitStat 第四轮优化报告 — 去重 · 健壮性 · 测试 · 文档

**日期:** 2026-06-08 | **v1+v2+v3 已完成 42/44 项** | **v4 新发现 18 项**

---

## 🔴 高优先级 — 代码质量

### 1. main.py 与 gitee.py 4 个函数完全重复
`gitee_api`、`gitee_list_repos`、`gitee_get_repo`、`clone_gitee_repo` 在两个文件中各有一份完整实现。main.py 已 `from gitee import ...` 但仍保留自己的副本。

**修复:** 删除 main.py 中重复的函数（~170 行），仅保留 `from gitee import ...`。

### 2. main.py 与 git_utils.py 函数重复
`git_exec`、`get_git_version`、`run_git_log`、`parse_git_log` 同样存在于 main.py 和 git_utils.py 中。main.py 已 `from git_utils import ...`，但未删除原函数。

**修复:** 删除 main.py 中的重复 git 函数（~120 行）。

### 3. main.py 仍 2154 行
经过 v2 模块化（拆分 git_utils/store/gitee/weather），但 main.py 因 #1 #2 的重复代码仍然很大。

**修复:** 完成 #1 #2 后，预计 main.py 降至 ~1800 行。后续可继续提取 aggregator、streak、token 模块。

---

## 🟡 中优先级 — 前端优化

### 4. 零前端测试
92 个测试全部是后端 pytest，`frontend/src/__tests__/i18n.test.js` 仅 13 行骨架。

**建议:** 用 vitest 加 10-15 个组件和 API 层测试。

### 5. 硬编码坐标未配置化
```javascript
fetchWeather(34.34, 108.94)  // 西安 — 硬编码
```

**建议:** 提取到 `config.js` 或 localStorage，支持用户自定义默认城市。

### 6. BootSequence 6 个定时器无清理
`BootSequence.vue` 中 6 处 `setTimeout`，`onUnmounted` 可能未全部清理。快速切换页面可能导致定时器泄漏。

**修复:** 确保 `onUnmounted` 中 `clearTimeout` 所有 timer ID。

### 7. 图表 resize 未在 KeepAlive 激活时触发
Dashboard 使用 `<KeepAlive>`，切换到其他页面再回来时 echarts 图表可能尺寸错乱。

**修复:** 监听 `onActivated` 生命周期，调用 `chart.resize()`。

---

## 🟢 低优先级 — 完善

### 8. 无 API 文档
36 个 API 端点，无 Swagger UI 描述、无 summary/tags。

**建议:** 利用 FastAPI 自动生成的 `/docs`（已在 `app = FastAPI()` 中启用？需检查）。

### 9. Gitee API 调用无重试
`_gitee_request` 调用失败立即抛异常，无重试机制。Gitee API 偶尔 503。

**建议:** 添加 3 次指数退避重试。

### 10. 离线/弱网提示缺失
网络中断时无任何提示，页面静默失败。

**建议:** 添加 `navigator.onLine` 监听 + toast 通知。

### 11. 键盘快捷键缺失
无 `/` 聚焦搜索、`Esc` 关闭弹窗、`Ctrl+K` 命令面板等快捷键。

**建议:** 至少添加搜索聚焦快捷键。

### 12. 日志轮转缺失
`gitstat.log` 无限增长，无 `RotatingFileHandler`。

**修复:** 改用 `RotatingFileHandler(maxBytes=10*1024*1024, backupCount=3)`。

### 13. `rate_limited` 变量未使用
main.py 中定义 `rate_limited` 响应模板但从未引用。

**修复:** 删除或在限流处使用。

### 14. 仓库删除无二次确认
设置页面中删除仓库直接生效，无确认弹窗。ConfirmDialog 组件已建立，但未接入。

**修复:** 在删除按钮处接入 ConfirmDialog。

### 15. 语言检测不完整
`getBrowserLocale()` 只检测 `zh` 前缀，未处理 `zh-CN`/`zh-TW` 等变体。

### 16. SQLite 无 WAL checkpoint
WAL 模式启用但无定期 checkpoint，WAL 文件可能增长。

**建议:** 添加定时 checkpoint 逻辑。

### 17. 颜色主题未同步到图表
切换 neon 主题时 echarts 图表颜色方案不变，仅 CSS 变量生效。

**建议:** 主题切换时重新 `setOption` 图表。

### 18. 无贡献指南
缺少 `CONTRIBUTING.md`，新贡献者不知如何参与。

---

## 📊 四轮总览

| 轮次 | 完成 | 范围 |
|------|------|------|
| v1 | 11/12 ✅ | 代码质量、去重、日志、测试基础 |
| v2 | 11/12 ✅ | 架构、SQLite、Docker、限流 |
| v3 | 20/20 ✅ | 安全、UI、功能、92 测试 |
| v4 | 0/18 🔲 | 去重、前端测试、健壮性、文档 |

### 🎯 v4 推荐实施顺序

| 优先级 | 项目 | 工作量 |
|--------|------|--------|
| 🔴 1 | #1 删除 main.py 中重复的 Gitee 函数 | 15 min |
| 🔴 2 | #2 删除 main.py 中重复的 git 函数 | 15 min |
| 🟡 3 | #4 前端 vitest 测试 | 1h |
| 🟡 4 | #6 BootSequence 定时器清理 | 30 min |
| 🟡 5 | #7 KeepAlive 图表 resize | 15 min |
| 🟢 6 | #5 城市配置化 | 30 min |
| 🟢 7 | #14 确认弹窗接入 | 30 min |
| 🟢 8 | #12 日志轮转 | 10 min |
| 🟢 9 | #9 Gitee 重试 | 30 min |
| 🟢 10-18 | 其余 9 项 | 4h |
