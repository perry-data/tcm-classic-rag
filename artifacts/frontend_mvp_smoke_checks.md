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

## 本轮 smoke 方法

本地环境没有现成浏览器自动化依赖，因此本轮 smoke 采用以下最小验证组合：

1. 同源页面可达性检查
2. 静态资源可达性检查
3. 页面 DOM 结构检查
4. 前端脚本对 `/api/v1/answers` 的 fetch 绑定检查
5. 三条冻结 query 的真实 HTTP 调用检查

## 结论

- frontend_entry_served: `True`
- same_origin_static_assets_served: `True`
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

- 使用 `fetch("/api/v1/answers", { method: "POST" ... })`
- 请求体只发送 `JSON.stringify({ query })`
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

## 冻结样例检查

### 1. `黄连汤方的条文是什么？`

- HTTP `200`
- `answer_mode = strong`
- `primary_evidence` 数量为 `3`
- 主依据 record_id 保持：
  - `safe:main_passages:ZJSHL-CH-010-P-0145`
  - `safe:main_passages:ZJSHL-CH-010-P-0146`
  - `safe:main_passages:ZJSHL-CH-010-P-0147`
- 该页面实现会把以上 `record_id` 直接渲染到主依据卡片上

### 2. `烧针益阳而损阴是什么意思？`

- HTTP `200`
- `answer_mode = weak_with_review_notice`
- `primary_evidence` 数量为 `0`
- `secondary_evidence` 数量为 `3`
- `review_materials` 数量为 `2`
- 页面实现会隐藏主依据区，保留补充依据区和核对材料区分开显示

### 3. `书中有没有提到量子纠缠？`

- HTTP `200`
- `answer_mode = refuse`
- `refuse_reason` 有值
- `suggested_followup_questions` 数量为 `3`
- `primary_evidence / secondary_evidence / review_materials / citations` 全为空
- 页面实现会隐藏证据区，显示拒答原因、改问建议和空证据提示区

## 风险说明

本轮没有执行真实浏览器点击自动化；因此 smoke 结果基于：

- 同源页面已可打开
- 静态资源已可访问
- 页面结构已具备
- 前端脚本已绑定正确 API
- API 实调用结果已覆盖三模式

对当前最小 MVP 来说，这一验证强度足以支持联调和毕设演示。
