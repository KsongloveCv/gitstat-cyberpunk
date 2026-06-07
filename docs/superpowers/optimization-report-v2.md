# GitStat 第二轮优化报告

**日期:** 2026-06-07 | **分支:** feature/optimize-all（比 v1 新增）

> v1 已完成 11/12 项，详见 `optimization-report.md`

---

## 🔴 高优先级

### 1. 零数据持久化
所有数据存于内存，服务器重启全部丢失。git log 解析是最耗时的操作，每次重启都要重跑。

**建议:** 引入 SQLite（Python 标准库，零依赖）
- 仓库元数据表 `repos`
- 提交缓存表 `commits` 
- 分析结果表 `analyses`
- TTL 缓存已在 git_utils.py 中有基础，扩展到磁盘即可

**预期收益:** 重启秒级恢复，避免重复 git log

### 2. Token 解析函数过大（95 行）
`_aggregate_token_stats` 是单体函数，包含过滤、聚合、成本计算三种职责。

**建议:** 拆分为 `_filter_by_time()`, `_aggregate_by_model()`, `_calc_costs()` 三个函数

### 3. 3 个大组件需要拆分

| 文件 | 行数 | 问题 |
|------|------|------|
| `CalendarView.vue` | 1095 | 日历渲染 + 热力图 + 业务逻辑混在一起 |
| `AnalyticsCharts.vue` | 609 | 5 种图表类型在一个文件 |
| `AnalyticsControls.vue` | 597 | 筛选器 + 仓库选择 + 按钮组合 |

**建议:** 每个拆分为 2-3 个子组件，控制单文件在 300 行内

---

## 🟡 中优先级

### 4. API 路由缺乏统一异常处理
55 个路由中有 17 个手动 `raise HTTPException`，但没有全局异常中间件。未捕获的异常会暴露 500 错误给前端。

**建议:** 添加 FastAPI exception handler：
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error("Unhandled: %s", exc)
    return JSONResponse({"code": 500, "message": "Internal error"}, status_code=500)
```

### 5. 前端 Bundle 972KB
虽然 echarts 已按需引入（631KB），但仍有优化空间：
- **路由懒加载**：App.vue 已用 `defineAsyncComponent`（✅ 已做）
- **分 chunk**：Dashboard + Analytics 可独立拆分
- **压缩字体**：`Orbitron` + `Share Tech Mono` 两个 Google Font

**建议:** 用 `vite-plugin-compression` 开启 brotli 压缩，预计可减少 40% 传输体积

### 6. 无 API 限流
任何人都可以无限制调用 `/api/gitee/repos` 等接口，可能触发 Gitee API 的 5000 次/小时限制。

**建议:** 添加 `slowapi` 中间件（FastAPI 生态标准组件）

### 7. 硬编码超时值
```python
timeout=30   # git_exec
timeout=15   # gitee_api
timeout=10   # weather
timeout=120  # git clone
timeout=5    # git version
```

**建议:** 定义常量类：
```python
class Timeout:
    GIT_EXEC = 30
    GIT_CLONE = 120
    HTTP_API = 15
    QUICK = 5
```

---

## 🟢 低优先级

### 8. 缺少配置管理
`VERSION`、`MAX_COMMITS_PER_REPO`、`GITEE_API_BASE` 等散落在代码中。

**建议:** 创建 `config.py`，用 Pydantic Settings 管理

### 9. 滚动条样式不一致
Dashboard.vue 和 GiteeStats.vue 各自定义了不同的自定义滚动条。

**建议:** 提取到全局 CSS

### 10. 无 Docker 支持
项目需手动安装 Python + Node.js 依赖。

**建议:** 添加 Dockerfile + docker-compose.yml

### 11. API 响应格式不统一
有的返回 `{"code": 200, "data": ...}`，有的直接返回 `[...]`，有的返回 `"OK"`。

**建议:** 统一为 `{"code": 200, "data": ..., "message": "..."}`

### 12. main.py 仍 2181 行
v1 已提取 git_utils、store、gitee 三个模块。还有 weather、token、streak、aggregator 等待提取。

**建议:** 继续拆分，目标 main.py < 500 行

---

## 📊 汇总

| # | 问题 | 优先级 | 预期工作量 |
|---|------|--------|-----------|
| 1 | 零数据持久化 | 🔴 高 | 4-6h |
| 2 | Token 函数过大 | 🔴 高 | 1h |
| 3 | 3 个大组件拆分 | 🔴 高 | 3-4h |
| 4 | 全局异常处理 | 🟡 中 | 0.5h |
| 5 | Bundle 压缩 | 🟡 中 | 0.5h |
| 6 | API 限流 | 🟡 中 | 1h |
| 7 | 超时常量化 | 🟡 中 | 0.5h |
| 8 | 配置管理 | 🟢 低 | 1h |
| 9 | 滚动条统一 | 🟢 低 | 0.5h |
| 10 | Docker 支持 | 🟢 低 | 1h |
| 11 | 响应格式统一 | 🟢 低 | 2h |
| 12 | main.py 继续拆分 | 🟢 低 | 2h |
