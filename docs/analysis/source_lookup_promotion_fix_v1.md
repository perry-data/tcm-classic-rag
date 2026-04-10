# Batch A source_lookup promotion fix v1

## 目标范围

本轮只修 `eval_seed_q076` 和 `eval_seed_q082` 暴露出的 source_lookup strong 晋级问题，不修改 `goldset_v2_working_102.json`，不修改旧 72 条，不继续 Batch B，也不处理 `eval_seed_q093` / `eval_seed_q095` / `eval_seed_q096`。

## 失败根因

修复前，两题的 gold citation check 均已通过，但 actual_mode 仍为 `weak_with_review_notice`。原因不是检索不到 gold，而是 retrieval 的 topic consistency 判断使用未清洗的方名标题锚点，把 A 层 main_passages 方文误判为 `different_formula_anchor` 并降级到 secondary。

| question_id | query | gold 命中情况 | 修复前 actual_mode | 根因 |
| --- | --- | --- | --- | --- |
| `eval_seed_q076` | 麻黄杏仁甘草石膏汤方的条文是什么？ | `ZJSHL-CH-009-P-0100`、`ZJSHL-CH-009-P-0102` 已在 citations 中命中 | `weak_with_review_notice` | 方文标题为 `麻黄杏人赵本作「仁」甘草石膏汤方`，校注与杏人/杏仁异文导致 exact formula anchor 未命中 |
| `eval_seed_q082` | 麻子仁丸方的条文是什么？ | `ZJSHL-CH-011-P-0172`、`ZJSHL-CH-011-P-0174` 已在 citations 中命中 | `weak_with_review_notice` | 方文标题为 `麻赵本有「子」字仁丸方`，校注插入导致 exact formula anchor 未命中 |

由于 primary_evidence 为空，retrieval mode 被 `_determine_mode()` 正常压成 `weak_with_review_notice`。这符合现有 gating 机制，但暴露出方名锚点归一不足。

## 修复策略

在 `backend/retrieval/minimal.py` 的方名主题一致性判断中补充窄口径方名锚点归一：

- 新增 raw title anchor 抽取，避免过早 compact 后丢失 `「...」` 校注结构。
- 对 `赵本有「...」字`、`赵本/医统本并有「...」字` 这类插入型校注，将引号内文本还原到方名锚点中。
- 对 `赵本作「...」`、`赵本无「...」字` 这类校注噪声，从方名锚点中剔除。
- 在 formula anchor normalization 中统一 `厚朴/浓朴`、`杏仁/杏人/杏子` 变体。
- `evaluate_topic_consistency()` 使用清洗后的 candidate formula anchor 再判断 `exact_formula_anchor`，使 A 层 main_passages 方文可以进入 primary_evidence。

本轮没有修改 answer assembler 的输出模式规则，也没有通过修改 expected_mode 规避失败；mode 晋级来自 primary_evidence 正常恢复。

## 修复后结果

完整重跑 `goldset_v2_working_102.json` 后：

| question_id | 修复后 actual_mode | primary | total_evidence | citations | gold_citation_check | failed_checks |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `eval_seed_q076` | `strong` | 2 | 10 | 2 | PASS | 无 |
| `eval_seed_q082` | `strong` | 2 | 3 | 2 | PASS | 无 |

完整 102 题 evaluator 汇总：

- total_questions: `102`
- mode_match_count: `99/102`
- citation_basic_pass: `81/82`
- failure_count: `3`，较 comparison 修复后的 `5` 下降 2
- source_lookup 题型：`30/30` mode match，`30/30` citation basic pass，`failure_count = 0`

旧 72 条 source_lookup 样本检查：旧 source_lookup 共 20 条，修复后 `20/20` 仍通过，没有新增旧 source_lookup 失败。

## 未处理项

本轮剩余失败均为任务约束中明确不处理的样本：

- `eval_seed_q093`
- `eval_seed_q095`
- `eval_seed_q096`
