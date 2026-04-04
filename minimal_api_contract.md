# Minimal API Contract

## 1. 文档目标

本文件定义前端未来应依赖的最小后端接口合同。

即使本轮还不实现 HTTP API，也先冻结 transport 层的最小形态，保证前端不会直接依赖脚本细节、检索 trace 或非稳定字段。

## 2. 最小接口定义

建议前端统一依赖一个最小接口：

- `POST /api/v1/answers`

接口职责：

- 输入一个 `query`
- 返回一个完整 answer payload

本接口的响应体不再额外包一层 `data`，而是直接返回当前 answer payload 对象本身。这样可保持与 `answer_payload_contract.md` 一致，避免前后端双重合同。

## 3. 请求合同

### 3.1 请求头

- `Content-Type: application/json`

### 3.2 请求体

```json
{
  "query": "黄连汤方的条文是什么？"
}
```

### 3.3 请求字段

| field | type | required | 说明 |
| --- | --- | --- | --- |
| `query` | `string` | yes | 用户原始问题；前端当前唯一应依赖的输入字段 |

### 3.4 输入约束

- `query` 必须是非空字符串。
- 前端提交原始用户输入即可，不需要自行做 query 归一化。
- 前端不应自行拼接检索参数、模式参数或证据层级参数。

### 3.5 未来可扩展字段

以下字段即使未来出现，当前前端也不应依赖：

- `debug`
- `trace`
- `candidate_limit`
- `scope_filters`
- `book_id`
- `session_id`

这些字段即便未来存在，也只能视为扩展能力，不属于本轮最小 contract。

## 4. 响应合同

### 4.1 响应语义

- `strong`、`weak_with_review_notice`、`refuse` 都是业务上的合法响应。
- 前端必须通过 `answer_mode` 判断展示分支，而不是通过 HTTP 状态码猜测。
- `refuse` 不是接口错误，而是“已成功完成检索与裁决后的拒答结果”。

### 4.2 响应体

响应体直接等于当前 answer payload，对象至少包含以下字段：

| field | type | required | 说明 |
| --- | --- | --- | --- |
| `query` | `string` | yes | 回显用户原始问题 |
| `answer_mode` | `string` | yes | `strong` / `weak_with_review_notice` / `refuse` |
| `answer_text` | `string` | yes | 当前模式下的回答文本；三模式都必须存在 |
| `primary_evidence` | `array` | yes | 主证据数组 |
| `secondary_evidence` | `array` | yes | 补充依据数组 |
| `review_materials` | `array` | yes | 核对材料数组 |
| `disclaimer` | `string \| null` | yes | 模式相关说明 |
| `review_notice` | `string \| null` | yes | 核对提示 |
| `refuse_reason` | `string \| null` | yes | 拒答原因 |
| `suggested_followup_questions` | `array` | yes | 拒答后的改问建议 |
| `citations` | `array` | yes | 展示引用对象 |
| `display_sections` | `array` | yes | 稳定的展示区块定义 |

### 4.3 Evidence Item 结构

`primary_evidence`、`secondary_evidence`、`review_materials` 中的对象使用统一结构：

| field | type | required | 说明 |
| --- | --- | --- | --- |
| `record_id` | `string` | yes | 记录 ID |
| `record_type` | `string` | yes | `main_passages` / `annotations` / `passages` / `ambiguous_passages` |
| `display_role` | `string` | yes | `primary` / `secondary` / `review` |
| `title` | `string` | yes | 展示标题 |
| `evidence_level` | `string` | yes | `A` / `B` / `C` |
| `chapter_id` | `string \| null` | yes | 章节 ID |
| `chapter_title` | `string \| null` | yes | 章节标题 |
| `snippet` | `string` | yes | 展示摘录 |
| `risk_flags` | `array` | yes | 风险标签数组 |

### 4.4 Citation 结构

| field | type | required | 说明 |
| --- | --- | --- | --- |
| `citation_id` | `string` | yes | payload 内局部引用 ID |
| `record_id` | `string` | yes | 对应证据记录 |
| `record_type` | `string` | yes | 证据对象类型 |
| `title` | `string` | yes | 简短标签 |
| `evidence_level` | `string` | yes | 证据层级 |
| `snippet` | `string` | yes | 展示摘录 |
| `chapter_id` | `string \| null` | yes | 章节 ID |
| `chapter_title` | `string \| null` | yes | 章节标题 |
| `citation_role` | `string` | yes | `primary` / `secondary` / `review` |

### 4.5 Display Section 结构

`display_sections` 用于给前端提供稳定的显示顺序和区块可见性。

每个 section 至少包含：

- `section_id`
- `title`
- `section_type`
- `visible`
- `field`

