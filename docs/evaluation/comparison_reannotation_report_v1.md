# Comparison Reannotation Report v1

- 报告日期：2026-04-08
- 范围：仅 `question_type = comparison`
- 输入总集：`artifacts/evaluation/goldset_v1_seed.json`
- 子集输出：`artifacts/evaluation/goldset_v1_comparison_reannotated.json`
- 重标日志：`artifacts/evaluation/comparison_reannotation_log_v1.json`

## 1. 总结

comparison 总量为 12 条。independence audit v1 基线中，comparison 有 2 条 `manual_with_system_reference` 和 10 条 `system_bootstrapped`。

本轮逐题从题面两端对象出发，核对 `data/processed/zjshl_dataset_v2/main_passages.json` 中的双方方文、连续方文块与直接条文语境，将 12 条 comparison 全部修正为 `manual_independent`。其中，10 条从 `system_bootstrapped` 升级，2 条从 `manual_with_system_reference` 升级。

`eval_seed_q007` 仍保留 `weak_with_review_notice` 与 `must_keep_primary_empty` 边界；本轮只是把方文和核对语境改为独立来源，并没有把弱语境强行升格为 stable primary。

## 2. 数量变化

| 指标 | 数量 |
| --- | ---: |
| comparison 总量 | 12 |
| 旧 `system_bootstrapped` | 10 |
| 旧 `manual_with_system_reference` | 2 |
| 新 `manual_independent` | 12 |
| 从 bootstrapped 修正为 independent | 10 |
| 从 manual_with_system_reference 修正为 independent | 2 |
| 本轮成功提升为 `manual_independent` | 12 |
| 仍未修好 | 0 |
| 保留 weak 边界 | 1 |

## 3. 本轮实质修正

1. `eval_seed_q006`：补入桂枝加浓朴杏子汤的独立语境 `ZJSHL-CH-009-P-0053`，不再只保留 A 方语境。
2. `eval_seed_q007`：将语境 `ZJSHL-CH-008-P-0238` 改为 main_passages 核对来源并保留 `review` 角色。
3. `eval_seed_q051`：移出旧 replay 中的桂枝加葛根/麻杏石甘汤语境，改为桂枝汤与葛根汤的核心方文块和直接条文。
4. `eval_seed_q052`：补齐麻黄汤杏仁段与两方煎服法，语境只保留能独立核对的直接条文。
5. `eval_seed_q053`：补入大小承气汤煎服法和紧邻原文直接比较段 `ZJSHL-CH-011-P-0072`。
6. `eval_seed_q054`：改用小柴胡汤与大柴胡汤的同章直接语境，替代 replay 回填语境。
7. `eval_seed_q055`：补入五苓散、猪苓汤服法，并用各自小便不利/消渴相关直接条文作 secondary。
8. `eval_seed_q056`：移除旧 replay 中误入的通脉四逆汤语境，改为四逆汤与茯苓四逆汤双方方文块和直接语境。
9. `eval_seed_q057`：补入甘草乾姜汤、芍药甘草汤煎服法，并保留同一条文中先复阳后益阴的语境。
10. `eval_seed_q058`：用栀子豉汤、栀子乾姜汤各自直接主治条文替代泛化 replay 语境。
11. `eval_seed_q059`：去除 `full:*` / `full:ambiguous_passages:*` gold record 依赖，改为 main_passages 中两方方文块和直接语境。
12. `eval_seed_q060`：补入白虎汤煎服法，保留白虎汤与白虎加人参汤各自直接主治条文。

## 4. 仍未修好的题

本轮 comparison 中没有剩余 `system_bootstrapped`、`manual_with_system_reference` 或 `needs_reannotation` 样本。

边界说明：`eval_seed_q007` 虽已修正为 `manual_independent` 来源，但仍保留弱回答模式，因为当前比较只能作为待核对整理，不应升格为 strong。

## 5. 对 72 条正式化进度的贡献

source_lookup reannotation v1 完成后，72 条中已有 34 条 `manual_independent`。本轮新增 12 条 comparison `manual_independent`，独立样本累计可提升到 46 条。

从 bootstrapped 修正成功的 question_id：

`eval_seed_q051`, `eval_seed_q052`, `eval_seed_q053`, `eval_seed_q054`, `eval_seed_q055`, `eval_seed_q056`, `eval_seed_q057`, `eval_seed_q058`, `eval_seed_q059`, `eval_seed_q060`

从 manual_with_system_reference 修正成功的 question_id：

`eval_seed_q006`, `eval_seed_q007`

## 6. 验证结果

本轮已用更新后的 72 条总集重跑 evaluator v1：

```bash
./.venv/bin/python scripts/run_evaluator_v1.py --goldset artifacts/evaluation/goldset_v1_seed.json --report-json artifacts/evaluation/comparison_reannotation_eval_report.json --report-md artifacts/evaluation/comparison_reannotation_eval_report.md --fail-on-evaluation-failure
```

结果：

1. 总题量：72。
2. `answer_mode` 匹配：72 / 72。
3. `citation_check_required` 基础通过：58 / 58。
4. comparison 题型：12 / 12 mode match，12 / 12 citation basic pass。
5. `failure_count`：0。
6. `all_checks_passed`：true。

完整 evaluator 报告写入：

1. `artifacts/evaluation/comparison_reannotation_eval_report.json`
2. `artifacts/evaluation/comparison_reannotation_eval_report.md`
