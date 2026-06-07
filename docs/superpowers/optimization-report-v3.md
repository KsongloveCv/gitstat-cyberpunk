# GitStat 第三轮优化报告 — 安全性 · UI · 功能 · 实用性

**日期:** 2026-06-07 | **v1+v2 已完成 22/24 项** | **v3 新发现 20 项**

---

## 🔴 安全性（最紧急）

### 1. GITEE_TOKEN 通过 URL Query 传输
```python
url += f"&access_token={GITEE_ACCESS_TOKEN}"  # ← token 暴露在 URL 中
```
Token 出现在服务器日志、代理日志、浏览器历史中。**严重安全风险。**

**修复:** 改为 HTTP Header 传 token：
```python
headers = {"Authorization": f"Bearer {GITEE_ACCESS_TOKEN}"} if GITEE_ACCESS_TOKEN else {}
```

### 2. 路径遍历攻击
`/api/repos/info?path=../../etc/passwd` 未被过滤。`os.path.join(repo_path, rel)` 在 `discover_repos` 中可能被利用。

**修复:** 添加 `Path(path).resolve()` 校验，确保路径在允许范围内。

### 3. 零安全头
无 `X-Content-Type-Options`、`X-Frame-Options`、`HSTS`、`CSP`。

**修复:** 添加 FastAPI middleware：
```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

### 4. XSS 风险
`AnalyticsPanels.vue:37` 使用 `v-html="insight.iconSvg"` — 如果 SVG 来源不可信，存在 XSS 注入风险。

**修复:** 改用 `v-text` 或净化 SVG 输入。

### 5. CORS 配置过于宽松
```python
allow_origins=["*"]  # 允许任意来源
```
**修复:** 限定为具体域名，或至少从环境变量读取。

---

## 🟡 实用性 / 功能缺失

### 6. 零数据刷新机制
所有页面需手动刷新浏览器才能看到新数据。Dashboard 无轮询、无 WebSocket 推送。

**建议:** 添加可配置的自动刷新（30s/60s/off），在顶部加刷新按钮 + 倒数计时。

### 7. 导出仅支持 JSON
`/api/export/json` 只能导出 JSON，日常使用场景更需 CSV/Excel。

**建议:** 添加 `/api/export/csv`，用 Python 标准库 `csv` 模块生成。

### 8. 仓库搜索缺失
Dashboard + Repo 页面共 5 个视图，无全局搜索。仓库多时（50+）定位困难。

**建议:** Dashboard 顶部加搜索框，支持仓库名/作者名模糊过滤。

### 9. 无操作确认
删除仓库（设置页面）、移除 Gitee 缓存等操作无二次确认，误点击即丢失数据。

**建议:** 添加确认弹窗组件。

### 10. 数据时间范围指示不清
Dashboard 显示"本周"数据，但页面上无日期范围标签。用户不清楚数据的时间跨度。

**建议:** 每个统计卡片标注 "2026-06-01 ~ 2026-06-07" 风格的时间范围。

### 11. PWA 支持缺失
无 Service Worker、无 manifest.json。离线不可用。

**建议:** 添加 `vite-plugin-pwa`，生成 `manifest.json` + `sw.js`，支持离线缓存。

---

## 🟢 UI / UX

### 12. 零可访问性
23 个 Vue 文件中无任何 ARIA 属性、无 alt、无 role、无 tabindex。键盘导航不可用。

**建议:** 至少为导航栏、按钮、表单添加 `role` + `aria-label` + `:focus-visible` 样式。

### 13. 移动端体验缺失
- Dashboard 9 个组件中仅 5 个有 `@media` 查询
- 导航栏在小屏上堆叠但不隐藏，占用大量空间
- 图表横屏查看体验差

**建议:** 添加汉堡菜单 + echarts `resize()` 响应式 + 表格横向滚动。

### 14. 加载态/错误态不一致
- 仪表盘有骨架屏（✅ 优秀）
- GiteeStats 有骨架屏（✅ 优秀）
- TokenAnalytics / Analytics 只有 Loading 文字（❌ 简陋）
- 无网络错误恢复提示

**建议:** 统一为骨架屏 + 错误重试按钮组件。

### 15. 硬编码中文文本
RepoSection.vue 和 GiteeStats.vue 中有未国际化的中文硬编码（如"深度分析代码结构""加载更多仓库"）。

**建议:** 全部迁移到 i18n.js。

### 16. 颜色主题不持久
`cycleTheme()` 循环切换主题，但刷新后默认回到 default。用户无法固定主题偏好。

**建议:** 已有 `localStorage.getItem('neonTheme')` 保存（✅ 已做），检查一致性。

### 17. Gitee 克隆进度不可见
Deep analyze 触发后，用户看到 loading 动画但不知道 clone 进度（尤其是大仓库 clone 可能耗时 30s+）。

**建议:** 后端用 SSE 推送克隆进度百分比，前端显示进度条。

---

## 🟢 架构 / 长期

### 18. main.py 仍 2435 行
经过两轮模块化，main.py 仍有 2400+ 行。还有 aggregator、streak、token 模块可提取。

**目标:** main.py < 500 行，每个业务模块独立。

### 19. logging 未写入文件
日志只输出到 stderr，无持久化。排查线上问题没有日志可查。

**建议:** 添加 `logging.FileHandler("gitstat.log")`。

### 20. 无 Helm/Docker Compose 健康检查
Dockerfile 缺少 `HEALTHCHECK` 指令。`docker-compose.yml` 缺少 healthcheck。

**修复:**
```dockerfile
HEALTHCHECK --interval=30s CMD curl -f http://localhost:12580/health || exit 1
```

---

## 📊 v1 + v2 + v3 总览

| 轮次 | 项目 | 完成 |
|------|------|------|
| v1 | 代码质量（去重/日志/缓存/CSS变量/测试） | 11/12 ✅ |
| v2 | 架构（SQLite/Docker/限流/压缩/模块化） | 11/12 ✅ |
| v3 | 安全+UI+功能+实用性 | 0/20 🔲 |

### 🎯 v3 推荐实施顺序

| 优先级 | 项目 | 工作量 |
|--------|------|--------|
| 🔴 1 | #1 Token 安全（URL→Header） | 10 min |
| 🔴 2 | #3 安全头中间件 | 10 min |
| 🔴 3 | #2 路径遍历防护 | 15 min |
| 🟡 4 | #7 CSV 导出 | 30 min |
| 🟡 5 | #6 自动刷新机制 | 1h |
| 🟡 6 | #9 确认弹窗组件 | 1h |
| 🟡 7 | #15 硬编码文本国际化 | 1h |
| 🟡 8 | #13 移动端汉堡菜单 | 1h |
| 🟢 9 | #12 ARIA 可访问性 | 2h |
| 🟢 10 | #11 PWA 支持 | 1h |
| 🟢 11 | #17 Gitee 克隆进度 SSE | 2h |
| 🟢 12 | #10 数据时间范围标签 | 1h |
| 🟢 13 | #8 全局搜索 | 2h |
| 🟢 14 | #14 统一骨架屏组件 | 2h |
| 🟢 15 | #18 main.py 继续拆分 | 3h |
| 🟢 16 | #19 日志文件 | 15 min |
| 🟢 17 | #4 XSS 修复 | 15 min |
| 🟢 18 | #5 CORS 收紧 | 5 min |
| 🟢 19 | #16 主题一致性检查 | 30 min |
| 🟢 20 | #20 Docker HEALTHCHECK | 5 min |
