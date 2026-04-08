# Batch A comparison entity fix v1

## 目标范围

本轮只修 `eval_seed_q085` 和 `eval_seed_q090` 暴露出的 comparison 双实体识别与方名归一问题，不修改 `goldset_v2_working_102.json`，不修改旧 72 条，不继续 Batch B，也不处理 source_lookup / meaning_explanation / general_overview 的剩余失败。

## 失败根因

修复前，两题都已被 comparison query detector 接管，但 `_find_formula_mentions()` 只能识别到一个方名，因此 `_detect_comparison_query()` 返回 `entity_resolution_failed`，最终进入 comparison refusal：

| question_id | query | 修复前识别结果 | 修复前 actual_mode |
| --- | --- | --- | --- |
| `eval_seed_q085` | 麻黄杏仁甘草石膏汤方和桂枝加厚朴杏子汤方有什么不同？ | 只识别到 `桂枝加浓朴杏子汤方` | `refuse` |
| `eval_seed_q090` | 白通汤方和白通加猪胆汁汤方的区别是什么？ | 只识别到 `白通汤方` | `refuse` |

具体原因在 formula catalog 的标题抽取和 alias 构建：

- `eval_seed_q085` 的方文标题原文为 `麻黄杏人赵本作「仁」甘草石膏汤方`。旧逻辑直接把校注语压入 alias，形成 `麻黄杏子赵本作仁甘草石膏汤方` 一类 key，无法命中题面中的 `麻黄杏仁甘草石膏汤方`。
- `eval_seed_q090` 的方文标题原文为 `白通加猪胆汁赵本医统本并有「汤」字方`。旧逻辑把校注语压入 canonical name，无法命中题面中的 `白通加猪胆汁汤方`。
- 厚朴/浓朴、杏子/杏仁/杏人已有基础归一，但校注片段未被清洗，导致 alias 仍无法稳定落到通行方名。

## 修复策略

在 `backend/answers/assembler.py` 的 comparison formula catalog 构建中增加方名标题清洗与 alias 扩展：

- 新增 raw title anchor 抽取，保留原始标题中的校注标记，避免过早 `compact_text()` 丢失结构。
- 对 `赵本/医统本并有「汤」字` 这类插入型校注，生成带 `汤` 的 canonical title，例如 `白通加猪胆汁汤方`。
- 对 `赵本作「仁」`、`赵本无「...」字` 等校注片段，在 catalog title 中剔除校注，避免 query alias 携带校注噪声。
- 同时保留原始标题、清洗标题、替换型标题、删除型标题的 alias variants，再走既有的 `厚朴/浓朴`、`杏子/杏仁/杏人` 归一。
- `_row_is_formula_heading_for_entity()` 改用同一套标题清洗逻辑，确保清洗后的 canonical title 仍能定位原始方文记录。

## 修复后结果

完整重跑 `goldset_v2_working_102.json` 后：

| question_id | 修复后 actual_mode | primary | total_evidence | citations | gold_citation_check | failed_checks |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `eval_seed_q085` | `strong` | 2 | 7 | 5 | PASS | 无 |
| `eval_seed_q090` | `strong` | 2 | 7 | 5 | PASS | 无 |

完整 102 题 evaluator 汇总：

- total_questions: `102`
- mode_match_count: `97/102`
- citation_basic_pass: `81/82`
- failure_count: `5`，较 refusal policy 修复后的 `7` 下降 2
- comparison 题型：`20/20` mode match，`20/20` citation basic pass，`failure_count = 0`

旧 72 条 comparison 样本检查：旧 comparison 共 12 条，修复后 `12/12` 仍通过，没有新增旧 comparison 失败。

## 未处理项

本轮剩余失败均为任务约束中明确不处理的样本：

- `eval_seed_q076`
- `eval_seed_q082`
- `eval_seed_q093`
- `eval_seed_q095`
- `eval_seed_q096`
