# Batch Promotion Policy v1

A 类对象进入 `definition_term_registry`，并在 `is_safe_primary_candidate=1` 时通过 `retrieval_ready_definition_view` 暴露给 runtime。

## A 类

- 来源可以是 B 级 main、full passage 或 ambiguous risk registry，但 primary 只指向切出的干净句段。
- 来自 full/risk/ambiguous 的对象默认 `source_confidence=medium`，不硬升 high。
- 只有 canonical/learner_safe alias 进入 active runtime normalization。

## B 类

- 写入 registry，`promotion_state=review_only`，`is_safe_primary_candidate=0`。
- 允许 canonical support alias，但不写 learner-safe normalization。
- 句子在 `sentence_role_registry` 标记 `review_only_support`。

## C 类

- 不写 runtime normalization。
- 只在候选池和 ledger 中记录拒绝理由、风险来源和未来处理条件。
