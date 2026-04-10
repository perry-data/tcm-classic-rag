# q004 Reannotation v1 Patch Note

## 1. 本轮目标

本轮只处理 `eval_seed_q004`，即“少阴病应该怎么办？”。不处理其他 question_id，不处理其他题型，不修改 retrieval / rerank / gating / answer assembler / API / frontend。

## 2. 改动内容

1. 新增 `docs/evaluation/q004_reannotation_guideline_v1.md`，定义 q004 专项口径。
2. 新增 `artifacts/evaluation/q004_reannotation_record_v1.json`，记录 q004 旧值、新值、动作、依据与边界。
3. 更新 `artifacts/evaluation/goldset_v1_seed.json`，仅回写 q004。
4. 新增 `docs/evaluation/q004_reannotation_report_v1.md`，说明旧问题、新口径和状态判断。
5. 新增 `artifacts/evaluation/q004_reannotation_eval_report.json` 与 `artifacts/evaluation/q004_reannotation_eval_report.md`，保存 evaluator v1 重跑结果。

## 3. q004 最终状态

q004 从 `needs_reannotation` 收口为 `manual_independent`。

一句话口径：

> “少阴病应该怎么办？” = 少阴病的最小稳定治法分支整理；不是当前系统 strong 回答 citation 集，也不是少阴病章全量穷举。

本轮保留 6 条少阴病章内直接方证分支作为 primary gold：`ZJSHL-CH-014-P-0062`, `ZJSHL-CH-014-P-0072`, `ZJSHL-CH-014-P-0078`, `ZJSHL-CH-014-P-0093`, `ZJSHL-CH-014-P-0112`, `ZJSHL-CH-014-P-0162`。

## 4. 未改动范围

1. 未修改 q004 以外的任何样本。
2. 未改 retrieval / rerank / gating / answer assembler。
3. 未改 API / frontend。
4. 未新增题目。
5. 未重写 evaluator v1。

## 5. 验证

本轮已用更新后的 72 条 goldset 跑 evaluator v1：

```bash
./.venv/bin/python scripts/run_evaluator_v1.py --goldset artifacts/evaluation/goldset_v1_seed.json --report-json artifacts/evaluation/q004_reannotation_eval_report.json --report-md artifacts/evaluation/q004_reannotation_eval_report.md --fail-on-evaluation-failure
```

结果：

1. 总题量：72。
2. `answer_mode` 匹配：72 / 72。
3. `citation_check_required` 基础通过：58 / 58。
4. q004：expected `strong`，actual `strong`，gold citation check passed。
5. `failure_count`：0。
6. `all_checks_passed`：true。

报告输出：

1. `artifacts/evaluation/q004_reannotation_eval_report.json`
2. `artifacts/evaluation/q004_reannotation_eval_report.md`
