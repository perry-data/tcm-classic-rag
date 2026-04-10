# Frontend Streaming UX Demo

## 演示方式

当前仓库未额外产出浏览器录屏文件；本次使用真实本地接口回放与事件转录，说明“等待态 + 渐进显示”已经生效。

对应服务：

- 页面入口：`http://127.0.0.1:8001/`
- 同步接口：`POST /api/v1/answers`
- 流式接口：`POST /api/v1/answers/stream`

## 体验前后差异

### 变更前

- 提交后主要是静默等待
- 用户不知道系统卡在检索、证据裁决还是回答生成
- `answer_text` 在最后一次性整段出现

### 变更后

- 提交后立刻进入显式等待态
- 页面显示四步进度：
  - 正在检索依据
  - 正在组织证据
  - 正在生成回答
  - 已完成
- 在 `evidence_ready` 后先稳定渲染证据区
- `answer_text` 通过 `answer_delta` 分段出现

## 真实事件转录

### 1. `refuse` 示例

query：

- `书中有没有提到量子纠缠？`

观测到的事件顺序：

1. `phase` -> `retrieving_evidence`
2. `phase` -> `organizing_evidence`
3. `phase` -> `generating_answer`
4. `evidence_ready` -> `answer_mode = refuse`
5. `answer_delta`
6. `completed`

### 2. `strong` 示例

query：

- `黄连汤方的条文是什么？`

观测到的事件顺序：

1. `phase` -> `retrieving_evidence`
2. `phase` -> `organizing_evidence`
3. `phase` -> `generating_answer`
4. `evidence_ready` -> `answer_mode = strong`
5. 多个 `answer_delta`
6. `completed`

可见 `answer_text` 已按多段输出，而不是最终整段突现。

### 3. `weak_with_review_notice` 示例

query：

- `烧针益阳而损阴是什么意思？`

观测到的事件顺序：

1. `phase` -> `retrieving_evidence`
2. `phase` -> `organizing_evidence`
3. `phase` -> `generating_answer`
4. `evidence_ready` -> `answer_mode = weak_with_review_notice`
5. `answer_delta`
6. `completed`

同时保持：

- `primary_evidence = []`
- `review_notice` 仍存在
- `secondary_evidence` 与 `review_materials` 分区语义未变

## 验收结论

本轮已经满足最小可用目标：

- 提交后立即有可见反馈
- 不再是静默等待后整段突现
- `answer_text` 具备渐进显示
- `strong / weak / refuse` 三模式都已测通
- 最终 payload 消费方式未变
