# Meaning Explanation Reannotation v1 Patch Note

## 1. 本轮目标

本轮只正式化修正 72 条 goldset 中的 `meaning_explanation` 题型，不处理 source_lookup、comparison、general_overview 或 refusal。

## 2. 改动内容

1. 新增 `docs/evaluation/meaning_explanation_reannotation_guideline_v1.md`，定义 meaning_explanation 人工重标规则。
2. 新增 `artifacts/evaluation/goldset_v1_meaning_explanation_reannotated.json`，保存 14 条 meaning_explanation 子集。
3. 更新 `artifacts/evaluation/goldset_v1_seed.json`，仅回写 meaning_explanation 样本。
4. 新增 `artifacts/evaluation/meaning_explanation_reannotation_log_v1.json`，保存逐题旧值、新值、动作与理由。
5. 新增 `docs/evaluation/meaning_explanation_reannotation_report_v1.md`，总结正式化进度。
6. 新增 `artifacts/evaluation/meaning_explanation_reannotation_eval_report.json` 与 `artifacts/evaluation/meaning_explanation_reannotation_eval_report.md`，保存 evaluator v1 重跑结果。

## 3. 来源标记变化

| 指标 | 数量 |
| --- | ---: |
| meaning_explanation 总量 | 14 |
| 旧 `system_bootstrapped` | 13 |
| 旧 `manual_with_system_reference` | 1 |
| 新 `manual_independent` | 14 |
| 从 bootstrapped 修正为 independent | 13 |
| 从 manual_with_system_reference 修正为 independent | 1 |
| 仍未完成 | 0 |
| 保留 weak 边界 | 10 |

本轮没有把弱解释材料强行改成 strong。`eval_seed_q002`, `eval_seed_q029`, `eval_seed_q030`, `eval_seed_q031`, `eval_seed_q032`, `eval_seed_q033`, `eval_seed_q037`, `eval_seed_q039`, `eval_seed_q040`, `eval_seed_q041` 仍保持 `weak_with_review_notice` 和 `must_keep_primary_empty`，但其 gold 来源已改为正文、注解或紧邻解释材料的人工独立核对。

## 4. 未改动范围

1. 未改 retrieval / rerank / gating / answer assembler。
2. 未改 API / frontend。
3. 未新增题目。
4. 未重写 evaluator v1。
5. 未修改非 meaning_explanation 题型。
6. 未修改 source_lookup reannotation v1 与 comparison reannotation v1 的既有结果。
7. 未处理 q004 单独重标。

## 5. 验证

本轮已用更新后的 72 条 goldset 跑 evaluator v1：

```bash
./.venv/bin/python scripts/run_evaluator_v1.py --goldset artifacts/evaluation/goldset_v1_seed.json --report-json artifacts/evaluation/meaning_explanation_reannotation_eval_report.json --report-md artifacts/evaluation/meaning_explanation_reannotation_eval_report.md --fail-on-evaluation-failure
```

结果：

1. 总题量：72。
2. `answer_mode` 匹配：72 / 72。
3. `citation_check_required` 基础通过：58 / 58。
4. meaning_explanation 题型：14 / 14 mode match，14 / 14 citation basic pass。
5. `failure_count`：0。
6. `all_checks_passed`：true。

报告输出：

1. `artifacts/evaluation/meaning_explanation_reannotation_eval_report.json`
2. `artifacts/evaluation/meaning_explanation_reannotation_eval_report.md`