当前固定 section 语义如下：

| section_id | field | 说明 |
| --- | --- | --- |
| `answer` | `answer_text` | 主回答文本 |
| `review_notice` | `review_notice` | 核对提示 |
| `primary_evidence` | `primary_evidence` | 主依据 |
| `secondary_evidence` | `secondary_evidence` | 补充依据 |
| `review_materials` | `review_materials` | 核对材料 |
| `citations` | `citations` | 引用 |
| `refusal_guidance` | `suggested_followup_questions` | 改问建议 |

## 5. 三种模式的前端依赖说明

### 5.1 `strong`

前端应这样依赖：

- 重点展示 `answer_text`
- 展示 `primary_evidence`
- `secondary_evidence` / `review_materials` 作为补充
- `citations` 默认可展示
- `review_notice` 如果存在，应作为“补充说明”而不是风险警报

前端不应这样做：

- 不要把 `secondary_evidence` 当成主结论来源
- 不要忽略 `primary_evidence` 而只展示文本

### 5.2 `weak_with_review_notice`

前端应这样依赖：

- 不显示主结论姿态
- 强调 `review_notice`
- 弱化 `answer_text` 的确定性表达
- 分区展示 `secondary_evidence` 与 `review_materials`
- `primary_evidence` 预期为空，前端应按空数组处理
- `citations` 可以展示，但应与 `secondary_evidence` / `review_materials` 对齐理解

前端不应这样做：

- 不要把 `answer_text` 渲染成“已确认答案”
- 不要把 `secondary_evidence` 与 `review_materials` 混成同一证据层

### 5.3 `refuse`

前端应这样依赖：

- 展示 `refuse_reason`
- 展示 `suggested_followup_questions`
- `answer_text` 只视为统一拒答话术，不视为正文答案
- `primary_evidence`、`secondary_evidence`、`review_materials`、`citations` 应按空数组处理

前端不应这样做：

- 不要把 `refuse` 当作接口异常页
- 不要因为证据为空就推断接口失败

## 6. HTTP 状态建议

为了让前端逻辑稳定，建议 transport 层遵守以下最小状态约定：

- `200 OK`：成功返回 answer payload，包含 `strong` / `weak_with_review_notice` / `refuse`
- `400 Bad Request`：请求体缺失或 `query` 非法
- `500 Internal Server Error`：后端执行失败

前端业务分支必须依赖 `answer_mode`，而不是依赖 `200` 之内再拆别的状态码。

## 7. 最小示例

以下示例为“节选版骨架”，用来说明结构，不代表完整数组长度；但所有字段都按当前合同保留。

### 7.1 Strong 示例骨架

```json
{
  "query": "黄连汤方的条文是什么？",
  "answer_mode": "strong",
  "answer_text": "根据主依据，与“黄连汤方”直接对应的条文主要有：...",
  "primary_evidence": [
    {
      "record_id": "safe:main_passages:ZJSHL-CH-010-P-0145",
      "record_type": "main_passages",
      "display_role": "primary",
      "title": "黄连汤方",
      "evidence_level": "A",
      "chapter_id": "ZJSHL-CH-010",
      "chapter_title": "辨太阳病脉证并治法第七",
      "snippet": "黄连汤方：黄连味苦寒...",
      "risk_flags": []
    }
  ],
  "secondary_evidence": [
    {
      "record_id": "safe:main_passages:ZJSHL-CH-009-P-0017",
      "record_type": "main_passages",
      "display_role": "secondary",
      "title": "葛根黄芩黄连汤方",
      "evidence_level": "A",
      "chapter_id": "ZJSHL-CH-009",
      "chapter_title": "辨太阳病脉证并治第六",
      "snippet": "葛根半斤 甘草二两...",
      "risk_flags": [
        "topic_mismatch_demoted"
      ]
    }
  ],
  "review_materials": [
    {
      "record_id": "full:passages:ZJSHL-CH-010-P-0145",
      "record_type": "passages",
      "display_role": "review",
      "title": "黄连汤方",
      "evidence_level": "C",
      "chapter_id": "ZJSHL-CH-010",
      "chapter_title": "辨太阳病脉证并治法第七",
      "snippet": "黄连汤方：黄连味苦寒...",
      "risk_flags": [
        "ledger_mixed_roles"
      ]
    }
  ],
  "disclaimer": "主证据优先；补充依据与核对材料不参与主结论判定。",
  "review_notice": "以下补充依据与核对材料仅作说明，不作为主依据。",
  "refuse_reason": null,
  "suggested_followup_questions": [],
  "citations": [
    {
      "citation_id": "c1",
      "record_id": "safe:main_passages:ZJSHL-CH-010-P-0145",
      "record_type": "main_passages",
      "title": "黄连汤方",
      "evidence_level": "A",
      "snippet": "黄连汤方：黄连味苦寒...",
      "chapter_id": "ZJSHL-CH-010",
      "chapter_title": "辨太阳病脉证并治法第七",
      "citation_role": "primary"
    }
  ],
  "display_sections": [
    {
      "section_id": "answer",
      "title": "回答",
      "section_type": "text",
      "visible": true,
      "field": "answer_text"
    },
    {
      "section_id": "primary_evidence",
      "title": "主依据",
      "section_type": "slot_ref",
      "visible": true,
      "field": "primary_evidence"
    },
    {
      "section_id": "citations",
      "title": "引用",
      "section_type": "slot_ref",
      "visible": true,
      "field": "citations"
    }
  ]
}
```

