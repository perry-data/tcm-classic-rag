# Batch Promotion Policy v2

## A 类 safe primary

- 只允许干净、独立、术语锚点明确的句段进入 object primary。
- full/risk/ambiguous 抽句默认 `source_confidence=medium`。
- `primary_evidence_text` 必须是切出的句段，不能是整段 raw passage。
- canonical alias 和 learner-safe alias 均 exact-match。

## B 类 support/review-only

- 登记为 `promotion_state=review_only`，`is_safe_primary_candidate=0`。
- 不写 active learner normalization；support alias 也保持 inactive。
- 适合 weak answer 或 review_materials 参考，不进入 safe primary view。

## C 类 reject

- 只记录拒绝理由、风险来源和未来条件。
- 不写 registry/view/normalization。
