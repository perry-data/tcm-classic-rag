# 评估规格说明 v1

- 文档版本：v1
- 文档日期：2026-04-06
- 文档定位：定义当前正式系统的评估对象、题型、维度与边界

## 1. 评估目标

当前评估基线 v1 的目标，不是立刻给出“系统最终效果分数”，而是先把论文第 4 章、答辩演示与后续功能回归所需的评估口径正式建立起来。

本轮评估要回答四个核心问题：

1. 当前 retrieval 是否能命中人工确认过的标准依据。
2. 当前 citations 是否正确指向应当被引用的条文/材料。
3. 当前 `answer_mode` 是否与问题类型和证据强度匹配。
4. 当前系统是否出现“无证据强答”或“错引后强答”。

## 2. 当前正式系统边界

本评估规格严格对应当前正式系统边界：

`query -> hybrid retrieval -> evidence gating -> answer assembler -> POST /api/v1/answers -> frontend`

因此，v1 评估只覆盖：

1. 《伤寒论》单书范围。
2. 当前 hybrid retrieval 主链。
3. 当前 evidence gating 与 answer assembler。
4. 当前冻结的 answer payload contract。

v1 评估明确不覆盖：

1. 真实 LLM / Prompt 栈效果。
2. 多书混合检索表现。
3. 用户满意度问卷与大规模线上日志评估。
4. 新功能补丁带来的额外能力。

## 3. 题型定义

当前 goldset 与人工标注至少覆盖以下五类问题：

| question_type | 中文名称 | 典型问题 | 当前主要判定点 |
| --- | --- | --- | --- |
| `source_lookup` | 条文/出处类 | `黄连汤方的条文是什么？` | 主条是否稳定命中，主引用是否正确 |
| `meaning_explanation` | 含义解释类 | `烧针益阳而损阴是什么意思？` | 是否正确降级为弱回答，是否避免把注解包装成主依据 |
| `general_overview` | 泛问/总括类 | `太阳病应该怎么办？` | 是否按分支整理，是否在证据不足时降级 |
| `comparison` | 比较类 | `A 和 B 的区别是什么？` | 是否只在证据足够时比较，是否保持 pairwise 边界 |
| `refusal` | 无证据拒答类 | `书中有没有提到量子纠缠？` | 是否正确拒答，是否给出改问建议 |

## 4. 评估维度

### 4.1 Retrieval 命中

目标是判断：系统候选或最终引用中，是否出现人工标注的 gold 条文。

v1 重点记录：

1. `gold_passage_ids` 在 TopK 中是否命中。
2. `gold_record_ids` 是否被最终 payload 引用。
3. 多分支问题是否至少命中若干核心分支，而不是只命中一条边缘材料。

建议在后续扩容阶段统计：

- `Hit@K`
- `Recall@K`
- 题型分组命中率

### 4.2 引用正确性

目标是判断：系统给出的 citations，是否真的对应当前问题的标准依据。

v1 的人工核对重点：

1. 引用记录是否落在 `gold_record_ids` 或同一 `gold_passage_ids` 上。
2. 引用角色是否合理。
3. 是否把只能作 `secondary` 或 `review` 的材料误包装为主依据。

### 4.3 `answer_mode` 合理性

目标是判断：系统选择 `strong / weak_with_review_notice / refuse` 是否符合问题类型与证据强度。

核心规则：

1. `strong` 必须建立在稳定主证据上。
2. `weak_with_review_notice` 必须显式承认证据不足，且 `primary_evidence` 为空。
3. `refuse` 必须给出拒答理由，并保持证据槽位为空。

### 4.4 无证据强答

目标是识别最需要在论文中单独说明的失败类型。

v1 中以下情形记为失败：

1. 没有 gold 证据却给出确定性结论。
2. 引用与结论不匹配，但仍以强回答呈现。
3. 明显超出当前功能边界的问题被系统伪装成“已回答”。

### 4.5 证据分层一致性

该维度是引用检查的补充项，用来确保评估口径与当前系统 spec 一致。

重点看：

1. `primary_evidence` 是否仍只来自合规 `main_passages`。
2. `secondary_evidence` 是否承载注解或降级条文。
3. `review_materials` 是否仍只是核对材料而非主结论来源。

## 5. 评估样本单元

v1 goldset 的基本评估单元是一条“问题样本”，每条样本至少包含：

1. `question_id`
2. `query`
3. `question_type`
4. `expected_mode`
5. `gold_record_ids`
6. `gold_passage_ids`
7. `gold_evidence_spans`
8. `annotation_notes`
9. `citation_check_required`

其中：

1. `gold_record_ids` 用于精确引用核对。
2. `gold_passage_ids` 用于把 safe/full 等对象层折叠到同一 canonical passage 上，便于做 retrieval 命中统计。
3. `gold_evidence_spans` 用于记录 1-3 段最核心证据片段，支撑人工核对引用与答案。

## 6. v1 边界说明

当前 v1 评估基线明确是“可运行、可标注、可扩写”的第一版，而不是完整终版。

本轮只正式建立：

1. 评估规格文档。
2. 标注规范文档。
3. goldset schema。
4. seed goldset。
5. smoke checks。

本轮暂不正式建立：

1. 自动化 evaluator runner。
2. 大规模统计报表。
3. 双人标注一致性报告。
4. 200–250 条完整金标准集。

## 7. 与论文第 4 章的对应关系

当前 v1 基线可以直接承接论文第 4 章中的三部分内容：

1. 测试方案：功能 smoke + seed goldset + 人工核对引用。
2. 结果口径：按题型报告命中、模式和引用情况。
3. 失败分析：重点分析错引、弱答、拒答与无证据强答。

因此，本规格的正式意义是：先把“评估什么、怎么评、边界在哪里”冻结下来，再扩写样本规模。
