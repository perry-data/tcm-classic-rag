# Frontend MVP Spec

## 1. 目标

本轮只实现《伤寒论》RAG 系统的最小前端 MVP 页面，用来消费已冻结的最小接口：

- `POST /api/v1/answers`

前端职责只有：

- 输入 `query`
- 调用最小 API
- 按当前 answer payload 合同展示结果

本轮不重做后端，不修改 answer payload 顶层字段，不引入复杂前端工程。

## 2. 联调方案

本轮固定采用方案 A：前端与后端同源运行。

原因：

- 最省事
- 最稳定
- 不需要新增 CORS 支持
- 启动方式只有一条命令，便于毕设演示和验收

同源路由约定：

- `GET /` -> 前端单页入口
- `GET /frontend/styles.css` -> 样式文件
- `GET /frontend/app.js` -> 前端逻辑
- `POST /api/v1/answers` -> 现有最小 API

## 3. 页面结构

页面固定为单页，不做多页路由。

至少包含以下区域：

- 问题输入框
- 提交按钮
- 状态提示区
- 回答文本区
- 主依据区
- 补充依据区
- 核对材料区
- 引用区
- `review_notice` / `refuse_reason` / 改问建议区

## 4. 文件结构

本轮前端文件保持最小化：

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`

不引入：

- 打包器
- 前端框架
- 复杂构建配置
- 多页路由

## 5. 数据依赖边界

前端只允许依赖：

- `POST /api/v1/answers`
- `minimal_api_contract.md`
- `answer_payload_contract.md`

前端明确不依赖：

- Hybrid retrieval 内部细节
- rerank 分数
- sparse / dense 候选信息
- 未冻结的内部 trace 字段

## 6. 渲染规则

### 6.1 通用规则

- 所有展示都来自 answer payload 顶层字段。
- 证据对象统一展示：
  - `title`
  - `record_id`
  - `evidence_level`
  - `chapter_title`
  - `snippet`
  - `risk_flags`
- `record_id` 必须显示，便于验收样例直接核对。
- 证据区为空时必须优雅隐藏或给出空态说明，不能报错。

### 6.2 `strong`

- 突出 `answer_text`
- 突出 `primary_evidence`
- `secondary_evidence` 和 `review_materials` 作为补充显示
- `citations` 正常显示

### 6.3 `weak_with_review_notice`

- 突出 `review_notice`
- `primary_evidence` 为空时不显示主依据区
- `secondary_evidence` 与 `review_materials` 必须分区展示
- `answer_text` 按“待核对”语气展示，不包装成确定答案

### 6.4 `refuse`

- 突出 `refuse_reason`
- 展示 `suggested_followup_questions`
- 证据区为空时显示统一空态，不报错

## 7. 交互规则

- 用户输入问题后点击提交，前端发起：

```http
POST /api/v1/answers
Content-Type: application/json
```

请求体：

```json
{
  "query": "黄连汤方的条文是什么？"
}
```

- 请求中只发送 `query`
- 不发送任何 retrieval 内部参数
- `loading` 时禁用提交按钮并显示状态提示
- 请求失败时显示错误提示，不清空输入框

## 8. 启动方式

统一启动命令：

```bash
./.venv/bin/python -m backend.api.minimal_api --host 127.0.0.1 --port 8000
```

打开页面：

- [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 9. 本轮非目标

- 不改 `POST /api/v1/answers` 合同
- 不改 answer payload 顶层字段
- 不重构后端
- 不做复杂前端工程
- 不做鉴权
- 不做用户系统
- 不做历史记录
- 不做收藏 / 分享 / 深色模式 / 动画花活
- 不扩展多书
- 不恢复 `annotation_links`
