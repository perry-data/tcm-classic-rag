# Full Chain Regression After P0/P1 v2

## 本轮目标

在 P0 boundary repairs 和 P1 minimal repairs 完成后，复用完整 120 条 full-chain query set，重新运行 A/B/C 三种模式，生成新的系统级回归基线。本轮只做验证与归档，不做 AHV3、不新增 definition object、不修 P2、不改 prompt、不改前端、不改 API contract。

## 与 v1 的区别

- v1 是 P0/P1 修复前的 full_chain_production_like_regression_v1 基线。
- v2 使用当前代码库、当前 artifacts/zjshl_v1.db，以及 P0/P1 修复后的运行时行为重新跑同一 120-query set。
- v2 额外显式归档 P0 四个原始 query 与 P1 三个 query 的 guard 状态，并生成 v1-v2 delta 与剩余 P2/P3 队列。

## A / B / C 运行情况

| mode | status | production_like | llm_preflight_used | reason |
| --- | --- | --- | --- | --- |
| A_data_plane_baseline | completed | False | None |  |
| B_retrieval_rerank | completed | False | None |  |
| C_production_like_full_chain | completed | True | True |  |

## 总体结果

- query_count: `120`
- record_count: `360`
- pass_count: `345`
- fail_count: `15`
- v1_total_failures: `37`
- v2_total_failures: `15`
- fixed_failures: `22`
- persistent_failures: `15`
- new_failures: `0`

## Failure Type 统计

| failure_type | count |
| --- | --- |
| answer_mode_calibration_error | 12 |
| assembler_slot_error | 3 |

## Evidence Boundary

- forbidden_primary_total: `0`
- review_only_primary_conflict_total: `0`
- wrong_definition_primary_total: `0`
- formula_bad_anchor_top5_total: `0`

## P0 / P1 Guard 状态

- P0 四个原始 query 仍通过: `True`
- P1 三个 query 仍通过: `True`
- P0 v1_failed_cases -> v2_failed_cases: `10 -> 0`
- P1 v1_failed_cases -> v2_failed_cases: `9 -> 0`

## 新失败与剩余队列

- 是否有新失败: `False`
- P2 candidates: `5`
- P3 observations: `1`

## 论文测试结果整理判断

- 是否可以进入论文第 4 章测试结果整理: `True`
- 建议：v2 已可作为 P0/P1 后的系统级测试基线；若要继续提升系统正确性，下一轮再单独处理 residual P2 queue。论文写作可基于本基线整理整体测试结果，并把剩余失败作为系统不足与展望。
