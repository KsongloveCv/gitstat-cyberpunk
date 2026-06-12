# GitStat Cyberpunk — 项目规范

## 工作约束（最高优先级）

1. **先列计划，批准再动手** — 开始任何任务前，先列出执行步骤并等待用户明确批准。计划未经确认，不得开始实施。
2. **改之前先读文件** — 编辑任何文件之前，必须先读一遍当前内容。
3. **别重复造轮子** — 尽量缩小改动范围，优先复用项目已有的抽象和函数，绝对禁止将代码重新穿透多层调用链实现一遍。
4. **不确定先说，不要猜** — 如果没有可参考的先例，停下来问，不要自己发明需求，那是人类的工作。
5. **中途转向，先问再动** — 实施可能影响用户的改动前，先确认方案。如果范围发生变化，重新制定计划。
6. **计划外的问题先报告** — 遇到与当前任务无关的废弃代码或可疑行为，说出来，严禁自己动手。
7. **改了什么必须汇报** — 提交之前，把完整的改动差异展示给用户，并获得明确批准。
8. **没跑过测试不算完成** — 在宣布实现就绪前，针对改动的包跑一遍能覆盖 lint、类型检查和测试失败的最小验证。

## 项目概况

Git 仓库提交统计与可视化分析平台（赛博朋克风格），后端 Python/FastAPI，前端 Vue 3 SPA，端口 12580。

## 技术栈

- **后端**: Python 3.9+ / FastAPI / uvicorn / SQLite (WAL) / git log --numstat
- **前端**: Vue 3.5 Composition API (`<script setup>`) / Vite 8 / ECharts 6
- **字体**: Orbitron / Rajdhani / Share Tech Mono (Google Fonts)
- **i18n**: 自研 composable，zh / en 双语

## 关键路径

| 用途 | 路径 |
|------|------|
| 后端入口 | `backend-py/main.py` |
| SQLite 层 | `backend-py/database.py` |
| 内存缓存 | `backend-py/store.py` |
| Git 命令 | `backend-py/git_utils.py` |
| Gitee API | `backend-py/gitee.py` |
| 天气代理 | `backend-py/weather.py` |
| 配置常量 | `backend-py/config.py` |
| 前端入口 | `frontend/src/App.vue` |
| API 层 | `frontend/src/api/index.js` |
| 状态管理 | `frontend/src/stores/data.js` + `weather.js` |
| 国际化 | `frontend/src/i18n.js` |
| 测试 | `tests/` (pytest) |
| 脚本 | `scripts/start.sh` / `stop.sh` / `watchdog.sh` |

## 开发流程

### 启动开发

```bash
# 前端 (Vite HMR, 端口 5173)
cd frontend && npm run dev

# 后端 (端口 12580, 不自动开浏览器)
python3 backend-py/main.py ~/your-git-projects --no-browser
```

### 构建 & 运行

```bash
cd frontend && npm install && npm run build && cd ..
python3 backend-py/main.py ~/your-git-projects
```

### 测试

```bash
pytest tests/
```

### 浏览器

用 Google Chrome 打开 `http://localhost:12580`。

## 编码规范

### 后端 (Python)

- 函数/类用简短 docstring（一行），不写长篇注释
- API 路由统一注册在 `main.py`，模块化拆分到各 `.py` 文件
- 异步用 `async def`，git 命令调用用 `asyncio.create_subprocess_exec`
- SQLite 操作注意线程安全，使用 WAL 模式
- 超时常量集中在 `config.Timeout`
- 新增 API 遵循已有 REST 命名风格（`/api/stats/...`, `/api/repos/...`）
- 不引入额外 HTTP 依赖，天气/Gitee 用 `urllib.request`

### 前端 (Vue)

- 使用 `<script setup>` + Composition API，不用 Options API
- 新组件放 `frontend/src/components/`，新页面放 `frontend/src/views/`
- ECharts 按需引入，不要全量 import
- 状态管理用自研 Store（`stores/data.js` / `weather.js`），不用 Pinia/Vuex
- 所有用户可见文本必须走 i18n（`i18n.js`），新增 key 同步 zh + en
- WeatherCard 数据源绑定 `weatherState`（`stores/weather.js`），不要从 `data.js` 取
- 赛博朋克视觉效果：CRT 扫描线 / Matrix 数字雨 / 霓虹发光 / Glitch / 全息卡片，保持风格一致
- CSS 变量用主题色：cyan / magenta（三套主题 Default / Amber / Green）
- 不使用 emoji 在代码中

### 通用

- 不引入不必要的依赖或抽象
- 注释只写 WHY，不写 WHAT
- 不做过度 error handling 或 fallback，只在系统边界（用户输入、外部 API）验证
- Git commit message 风格：`feat:` / `fix:` / `refactor:` / `merge:` 前缀，简要说明意图