# React 前端重构 v1

## 范围

本轮只做两件事：

1. 将原生 `frontend/index.html + app.js + styles.css` 重构为 `Vite + React + TypeScript` 前端。
2. 在不改后端业务逻辑与 payload contract 的前提下，优化 `answer_text` 中 `[E#]` 的前端呈现体验。

未改内容：

- retrieval / rerank / gating / AnswerAssembler
- `backend/llm/prompt_builder.py` 与 `backend/llm/validator.py` 的规则
- answer payload 字段结构
- 登录、权限、产品范围扩张

## 目录与技术栈

`frontend/` 现已替换为 React 工程：

- `frontend/index.html`
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig*.json`
- `frontend/src/`

主要依赖：

- `react`
- `react-dom`
- `react-router-dom`
- `vite`
- `typescript`

## 实现要点

### 1. 会话与路由

- 使用 `react-router-dom` 对齐两条壳路由：
  - `/`
  - `/chat/:conversationId`
- 保留原有会话行为：
  - 左侧历史会话列表
  - 搜索历史会话
  - 新建对话回到真正空白态
  - 切换会话不串状态
  - 发送消息时自动创建会话
  - 删除会话

### 2. API 对齐

React 前端继续只依赖现有接口：

- `GET /api/v1/conversations`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations/{id}`
- `POST /api/v1/conversations/{id}/messages`
- `DELETE /api/v1/conversations/{id}`

没有新增任何后端业务字段，也没有改变请求/响应结构。

### 3. `[E#]` 体验优化

前端按既有规则复刻 evidence 编号：

- `primary_evidence -> E1..`
- `secondary_evidence -> ...`
- `review_materials -> ...`

然后将 `answer_text` 中的 `[E#]` 做前端级解析：

- 默认隐藏正文中的原始 `[E#]`
- 改为行尾轻量 `E1 / E2 / E3` 徽标
- 顶栏提供 `显示证据标记` 开关
- 开启后显示原始 `[E#]`
- 点击徽标可滚动并高亮对应 evidence card
- 徽标 `title` 中展示 evidence 标题与 snippet

### 4. 样式方向

继续保持“简约、克制、低装饰”：

- 稳定侧栏 + 单主阅读轴
- 减少厚重卡片堆叠
- 弱化阴影与装饰
- 仅保留必要的 hover / highlight 反馈

### 5. 后端静态托管

`backend/api/minimal_api.py` 本轮只改静态托管层：

- 后端现在托管 `frontend/dist/`
- `/chat/:id` 刷新时返回同一个 SPA shell
- `/assets/*` 直接指向 Vite 构建产物
- 若 `frontend/dist/` 不存在，则返回“请先 build 前端”的提示页

## 运行方式

### 开发模式

先启动后端 API：

```bash
./.venv/bin/python -m backend.api.minimal_api --host 127.0.0.1 --port 8000 --llm-enabled
```

再启动 React dev server：

```bash
cd frontend
npm install
npm run dev
```

说明：

- Vite 默认运行在 `http://127.0.0.1:5173`
- `/api` 已代理到 `http://127.0.0.1:8000`

### 构建后由后端托管

```bash
cd frontend
npm install
npm run build
cd ..
./.venv/bin/python -m backend.api.minimal_api --host 127.0.0.1 --port 8000 --llm-enabled
```

访问：

- [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 验证

已完成：

- `npm run build`
- `PYTHONPYCACHEPREFIX=/tmp/tcm_pycache python3 -m py_compile backend/api/minimal_api.py`
- `curl -I http://127.0.0.1:8000/`
- `curl -I http://127.0.0.1:8000/chat/test-conv`
- `curl -I http://127.0.0.1:8000/assets/...`
- `curl http://127.0.0.1:5173/api/v1/conversations` 验证 dev proxy

端到端验收问例：

1. `黄连汤方的条文是什么？`
   - `strong`
   - 正文默认隐藏 `[E#]`
   - 行尾 `E#` 徽标可点击并高亮主依据
2. `烧针益阳而损阴是什么意思？`
   - `weak_with_review_notice`
   - 核对提示仍保留
3. `书中有没有提到量子纠缠？`
   - `refuse`
   - 拒答原因与改问建议清晰展示

## 截图产物

目录：

- `artifacts/frontend_react_refactor_v1/`

文件：

- `01_new_chat_initial_state.png`
- `02_sidebar_independent_scroll.png`
- `03_strong_default_hidden.png`
- `04_strong_raw_markers_on.png`
- `05_strong_chip_highlight.png`
- `06_weak_review_notice.png`
- `07_refuse_clear_state.png`

## 备注

- 运行联调后，`artifacts/runtime/chat_history_v1.db-wal` 与 `chat_history_v1.db-shm` 会被 SQLite 写脏；提交前应回到基线状态。
- 当前仓库里原本就存在若干与本轮无关的未跟踪草稿文件，整理 commit 时需要避免把它们误并入本补丁。
