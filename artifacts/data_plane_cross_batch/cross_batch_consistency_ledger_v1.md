# Cross-Batch AHV Consistency Ledger v1

- audited_object_count: `40`
- ahv_v1_object_count: `20`
- ahv2_object_count: `20`
- duplicate_concept_count: `0`
- active_contains_count: `0`
- active_single_char_alias_count: `0`
- duplicate_active_alias_count: `0`
- inactive_alias_primary_backdoor_count: `0`
- review_only_learner_safe_conflict_count: `0`
- confidence_consistent_count: `40`
- confidence_inconsistent_count: `0`
- evidence_type_consistent_count: `40`
- evidence_type_inconsistent_count: `0`

## Concept Groups

| group | present_terms | missing_terms | conclusion | rationale |
| --- | --- | --- | --- | --- |
| convulsion_terms | 痓病, 刚痓, 柔痓 | - | no_cross_batch_conflict | 对象边界按 canonical term exact 命中；未发现 active alias 跨对象复用。 |
| pulse_terms | 结脉, 促脉, 数脉, 滑脉, 弦脉, 革脉, 毛脉, 纯弦脉 | - | no_cross_batch_conflict | 对象边界按 canonical term exact 命中；未发现 active alias 跨对象复用。 |
| six_channel_outline_terms | 太阳病, 阳明病, 太阴病, 少阴病, 厥阴病 | - | no_cross_batch_conflict | 对象边界按 canonical term exact 命中；未发现 active alias 跨对象复用。 |
| seasonal_disease_terms | 伤寒, 温病, 暑病, 冬温, 时行寒疫 | - | no_cross_batch_conflict | 对象边界按 canonical term exact 命中；未发现 active alias 跨对象复用。 |
| post_recovery_terms | 劳复, 食复, 过经 | - | no_cross_batch_conflict | 对象边界按 canonical term exact 命中；未发现 active alias 跨对象复用。 |
| chest_and_location_terms | 结胸, 半表半里证, 水逆 | 水结胸 | no_cross_batch_conflict | 对象边界按 canonical term exact 命中；未发现 active alias 跨对象复用。 |

## Evidence Type Inconsistencies

- none

## Confidence Inconsistencies

- none
