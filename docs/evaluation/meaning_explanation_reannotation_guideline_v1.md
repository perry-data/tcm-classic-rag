# Meaning Explanation Reannotation Guideline v1

- 文档日期：2026-04-08
- 适用范围：`question_type = meaning_explanation`
- 本轮目标：把解释类题中依赖系统样例、弱来源说明或 evaluator replay 回填的 gold，收紧为可由正文、注解或紧邻解释材料独立说明的 gold

## 1. 什么叫 meaning_explanation 的独立 gold

meaning_explanation 的独立 gold 必须先从题面句子或概念出发，而不是从当前系统 citations 出发。

本轮采用的独立 gold 标准：

1. 先识别题面要求解释的句子、短语或概念，例如“阳为气，阴为血”“蔼蔼如车盖”。
2. 到 `data/processed/zjshl_dataset_v2/annotations.json` 中核对直接解释该句的注解。
3. 到 `data/processed/zjshl_dataset_v2/main_passages.json` 中核对题面句的正文出处、同义正文或紧邻上下文。
4. strong 题可以用正文主条作为 `primary`；注解只在不改变强弱边界时作为 `secondary` 或 `review`。
5. weak 题即使注解解释得很顺，也不自动升成 `primary`；应保留 `weak_with_review_notice` 和 `must_keep_primary_empty`，把注解/正文放在 `secondary` 或 `review`。
6. 若只能依赖系统 replay 才知道 gold 是什么，或无法判断解释材料与题面是否对应，不得标为 `manual_independent`。

## 2. evidence_role 写法

1. `primary`：只用于 strong 题中可直接回答题面的正文主条或同等稳定正文证据。
2. `secondary`：直接解释题面句的注解、题面句正文出处、紧邻解释材料、同义概念正文。
3. `review`：远端同概念材料、跨章节引用、可帮助核对但不应支撑强结论的材料。

## 3. gold_record_ids / gold_passage_ids 写法

1. 注解层使用 `full:annotations:<passage_id>`，来源指向 `data/processed/zjshl_dataset_v2/annotations.json`。
2. 正文层使用 `safe:main_passages:<passage_id>`，来源指向 `data/processed/zjshl_dataset_v2/main_passages.json`。
3. 不继续把 `full:passages:*` 或 `full:ambiguous_passages:*` 作为唯一 gold 来源；如需使用完整层命中，只通过 canonical passage id 与人工核对段对应。
4. `gold_passage_ids` 保持 canonical passage id 去重。
5. weak 题可有 gold 引用要求，但 gold evidence roles 应避免 `primary`，以免和 `must_keep_primary_empty` 的评估边界冲突。

## 4. 本轮处理边界

1. 只处理 `question_type = meaning_explanation`。
2. 不处理 `source_lookup`、`comparison`、`general_overview`、`refusal`。
3. 不处理 q004 单独重标，不新增题目。
4. 不改 retrieval / rerank / gating / answer assembler，不改 API / frontend，不重写 evaluator v1。
