# Formula Runtime Regression v1

- generated_at_utc: `2026-04-22T11:14:12.962500+00:00`
- engine: `hybrid`
- query_count: `15`
- before formula object: disabled via `TCM_DISABLE_FORMULA_OBJECT_RETRIEVAL=1`
- after formula object: enabled

## Aggregate Before / After

| metric | before | after | delta |
| --- | ---: | ---: | ---: |
| top5_bad_formula_anchor_total | 11 | 0 | -11 |
| top5_different_formula_anchor_total | 0 | 0 | 0 |
| top5_expanded_formula_anchor_total | 10 | 0 | -10 |
| top5_risk_candidate_total | 27 | 15 | -12 |
| formula_cross_target_candidates_trigger_count | 8 | 0 | -8 |
| high_risk_candidate_dominance_trigger_count | 9 | 1 | -8 |
| primary_formula_backref_total | 0 | 20 | 20 |
| primary_target_topic_total | 20 | 38 | 18 |

## Per Query Summary

| query | type | before bad top5 | after bad top5 | before risk top5 | after risk top5 | after formula ids | after primary |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 桂枝去芍药汤方和桂枝去芍药加附子汤方的条文语境有什么不同？ | comparison | 0 | 0 | 0 | 0 | ["FML-bc9f2a4ed524", "FML-3f081531c40e"] | ["safe:main_passages:ZJSHL-CH-025-P-0006", "safe:main_passages:ZJSHL-CH-025-P-0005"] |
| 葛根黄芩黄连汤方的条文是什么？ | source_lookup | 1 | 0 | 3 | 3 | ["FML-1df3a038d2f7"] | ["safe:main_passages:ZJSHL-CH-009-P-0017", "safe:main_passages:ZJSHL-CH-009-P-0019"] |
| 甘草乾姜汤方和芍药甘草汤方的区别是什么？ | comparison | 0 | 0 | 3 | 1 | ["FML-dcf9a8a122b7", "FML-b6b86919b277"] | ["safe:main_passages:ZJSHL-CH-008-P-0258", "safe:main_passages:ZJSHL-CH-008-P-0261", "safe:main_passages:ZJSHL-CH-008-P-0256"] |
| 麻黄汤方的条文是什么？ | source_lookup | 1 | 0 | 2 | 1 | ["FML-04f61fac7138"] | ["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0023", "safe:main_passages:ZJSHL-CH-009-P-0025"] |
| 大青龙汤方的条文是什么？ | source_lookup | 1 | 0 | 2 | 1 | ["FML-41e6b4407fe9"] | ["safe:main_passages:ZJSHL-CH-009-P-0033", "safe:main_passages:ZJSHL-CH-009-P-0034", "safe:main_passages:ZJSHL-CH-009-P-0035"] |
| 葛根加半夏汤方的条文是什么？ | source_lookup | 0 | 0 | 1 | 1 | ["FML-c3adfda0ffe4"] | ["safe:main_passages:ZJSHL-CH-009-P-0012", "safe:main_passages:ZJSHL-CH-026-P-0001", "safe:main_passages:ZJSHL-CH-009-P-0013"] |
| 调胃承气汤方的条文是什么？ | source_lookup | 2 | 0 | 3 | 1 | ["FML-be7f7d55c124"] | ["safe:main_passages:ZJSHL-CH-008-P-0264", "safe:main_passages:ZJSHL-CH-008-P-0266"] |
| 栀子豉汤方和栀子乾姜汤方有什么不同？ | comparison | 0 | 0 | 1 | 1 | ["FML-03bfe5c6c2a8", "FML-ae19c8d79625"] | ["safe:main_passages:ZJSHL-CH-009-P-0175", "safe:main_passages:ZJSHL-CH-009-P-0159", "safe:main_passages:ZJSHL-CH-009-P-0173"] |
| 白虎汤方和白虎加人参汤方的区别是什么？ | comparison | 0 | 0 | 1 | 1 | ["FML-47765c7ee78a", "FML-e55f3490b8f5"] | ["safe:main_passages:ZJSHL-CH-025-P-0012", "safe:main_passages:ZJSHL-CH-010-P-0165", "safe:main_passages:ZJSHL-CH-011-P-0104"] |
| 茯苓桂枝甘草大枣汤方的条文是什么？ | source_lookup | 2 | 0 | 3 | 1 | ["FML-7c8ba7b6d3bb"] | ["safe:main_passages:ZJSHL-CH-009-P-0110", "safe:main_passages:ZJSHL-CH-009-P-0112"] |
| 茯苓桂枝白术甘草汤方的条文是什么？ | source_lookup | 2 | 0 | 1 | 1 | ["FML-e327d5c79e9c"] | ["safe:main_passages:ZJSHL-CH-009-P-0120", "safe:main_passages:ZJSHL-CH-009-P-0122", "safe:main_passages:ZJSHL-CH-009-P-0118"] |
| 猪苓汤方的条文是什么？ | source_lookup | 1 | 0 | 2 | 1 | ["FML-5044258f6493"] | ["safe:main_passages:ZJSHL-CH-011-P-0109"] |
| 桃核承气汤方的条文是什么？ | source_lookup | 1 | 0 | 2 | 1 | ["FML-e6e8ed2aa322"] | ["safe:main_passages:ZJSHL-CH-009-P-0261", "safe:main_passages:ZJSHL-CH-009-P-0263"] |
| 麻黄汤方和大青龙汤方的区别是什么？ | comparison | 0 | 0 | 2 | 1 | ["FML-04f61fac7138", "FML-41e6b4407fe9"] | ["safe:main_passages:ZJSHL-CH-009-P-0033", "safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0034"] |
| 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | comparison | 0 | 0 | 1 | 0 | ["FML-040863271409", "FML-ab783d366a21"] | ["safe:main_passages:ZJSHL-CH-025-P-0003", "safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-008-P-0236"] |

