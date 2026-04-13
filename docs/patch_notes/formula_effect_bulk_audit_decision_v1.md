# formula_effect_bulk_audit_decision_v1

## 是否值得继续深挖

- 建议：`继续 formula_effect`
- 判断依据：虽然全量失败里可能有大量 review-only / raw recall 限制，但仍存在可观的 assembler 级失配，继续修还有明确收益。

## 若继续修，下一轮应只修哪个最大类问题

- 下一轮只建议集中修：`cross_chapter_bridge_primary`

## 若不值得继续修，理由是什么

- 当失败主因主要落在 `raw_recall_missing_direct_context` 或 `review_only_should_remain_weak` 时，本轮约束下无法通过 assembler 小修带来结构性收益。

## 明确建议

- 当前建议：`继续 formula_effect`
- 当前最大 failure pattern（全量）：`review_only_should_remain_weak`
- 当前最大可修 failure pattern：`cross_chapter_bridge_primary`
- strong 但 primary 可疑（query 级）：`111`
- review-only weak（query 级）：`77`
- raw recall 缺失（query 级）：`28`
- assembler weak（query 级）：`0`
