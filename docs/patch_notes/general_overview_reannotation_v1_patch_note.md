# General Overview Reannotation v1 Patch Note

## 1. 本轮目标

本轮只正式化修正 72 条 goldset 中的常规 `general_overview` 题型，并明确排除 `eval_seed_q004`。不处理 source_lookup、comparison、meaning_explanation 或 refusal。

## 2. 改动内容

1. 新增 `docs/evaluation/general_overview_reannotation_guideline_v1.md`，定义 general_overview 人工重标规则和 q004 排除规则。
2. 新增 `artifacts/evaluation/goldset_v1_general_overview_reannotated.json`，保存本轮处理的 11 条 general_overview 子集，不含 q004。
3. 更新 `artifacts/evaluation/goldset_v1_seed.json`，仅回写本轮目标 general_overview 样本。
4. 新增 `artifacts/evaluation/general_overview_reannotation_log_v1.json`，保存逐题旧值、新值、动作与理由。
5. 新增 `docs/evaluation/general_overview_reannotation_report_v1.md`，总结正式化进度。
6. 新增 `artifacts/evaluation/general_overview_reannotation_eval_report.json` 与 `artifacts/evaluation/general_overview_reannotation_eval_report.md`，保存 evaluator v1 重跑结果。

## 3. 来源标记变化

| 指标 | 数量 |
| --- | ---: |
| general_overview 总量 | 12 |
| 本轮排除 q004 | 1 |
| 本轮处理 general_overview | 11 |
| 旧 `system_bootstrapped` | 9 |
| 旧 `manual_with_system_reference` | 2 |
| 新 `manual_independent` | 11 |
| 从 bootstrapped 修正为 independent | 9 |
| 从 manual_with_system_reference 修正为 independent | 2 |
| 仍未完成 | 0 |
| 保留 weak 边界 | 4 |

本轮没有把 weak 总括题强行改成 strong。`eval_seed_q005`, `eval_seed_q043`, `eval_seed_q044`, `eval_seed_q050` 仍保持 `weak_with_review_notice` 和 `must_keep_primary_empty`。

## 4. q004 排除说明

`eval_seed_q004` 是“少阴病应该怎么办？”专项样本，当前仍为 `needs_reannotation`。它的 gold 曾因当前正式系统 citations 扩展，覆盖口径需要单独定义。本轮未修改 q004，也未把 q004 写入 general_overview 子集文件。

## 5. 未改动范围

1. 未改 retrieval / rerank / gating / answer assembler。
2. 未改 API / frontend。
3. 未新增题目。
4. 未重写 evaluator v1。
5. 未修改非本轮目标 general_overview 题型。
6. 未修改 q004。
7. 未修改 source_lookup、comparison、meaning_explanation reannotation v1 的既有结果。

## 6. 验证

本轮已用更新后的 72 条 goldset 跑 evaluator v1：

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

报告输出：

1. `artifacts/evaluation/general_overview_reannotation_eval_report.json`
2. `artifacts/evaluation/general_overview_reannotation_eval_report.md`