### 7.2 Weak 示例骨架

```json
{
  "query": "烧针益阳而损阴是什么意思？",
  "answer_mode": "weak_with_review_notice",
  "answer_text": "正文强证据不足，以下内容需核对，暂不能视为确定答案。...",
  "primary_evidence": [],
  "secondary_evidence": [
    {
      "record_id": "full:annotations:ZJSHL-CH-003-P-0016",
      "record_type": "annotations",
      "display_role": "secondary",
      "title": "烧针益阳而损阴",
      "evidence_level": "B",
      "chapter_id": "ZJSHL-CH-003",
      "chapter_title": "辨脉法第一",
      "snippet": "卫阳也，荣阴也。烧针益阳而损阴...",
      "risk_flags": []
    }
  ],
  "review_materials": [
    {
      "record_id": "full:ambiguous_passages:ZJSHL-CH-003-P-0016",
      "record_type": "ambiguous_passages",
      "display_role": "review",
      "title": "烧针益阳而损阴",
      "evidence_level": "C",
      "chapter_id": "ZJSHL-CH-003",
      "chapter_title": "辨脉法第一",
      "snippet": "烧针益阳而损阴...",
      "risk_flags": [
        "ambiguous_source"
      ]
    }
  ],
  "disclaimer": "当前只输出弱表述与核对材料，不输出确定性答案。",
  "review_notice": "正文强证据不足，以下内容需核对，不应视为确定答案。",
  "refuse_reason": null,
  "suggested_followup_questions": [],
  "citations": [
    {
      "citation_id": "c1",
      "record_id": "full:annotations:ZJSHL-CH-003-P-0016",
      "record_type": "annotations",
      "title": "烧针益阳而损阴",
      "evidence_level": "B",
      "snippet": "卫阳也，荣阴也。烧针益阳而损阴...",
      "chapter_id": "ZJSHL-CH-003",
      "chapter_title": "辨脉法第一",
      "citation_role": "secondary"
    }
  ],
  "display_sections": [
    {
      "section_id": "review_notice",
      "title": "核对提示",
      "section_type": "notice",
      "visible": true,
      "field": "review_notice"
    },
    {
      "section_id": "secondary_evidence",
      "title": "补充依据",
      "section_type": "slot_ref",
      "visible": true,
      "field": "secondary_evidence"
    },
    {
      "section_id": "review_materials",
      "title": "核对材料",
      "section_type": "slot_ref",
      "visible": true,
      "field": "review_materials"
    }
  ]
}
```

### 7.3 Refuse 示例骨架

```json
{
  "query": "书中有没有提到量子纠缠？",
  "answer_mode": "refuse",
  "answer_text": "当前未检索到足以支撑回答的依据，暂不提供答案。",
  "primary_evidence": [],
  "secondary_evidence": [],
  "review_materials": [],
  "disclaimer": "当前为统一拒答结构，不输出推测性答案。",
  "review_notice": null,
  "refuse_reason": "未检索到足以支撑回答的主证据、辅助证据或可供核对的风险材料。",
  "suggested_followup_questions": [
    "请改问具体条文，例如：某一条文的原文或含义是什么？"
  ],
  "citations": [],
  "display_sections": [
    {
      "section_id": "answer",
      "title": "回答",
      "section_type": "text",
      "visible": true,
      "field": "answer_text"
    },
    {
      "section_id": "refusal_guidance",
      "title": "改问建议",
      "section_type": "list",
      "visible": true,
      "field": "suggested_followup_questions"
    }
  ]
}
```

## 8. 前端的唯一稳定依赖结论

前端未来只应依赖这一件事：

- 发送 `query`
- 收到 answer payload
- 基于 `answer_mode` 和 `display_sections` 决定展示分支

除此之外，前端不应绑定任何内部检索实现细节。