## Typical Before / After Traces

### 葛根黄芩黄连汤方的条文是什么？

- before top5: `["safe:main_passages:ZJSHL-CH-009-P-0016:exact_formula_anchor", "full:passages:ZJSHL-CH-009-P-0016:exact_formula_anchor", "safe:chunks:ZJSHL-CK-F-0009:exact_formula_anchor", "full:passages:ZJSHL-CH-009-P-0015:formula_query_off_topic"]`
- after top5: `["formula:FML-1df3a038d2f7:formula_object_exact", "safe:main_passages:ZJSHL-CH-009-P-0016:same_formula_span", "full:passages:ZJSHL-CH-009-P-0016:same_formula_span", "safe:chunks:ZJSHL-CK-F-0009:same_formula_span", "full:passages:ZJSHL-CH-009-P-0015:phrase_only_match"]`
- after formula_normalization: `{"enabled": true, "type": "exact", "formula_ids": ["FML-1df3a038d2f7"], "target_formula_id": "FML-1df3a038d2f7", "matches": [{"formula_id": "FML-1df3a038d2f7", "canonical_name": "葛根黄芩黄连汤", "alias": "葛根黄芩黄连汤", "normalized_alias": "葛根黄芩黄连汤", "alias_type": "canonical", "confidence": 1.0, "span": [0, 7]}], "disabled_reason": null}`

### 麻黄汤方的条文是什么？

- before top5: `["safe:main_passages:ZJSHL-CH-009-P-0022:exact_formula_anchor", "full:passages:ZJSHL-CH-009-P-0022:exact_formula_anchor", "safe:chunks:ZJSHL-CK-F-0010:exact_formula_anchor", "full:passages:ZJSHL-CH-011-P-0128:expanded_formula_anchor"]`
- after top5: `["formula:FML-04f61fac7138:formula_object_exact", "safe:main_passages:ZJSHL-CH-009-P-0022:same_formula_span", "full:passages:ZJSHL-CH-009-P-0022:same_formula_span", "safe:chunks:ZJSHL-CK-F-0010:same_formula_span"]`
- after formula_normalization: `{"enabled": true, "type": "exact", "formula_ids": ["FML-04f61fac7138"], "target_formula_id": "FML-04f61fac7138", "matches": [{"formula_id": "FML-04f61fac7138", "canonical_name": "麻黄汤", "alias": "麻黄汤", "normalized_alias": "麻黄汤", "alias_type": "canonical", "confidence": 1.0, "span": [0, 3]}], "disabled_reason": null}`

