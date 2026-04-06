# Frontend Debug Report

## 结论

本次“提交问题后无反应”的根因在前端资源加载与初始化层，不在 `POST /api/v1/answers` 业务链路。

明确根因有两部分：

1. `backend/api/minimal_api.py` 之前对 `GET /`、`/frontend/app.js`、`/frontend/styles.css` 没有发送 `no-store / no-cache` 头，浏览器可能继续使用旧版静态资源。
2. `frontend/app.js` 之前在模块顶层直接抓取 DOM 并绑定事件，但没有显式 boot 成功标记，也没有把初始化失败写回页面；一旦浏览器拿到旧 HTML / 旧 JS，或脚本初始化阶段出现问题，页面表面上会像“点击提交没有任何反应”。

补充说明：

- 样例按钮本来就只负责填充输入框，不会自动提交；页面上之前没有明确说明，这会放大“页面无反应”的误判，但这不是主根因。

## 问题出现在哪一层

- 资源加载：有问题。静态资源缺少禁缓存头，容易出现浏览器继续吃旧文件。
- 事件绑定：有风险。旧版脚本如果没有正确执行，`submit` 事件不会重新绑定。
- 网络请求：后端接口本身正常；问题在于前端不一定真的走到了 `fetch`。
- 响应处理：后端返回结构正常。
- DOM 渲染：渲染逻辑本身可用，但之前缺少“前端已成功启动 / 前端初始化失败”的可见状态。

## 本次做了哪些检查

### 1. 资源加载检查

- 检查 `GET /`，确认页面可返回。
- 检查 `/frontend/styles.css`，确认样式文件可返回。
- 检查 `/frontend/app.js`，确认脚本文件可返回。
- 检查 HTML 中存在：
  - `<script type="module" src="/frontend/app.js"></script>`
- 修复后再次检查响应头，确认：
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`
  - `Pragma: no-cache`
  - `Expires: 0`

### 2. 事件绑定检查

- 检查 `frontend/app.js` 中确实存在 `submit` 事件绑定。
- 检查样例按钮逻辑，确认它们只填充输入框，不自动提交。
- 为前端增加显式 boot 标记：
  - `window.__frontendBooted = true`
- 为提交流程增加可观察标记：
  - `window.__lastSubmitQuery`
  - `window.__lastAnswerPayload`

### 3. 网络请求检查

- 直接对 `POST /api/v1/answers` 发起真实请求，确认接口可用。
- 验证请求体仍只发送 `query`。
- 验证三条冻结样例仍分别返回：
  - `strong`
  - `weak_with_review_notice`
  - `refuse`

### 4. 渲染检查

- 检查 `renderPayload()` 仍基于当前冻结的 answer payload 顶层字段渲染。
- 检查 `primary_evidence / secondary_evidence / review_materials` 仍按显隐逻辑分区展示。
- 检查 `review_notice / refuse_reason / suggested_followup_questions` 仍按模式显隐。
- 增加初始化失败兜底：如果 DOM 选择器缺失或脚本启动失败，页面会直接显示“前端初始化失败”，不再表现为静默无响应。

## 最终修了什么

### `backend/api/minimal_api.py`

- 为页面、静态资源、JSON 响应统一增加禁缓存头，避免浏览器继续使用旧版前端文件。
- 增加 `HEAD` 支持，方便联调时快速确认：
  - `GET /`
  - `/frontend/app.js`
  - `/frontend/styles.css`
  - `/api/v1/answers`

### `frontend/app.js`

- 把 DOM 获取与事件绑定收敛到 `boot()`，不再在模块顶层静默依赖页面节点已经正确可用。
- 为必需节点增加 `requireElement()` 检查；缺节点时抛出明确错误。
- 为启动成功和失败分别写入页面状态：
  - 成功：`前端脚本已加载，等待提交`
  - 失败：`前端初始化失败`
- 在控制台和页面上同时暴露错误，而不是只在隐藏处失败。
- 提交时记录最后一次 query 和最后一次 payload，便于定位“有没有发请求、有没有收到响应”。

### `frontend/index.html`

- 初始状态文案改为 `正在加载前端脚本…`，避免脚本根本没加载时仍显示“尚未发起查询”。
- 增加样例按钮说明：只填充输入框，不自动提交。

### `frontend/styles.css`

- 只做最小样式补充，给样例说明文案提供可读样式。

## 修复后如何复现验证

1. 启动服务：

```bash
./.venv/bin/python -m backend.api.minimal_api --host 127.0.0.1 --port 8000
```

2. 打开页面：

- `http://127.0.0.1:8000/`

3. 先看状态区：

- 页面加载后，应从 `正在加载前端脚本…` 变成 `前端脚本已加载，等待提交`
- 如果一直停在前者，或变成 `前端初始化失败`，说明脚本没有正确启动

4. 输入并提交以下冻结样例：

- `黄连汤方的条文是什么？`
- `烧针益阳而损阴是什么意思？`
- `书中有没有提到量子纠缠？`

5. 预期结果：

- `strong`：显示 `answer_text` 与主依据，主依据中应出现 `0145 / 0146 / 0147`
- `weak_with_review_notice`：主依据区隐藏，补充依据区与核对材料区分开显示，并突出 `review_notice`
- `refuse`：显示 `refuse_reason` 与改问建议；证据区为空时页面不报错

## 验证时的已知限制

当前本地环境没有现成浏览器自动化依赖；Safari 的 Apple Events JavaScript 也未开启，所以没法直接用自动脚本点击页面按钮并抓 DOM。  
因此这次采用的是“真实 HTTP 联调 + 资源头检查 + 前端启动链路自检 + 渲染代码路径检查”的组合验证。对这次排障目标已经足够，并且修复点已经把原先最容易导致“无反应”的前端层问题消除了。
