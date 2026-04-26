# Ambiguous High Value Evidence Upgrade v1

本轮目标是从 ambiguous/full-risk/B 级材料中处理 30 条左右高价值 definition/concept 候选，并让 A 类对象通过 registry/view/normalization 被 runtime 命中。

## Scope Frozen

- 不改 prompt、前端、API payload 顶层 contract、answer_mode、commentarial 主逻辑。
- 不重新放开 raw full passages 或 ambiguous passages 直接进入 primary。
- 不为提升 strong 数量硬抬 review-only 材料。

## Outputs

- 候选池: `artifacts/data_plane_batch_upgrade/ambiguous_high_value_candidate_pool_v1.json`
- ledger: `artifacts/data_plane_batch_upgrade/batch_upgrade_ledger_v1.json`
- registry snapshots: `artifacts/data_plane_batch_upgrade/*_snapshot.json`
- regression: `artifacts/data_plane_batch_upgrade/batch_upgrade_regression_v1.json`
