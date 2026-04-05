# Frontend MVP Examples

## 页面用途

当前前端 MVP 是一个单页演示页，用来消费：

- `POST /api/v1/answers`

页面固定展示：

- 问题输入框
- 提交按钮
- 状态提示
- 回答文本
- 主依据
- 补充依据
- 核对材料
- 引用
- 核对提示 / 拒答原因 / 改问建议

## 冻结样例 1

### Query

`黄连汤方的条文是什么？`

### 页面展示摘要

- mode badge 显示 `strong`
- 回答区显示 `answer_text`
- 主依据区显示 3 条主证据卡片
- 主证据卡片中应直接看到以下 `record_id`
  - `safe:main_passages:ZJSHL-CH-010-P-0145`
  - `safe:main_passages:ZJSHL-CH-010-P-0146`
  - `safe:main_passages:ZJSHL-CH-010-P-0147`
- 补充依据区继续显示“葛根黄芩黄连汤方”相关降级材料，但它们只在 `secondary_evidence`
- 核对材料区继续独立显示 `review_materials`
- 引用区显示 3 条 `primary` citations
- 页面不把降级材料渲染成主依据

## 冻结样例 2

### Query

`烧针益阳而损阴是什么意思？`

### 页面展示摘要

- mode badge 显示 `weak_with_review_notice`
- 核对提示区高亮显示 `review_notice`
- 回答区显示弱表述的 `answer_text`
- 主依据区隐藏
- 补充依据区显示 3 条 `secondary_evidence`
- 核对材料区显示 2 条 `review_materials`
- 引用区显示 `secondary` 与 `review` 两类 citations
- 页面不会把该结果渲染成“已确认答案”

## 冻结样例 3

### Query

`书中有没有提到量子纠缠？`

### 页面展示摘要

- mode badge 显示 `refuse`
- 回答区显示统一拒答话术
- 拒答原因区显示 `refuse_reason`
- 改问建议区显示 3 条 `suggested_followup_questions`
- 主依据 / 补充依据 / 核对材料 / 引用区全部隐藏
- 空证据提示区显示“当前结果没有可展示证据。若为拒答模式，这是预期行为。”

## 页面与 payload 的映射关系

| 页面区块 | payload 字段 |
| --- | --- |
| 回答区 | `answer_text` |
| 核对提示区 | `review_notice` |
| 拒答原因区 | `refuse_reason` |
| 主依据区 | `primary_evidence` |
| 补充依据区 | `secondary_evidence` |
| 核对材料区 | `review_materials` |
| 引用区 | `citations` |
| 改问建议区 | `suggested_followup_questions` |

## 本轮保持不变

- 没有改 answer payload 顶层字段
- 没有改 `POST /api/v1/answers` 合同
- 没有改 Hybrid retrieval / answer assembler 的业务规则
