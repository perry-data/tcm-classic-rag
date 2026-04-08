# General Overview Reannotation Report v1

- 报告日期：2026-04-08
- 范围：仅 `question_type = general_overview` 且排除 `eval_seed_q004`
- 输入总集：`artifacts/evaluation/goldset_v1_seed.json`
- 子集输出：`artifacts/evaluation/goldset_v1_general_overview_reannotated.json`
- 重标日志：`artifacts/evaluation/general_overview_reannotation_log_v1.json`

## 1. 总结

general_overview 总量为 12 条。本轮按任务要求排除 `eval_seed_q004`，实际处理 11 条常规 general_overview 样本。

处理前，这 11 条中有 2 条 `manual_with_system_reference`，9 条 `system_bootstrapped`。本轮逐题从题面主题出发，核对 `data/processed/zjshl_dataset_v2/main_passages.json` 中的最小稳定分支集合，将 11 条全部修正为 `manual_independent`。

本轮没有为提升 independent 数量而改变回答强弱边界。`eval_seed_q005`, `eval_seed_q043`, `eval_seed_q044`, `eval_seed_q050` 仍保留 `weak_with_review_notice` 与 `must_keep_primary_empty`，只用 `secondary` / `review` evidence。

## 2. 数量变化

| 指标 | 数量 |
| --- | ---: |
| general_overview 总量 | 12 |
| 本轮排除 q004 | 1 |
| 本轮处理的 general_overview 数量 | 11 |
| 旧 `system_bootstrapped` | 9 |
| 旧 `manual_with_system_reference` | 2 |
| 新 `manual_independent` | 11 |
| 从 bootstrapped 修正为 independent | 9 |
| 从 manual_with_system_reference 修正为 independent | 2 |
| 本轮成功提升为 `manual_independent` | 11 |
| 保留 weak 边界 | 4 |
| 本轮处理范围内仍未修好 | 0 |

## 3. q004 为什么单列排除

`eval_seed_q004` 是“少阴病应该怎么办？”专项样本，audit 中为 `needs_reannotation`。它曾因当前正式系统实际 citations 扩展过 gold 集合，少阴病“应该怎么办”的覆盖口径需要单独定义，不能与常规总括题一起顺手处理。

因此本轮没有修改 q004 的 `gold_source_type`、gold ids、evidence spans 或 `source_refs`。q004 仍保留为 `needs_reannotation`，等待后续专项重标；它不计入本轮 11 条的“仍未修好”数量。

## 4. 本轮实质修正

1. `eval_seed_q003`：用太阳病桂枝汤、葛根汤、针足阳明防传等分支支撑 strong 总括，并保留太阳伤寒条作语境。
2. `eval_seed_q005`：保留六经病 weak 边界，用三阳可汗、三阴可下、传经和六经病衰语境作弱整理。
3. `eval_seed_q042`：用阳明病小柴胡、小承气、大承气、栀子豉等分支支撑 strong 治法总括。
4. `eval_seed_q043`：移除旧 replay 中的少阴语境，收紧为太阴章内定义、桂枝汤、四逆辈、桂枝加芍药汤和减药语境，保留 weak。
5. `eval_seed_q044`：移除旧 replay 中的少阴语境，收紧为厥阴章内定义、少少与水、灸厥阴、麻黄升麻汤和预后核对语境，保留 weak。
6. `eval_seed_q045`：用伤寒逐日浅深、临时消息制方框架，以及栀子乾姜汤、抵当丸等分支支撑 strong。
7. `eval_seed_q046`：用太阳中风桂枝汤、大青龙汤、五苓散、十枣汤等分支支撑 strong。
8. `eval_seed_q047`：用太阳病中风、伤寒、桂枝汤证、葛根汤证等分支支撑 strong。
9. `eval_seed_q048`：用阳明病栀子豉、小柴胡、小承气、大承气等情况支撑 strong。
10. `eval_seed_q049`：只处理“少阴病有哪些分支”这道分支题，用麻黄附子细辛汤、黄连阿胶汤、附子汤、苦酒汤等分支支撑 strong；不处理 q004 的“少阴病应该怎么办”专项口径。
11. `eval_seed_q050`：保留霍乱病 weak 边界，补入五苓散/理中丸治法条文，并保留霍乱定义与伤寒关系作弱语境。

## 5. 仍未修好的题

本轮处理范围内没有剩余 `system_bootstrapped`、`manual_with_system_reference` 或 `needs_reannotation` 样本。

未修好的原因：无。

范围外说明：`eval_seed_q004` 仍为 `needs_reannotation`，但它被本轮明确排除，后续应单独重标。

## 6. 对 72 条正式化进度的贡献

source_lookup、comparison 和 meaning_explanation reannotation 完成后，72 条中已有 60 条 `manual_independent`。本轮新增 11 条 general_overview `manual_independent`，独立样本累计提升到 71 条。

从 bootstrapped 修正成功的 question_id：

`eval_seed_q042`, `eval_seed_q043`, `eval_seed_q044`, `eval_seed_q045`, `eval_seed_q046`, `eval_seed_q047`, `eval_seed_q048`, `eval_seed_q049`, `eval_seed_q050`

从 manual_with_system_reference 修正成功的 question_id：

`eval_seed_q003`, `eval_seed_q005`

保留 weak 边界的 question_id：

`eval_seed_q005`, `eval_seed_q043`, `eval_seed_q044`, `eval_seed_q050`

## 7. 验证结果

本轮已用更新后的 72 条总集重跑 evaluator v1：

```bash
./.venv/bin/python scripts/run_evaluator_v1.py --goldset artifacts/evaluation/goldset_v1_seed.json --report-json artifacts/evaluation/general_overview_reannotation_eval_report.json --report-md artifacts/evaluation/general_overview_reannotation_eval_report.md --fail-on-evaluation-failure
```

结果：

1. 总题量：72。
2. `answer_mode` 匹配：72 / 72。
3. `citation_check_required` 基础通过：58 / 58。
4. general_overview 题型：12 / 12 mode match，12 / 12 citation basic pass。
5. 本轮处理的 general_overview 子集：11 / 11 mode match，11 / 11 citation basic pass。
6. `failure_count`：0。
7. `all_checks_passed`：true。

完整 evaluator 报告写入：

1. `artifacts/evaluation/general_overview_reannotation_eval_report.json`
2. `artifacts/evaluation/general_overview_reannotation_eval_report.md`
