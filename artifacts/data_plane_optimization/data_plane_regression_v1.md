# Data Plane Regression v1

- generated_at_utc: `2026-04-22T13:24:04.245170+00:00`
- before_db: `/private/tmp/zjshl_v1_before_data_plane_v1.db`
- after_db: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/zjshl_v1.db`

## Registry Snapshot

- before definition_term_registry_count: `6`
- after definition_term_registry_count: `32`
- before retrieval_ready_definition_view_count: `5`
- after retrieval_ready_definition_view_count: `29`
- after term_alias_registry_count: `86`
- after learner_query_normalization_lexicon_count: `97`

## Summary

- before mode_counts: `{"refuse": 13, "strong": 19, "weak_with_review_notice": 9}`
- after mode_counts: `{"strong": 39, "weak_with_review_notice": 2}`
- forbidden_primary before -> after: `0 -> 0`
- formula bad anchors top5 before -> after: `0 -> 0`
- support_only before -> after: `9 -> 2`
- promoted_to_strong_count: `20`
- short_term_strong before -> after: `0 -> 9`

## Query Table

| category | query | before | after | promoted | support_only_reduced | focus_source_before | focus_source_after | primary_after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| formula_exact | 桂枝汤方的条文是什么？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-008-P-0217<br>safe:main_passages:ZJSHL-CH-016-P-0034<br>safe:main_passages:ZJSHL-CH-008-P-0219 |
| formula_exact | 麻黄汤方的条文是什么？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-009-P-0023<br>safe:main_passages:ZJSHL-CH-009-P-0025 |
| formula_exact | 猪苓汤方的条文是什么？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-011-P-0109 |
| formula_exact | 葛根黄芩黄连汤方的条文是什么？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-009-P-0017<br>safe:main_passages:ZJSHL-CH-009-P-0019 |
| formula_similar | 桂枝去芍药汤方的条文是什么？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0005 |
| formula_similar | 桂枝去芍药加附子汤方的条文是什么？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0006 |
| formula_comparison | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-025-P-0003 |
| formula_comparison | 栀子豉汤方和栀子干姜汤方有什么不同？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-009-P-0175<br>safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-026-P-0004 |
| formula_comparison | 白虎汤方和白虎加人参汤方的区别是什么？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-010-P-0165<br>safe:main_passages:ZJSHL-CH-025-P-0012 |
| formula_comparison | 甘草乾姜汤方和芍药甘草汤方的区别是什么？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-008-P-0258<br>safe:main_passages:ZJSHL-CH-008-P-0261<br>safe:main_passages:ZJSHL-CH-008-P-0256 |
| formula_easy_confuse | 桂枝去芍药汤方和桂枝去芍药加附子汤方有什么不同？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0006<br>safe:main_passages:ZJSHL-CH-025-P-0005 |
| formula_easy_confuse | 四逆汤方和四逆加人参汤方有什么不同？ | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-029-P-0001<br>safe:main_passages:ZJSHL-CH-008-P-0267<br>safe:main_passages:ZJSHL-CH-008-P-0268 |
| definition | 什么是发汗药 | strong | strong | no | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-c8ac10b5ac88 |
| definition | 发汗药是什么意思 | strong | strong | no | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-c8ac10b5ac88 |
| definition | 什么是下药 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-033fc08d3b2a |
| definition | 下药是什么意思 | strong | strong | no | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-033fc08d3b2a |
| definition | 什么是坏病 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-f2fb5cd46de2 |
| definition | 坏病是什么意思 | strong | strong | no | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-f2fb5cd46de2 |
| definition | 什么是消渴 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-5261066339f8 |
| definition | 什么是风温 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-5df60e5f4e98 |
| definition | 风温是什么意思 | strong | strong | no | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-5df60e5f4e98 |
| definition | 什么是小结胸 | strong | strong | no | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-3110870253d3 |
| definition | 什么是脏结 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-0dd3b8ec1a82 |
| definition | 什么是虚烦 | weak_with_review_notice | strong | yes | yes | noise_stripped_query | term_normalization | safe:definition_terms:DPO-04bc5587d5f4 |
| definition | 什么是内烦 | weak_with_review_notice | strong | yes | yes | noise_stripped_query | term_normalization | safe:definition_terms:DPO-f3bab230a1db |
| definition | 什么是伏气 | weak_with_review_notice | strong | yes | yes | noise_stripped_query | term_normalization | safe:definition_terms:DPO-d1cbcfc0c2e2 |
| definition | 什么是两感 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-3883d70fcc3a |
| definition | 什么是湿痹 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-b5650615b93f |
| definition | 什么是胆瘅 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-3239213192a3 |
| learner_short | 下药是干什么的 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-033fc08d3b2a |
| learner_short | 睡着出汗是什么意思 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-246b6bf4c029 |
| learner_short | 四肢不温是什么 | weak_with_review_notice | strong | yes | yes | noise_stripped_query | term_normalization | safe:definition_terms:DPO-ce8ffb681e3f |
| learner_short | 口苦病是什么意思 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-3239213192a3 |
| learner_short | 时气是什么意思 | weak_with_review_notice | strong | yes | yes | noise_stripped_query | term_normalization | safe:definition_terms:DPO-2436635882e1 |
| learner_short | 气从少腹上冲是什么意思 | weak_with_review_notice | strong | yes | yes | noise_stripped_query | term_normalization | safe:definition_terms:DPO-e3ac03414a67 |
| learner_short | 表里两感是什么意思 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-3883d70fcc3a |
| learner_short | 水饮结胸是什么意思 | weak_with_review_notice | strong | yes | yes | noise_stripped_query | term_normalization | safe:definition_terms:DPO-e8f5807c114a |
| learner_short | 泻下药是什么意思 | refuse | strong | yes | no | noise_stripped_query | term_normalization | safe:definition_terms:DPO-033fc08d3b2a |
| boundary_review_only | 神丹是什么意思 | weak_with_review_notice | weak_with_review_notice | no | no | noise_stripped_query | noise_stripped_query | - |
| boundary_review_only | 两阳是什么意思 | strong | strong | no | no | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-009-P-0275<br>safe:main_passages:ZJSHL-CH-017-P-0049<br>safe:main_passages:ZJSHL-CH-009-P-0159 |
| boundary_review_only | 将军是什么意思 | weak_with_review_notice | weak_with_review_notice | no | no | noise_stripped_query | noise_stripped_query | - |

## Typical Before / After

### 什么是下药

- category: `definition`
- before: `refuse`
- after: `strong`
- before primary: `[]`
- after primary: `["safe:definition_terms:DPO-033fc08d3b2a"]`
- after term_normalization: `{"enabled": true, "type": "normalized_query", "concept_ids": ["DPO-033fc08d3b2a"], "matches": [{"concept_id": "DPO-033fc08d3b2a", "canonical_term": "下药", "alias": "下药", "normalized_alias": "下药", "alias_type": "canonical", "confidence": 1.0, "source": "data_plane_optimization_v1", "span": [0, 2]}], "matched_query_family": {"surface_form": "什么是", "match_mode": "prefix", "intent_hint": "what_is", "canonical_query_template": "什么是{topic}"}, "normalized_target_term": "下药", "canonical_target_term": "下药", "canonical_query": "什么是下药", "disabled_reason": null}`

### 什么是坏病

- category: `definition`
- before: `refuse`
- after: `strong`
- before primary: `[]`
- after primary: `["safe:definition_terms:DPO-f2fb5cd46de2"]`
- after term_normalization: `{"enabled": true, "type": "normalized_query", "concept_ids": ["DPO-f2fb5cd46de2"], "matches": [{"concept_id": "DPO-f2fb5cd46de2", "canonical_term": "坏病", "alias": "坏病", "normalized_alias": "坏病", "alias_type": "canonical", "confidence": 1.0, "source": "data_plane_optimization_v1", "span": [0, 2]}], "matched_query_family": {"surface_form": "什么是", "match_mode": "prefix", "intent_hint": "what_is", "canonical_query_template": "什么是{topic}"}, "normalized_target_term": "坏病", "canonical_target_term": "坏病", "canonical_query": "什么是坏病", "disabled_reason": null}`

### 什么是消渴

- category: `definition`
- before: `refuse`
- after: `strong`
- before primary: `[]`
- after primary: `["safe:definition_terms:DPO-5261066339f8"]`
- after term_normalization: `{"enabled": true, "type": "normalized_query", "concept_ids": ["DPO-5261066339f8"], "matches": [{"concept_id": "DPO-5261066339f8", "canonical_term": "消渴", "alias": "消渴", "normalized_alias": "消渴", "alias_type": "canonical", "confidence": 1.0, "source": "data_plane_optimization_v1", "span": [0, 2]}], "matched_query_family": {"surface_form": "什么是", "match_mode": "prefix", "intent_hint": "what_is", "canonical_query_template": "什么是{topic}"}, "normalized_target_term": "消渴", "canonical_target_term": "消渴", "canonical_query": "什么是消渴", "disabled_reason": null}`

### 什么是风温

- category: `definition`
- before: `refuse`
- after: `strong`
- before primary: `[]`
- after primary: `["safe:definition_terms:DPO-5df60e5f4e98"]`
- after term_normalization: `{"enabled": true, "type": "normalized_query", "concept_ids": ["DPO-5df60e5f4e98"], "matches": [{"concept_id": "DPO-5df60e5f4e98", "canonical_term": "风温", "alias": "风温", "normalized_alias": "风温", "alias_type": "canonical", "confidence": 1.0, "source": "data_plane_optimization_v1", "span": [0, 2]}], "matched_query_family": {"surface_form": "什么是", "match_mode": "prefix", "intent_hint": "what_is", "canonical_query_template": "什么是{topic}"}, "normalized_target_term": "风温", "canonical_target_term": "风温", "canonical_query": "什么是风温", "disabled_reason": null}`

### 什么是虚烦

- category: `definition`
- before: `weak_with_review_notice`
- after: `strong`
- before primary: `[]`
- after primary: `["safe:definition_terms:DPO-04bc5587d5f4"]`
- after term_normalization: `{"enabled": true, "type": "normalized_query", "concept_ids": ["DPO-04bc5587d5f4"], "matches": [{"concept_id": "DPO-04bc5587d5f4", "canonical_term": "虚烦", "alias": "虚烦", "normalized_alias": "虚烦", "alias_type": "canonical", "confidence": 1.0, "source": "data_plane_optimization_v1", "span": [0, 2]}], "matched_query_family": {"surface_form": "什么是", "match_mode": "prefix", "intent_hint": "what_is", "canonical_query_template": "什么是{topic}"}, "normalized_target_term": "虚烦", "canonical_target_term": "虚烦", "canonical_query": "什么是虚烦", "disabled_reason": null}`

### 什么是内烦

- category: `definition`
- before: `weak_with_review_notice`
- after: `strong`
- before primary: `[]`
- after primary: `["safe:definition_terms:DPO-f3bab230a1db"]`
- after term_normalization: `{"enabled": true, "type": "normalized_query", "concept_ids": ["DPO-f3bab230a1db"], "matches": [{"concept_id": "DPO-f3bab230a1db", "canonical_term": "内烦", "alias": "内烦", "normalized_alias": "内烦", "alias_type": "canonical", "confidence": 1.0, "source": "data_plane_optimization_v1", "span": [0, 2]}], "matched_query_family": {"surface_form": "什么是", "match_mode": "prefix", "intent_hint": "what_is", "canonical_query_template": "什么是{topic}"}, "normalized_target_term": "内烦", "canonical_target_term": "内烦", "canonical_query": "什么是内烦", "disabled_reason": null}`

### 什么是发汗药

- category: `definition`
- before: `strong`
- after: `strong`
- before primary: `["safe:definition_terms:DEF-FAHAN-YAO"]`
- after primary: `["safe:definition_terms:DPO-c8ac10b5ac88"]`
- after term_normalization: `{"enabled": true, "type": "normalized_query", "concept_ids": ["DPO-c8ac10b5ac88"], "matches": [{"concept_id": "DPO-c8ac10b5ac88", "canonical_term": "发汗药", "alias": "发汗药", "normalized_alias": "发汗药", "alias_type": "canonical", "confidence": 1.0, "source": "data_plane_optimization_v1", "span": [0, 3]}], "matched_query_family": {"surface_form": "什么是", "match_mode": "prefix", "intent_hint": "what_is", "canonical_query_template": "什么是{topic}"}, "normalized_target_term": "发汗药", "canonical_target_term": "发汗药", "canonical_query": "什么是发汗药", "disabled_reason": null}`

### 发汗药是什么意思

- category: `definition`
- before: `strong`
- after: `strong`
- before primary: `["safe:definition_terms:DEF-FAHAN-YAO"]`
- after primary: `["safe:definition_terms:DPO-c8ac10b5ac88"]`
- after term_normalization: `{"enabled": true, "type": "normalized_query", "concept_ids": ["DPO-c8ac10b5ac88"], "matches": [{"concept_id": "DPO-c8ac10b5ac88", "canonical_term": "发汗药", "alias": "发汗药", "normalized_alias": "发汗药", "alias_type": "canonical", "confidence": 1.0, "source": "data_plane_optimization_v1", "span": [0, 3]}], "matched_query_family": {"surface_form": "是什么意思", "match_mode": "suffix", "intent_hint": "what_means", "canonical_query_template": "{topic}是什么意思"}, "normalized_target_term": "发汗药", "canonical_target_term": "发汗药", "canonical_query": "发汗药是什么意思", "disabled_reason": null}`
