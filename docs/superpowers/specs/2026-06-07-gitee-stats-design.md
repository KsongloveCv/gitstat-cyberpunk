# Gitee 代码统计页面 — 设计文档

**日期:** 2026-06-07 | **分支:** feature/gitee-stats

## 概述

在现有 GitStat 平台新增 Gitee（码云）代码仓库统计页面。采用 **混合模式**：
- **Gitee Open API** 获取仓库列表与基础概况（快速浏览）
- **本地 Clone + git log** 实现深度分析（完整统计）

## 后端变更（backend-py/main.py）

### 新增 API 路由

| 路由 | 方法 | 描述 |
|------|------|------|
| `/api/gitee/repos` | GET | 传入 `owner`(用户名/组织名)，调用 Gitee API 返回仓库列表 |
| `/api/gitee/repos/info` | GET | 传入 `owner` + `repo`，获取单个仓库基础信息 |
| `/api/gitee/repos/clone` | POST | 传入 `clone_url`，clone 到本地临时目录，跑 git log 解析 |
| `/api/gitee/repos/analyze` | GET | 传入本地路径，返回深度分析（复用现有 analyze 逻辑） |
| `/api/gitee/repos/remove` | POST | 删除已 clone 的本地仓库缓存 |

### Gitee API 调用

- 使用 `urllib.request`（Python 标准库，已有依赖）
- Gitee Open API v5: `https://gitee.com/api/v5`
- 无需认证即可访问公开仓库（速率限制 5000次/小时）
- 可选：支持 personal access token 提高限速

### 新增函数

```
gitee_api(path: str) -> dict          # 调用 Gitee API 的通用函数
gitee_list_repos(owner: str) -> list  # 获取某用户/组织的仓库列表
gitee_get_repo(owner, repo) -> dict   # 获取单个仓库信息
clone_gitee_repo(url: str) -> str     # Clone 仓库到本地缓存目录
```

### 缓存目录

- 克隆的 Gitee 仓库存放于 `~/.gitstat-gitee-cache/` 下
- 加载到 Store 中，与本地扫描仓库共享同一套 stats 接口

## 前端变更（frontend/）

### 新增文件

- `src/views/GiteeStats.vue` — Gitee 统计页面主组件
- `src/components/GiteeRepoList.vue` — 仓库列表卡片组件
- `src/components/GiteeAnalysisPanel.vue` — 深度分析结果面板

### 修改文件

- `src/App.vue` — 导航栏新增 "Gitee" 入口，注册 GiteeStats 组件
- `src/api/index.js` — 新增 Gitee API 调用函数
- `src/i18n.js` — 新增 Gitee 相关中英文文案

### 页面 UI 结构

```
┌────────────────────────────────────────────┐
│  🔍 [输入Gitee用户名/组织名] [扫描仓库]      │
├────────────────────┬───────────────────────┤
│  📦 仓库列表 (API)  │  📊 深度分析结果       │
│                    │  ┌─────┐ ┌─────┐      │
│  user/repo-1  ⚡   │  │趋势图│ │贡献者│      │
│  user/repo-2  ⚡   │  └─────┘ └─────┘      │
│  user/repo-3  ⚡   │  ┌─────┐ ┌─────┐      │
│                    │  │热力图│ │变更  │      │
│                    │  └─────┘ └─────┘      │
├────────────────────┴───────────────────────┤
│  💾 已缓存仓库: repo-1 (已分析) repo-2 (分析中)│
└────────────────────────────────────────────┘
```

### 状态管理

- 利用现有 `stores/data.js` 的 reactive state，新增 gitee 相关字段
- 或新建 `stores/gitee.js` 独立管理 Gitee 状态

## i18n 新增文案

```js
gitee: {
  title: 'Gitee 统计',          // 'Gitee Stats'
  searchPlaceholder: '输入 Gitee 用户名或组织名...',
  scanRepos: '扫描仓库',
  repoList: '仓库列表',
  deepAnalyze: '深度分析',
  analyzing: '分析中...',
  cachedRepos: '已缓存仓库',
  noData: '请输入用户名开始探索',
}
```

## 实现步骤

1. 后端：新增 Gitee API 调用 + 路由
2. 前端：App.vue 导航 + i18n
3. 前端：GiteeStats.vue 页面 + 组件
4. 前端：api/index.js 接口函数
5. 测试：启动服务验证完整流程
