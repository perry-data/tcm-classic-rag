# source_lookup_promotion_fix_v1 patch note

## 变更范围

本轮只修 `eval_seed_q076` 和 `eval_seed_q082` 对应的 source_lookup strong 晋级问题，不修改 goldset，不修改旧 72 条，不继续 Batch B，不处理 meaning_explanation / general_overview 的剩余失败。

## 代码变更

- 在 `backend/retrieval/minimal.py` 中新增 formula raw title anchor 抽取与方名锚点清洗。
- 支持清洗或还原 `赵本有「...」字`、`赵本/医统本并有「...」字`、`赵本作「...」`、`赵本无「...」字` 等标题校注。
- 在 formula anchor normalization 中统一 `厚朴/浓朴`、`杏仁/杏人/杏子`。
- `evaluate_topic_consistency()` 改用清洗后的 candidate formula anchor，恢复 q076/q082 的 `exact_formula_anchor` 和 primary_evidence 晋级。

## 评估结果

- 重跑完整 `artifacts/evaluation/goldset_v2_working_102.json`。
- 新报告：
  - `artifacts/evaluation/source_lookup_promotion_fix_v1_eval_report.json`
  - `artifacts/evaluation/source_lookup_promotion_fix_v1_eval_report.md`
- `eval_seed_q076` 与 `eval_seed_q082` 均从 `weak_with_review_notice` 修复为 `strong`。
- 两题 gold citation check 均继续通过。
- 完整 102 题 `failure_count` 从 `5` 降至 `3`。
- source_lookup 题型 `failure_count = 0`。
- 旧 72 条 source_lookup 样本保持 `20/20` 通过；未新增旧 source_lookup 失败。

## 保留问题

以下失败未在本轮修复，按任务约束保留给后续专项处理：

- `eval_seed_q093`
- `eval_seed_q095`
- `eval_seed_q096`
