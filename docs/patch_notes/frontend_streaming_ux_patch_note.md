# Frontend Streaming UX Patch Note

## 本轮目标

本轮只处理“提交问题后静默等待，结果整段突然出现”的体验问题。

约束保持不变：

- 不重写前端技术栈
- 不改最终 answer payload 顶层字段语义
- 不改 retrieval / rerank / prompt 主逻辑
- 不改 evaluator / goldset 主逻辑

## 本轮采用的方案

本轮采用的是：

- 最小后端流式事件接口
- 前端阶段性等待态
- `answer_text` 渐进显示

说明：

- 这不是直接从 `qwen-plus` 做 token 级透传的“真模型流式”。
- 当前实现是在保持正式主链与最终 payload 不变的前提下，新增一个最小 `NDJSON` 事件流接口。
- 页面优先消费事件流；当证据与最终 payload 已确定后，前端先稳定渲染证据区，再按分段事件渐进显示 `answer_text`。
- 若流式接口不可用，前端会回退到原 `POST /api/v1/answers`，但仍保留立即可见的等待态。

## 代码改动

### `backend/api/minimal_api.py`

- 保留原 `POST /api/v1/answers` 不变
- 新增 `POST /api/v1/answers/stream`
- 新增最小事件流协议：
  - `phase`
  - `evidence_ready`
  - `answer_delta`
  - `completed`
  - `error`
- 新增 `answer_text` 分段输出逻辑
- 服务启动日志补充流式端点

### `backend/answers/assembler.py`

- `assemble()` 新增可选 `progress_callback`
- 在不改变 payload 组装逻辑的前提下，补充三个阶段回调：
  - `retrieving_evidence`
  - `organizing_evidence`
  - `generating_answer`
- `strong / weak_with_review_notice / refuse` 三模式仍走原有裁决与组装逻辑

### `frontend/index.html`

- 在现有回答区内新增轻量进度区
- 页面文案补充“流式增强已接入”的说明

### `frontend/styles.css`

- 新增 `loading` 模式徽标
- 新增进度区样式
- 新增回答区最小高度与流式光标效果
- 保持现有视觉语言，不做整体 UI 改版

### `frontend/app.js`

- 提交后立即切换到显式等待态
- 优先调用 `/api/v1/answers/stream`
- 消费流式 `NDJSON` 事件并驱动阶段状态
- 在 `evidence_ready` 后先稳定渲染证据 / 引用 / 边界区块
- 使用 `answer_delta` 渐进渲染 `answer_text`
- 在 `completed` 时用最终 payload 收尾，避免残留半状态
- 流式不可用时回退到原 `POST /api/v1/answers`

## 交互变化

### 变更前

- 点击提交后页面只有按钮禁用
- 用户看不到系统处于哪一阶段
- 回答会在等待结束后整段替换出现

### 变更后

- 点击提交后 100% 立即可见反馈
- 页面会依次显示：
  - 正在检索依据
  - 正在组织证据
  - 正在生成回答
  - 已完成
- 证据区会先稳定下来
- `answer_text` 会按分段渐进出现
- 完成时统一切回最终 payload 展示，不留 loading 残影

## 稳定性边界

本轮明确保持：

- 原 `POST /api/v1/answers` contract 不变
- 最终消费仍是完整 answer payload
- `strong / weak_with_review_notice / refuse` 语义不变
- `primary_evidence / secondary_evidence / review_materials / citations` 语义不变

## 最小验证结果

已本地验证以下 query：

- `黄连汤方的条文是什么？` -> `strong`
- `烧针益阳而损阴是什么意思？` -> `weak_with_review_notice`
- `书中有没有提到量子纠缠？` -> `refuse`

验证内容包括：

- 同步 `POST /api/v1/answers` 三模式仍正确
- 流式 `POST /api/v1/answers/stream` 可返回阶段事件
- `evidence_ready -> answer_delta -> completed` 顺序可观察
- 最终 payload 未发生字段漂移

## 未做内容

- 未改 retrieval 逻辑
- 未改 prompt 策略
- 未改 evaluator
- 未做 React / Tailwind 重写
- 未做整体视觉重设计
- 未做多轮会话改造