### 大青龙汤方的条文是什么？

- before top5: `["safe:main_passages:ZJSHL-CH-009-P-0033:exact_formula_anchor", "full:passages:ZJSHL-CH-009-P-0033:exact_formula_anchor", "safe:chunks:ZJSHL-CK-F-0011:exact_formula_anchor", "full:passages:ZJSHL-CH-009-P-0031:expanded_formula_anchor"]`
- after top5: `["formula:FML-41e6b4407fe9:formula_object_exact", "safe:main_passages:ZJSHL-CH-009-P-0033:same_formula_span", "full:passages:ZJSHL-CH-009-P-0033:same_formula_span", "safe:chunks:ZJSHL-CK-F-0011:same_formula_span"]`
- after formula_normalization: `{"enabled": true, "type": "exact", "formula_ids": ["FML-41e6b4407fe9"], "target_formula_id": "FML-41e6b4407fe9", "matches": [{"formula_id": "FML-41e6b4407fe9", "canonical_name": "大青龙汤", "alias": "大青龙汤", "normalized_alias": "大青龙汤", "alias_type": "canonical", "confidence": 1.0, "span": [0, 4]}], "disabled_reason": null}`

### 调胃承气汤方的条文是什么？

- before top5: `["safe:main_passages:ZJSHL-CH-008-P-0264:exact_formula_anchor", "full:passages:ZJSHL-CH-008-P-0264:exact_formula_anchor", "safe:chunks:ZJSHL-CK-F-0005:exact_formula_anchor", "full:passages:ZJSHL-CH-011-P-0064:expanded_formula_anchor", "full:annotations:ZJSHL-CH-009-P-0134:expanded_formula_anchor"]`
- after top5: `["formula:FML-be7f7d55c124:formula_object_exact", "safe:main_passages:ZJSHL-CH-008-P-0264:same_formula_span", "full:passages:ZJSHL-CH-008-P-0264:same_formula_span", "safe:chunks:ZJSHL-CK-F-0005:same_formula_span"]`
- after formula_normalization: `{"enabled": true, "type": "exact", "formula_ids": ["FML-be7f7d55c124"], "target_formula_id": "FML-be7f7d55c124", "matches": [{"formula_id": "FML-be7f7d55c124", "canonical_name": "调胃承气汤", "alias": "调胃承气汤", "normalized_alias": "调胃承气汤", "alias_type": "canonical", "confidence": 1.0, "span": [0, 5]}], "disabled_reason": null}`

### 茯苓桂枝甘草大枣汤方的条文是什么？

- before top5: `["safe:main_passages:ZJSHL-CH-009-P-0110:exact_formula_anchor", "full:passages:ZJSHL-CH-009-P-0110:exact_formula_anchor", "safe:chunks:ZJSHL-CK-F-0016:exact_formula_anchor", "full:passages:ZJSHL-CH-009-P-0108:expanded_formula_anchor", "full:annotations:ZJSHL-CH-009-P-0109:expanded_formula_anchor"]`
- after top5: `["formula:FML-7c8ba7b6d3bb:formula_object_exact", "safe:main_passages:ZJSHL-CH-009-P-0110:same_formula_span", "full:passages:ZJSHL-CH-009-P-0110:same_formula_span", "safe:chunks:ZJSHL-CK-F-0016:same_formula_span"]`
- after formula_normalization: `{"enabled": true, "type": "exact", "formula_ids": ["FML-7c8ba7b6d3bb"], "target_formula_id": "FML-7c8ba7b6d3bb", "matches": [{"formula_id": "FML-7c8ba7b6d3bb", "canonical_name": "茯苓桂枝甘草大枣汤", "alias": "茯苓桂枝甘草大枣汤", "normalized_alias": "茯苓桂枝甘草大枣汤", "alias_type": "canonical", "confidence": 1.0, "span": [0, 9]}], "disabled_reason": null}`
