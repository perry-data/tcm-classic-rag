# Ambiguous High Value Evidence Upgrade v2

本轮目标是从 ambiguous/full-risk/B 级材料中新增第二批可审计 definition/concept objects，并把 batch upgrade、quality audit、adversarial regression 和 minimal fix 放在同一闭环内。

## Frozen Boundaries

- 不改 prompt、前端、API payload 顶层 contract、answer_mode、commentarial 主逻辑。
- 不重新放开 raw `full:passages:*` 或 `full:ambiguous_passages:*` 直接进入 primary。
- 不处理 formula medium span；formula query 只作为 guard。
- AHV2 learner normalization 默认 `exact`，不得新增 active `contains` learner surface。

## Runtime Shape

- A 类写入 `definition_term_registry`，`promotion_source_layer=ambiguous_high_value_evidence_upgrade_v2_safe_primary`。
- B 类写入 support/review-only registry row，`is_safe_primary_candidate=0`，不写 active learner normalization。
- C 类只进入候选池和 ledger，不进入 runtime registry。
