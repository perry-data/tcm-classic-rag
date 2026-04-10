# Source Lookup Reannotation v1 Patch Note

## 1. 本轮目标

本轮只正式化修正 72 条 goldset 中的 `source_lookup` 题型，不处理 comparison、general_overview、meaning_explanation 或 refusal。

## 2. 改动内容

1. 新增 `docs/evaluation/source_lookup_reannotation_guideline_v1.md`，定义 source_lookup 人工重标规则。
2. 新增 `artifacts/evaluation/goldset_v1_source_lookup_reannotated.json`，保存 20 条 source_lookup 子集。
3. 更新 `artifacts/evaluation/goldset_v1_seed.json`，仅回写 source_lookup 样本。
4. 新增 `artifacts/evaluation/source_lookup_reannotation_log_v1.json`，保存逐题旧值、新值、动作与理由。
5. 新增 `docs/evaluation/source_lookup_reannotation_report_v1.md`，总结正式化进度。

## 3. 来源标记变化

| 指标 | 数量 |
| --- | ---: |
| source_lookup 总量 | 20 |
| 旧 `system_bootstrapped` | 19 |
| 新 `system_bootstrapped` | 0 |
| 新 `manual_independent` | 20 |
| 从 bootstrapped 修正为 independent | 19 |
| 仍未完成 | 0 |

本轮没有把无法独立确认的 source_lookup 伪装成 `manual_independent`；20 条 source_lookup 均已能由题面方名和 `main_passages.json` 中的方文/连续段解释。

## 4. 未改动范围

1. 未改 retrieval / rerank / gating / answer assembler。
2. 未改 API / frontend。
3. 未新增题目。
4. 未重写 evaluator v1。
5. 未修改非 source_lookup 题型。

## 5. 验证

本轮已用更新后的 72 条 goldset 跑 evaluator v1：

```bash
./.venv/bin/python scripts/run_evaluator_v1.py --goldset artifacts/evaluation/goldset_v1_seed.json --report-json artifacts/evaluation/source_lookup_reannotation_eval_report.json --report-md artifacts/evaluation/source_lookup_reannotation_eval_report.md --fail-on-evaluation-failure
```

结果：

1. 总题量：72。
2. `answer_mode` 匹配：72 / 72。
3. `citation_check_required` 基础通过：58 / 58。
4. source_lookup 题型：20 / 20 mode match，20 / 20 citation basic pass。
5. `failure_count`：0。
6. `all_checks_passed`：true。

报告输出：

1. `artifacts/evaluation/source_lookup_reannotation_eval_report.json`
2. `artifacts/evaluation/source_lookup_reannotation_eval_report.md`
