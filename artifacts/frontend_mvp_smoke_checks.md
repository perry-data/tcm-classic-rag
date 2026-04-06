# Frontend MVP Smoke Checks

## 运行方式

启动命令：

```bash
./.venv/bin/python app_minimal_api.py --host 127.0.0.1 --port 8000
```

页面入口：

- `GET /`

接口入口：

- `POST /api/v1/answers`

## 本次手工联调问题的根因

前端“提交后无反应”的真实根因在前端资源与初始化层，不在后端 API：

- 旧版实现对 `/`、`/frontend/app.js`、`/frontend/styles.css` 没有发送禁缓存头，浏览器可能继续使用旧静态资源。
- 前端脚本之前没有显式 boot 成功/失败状态；一旦浏览器拿到旧 HTML / JS，或脚本初始化出错，页面会表现成“点击提交没反应”。
- 样例按钮本来只填充输入框，不自动提交；此前没有明确写在页面上，容易造成交互误判。

## 本轮 smoke 方法

本地环境没有现成浏览器自动化依赖，因此本轮采用以下最小但可落地的验证组合：

1. 同源页面与静态资源真实可达性检查
2. 静态资源禁缓存头检查
3. 页面 DOM 结构与 `<script type="module">` 检查
4. 前端脚本事件绑定、fetch 调用、渲染逻辑检查
5. 三条冻结 query 的真实 HTTP 调用检查

## 结论

- frontend_entry_served: `True`
- same_origin_static_assets_served: `True`
- cache_busting_headers_enabled: `True`
- frontend_module_script_declared: `True`
- frontend_boot_visibility_added: `True`
- submit_handler_bound: `True`
- page_submit_should_post_api: `True`
- required_page_sections_present: `True`
- frontend_fetches_frozen_api: `True`
- strong_render_rule_supported: `True`
- weak_render_rule_supported: `True`
- refuse_render_rule_supported: `True`

## 页面入口检查

通过 `curl -s http://127.0.0.1:8000/` 验证：

- 页面标题为 `《伤寒论》RAG MVP`
- HTML 引用了 `/frontend/styles.css`
- HTML 引用了 `/frontend/app.js`
- HTML 通过 `<script type="module" src="/frontend/app.js"></script>` 加载脚本

## 静态资源与缓存头检查

通过 `curl -I -s` 验证：

- `GET /` -> `200`
- `GET /frontend/app.js` -> `200`
- `GET /frontend/styles.css` -> `200`
- 各响应都包含：
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`
  - `Pragma: no-cache`
  - `Expires: 0`

这一步的目的，是确保浏览器刷新时拿到的是最新前端文件，而不是继续复用旧脚本。

## DOM 结构检查

通过 `curl -s http://127.0.0.1:8000/ | rg ...` 验证页面包含以下关键区块：

- `query-input`
- `submit-button`
- `status-text`
- `review-notice-section`
- `refuse-section`
- `primary-section`
- `secondary-section`
- `review-section`
- `citations-section`
- `followups-section`

## 前端脚本检查

通过读取 `/frontend/app.js` 验证：

- 存在 `boot()` 初始化流程
- 存在 `window.__frontendBooted = true`
- 初始化失败时会把错误写回页面，不再静默失败
- 使用 `fetch("/api/v1/answers", { method: "POST" ... })`
- 请求体只发送 `JSON.stringify({ query })`
- 点击“提交查询”会进入 `submit` 监听逻辑
- 前端要求响应中存在以下顶层字段：
  - `query`
  - `answer_mode`
  - `answer_text`
  - `primary_evidence`
  - `secondary_evidence`
  - `review_materials`
  - `disclaimer`
  - `review_notice`
  - `refuse_reason`
  - `suggested_followup_questions`
  - `citations`
  - `display_sections`
- `primary_evidence` 为空时，主依据区会隐藏
- 三个证据区全空时，空证据提示区会显示
- `review_notice`、`refuse_reason`、`suggested_followup_questions` 会按字段值独立显隐

## 交互规则说明

- 点击样例按钮：只会把问题填入输入框，不会自动提交
- 点击“提交查询”：才会真实发出 `POST /api/v1/answers`
- 页面加载成功后，状态区应显示：`前端脚本已加载，等待提交`
- 请求发出时，状态区应显示：`正在请求 /api/v1/answers`
- 请求成功后，状态区应显示：`请求已完成`

## 冻结样例检查

### 1. `黄连汤方的条文是什么？`

- HTTP `200`
- `answer_mode = strong`
- `primary_evidence` 数量为 `3`
- 主依据 record_id 保持：
  - `safe:main_passages:ZJSHL-CH-010-P-0145`
  - `safe:main_passages:ZJSHL-CH-010-P-0146`
  - `safe:main_passages:ZJSHL-CH-010-P-0147`
- 修复后页面应显示 `answer_text`、主依据区、补充依据区、核对材料区、引用区
- 该页面实现会把以上 `record_id` 直接渲染到主依据卡片上，可用于核对黄连汤方主证据未回归

### 2. `烧针益阳而损阴是什么意思？`

- HTTP `200`
- `answer_mode = weak_with_review_notice`
- `primary_evidence` 数量为 `0`
- `secondary_evidence` 数量为 `3`
- `review_materials` 数量为 `2`
- `review_notice` 有值
- 修复后页面应隐藏主依据区，保留补充依据区和核对材料区分开显示，不渲染成确定答案姿态

### 3. `书中有没有提到量子纠缠？`

- HTTP `200`
- `answer_mode = refuse`
- `refuse_reason` 有值
- `suggested_followup_questions` 数量为 `3`
- `primary_evidence / secondary_evidence / review_materials / citations` 全为空
- 修复后页面应显示拒答原因、改问建议和空证据提示区；证据区为空时不报错

## 修复后页面提交是否真实发出 API 请求

已通过两类检查确认：

1. 源码检查：
   - `submit` 事件已绑定到表单
   - 提交逻辑调用 `fetch("/api/v1/answers", { method: "POST" ... })`
   - 请求体固定为 `JSON.stringify({ query })`
2. 真实 HTTP 检查：
   - 三条冻结 query 直接请求 `POST /api/v1/answers` 均返回 `200`
   - 模式分别保持 `strong / weak_with_review_notice / refuse`

因此，修复后的页面提交链路已经与当前冻结 API 合同对齐；只要页面状态区显示 `前端脚本已加载，等待提交`，点击“提交查询”就会真实进入该 POST 流程。

## 验证限制说明

本轮没有执行浏览器点击自动化，原因是当前环境缺少现成浏览器自动化依赖，且 Safari 未开启 Apple Events JavaScript。  
因此 smoke 结果基于：

- 同源页面已可打开
- 静态资源已可访问且禁缓存头已开启
- 页面结构已具备
- 前端脚本已绑定正确 API
- 前端启动失败将不再静默
- API 实调用结果已覆盖三模式

对这次“无反应”排障目标，这个验证强度已经足够；页面是否进入提交链路、以及提交后能否消费当前 payload，已经都有明确证据支撑。
