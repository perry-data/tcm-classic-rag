# refusal_policy_fix_v1 patch note

## 变更范围

本轮只修 Batch A refusal 边界问题，不修改 `goldset_v2_working_102.json`，不修改旧 72 条 goldset，不继续 Batch B，不处理 comparison / source_lookup / general_overview / meaning_explanation 的其他失败项。

## 代码变更

- 在 `backend/answers/assembler.py` 的 `AnswerAssembler.assemble()` 入口增加前置 refusal policy 判定。
- 对个人诊疗、体重/剂量换算、现代病名疗效判断、个体化用药方案、跨书价值判断等请求直接返回 `refuse`。
- policy refusal payload 保持 evidence 与 citations 全为空，并返回具体 `refuse_reason`。

## 评估结果

- 重跑完整 `artifacts/evaluation/goldset_v2_working_102.json`。
- 新报告：
  - `artifacts/evaluation/refusal_policy_fix_v1_eval_report.json`
  - `artifacts/evaluation/refusal_policy_fix_v1_eval_report.md`
- `eval_seed_q097` 至 `eval_seed_q102` 全部从失败变为通过。
- 完整 102 题 `failure_count` 从 `13` 降至 `7`。
- refusal 题型 `failure_count = 0`。
- 旧 72 条 refusal 样本保持通过；未新增 refusal 相关失败。

## 保留问题

以下失败未在本轮修复，按任务约束保留给后续专项处理：

- `eval_seed_q076`
- `eval_seed_q082`
- `eval_seed_q085`
- `eval_seed_q090`
- `eval_seed_q093`
- `eval_seed_q095`
- `eval_seed_q096`
