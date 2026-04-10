# Goldset Independence Review v1 Patch Note

## 1. 本轮目标

本轮只处理当前 72 条 evaluation goldset 的独立性审查与去自举标记，不扩题量，不改系统链路。

## 2. 主要改动

1. `config/evaluation/goldset_schema_v1.json`
   - 在 gold item 上新增最小来源字段 `gold_source_type`。
   - 枚举值为 `manual_independent`、`manual_with_system_reference`、`system_bootstrapped`、`needs_reannotation`。
2. `artifacts/evaluation/goldset_v1_seed.json`
   - 为 72 条样本逐条补充 `gold_source_type`。
3. `artifacts/evaluation/goldset_independence_audit_v1.json`
   - 记录逐题风险、抽样复核结果、正式评估建议和后续动作。
4. `docs/evaluation/goldset_independence_review_v1.md`
   - 形成面向论文第 4 章使用前的独立性审查报告。

## 3. 审查结论

来源分布：

| gold_source_type | 数量 |
| --- | --- |
| `manual_with_system_reference` | 6 |
| `needs_reannotation` | 1 |
| `manual_independent` | 14 |
| `system_bootstrapped` | 51 |

正式评估建议：

| recommendation | 数量 |
| --- | --- |
| `formal_candidate_with_provenance_note` | 6 |
| `exclude_until_reannotation` | 52 |
| `formal_core` | 14 |

核心结论：当前 72 条仍可用于开发回归；但 51 条非拒答扩写题属于明显 `system_bootstrapped`，q004 属于 `needs_reannotation`，因此不应把完整 72 条的 evaluator 通过率直接作为论文正式主评估结论。

## 4. 抽样复核

本轮按题型复核 40 条：

1. `source_lookup`：10 条。
2. `meaning_explanation`：8 条。
3. `general_overview`：8 条。
4. `comparison`：8 条。
5. `refusal`：6 条。

复核结果已写入 `artifacts/evaluation/goldset_independence_audit_v1.json` 的 `sampling_plan` 和逐题 `sample_review_result` 字段。

## 5. 未改动范围

1. 未改 API。
2. 未改 answer payload contract。
3. 未改 retrieval 主链。
4. 未改 answer assembler。
5. 未扩题量。

## 6. 验证

本轮实际执行的最小验证：

```bash
jq empty config/evaluation/goldset_schema_v1.json artifacts/evaluation/goldset_v1_seed.json artifacts/evaluation/goldset_independence_audit_v1.json
./.venv/bin/python scripts/run_evaluator_v1.py --goldset artifacts/evaluation/goldset_v1_seed.json --report-json /tmp/goldset_independence_eval.json --report-md /tmp/goldset_independence_eval.md --fail-on-evaluation-failure
```

验证结果：

1. JSON 解析通过。
2. evaluator v1 总题量：72。
3. `answer_mode` 匹配：72 / 72。
4. `citation_check_required` 基础通过：58 / 58。
5. `failure_count`：0。
6. `all_checks_passed`：true。
