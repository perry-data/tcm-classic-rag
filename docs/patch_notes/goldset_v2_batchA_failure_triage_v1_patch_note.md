# Goldset v2 Batch A Failure Triage v1 Patch Note

- 日期：2026-04-08
- 范围：只分析 Batch A evaluator v1 的 13 个失败样本
- 不做事项：不修系统、不改 goldset、不改旧 72 条、不继续 Batch B、不写论文正文

## 变更

1. 新增 `docs/evaluation/goldset_v2_batchA_failure_triage_v1.md`，逐题记录失败原因、归因类别和建议动作。
2. 新增 `artifacts/evaluation/goldset_v2_batchA_failure_triage_v1.json`，结构化记录 13 条失败样本的 expected/actual、failed_checks、failure_category、likely_owner、recommended_next_action 和 notes。

## 归因分布

- dataset: 0
- system: 12
- mixed: 1

## 建议

本轮建议先修系统，尤其是 refusal policy，其次是 comparison 双实体识别、source_lookup 证据分层/强弱模式晋级，以及 general_overview 主题检索。仅 `eval_seed_q096` 建议在系统侧复查后再考虑样本题面或 gold scope 收紧。

## 验证

本轮未修改 `goldset_v2_working_102.json`、旧 72 条或系统代码；只新增 triage 报告和 patch note。
