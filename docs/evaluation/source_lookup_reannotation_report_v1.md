# Source Lookup Reannotation Report v1

- 报告日期：2026-04-07
- 范围：仅 `question_type = source_lookup`
- 输入总集：`artifacts/evaluation/goldset_v1_seed.json`
- 子集输出：`artifacts/evaluation/goldset_v1_source_lookup_reannotated.json`
- 重标日志：`artifacts/evaluation/source_lookup_reannotation_log_v1.json`

## 1. 总结

source_lookup 总量为 20 条。independence audit v1 基线中，source_lookup 有 1 条 `manual_with_system_reference` 和 19 条 `system_bootstrapped`。

本轮逐题核对题面方名与 `data/processed/zjshl_dataset_v2/main_passages.json` 中的方文/连续段后，将 20 条 source_lookup 全部标为 `manual_independent`。其中，从 `system_bootstrapped` 成功修正为 `manual_independent` 的样本为 19 条。

## 2. 数量变化

| 指标 | 数量 |
| --- | ---: |
| source_lookup 总量 | 20 |
| 旧 `system_bootstrapped` | 19 |
| 新 `system_bootstrapped` | 0 |
| 旧 `manual_independent` | 0 |
| 新 `manual_independent` | 20 |
| 从 bootstrapped 修正为 independent | 19 |
| 仍未完成 | 0 |

## 3. 本轮实质修正

除来源标记外，本轮还按人工先验补齐了若干连续方文：

1. `eval_seed_q001`：补入黄连汤方煎服法 `ZJSHL-CH-010-P-0148`。
2. `eval_seed_q014`：补入小青龙汤方组成延续 `ZJSHL-CH-009-P-0041`。
3. `eval_seed_q016`：补入大柴胡汤方方后说明 `ZJSHL-CH-009-P-0251`。
4. `eval_seed_q017`：补入五苓散服法 `ZJSHL-CH-009-P-0140`。
5. `eval_seed_q021`：补入猪苓汤煎服法 `ZJSHL-CH-011-P-0111`。
6. `eval_seed_q022`：补入茵陈蒿汤方后说明 `ZJSHL-CH-011-P-0142`。
7. `eval_seed_q027`：补入桂枝甘草汤煎服法 `ZJSHL-CH-009-P-0107`。
8. `eval_seed_q028`：补入半夏泻心汤煎服法 `ZJSHL-CH-010-P-0070`。

这些新增段均来自 `main_passages.json`，不是从当前系统 replay citations 反推得到。

## 4. 仍未修好的题

本轮 source_lookup 中没有剩余 `system_bootstrapped` 或 `needs_reannotation` 样本。

仍需注意：方后说明段在本轮只作为 `secondary` 可接受补充；如果后续论文评估要做更严格的 citation grading，应要求回答至少命中方名段或连续方文段。

## 5. 对 72 条正式化进度的贡献

按 independence audit v1 的口径，原先全体 72 条中 `manual_independent` 为 14 条，主要是拒答边界题。本轮 source_lookup 完成后，新增 20 条 `manual_independent` source_lookup，因此可作为论文正式主评估候选的独立样本可从 14 条提升到 34 条。

从 bootstrapped 修正成功的 question_id：

`eval_seed_q010`, `eval_seed_q011`, `eval_seed_q012`, `eval_seed_q013`, `eval_seed_q014`, `eval_seed_q015`, `eval_seed_q016`, `eval_seed_q017`, `eval_seed_q018`, `eval_seed_q019`, `eval_seed_q020`, `eval_seed_q021`, `eval_seed_q022`, `eval_seed_q023`, `eval_seed_q024`, `eval_seed_q025`, `eval_seed_q026`, `eval_seed_q027`, `eval_seed_q028`

## 6. 验证结果

本轮已用更新后的 72 条总集重跑 evaluator v1：

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

完整 evaluator 报告写入：

1. `artifacts/evaluation/source_lookup_reannotation_eval_report.json`
2. `artifacts/evaluation/source_lookup_reannotation_eval_report.md`
