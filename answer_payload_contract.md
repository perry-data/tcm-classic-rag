# Answer Payload Contract

## 目标

`run_answer_assembler.py` 的唯一职责，是把当前最小检索结果组装成稳定、可展示、可直接供后续 API / 前端消费的 answer payload。

本层不负责：

- 前端展示
- HTTP API
- 向量检索
- LLM 生成
- 数据库结构修改

## 顶层字段

每个 answer payload 至少包含以下字段：

| field | type | required | 说明 |
| --- | --- | --- | --- |
| `query` | `string` | yes | 用户原始问题 |
| `answer_mode` | `string` | yes | `strong` / `weak_with_review_notice` / `refuse` |
| `answer_text` | `string` | yes | 模板化回答文本 |
| `primary_evidence` | `array` | yes | 仅允许主证据记录 |
| `secondary_evidence` | `array` | yes | 仅允许辅助证据记录 |
| `review_materials` | `array` | yes | 仅允许风险层 / 核对材料 |
| `disclaimer` | `string \| null` | yes | 模式相关说明 |
| `review_notice` | `string \| null` | yes | 核对提示；`weak_with_review_notice` 必须有值 |
| `refuse_reason` | `string \| null` | yes | `refuse` 模式下的拒答原因 |
| `suggested_followup_questions` | `array` | yes | `refuse` 模式下的改问建议 |
| `citations` | `array` | yes | 用于展示与定位的引用对象 |
| `display_sections` | `array` | yes | 面向展示层的稳定区块定义 |

## Evidence Item 结构

`primary_evidence`、`secondary_evidence`、`review_materials` 中的每个对象使用统一结构：

| field | type | 说明 |
| --- | --- | --- |
| `record_id` | `string` | 数据库记录主键 |
| `record_type` | `string` | `main_passages` / `annotations` / `passages` / `ambiguous_passages` |
| `display_role` | `string` | `primary` / `secondary` / `review` |
| `title` | `string` | 简短标签，优先使用方名 / 标题锚点 |
| `evidence_level` | `string` | `A` / `B` / `C` |
| `chapter_id` | `string \| null` | 章节 ID |
| `chapter_title` | `string \| null` | 章节标题 |
| `snippet` | `string` | 展示用短摘录 |
| `risk_flags` | `array` | 风险标签数组 |

## Citation 结构

`citations` 中的每个对象至少保留：

| field | type | 说明 |
| --- | --- | --- |
| `citation_id` | `string` | payload 内局部引用 ID |
| `record_id` | `string` | 对应证据记录 |
| `record_type` | `string` | 证据对象类型 |
| `title` | `string` | 简短标签 |
| `evidence_level` | `string` | 证据层级 |
| `snippet` | `string` | 摘录 |
| `chapter_id` | `string \| null` | 章节 ID |
| `chapter_title` | `string \| null` | 章节标题 |
| `citation_role` | `string` | `primary` / `secondary` / `review` |

## Display Sections 结构

`display_sections` 负责定义展示区块顺序和可见性，不重复承载调试信息。

推荐固定区块：

| section_id | field | 说明 |
| --- | --- | --- |
| `answer` | `answer_text` | 主回答文本 |
| `review_notice` | `review_notice` | 核对提示区 |
| `primary_evidence` | `primary_evidence` | 主依据区 |
| `secondary_evidence` | `secondary_evidence` | 补充依据区 |
| `review_materials` | `review_materials` | 核对材料区 |
| `citations` | `citations` | 引用区 |
| `refusal_guidance` | `suggested_followup_questions` | 拒答改问建议区 |

每个 section 至少包含：

- `section_id`
- `title`
- `section_type`
- `visible`
- `field`

## 模式约束

### `strong`

- `answer_text` 必须优先来自 `primary_evidence`
- `primary_evidence` 只能包含 `main_passages`
- `secondary_evidence` 只能作补充
- `review_materials` 只能作说明 / 提示，不得进入主依据
- `citations` 必须主要来自 `primary_evidence`

### `weak_with_review_notice`

- 必须显式提示“正文强证据不足，以下内容需核对”或等价表达
- `answer_text` 只能使用弱表述
- `primary_evidence` 必须为空
- `secondary_evidence` 与 `review_materials` 必须分区展示
- 不得把辅助材料包装成强证据

### `refuse`

- 必须输出统一拒答结构
- 不得伪造答案
- 必须提供 `refuse_reason`
- 必须提供 `suggested_followup_questions`

## 分层禁令

以下规则在 answer assembler 层继续强制保持：

- `annotation_links` 完全禁用
- `chunks` 只允许召回，不直接进入 `primary_evidence`
- `annotations` 只允许进入 `secondary_evidence`
- `passages` / `ambiguous_passages` 只允许进入 `review_materials`
- 不得破坏现有 `strong / weak_with_review_notice / refuse` 三模式框架
- 不得破坏“黄连汤方”主证据精度补丁
