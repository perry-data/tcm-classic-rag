# 胆瘅 Alias Fix Before/After v1

## Decision

保持 `胆瘅` 为 review-only，不恢复 safe primary；清理 review-only 对象上的 learner aliases `口苦病` / `胆瘅病`，仅保留 canonical alias `胆瘅` 作为对象登记面。

## Registry Before/After

- source_confidence: `review_only` -> `review_only`
- promotion_state: `review_only` -> `review_only`
- is_safe_primary_candidate: `0` -> `0`
- query_aliases: `["口苦病"]` -> `[]`
- learner_surface_forms: `[]` -> `[]`
- risk alias count: `2` -> `0`
- risk learner lexicon count: `0` -> `0`

## Alias Before

```json
[
  {
    "alias": "口苦病",
    "normalized_alias": "口苦病",
    "alias_type": "learner_surface",
    "confidence": 0.9,
    "source": "data_plane_optimization_v1",
    "notes": "learner-facing term surface",
    "is_active": 1
  },
  {
    "alias": "胆瘅",
    "normalized_alias": "胆瘅",
    "alias_type": "canonical",
    "confidence": 1.0,
    "source": "data_plane_optimization_v1",
    "notes": "canonical term alias",
    "is_active": 1
  },
  {
    "alias": "胆瘅病",
    "normalized_alias": "胆瘅病",
    "alias_type": "learner_surface",
    "confidence": 0.9,
    "source": "data_plane_optimization_v1",
    "notes": "learner-facing term surface",
    "is_active": 1
  }
]
```

## Alias After

```json
[
  {
    "alias": "胆瘅",
    "normalized_alias": "胆瘅",
    "alias_type": "canonical",
    "confidence": 1.0,
    "source": "data_plane_optimization_v1",
    "notes": "canonical term alias",
    "is_active": 1
  }
]
```

## Query Behavior

| category | query | before_mode | after_mode | before_focus | after_focus | before_target_hit | after_target_hit | primary_after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dandan | 什么是胆瘅 | refuse | refuse | noise_stripped_query | noise_stripped_query | False | False | - |
| dandan | 胆瘅是什么意思 | weak_with_review_notice | weak_with_review_notice | noise_stripped_query | noise_stripped_query | False | False | - |
| dandan_alias | 口苦病是什么意思 | refuse | refuse | noise_stripped_query | noise_stripped_query | False | False | - |
| dandan_alias | 胆瘅病是什么意思 | refuse | refuse | noise_stripped_query | noise_stripped_query | False | False | - |
