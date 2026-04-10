# meaning_explanation_boundary_fix_v1 patch note

## 变更范围

本轮只修 `eval_seed_q093` 的 meaning_explanation 强弱边界问题，不修改 goldset，不修改旧 72 条，不继续 Batch B，不处理 q095/q096。

## 代码变更

- 在 `backend/answers/assembler.py` 的标准回答组装路径中增加 meaning_explanation demotion 规则。
- 对 `是什么意思` / `什么意思` 问法，如果当前 strong primary 证据缺少 `名曰`、`谓之` 或 `者...也` 等定义句式，则把 primary_evidence 降入 secondary_evidence。
- demotion 后输出 `weak_with_review_notice`，并保留证据和 citation；`primary_evidence` 归零。
- 旧 strong meaning_explanation 的定义句式主证据保持 strong，不做全局弱化。

## 评估结果

- 重跑完整 `artifacts/evaluation/goldset_v2_working_102.json`。
- 新报告：
  - `artifacts/evaluation/meaning_explanation_boundary_fix_v1_eval_report.json`
  - `artifacts/evaluation/meaning_explanation_boundary_fix_v1_eval_report.md`
- `eval_seed_q093` 从 `strong` 修复为 `weak_with_review_notice`。
- q093 `primary_evidence = 0`，`unsupported_assertion_check = PASS`，gold citation check 继续通过。
- 完整 102 题 `failure_count` 从 `3` 降至 `2`。
- meaning_explanation 题型 `failure_count = 0`。
- 旧 72 条 meaning_explanation 样本保持 `14/14` 通过。

## 保留问题

以下失败未在本轮修复，按任务约束保留给后续专项处理：

- `eval_seed_q095`
- `eval_seed_q096`
