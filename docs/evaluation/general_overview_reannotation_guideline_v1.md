# General Overview Reannotation Guideline v1

- 文档日期：2026-04-08
- 适用范围：`question_type = general_overview`
- 本轮排除：`question_id = eval_seed_q004`
- 本轮目标：把常规总括类题中依赖系统样例、弱来源说明或 evaluator replay 回填的 gold，收紧为可由 `main_passages` 中多个稳定分支条文独立说明的 gold

## 1. 什么叫 general_overview 的独立 gold

general_overview 的独立 gold 必须先从题面主题出发，而不是从当前系统 citations 出发。

本轮采用的独立 gold 标准：

1. 先识别题面主题，例如“太阳病应该怎么办”“阳明病有哪些情况”“霍乱病应该怎么办”。
2. 到 `data/processed/zjshl_dataset_v2/main_passages.json` 中核对直接属于该主题的分支条文。
3. 先确定“最小稳定分支集合”，再决定 `gold_record_ids`、`gold_passage_ids` 和 `gold_evidence_spans`。
4. strong 题必须由多个稳定 `main_passages` 分支支撑，不得退化为单条直答。
5. weak 题保留 `weak_with_review_notice` 和 `must_keep_primary_empty`，证据角色只用 `secondary` 或 `review`。
6. 若只能依赖当前 replay citations 才知道 gold 是什么，或主题边界容易被系统输出牵引，不得标为 `manual_independent`。

## 2. evidence_role 写法

1. `primary`：只用于 strong 题中可直接支撑总括回答的稳定分支条文。
2. `secondary`：主题定义、治法语境、同一主题下的补充分支条文、weak 题中的主要整理依据。
3. `review`：远端语境、传经语境、预后或欲解时等可帮助核对但不应支撑强结论的材料。

## 3. gold_record_ids / gold_passage_ids 写法

1. 本轮 general_overview gold 只使用 `safe:main_passages:<passage_id>`。
2. 来源指向 `data/processed/zjshl_dataset_v2/main_passages.json`。
3. 不继续把 `full:passages:*` 或 `full:ambiguous_passages:*` 作为 gold 来源。
4. `gold_passage_ids` 保持 canonical passage id 去重。
5. strong 题至少保留两个以上稳定分支条文；weak 题不得加入 `primary` evidence。

## 4. q004 排除规则

`eval_seed_q004` 是“少阴病应该怎么办？”专项样本，audit 中已标为 `needs_reannotation`。它曾因当前正式系统实际 citations 扩展过 gold 集合，主题覆盖口径需要单独定义。

本轮不读取 q004 作为重标目标，不更新它的 `gold_source_type`、gold ids、evidence spans 或 `source_refs`。q004 继续保留给后续专项重标。

## 5. 本轮处理边界

1. 只处理 `question_type = general_overview` 且 `question_id != eval_seed_q004`。
2. 不处理 `source_lookup`、`comparison`、`meaning_explanation`、`refusal`。
3. 不新增题目。
4. 不改 retrieval / rerank / gating / answer assembler，不改 API / frontend，不重写 evaluator v1。
