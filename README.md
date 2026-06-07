# GitStat // Netrunner Edition

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js&style=flat-square" alt="Vue">
  <img src="https://img.shields.io/badge/Vite-8.0-646CFF?logo=vite&style=flat-square" alt="Vite">
  <img src="https://img.shields.io/badge/ECharts-6.0-AA344D?logo=apacheecharts&style=flat-square" alt="ECharts">
  <img src="https://img.shields.io/badge/OpenMeteo-Free-FF6B35?style=flat-square" alt="Open-Meteo">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
</p>

> **Git 仓库提交统计与可视化分析平台 — 赛博朋克增强版**
>
> Git Repository Commit Statistics & Visualization Platform — Cyberpunk Enhanced

---

## 📡 目录

- [项目简介](#-项目简介)
- [更新日志](#-更新日志)
- [核心特点](#-核心特点)
- [视觉效果](#-视觉效果)
- [快速开始](#-快速开始)
- [项目架构](#-项目架构)
- [API 接口](#-api-接口)
- [从源码运行](#-从源码运行)
- [前端开发](#-前端开发)
- [技术栈](#-技术栈)
- [项目结构](#-项目结构)
- [许可证](#-许可证)

---

## 📡 项目简介

GitStat Netrunner Edition 是一个 Git 仓库提交统计可视化工具。基于 [gitstat](https://github.com/wsyqn6/gitstat) 增强开发，在原有暗色霓虹风格基础上，加入了 CRT 扫描线、Matrix 数字雨、全息投影动画、故障艺术效果等经典赛博朋克视觉元素。

只需一条命令，即可扫描本地 Git 仓库目录，启动 Web 仪表盘，在浏览器中查看多维度提交数据分析、天气信息、Token 消耗统计、Gitee 仓库管理等。

---

## 📡 更新日志

### v2.0 — 赛博朋克增强版（重大重构 + 新功能）

**架构重构：**
- 移除 Go 后端代码（约 2600 行），仅保留 Python/FastAPI 后端（单文件 1250 行）
- 后端使用 `urllib.request`（stdlib）调用外部 API，零额外依赖
- 前端构建产物直接由 FastAPI SPA fallback 服务，无需独立部署

**新增功能：**

| 功能 | 说明 |
|------|------|
| **天气卡片** | 自动检测浏览器地理位置（拒绝时回退上海），显示当前天气 + 7 天预报。数据来自 Open-Meteo 免费 API（无需 API Key） |
| **今日提交详情增强** | 从简单汇总表升级为详细提交列表：每条提交显示短哈希、提交消息、作者、所属仓库、时间（刚刚/X分钟前/X小时前）、新增/删除行数 + 可视化变更条 |
| **连续贡献天数（Streak）** | 统计最长连续有提交的天数和当前连续天数，激励持续编码 |
| **Token 消耗分析** | 模型 Token 消耗统计分析页面：效率指标、成本预测、时段对比、对话 Top10、热力图日历、预算管理 |
| **Gitee 仓库管理** | 搜索/浏览 Gitee 仓库，一键克隆到本地扫描目录，深度分析，移除仓库 |

**视觉增强：**
- WeatherCard：赛博朋克风格天气卡片（霓虹 emoji 图标 + 温度数字 + 7 天预报条）
- Commit 列表：每行带短哈希标签（magenta 霓虹）+ 变更可视化条（绿/粉双色条）
- StreakCard：连续贡献天数全息投影卡片

---

## ✦ 核心特点

### 🚀 使用体验

| 特性 | 说明 |
|------|------|
| **轻量部署** | Python FastAPI 后端，`pip install` 即可运行，无需编译 |
| **全离线运行** | 直接调用 `git log` 解析提交数据，不依赖 GitHub API，无需联网 |
| **惰性加载** | 按需拉取 git log，大仓库秒开；支持增量补数据 |
| **开箱即用** | 启动后自动打开浏览器，0 配置 |
| **中英双语** | 完整的中英文国际化支持，自动检测浏览器语言 |
| **天气集成** | 基于浏览器定位自动显示当前天气 + 7 天预报（Open-Meteo 免费API） |

### 🎨 赛博朋克视觉（本版增强）

| 视觉效果 | 描述 |
|----------|------|
| **CRT 扫描线** | 全局 CSS 扫描线叠加，模拟复古 CRT 显示器效果 |
| **Matrix 数字雨** | Canvas 实现的可开关 Matrix 代码雨背景（日文片假名 + 数字） |
| **霓虹发光系统** | 全局 neon glow 配色，文字/边框/阴影三重发光 |
| **故障文字（Glitch）** | 悬停 LOGO 触发 RGB 通道分离 + 随机偏移动画 |
| **全息投影卡片** | 卡片悬停时的扫描线动画 + 四角霓虹装饰灯 |
| **启动序列** | 首次访问时的终端 Boot Sequence 打字机动画 |
| **三套主题** | 点击 LOGO 循环切换 Cyan/Magenta → Amber → Green 配色 |
| **赛博朋克滚动条** | 霓虹渐变滚动条，hover 渐变色翻转 |

### 📊 数据分析

| 功能 | 说明 |
|------|------|
| **仪表盘** | 天气卡片 + 今日概览 + 连续贡献天数 + 本周提交趋势 + 作者排行榜 + 仓库对比 + 今日提交详情列表 |
| **分析中心** | 多时间维度（日/周/月/年）、多仓库筛选、提交趋势、代码变更分布、活动热力图 |
| **Token 分析** | 模型 Token 消耗统计、效率指标、成本预测、时段对比、热力图日历、预算管理 |
| **仓库详情** | 分支列表、语言占比、代码总行数、贡献者排行、近期提交 |
| **Gitee 仓库** | 搜索浏览、一键克隆、深度分析、移除管理 |
| **数据导出** | JSON 格式导出分析数据 |

---

## ✦ 快速开始

### 安装依赖

```bash
pip3 install -r backend-py/requirements.txt
```

### 运行

```bash
# 扫描当前目录的所有 Git 仓库，启动 Web UI
python3 backend-py/main.py .

# 扫描指定目录
python3 backend-py/main.py ~/projects

# 自定义端口
python3 backend-py/main.py ~/projects --port 8080

# 不自动打开浏览器
python3 backend-py/main.py ~/projects --no-browser
```

启动后在浏览器中访问 `http://localhost:12580`。

> **交互提示**
> - 首次访问会播放 Boot Sequence 终端动画，点击任意位置跳过
> - 点击导航栏 `≋` 按钮开关 Matrix 数字雨背景
> - 点击顶部 `GITSTAT` LOGO 切换三套霓虹主题配色
> - 天气卡片自动检测浏览器位置（拒绝定位时回退上海坐标）

### 命令行参数

```
python3 backend-py/main.py [scan_path] [options]

参数:
  scan_path              扫描目录（默认: 当前工作目录）
  --port number          监听端口（默认: 12580）
  --no-browser           不自动打开浏览器
```

---

## ✦ 项目架构

```mermaid
flowchart TB
    subgraph browser [Browser]
        VueSPA["Vue 3 SPA"]
        subgraph pages [Pages]
            Dashboard["Dashboard"]
            Analytics["Analytics"]
            TokenAnalytics["Token Analytics"]
            GiteeStats["Gitee Stats"]
            Repos["Repos / Settings"]
        end
        pages --> VueSPA
    end
    subgraph backend [Python Backend]
        FastAPI["FastAPI + uvicorn"]
        Scanner["Scanner"]
        Store["Store"]
        Aggregator["Aggregator"]
        GitLog["git log parser"]
        WeatherProxy["Weather Proxy"]
    end
    browser -->|"HTTP :12580"| FastAPI
    FastAPI --> Scanner
    FastAPI --> Aggregator
    Aggregator --> GitLog
    FastAPI --> Store
    FastAPI --> WeatherProxy
    WeatherProxy -->|"urllib"| OpenMeteo["Open-Meteo API"]
```

**数据流：**
1. `scanner` 扫描指定目录 → 发现所有 Git 仓库
2. `store` 在内存中管理仓库列表，支持按需懒加载 commit 数据
3. `git log --numstat` 直接解析每个仓库的提交记录
4. `aggregator` 按时间/作者/仓库维度聚合统计数据
5. `handler` 提供 REST API，前端通过 fetch 调用
6. 前端静态文件通过 FastAPI SPA fallback 方式服务
7. 天气数据通过后端代理 Open-Meteo API（避免 CORS，无需 API Key）

---

## ✦ API 接口

### 扫描与仓库

| Method | Endpoint | 说明 |
|--------|----------|------|
| `POST` | `/api/scan/path` | 设置扫描目录路径 |
| `GET` | `/api/scan/path` | 获取当前扫描目录 |
| `GET` | `/api/repositories` | 获取仓库列表（快数据） |
| `GET` | `/api/repos/list` | 获取仓库详细信息列表 |
| `GET` | `/api/repos/info?path=` | 获取单个仓库信息 |
| `GET` | `/api/repos/stats?path=` | 获取仓库统计（大小/贡献者/近期提交） |
| `POST` | `/api/repos/analyze` | 深度分析（语言占比/分支列表/代码行数） |

### 统计接口

| Method | Endpoint | 参数 | 说明 |
|--------|----------|------|------|
| `GET` | `/api/stats/overview` | `repo`, `startDate`, `endDate`, `email` | 总览统计 |
| `GET` | `/api/stats/daily` | `repo`, `email`, `range`, `startDate`, `endDate` | 每日统计 |
| `GET` | `/api/stats/weekly` | `repo`, `email`, `range`, `startDate`, `endDate` | 每周统计 |
| `GET` | `/api/stats/monthly` | `repo`, `email`, `range`, `startDate`, `endDate` | 每月统计 |
| `GET` | `/api/stats/yearly` | `repo`, `email`, `range`, `startDate`, `endDate` | 每年统计 |
| `GET` | `/api/stats/authors` | `repo`, `range`, `startDate`, `endDate` | 作者排行 |
| `GET` | `/api/stats/activity-heatmap` | `repo`, `startDate`, `endDate` | 活动热力图 |
| `GET` | `/api/stats/repo-comparison` | `repo`, `range`, `startDate`, `endDate` | 仓库对比 |
| `GET` | `/api/stats/commit-list` | `repo`, `range`, `startDate`, `endDate`, `email`, `limit` | 提交详情列表（按时间倒序） |
| `GET` | `/api/stats/streak` | `repo` | 连续贡献天数统计 |
| `GET` | `/api/stats/tokens` | `range`, `model` | Token 消耗统计 |

### 天气接口（Open-Meteo 代理）

| Method | Endpoint | 参数 | 说明 |
|--------|----------|------|------|
| `GET` | `/api/weather/current` | `lat`, `lon` | 当前天气（温度/湿度/风速/体感温度/天气描述） |
| `GET` | `/api/weather/forecast` | `lat`, `lon`, `days` | 7 天天气预报（最高最低温/降水/风速/日出日落） |

> 天气数据来自 [Open-Meteo](https://open-meteo.com/)，免费、无需 API Key、支持非商业用途。

### Gitee 仓库管理

| Method | Endpoint | 说明 |
|--------|----------|------|
| `GET` | `/api/gitee/repos` | 搜索/浏览 Gitee 仓库 |
| `GET` | `/api/gitee/repos/info` | 获取 Gitee 仓库详细信息 |
| `POST` | `/api/gitee/repos/clone` | 一键克隆 Gitee 仓库到本地扫描目录 |
| `POST` | `/api/gitee/repos/analyze` | 深度分析已克隆的 Gitee 仓库 |
| `POST` | `/api/gitee/repos/remove` | 移除已克隆的 Gitee 仓库 |

### 数据导出

| Method | Endpoint | 说明 |
|--------|----------|------|
| `POST` | `/api/export/json` | 导出完整数据为 JSON |

### 其他

| Method | Endpoint | 说明 |
|--------|----------|------|
| `GET` | `/api/version` | 获取版本号 |
| `GET` | `/health` | 健康检查 |

---

## ✦ 从源码运行

### 前置要求

- **Python** ≥ 3.9
- **Node.js** ≥ 22
- **Git** (已安装并可在命令行使用)

### 启动后端

```bash
# 1. 克隆仓库
git clone https://github.com/KsongloveCv/gitstat-cyberpunk.git
cd gitstat-cyberpunk

# 2. 安装 Python 依赖
pip3 install -r backend-py/requirements.txt

# 3. 构建前端（如需开发或更新前端）
cd frontend
npm install
npm run build
# 产物输出到 frontend/dist/

# 4. 启动后端
cd ..
python3 backend-py/main.py ~/your-git-projects
```

### 开发模式

前端开发（热更新）：

```bash
cd frontend
npm dev          # Vite dev server，默认 :5173
```

后端单独运行（API only，需另行启动前端 dev server）：

```bash
python3 backend-py/main.py ~/your-git-projects --no-browser
```

---

## ✦ 前端开发指南

### 组件树

```
App.vue
├── MatrixRain.vue             # 全局 Matrix 数字雨背景
├── BootSequence.vue           # 首次访问启动动画
├── views/
│   ├── Dashboard.vue          # 仪表盘（天气 + 概览 + 连续贡献 + 趋势 + 排行 + 仓库对比 + 提交列表）
│   │   ├── WeatherCard.vue    # 天气卡片（当前天气 + 7 天预报）
│   │   ├── StatCard.vue       # 全息投影统计卡片
│   │   └── StreakCard.vue     # 连续贡献天数卡片
│   ├── Analytics.vue          # 分析中心（多维图表/日历视图）
│   │   ├── AnalyticsControls.vue  # 时间范围/仓库筛选
│   │   ├── AnalyticsCharts.vue    # 图表区域
│   │   │   └── ChartContainer.vue # 图表容器（加载状态）
│   │   ├── AnalyticsPanels.vue    # 日历/开发者面板
│   │   │   ├── CalendarView.vue   # 日历视图（周/月）
│   │   │   └── DatePicker.vue     # 日期选择器
│   ├── TokenAnalytics.vue     # Token 消耗分析
│   │   ├── TokenEfficiencyCards.vue # 效率指标卡片
│   │   ├── TokenComparison.vue     # 时段对比图表
│   │   ├── TokenHeatmapCalendar.vue # 热力图日历
│   │   └── TokenBudgetAlert.vue    # 预算管理/成本预测
│   ├── GiteeStats.vue         # Gitee 仓库管理
│   ├── RepoSection.vue        # 本地仓库管理
│   └── Settings.vue           # 设置（扫描配置/数据导出）
├── stores/
│   ├── data.js                # 响应式数据 store（Git + Weather + Commit）
│   └── weather.js             # 天气独立 store
├── api/
│   └── index.js               # API 请求层（Git + Weather + Token + Gitee）
├── utils/
│   ├── constants.js           # 霓虹色板 + 图表主题 + 天气图标映射
│   ├── echarts.js             # ECharts 按需引入
└── i18n.js                    # 中英文国际化（Vue composable）
```

### 主题系统

三套霓虹主题通过 CSS 变量驱动，点击 LOGO 切换：

| 主题 | cyan | magenta |
|------|------|---------|
| **Default** | `#00f5ff` | `#ff00ff` |
| **Amber** | `#ffb800` | `#ff6600` |
| **Green** | `#00ff88` | `#00ffcc` |

```css
/* 主题切换原理：直接修改 CSS 自定义属性 */
document.documentElement.style.setProperty('--neon-cyan', '#00ff88')
document.documentElement.style.setProperty('--neon-magenta', '#00ffcc')
```

### 新增组件说明

**WeatherCard.vue**
- 赛博朋克风格天气卡片（霓虹 emoji 图标 + Orbitron 温度数字 + 7 天预报条）
- 自动检测浏览器地理位置（拒绝时回退上海坐标 31.23/121.47）
- Skeleton 加载态 + 错误态（天气 API 不可用时）
- 中英双语天气描述（WMO 天气代码 → zh/en 映射，30+ 天气类型）

**StreakCard.vue**
- 连续贡献天数统计（最长连续天数 + 当前连续天数）
- 全息投影风格卡片，赛博朋克霓虹数字显示

**TokenAnalytics 页面组件**
- TokenEfficiencyCards：4 个效率指标全息卡片
- TokenComparison：时段对比图表
- TokenHeatmapCalendar：热力图日历
- TokenBudgetAlert：预算管理 + 成本预测

---

## ✦ 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端** | Python 3.9+ / FastAPI | 高性能异步 Web 框架 |
| **服务器** | uvicorn | ASGI 服务器 |
| **数据源** | git log | 直接调用 git 命令解析提交数据 |
| **天气源** | Open-Meteo API | 免费、无需 Key、CC BY 4.0 数据许可 |
| **HTTP 客户端** | urllib.request (stdlib) | 后端代理天气 API，零额外依赖 |
| **前端** | Vue 3.5 | Composition API + `<script setup>` |
| **构建** | Vite 8 | 极速 HMR & 构建 |
| **图表** | ECharts 6 | 按需引入（Line/Bar/Heatmap/Radar/Pie） |
| **字体** | Google Fonts | Orbitron（标题）+ Rajdhani（正文）+ Share Tech Mono（数据） |
| **国际化** | 自研 composable | 基于 `navigator.language` 自动检测，localStorage 持久化 |

---

## ✦ 项目结构

```
gitstat-cyberpunk/
├── README.md
├── LICENSE
├── backend-py/                            # Python 后端
│   ├── main.py                            # 入口：FastAPI 应用、扫描、API、天气代理、静态文件服务
│   └── requirements.txt                   # Python 依赖（仅 fastapi + uvicorn）
├── frontend/                              # Vue 3 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── dist/                              # Vite 构建产物
│   ├── public/
│   │   └── favicon.svg
│   ├── scripts/
│   │   └── sync-version.mjs               # 版本号同步脚本
│   └── src/
│       ├── main.js                        # Vue 入口
│       ├── App.vue                        # 根组件（5 页面导航/Matrix雨/启动序列/主题切换）
│       ├── i18n.js                        # 中英文国际化
│       ├── api/
│       │   └── index.js                   # API 请求层（Git + Weather + Token + Gitee）
│       ├── assets/
│       │   └── style.css                  # 全局样式（CRT扫描线/霓虹/glitch/滚动条/主题变量）
│       ├── components/
│       │   ├── MatrixRain.vue             # Matrix 数字雨背景
│       │   ├── BootSequence.vue           # 终端启动动画
│       │   ├── WeatherCard.vue            # 天气卡片（当前 + 7天预报）
│       │   ├── StreakCard.vue             # 连续贡献天数卡片
│       │   ├── StatCard.vue               # 全息投影统计卡片
│       │   ├── ChartContainer.vue         # 霓虹图表容器
│       │   ├── CalendarView.vue           # 日历视图（周/月）
│       │   ├── DatePicker.vue             # 日期选择器
│       │   ├── AnalyticsCharts.vue        # 分析图表集
│       │   ├── AnalyticsControls.vue      # 分析筛选控件
│       │   ├── AnalyticsPanels.vue        # 分析面板
│       │   ├── OverviewCards.vue          # 概览卡片
│       │   ├── TokenEfficiencyCards.vue   # Token 效率指标卡片
│       │   ├── TokenComparison.vue        # Token 时段对比图表
│       │   ├── TokenHeatmapCalendar.vue   # Token 热力图日历
│       │   └── TokenBudgetAlert.vue       # Token 预算管理
│       ├── stores/
│       │   ├── data.js                    # 响应式数据 store（Git + Weather + Commit + Token + Gitee）
│       │   └── weather.js                 # 天气独立 store
│       ├── utils/
│       │   ├── constants.js               # 霓虹色板 + 图表主题 + 天气图标映射
│       │   └── echarts.js                 # ECharts 按需引入配置
│       └── views/
│           ├── Dashboard.vue             # 仪表盘页面
│           ├── Analytics.vue             # 分析中心页面
│           ├── TokenAnalytics.vue        # Token 消耗分析页面
│           ├── GiteeStats.vue            # Gitee 仓库管理页面
│           ├── RepoSection.vue           # 本地仓库管理页面
│           └── Settings.vue              # 设置页面
└── docs/                                  # 文档目录
    └── assets/                            # 文档资源（截图等）
```

---

## ✦ 许可证

本项目基于 [gitstat](https://github.com/wsyqn6/gitstat) 增强开发，使用 [MIT License](LICENSE)。

---

<p align="center">
  <em>"The street finds its own uses for things."</em><br>
  — William Gibson
</p>