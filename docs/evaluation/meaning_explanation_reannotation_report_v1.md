# Meaning Explanation Reannotation Report v1

- 报告日期：2026-04-08
- 范围：仅 `question_type = meaning_explanation`
- 输入总集：`artifacts/evaluation/goldset_v1_seed.json`
- 子集输出：`artifacts/evaluation/goldset_v1_meaning_explanation_reannotated.json`
- 重标日志：`artifacts/evaluation/meaning_explanation_reannotation_log_v1.json`

## 1. 总结

meaning_explanation 总量为 14 条。independence audit v1 基线中，meaning_explanation 有 1 条 `manual_with_system_reference` 和 13 条 `system_bootstrapped`。

本轮逐题从题面句子或概念出发，核对 `data/processed/zjshl_dataset_v2/annotations.json` 中的直接注解，以及 `data/processed/zjshl_dataset_v2/main_passages.json` 中的正文出处、同义正文和紧邻语境，将 14 条 meaning_explanation 全部修正为 `manual_independent`。其中，13 条从 `system_bootstrapped` 升级，1 条从 `manual_with_system_reference` 升级。

本轮没有为追求 independent 数量而强行改强弱模式。`eval_seed_q002`, `eval_seed_q029`, `eval_seed_q030`, `eval_seed_q031`, `eval_seed_q032`, `eval_seed_q033`, `eval_seed_q037`, `eval_seed_q039`, `eval_seed_q040`, `eval_seed_q041` 仍保留 `weak_with_review_notice` 与 `must_keep_primary_empty` 边界；这些题的注解或正文可作解释材料，但不升格为 stable primary。

## 2. 数量变化

| 指标 | 数量 |
| --- | ---: |
| meaning_explanation 总量 | 14 |
| 旧 `system_bootstrapped` | 13 |
| 旧 `manual_with_system_reference` | 1 |
| 新 `manual_independent` | 14 |
| 从 bootstrapped 修正为 independent | 13 |
| 从 manual_with_system_reference 修正为 independent | 1 |
| 本轮成功提升为 `manual_independent` | 14 |
| 仍未修好 | 0 |
| 保留 weak 边界 | 10 |

## 3. 本轮实质修正

1. `eval_seed_q002`：保留“烧针益阳而损阴”的弱边界，改用 `ZJSHL-CH-003-P-0016` 注解作解释主体，并以烧针损阴血、复加烧针正文作语境补充。
2. `eval_seed_q029`：用 `ZJSHL-CH-003-P-0007` 注解解释“一阴一阳谓之道，偏阴偏阳谓之疾”，以冬至后一阳升正文作概念语境。
3. `eval_seed_q030`：用 `ZJSHL-CH-003-P-0009` 注解解释“阳为气，阴为血”，以“肺主气，心主血，气为阳，血为阴”正文作语境。
4. `eval_seed_q031`：用 `ZJSHL-CH-003-P-0011` 注解解释“脉沉者，知荣血内微”，并补入正文“其脉沉者，荣气微也”。
5. `eval_seed_q032`：用 `ZJSHL-CH-003-P-0013` 注解解释“卫气”的温分肉、肥腠理、司开合语义，并用同义注解 `ZJSHL-CH-004-P-0209` 复核。
6. `eval_seed_q033`：用 `ZJSHL-CH-003-P-0015` 与 `ZJSHL-CH-009-P-0302` 注解解释“荣气微者，加烧针，则血留不行”，将跨章引用 `ZJSHL-CH-011-P-0103` 降为 review。
7. `eval_seed_q034`：用正文 `ZJSHL-CH-003-P-0017` 作为“蔼蔼如车盖”的 primary，并用 `ZJSHL-CH-003-P-0018` 注解作 secondary。
8. `eval_seed_q035`：用正文 `ZJSHL-CH-003-P-0019` 作为“累累如循长竿”的 primary，并用 `ZJSHL-CH-003-P-0020` 注解作 secondary。
9. `eval_seed_q036`：用正文 `ZJSHL-CH-003-P-0023` 作为“如蜘蛛丝”的 primary，并用 `ZJSHL-CH-003-P-0024` 注解作 secondary。
10. `eval_seed_q037`：保留“绵绵”弱边界，只用 `ZJSHL-CH-003-P-0027` 注解作 secondary。
11. `eval_seed_q038`：用正文 `ZJSHL-CH-003-P-0031` 与 `ZJSHL-CH-004-P-0130` 支撑“阴阳相搏”的 strong 解释，注解作 secondary/review。
12. `eval_seed_q039`：用 `ZJSHL-CH-003-P-0041` 注解与 `ZJSHL-CH-003-P-0039` 正文说明“弦则为减，减则为寒”，远端语境 `ZJSHL-CH-023-P-0018` 保留为 review。
13. `eval_seed_q040`：用 `ZJSHL-CH-003-P-0043` 注解与 `ZJSHL-CH-003-P-0099` 正文解释“浮为阳，紧为阴”，将同章弦脉定义 `ZJSHL-CH-003-P-0037` 保留为 review。
14. `eval_seed_q041`：用 `ZJSHL-CH-003-P-0047` 注解和 `ZJSHL-CH-003-P-0088` 正文解释“阳胜则热，阴胜则寒”。

## 4. 仍未修好的题

本轮 meaning_explanation 中没有剩余 `system_bootstrapped`、`manual_with_system_reference` 或 `needs_reannotation` 样本。

未修好的原因：无。

边界说明：10 条题虽已修正为 `manual_independent` 来源，但仍保留 `weak_with_review_notice`，原因是这些题主要依赖注解解释、远端同义材料或弱语境核对；按本轮原则，不能因为注解解释顺畅就自动升为 strong primary。

## 5. 对 72 条正式化进度的贡献

source_lookup reannotation v1 和 comparison reannotation v1 完成后，72 条中已有 46 条 `manual_independent`。本轮新增 14 条 meaning_explanation `manual_independent`，独立样本累计提升到 60 条。

从 bootstrapped 修正成功的 question_id：

`eval_seed_q029`, `eval_seed_q030`, `eval_seed_q031`, `eval_seed_q032`, `eval_seed_q033`, `eval_seed_q034`, `eval_seed_q035`, `eval_seed_q036`, `eval_seed_q037`, `eval_seed_q038`, `eval_seed_q039`, `eval_seed_q040`, `eval_seed_q041`

从 manual_with_system_reference 修正成功的 question_id：

`eval_seed_q002`

保留 weak 边界的 question_id：

`eval_seed_q002`, `eval_seed_q029`, `eval_seed_q030`, `eval_seed_q031`, `eval_seed_q032`, `eval_seed_q033`, `eval_seed_q037`, `eval_seed_q039`, `eval_seed_q040`, `eval_seed_q041`

## 6. 验证结果

本轮已用更新后的 72 条总集重跑 evaluator v1：

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

完整 evaluator 报告写入：

1. `artifacts/evaluation/meaning_explanation_reannotation_eval_report.json`
2. `artifacts/evaluation/meaning_explanation_reannotation_eval_report.md`
