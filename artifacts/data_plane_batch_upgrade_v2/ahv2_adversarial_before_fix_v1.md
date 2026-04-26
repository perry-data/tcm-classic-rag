# AHV2 Adversarial Regression v1

- run_label: `before_fix`
- total_query_count: `94`
- strong / weak / refuse: `56 / 14 / 24`
- pass_count / fail_count: `90 / 4`
- new_safe_object_primary_hit_count: `16`
- wrong_ahv2_primary_hit_count: `0`
- wrong_term_normalization_count: `0`
- disabled_alias_still_hit_count: `0`
- partial_word_false_positive_count: `0`
- non_definition_intent_hijack_count: `0`
- negative_sample_false_positive_count: `0`
- forbidden_primary_total: `0`
- review_only_primary_conflict_count: `0`
- formula_bad_anchor_top5_total: `0`
- ahv_v1_guard_pass_count: `5`

## Failures

| query_id | query_type | query | mode | matched_ahv2_terms | ahv2_primary_terms | fail_reason |
| --- | --- | --- | --- | --- | --- | --- |
| ahv2_canonical_17 | ahv2_canonical_guard | 阳明病是什么 | error | - | - | exception: KeyError: 'query_request' |
| ahv2_canonical_18 | ahv2_canonical_guard | 太阴病是什么 | error | - | - | exception: KeyError: 'query_request' |
| ahv2_canonical_19 | ahv2_canonical_guard | 少阴病是什么 | error | - | - | exception: KeyError: 'query_request' |
| ahv2_canonical_20 | ahv2_canonical_guard | 厥阴病是什么 | error | - | - | exception: KeyError: 'query_request' |

## Query Results

| query_id | query_type | query | mode | primary_ids | pass |
| --- | --- | --- | --- | --- | --- |
| ahv2_canonical_01 | ahv2_canonical_guard | 荣气微是什么意思 | strong | safe:definition_terms:AHV2-850318ee8950 | True |
| ahv2_canonical_02 | ahv2_canonical_guard | 卫气衰是什么意思 | strong | safe:definition_terms:AHV2-81a12b6da994 | True |
| ahv2_canonical_03 | ahv2_canonical_guard | 阳气微是什么意思 | strong | safe:definition_terms:AHV2-767dfa46f2b1 | True |
| ahv2_canonical_04 | ahv2_canonical_guard | 亡血是什么意思 | strong | safe:definition_terms:AHV2-7882ca0aa96a | True |
| ahv2_canonical_05 | ahv2_canonical_guard | 平脉是什么 | strong | safe:definition_terms:AHV2-310eca701a93 | True |
| ahv2_canonical_06 | ahv2_canonical_guard | 数脉是什么意思 | strong | safe:definition_terms:AHV2-f9e89349db80 | True |
| ahv2_canonical_07 | ahv2_canonical_guard | 毛脉是什么 | strong | safe:definition_terms:AHV2-5f24c7010fec | True |
| ahv2_canonical_08 | ahv2_canonical_guard | 纯弦脉是什么意思 | strong | safe:definition_terms:AHV2-92d765f487d4 | True |
| ahv2_canonical_09 | ahv2_canonical_guard | 残贼是什么意思 | strong | safe:definition_terms:AHV2-dac342243a2d | True |
| ahv2_canonical_10 | ahv2_canonical_guard | 八邪是什么 | strong | safe:definition_terms:AHV2-c29e7aff2765 | True |
| ahv2_canonical_11 | ahv2_canonical_guard | 湿家是什么 | strong | safe:definition_terms:AHV2-1e3cd430a062 | True |
| ahv2_canonical_12 | ahv2_canonical_guard | 风湿是什么 | strong | safe:definition_terms:AHV2-f5bd47a65fa0 | True |
| ahv2_canonical_13 | ahv2_canonical_guard | 水逆是什么意思 | strong | safe:definition_terms:AHV2-1da410fb57b4 | True |
| ahv2_canonical_14 | ahv2_canonical_guard | 半表半里证是什么 | strong | safe:definition_terms:AHV2-aa28a21f86c8 | True |
| ahv2_canonical_15 | ahv2_canonical_guard | 过经是什么意思 | strong | safe:definition_terms:AHV2-dbeb47457236 | True |
| ahv2_canonical_16 | ahv2_canonical_guard | 结胸是什么 | strong | safe:definition_terms:AHV2-0f3d2d43c342 | True |
| ahv2_canonical_17 | ahv2_canonical_guard | 阳明病是什么 | error | - | False |
| ahv2_canonical_18 | ahv2_canonical_guard | 太阴病是什么 | error | - | False |
| ahv2_canonical_19 | ahv2_canonical_guard | 少阴病是什么 | error | - | False |
| ahv2_canonical_20 | ahv2_canonical_guard | 厥阴病是什么 | error | - | False |
| similar_01 | similar_concept_false_trigger | 荣气微弱是什么意思 | weak_with_review_notice | - | True |
| similar_02 | similar_concept_false_trigger | 卫气虚是什么意思 | weak_with_review_notice | - | True |
| similar_03 | similar_concept_false_trigger | 阳气不足是什么意思 | weak_with_review_notice | - | True |
| similar_04 | similar_concept_false_trigger | 亡阳是什么意思 | strong | safe:main_passages:ZJSHL-CH-014-P-0025 | True |
| similar_05 | similar_concept_false_trigger | 平是什么意思 | strong | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-011-P-0209 | True |
| similar_06 | similar_concept_false_trigger | 平脉和数脉有什么区别 | refuse | - | True |
| similar_07 | similar_concept_false_trigger | 数是什么意思 | strong | safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-008-P-0217<br>safe:main_passages:ZJSHL-CH-010-P-0113 | True |
| similar_08 | similar_concept_false_trigger | 毛是什么意思 | strong | safe:main_passages:ZJSHL-CH-004-P-0191<br>safe:main_passages:ZJSHL-CH-004-P-0193<br>safe:main_passages:ZJSHL-CH-004-P-0227 | True |
| similar_09 | similar_concept_false_trigger | 纯弦是什么意思 | weak_with_review_notice | - | True |
| similar_10 | similar_concept_false_trigger | 残是什么意思 | strong | safe:main_passages:ZJSHL-CH-004-P-0178 | True |
| similar_11 | similar_concept_false_trigger | 八邪和残贼有什么区别 | refuse | - | True |
| similar_12 | similar_concept_false_trigger | 湿病是什么 | refuse | - | True |
| similar_13 | similar_concept_false_trigger | 风湿病是什么 | refuse | - | True |
| similar_14 | similar_concept_false_trigger | 水逆反应是什么 | refuse | - | True |
| similar_15 | similar_concept_false_trigger | 半表半里和表里之间一样吗 | strong | safe:main_passages:ZJSHL-CH-010-P-0005 | True |
| similar_16 | similar_concept_false_trigger | 过经方是什么意思 | refuse | - | True |
| similar_17 | similar_concept_false_trigger | 结胸证和水结胸有什么区别 | weak_with_review_notice | - | True |
| similar_18 | similar_concept_false_trigger | 阳明是什么意思 | strong | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-011-P-0158 | True |
| similar_19 | similar_concept_false_trigger | 太阴是什么意思 | strong | safe:main_passages:ZJSHL-CH-004-P-0191<br>safe:main_passages:ZJSHL-CH-006-P-0067<br>safe:main_passages:ZJSHL-CH-006-P-0069 | True |
| similar_20 | similar_concept_false_trigger | 少阴和厥阴有什么区别 | refuse | - | True |
| disabled_alias_01 | disabled_alias_recheck | 平是什么意思 | strong | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-011-P-0209 | True |
| disabled_alias_02 | disabled_alias_recheck | 数是什么意思 | strong | safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-008-P-0217<br>safe:main_passages:ZJSHL-CH-010-P-0113 | True |
| disabled_alias_03 | disabled_alias_recheck | 毛是什么意思 | strong | safe:main_passages:ZJSHL-CH-004-P-0191<br>safe:main_passages:ZJSHL-CH-004-P-0193<br>safe:main_passages:ZJSHL-CH-004-P-0227 | True |
| disabled_alias_04 | disabled_alias_recheck | 纯弦是什么意思 | weak_with_review_notice | - | True |
| disabled_alias_05 | disabled_alias_recheck | 风湿病是什么 | refuse | - | True |
| partial_word_01 | partial_word_literal_similarity | 荣是什么意思 | strong | safe:main_passages:ZJSHL-CH-027-P-0001<br>safe:main_passages:ZJSHL-CH-009-P-0033<br>safe:main_passages:ZJSHL-CH-009-P-0034 | True |
| partial_word_02 | partial_word_literal_similarity | 卫是什么意思 | strong | safe:main_passages:ZJSHL-CH-027-P-0001<br>safe:main_passages:ZJSHL-CH-009-P-0033<br>safe:main_passages:ZJSHL-CH-009-P-0034 | True |
| partial_word_03 | partial_word_literal_similarity | 阳是什么意思 | strong | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-009-P-0022 | True |
| partial_word_04 | partial_word_literal_similarity | 血是什么意思 | strong | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-010-P-0123<br>safe:main_passages:ZJSHL-CH-017-P-0050 | True |
| partial_word_05 | partial_word_literal_similarity | 平是什么意思 | strong | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-011-P-0209 | True |
| partial_word_06 | partial_word_literal_similarity | 数是什么意思 | strong | safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-008-P-0217<br>safe:main_passages:ZJSHL-CH-010-P-0113 | True |
| partial_word_07 | partial_word_literal_similarity | 毛是什么意思 | strong | safe:main_passages:ZJSHL-CH-004-P-0191<br>safe:main_passages:ZJSHL-CH-004-P-0193<br>safe:main_passages:ZJSHL-CH-004-P-0227 | True |
| partial_word_08 | partial_word_literal_similarity | 湿是什么意思 | strong | safe:main_passages:ZJSHL-CH-010-P-0153<br>safe:main_passages:ZJSHL-CH-010-P-0159<br>safe:main_passages:ZJSHL-CH-004-P-0205 | True |
| partial_word_09 | partial_word_literal_similarity | 水是什么意思 | strong | safe:main_passages:ZJSHL-CH-027-P-0011<br>safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022 | True |
| partial_word_10 | partial_word_literal_similarity | 胸是什么意思 | strong | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-010-P-0123 | True |
| non_definition_01 | non_definition_intent | 荣气微怎么治？ | weak_with_review_notice | - | True |
| non_definition_02 | non_definition_intent | 卫气衰用什么方？ | weak_with_review_notice | - | True |
| non_definition_03 | non_definition_intent | 水逆怎么治？ | refuse | - | True |
| non_definition_04 | non_definition_intent | 结胸用什么方？ | refuse | - | True |
| non_definition_05 | non_definition_intent | 半表半里证有哪些方？ | weak_with_review_notice | - | True |
| non_definition_06 | non_definition_intent | 阳明病怎么治疗？ | strong | safe:main_passages:ZJSHL-CH-011-P-0054<br>safe:main_passages:ZJSHL-CH-011-P-0012<br>safe:main_passages:ZJSHL-CH-011-P-0038 | True |
| non_definition_07 | non_definition_intent | 太阴病的病机是什么？ | strong | safe:main_passages:ZJSHL-CH-013-P-0008<br>safe:main_passages:ZJSHL-CH-006-P-0076 | True |
| non_definition_08 | non_definition_intent | 风湿和湿家有什么区别？ | weak_with_review_notice | - | True |
| non_definition_09 | non_definition_intent | 少阴病有哪些方？ | weak_with_review_notice | - | True |
| non_definition_10 | non_definition_intent | 厥阴病怎么治？ | strong | safe:main_passages:ZJSHL-CH-015-P-0198<br>safe:main_passages:ZJSHL-CH-006-P-0076 | True |
| negative_01 | negative_unrelated | 平板电脑是什么 | refuse | - | True |
| negative_02 | negative_unrelated | 数学是什么意思 | refuse | - | True |
| negative_03 | negative_unrelated | 毛衣是什么 | refuse | - | True |
| negative_04 | negative_unrelated | 风湿免疫科是什么 | refuse | - | True |
| negative_05 | negative_unrelated | 水逆网络用语是什么意思 | refuse | - | True |
| negative_06 | negative_unrelated | 胸口健身动作是什么 | refuse | - | True |
| negative_07 | negative_unrelated | 太阴历是什么 | refuse | - | True |
| negative_08 | negative_unrelated | 阳明山在哪里 | refuse | - | True |
| negative_09 | negative_unrelated | 过经纪人是什么意思 | refuse | - | True |
| negative_10 | negative_unrelated | 八邪游戏是什么 | refuse | - | True |
| formula_guard_01 | formula_guard | 桂枝去芍药汤方的条文是什么？ | strong | safe:main_passages:ZJSHL-CH-025-P-0005 | True |
| formula_guard_02 | formula_guard | 桂枝去芍药加附子汤方的条文是什么？ | strong | safe:main_passages:ZJSHL-CH-025-P-0006 | True |
| formula_guard_03 | formula_guard | 四逆加人参汤方的条文是什么？ | strong | safe:main_passages:ZJSHL-CH-029-P-0001 | True |
| formula_guard_04 | formula_guard | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-025-P-0003 | True |
| formula_guard_05 | formula_guard | 桂枝去桂加茯苓白术汤方的条文是什么？ | strong | safe:main_passages:ZJSHL-CH-025-P-0013 | True |
| gold_safe_definition_01 | gold_safe_definition_guard | 下药是什么意思 | strong | safe:definition_terms:DPO-033fc08d3b2a | True |
| gold_safe_definition_02 | gold_safe_definition_guard | 四逆是什么意思 | strong | safe:definition_terms:DPO-ce8ffb681e3f | True |
| gold_safe_definition_03 | gold_safe_definition_guard | 盗汗是什么意思 | strong | safe:definition_terms:DPO-246b6bf4c029 | True |
| gold_safe_definition_04 | gold_safe_definition_guard | 水结胸是什么 | strong | safe:definition_terms:DPO-e8f5807c114a | True |
| gold_safe_definition_05 | gold_safe_definition_guard | 坏病是什么 | strong | safe:definition_terms:DPO-f2fb5cd46de2 | True |
| ahv_v1_guard_01 | ahv_v1_guard | 伤寒是什么 | strong | safe:definition_terms:AHV-82d1c8a78473 | True |
| ahv_v1_guard_02 | ahv_v1_guard | 霍乱是什么 | strong | safe:definition_terms:AHV-72cae785c0ac | True |
| ahv_v1_guard_03 | ahv_v1_guard | 劳复是什么意思 | strong | safe:definition_terms:AHV-68ab3aae2083 | True |
| ahv_v1_guard_04 | ahv_v1_guard | 食复是什么意思 | strong | safe:definition_terms:AHV-8df0a4ec9de9 | True |
| ahv_v1_guard_05 | ahv_v1_guard | 结脉是什么 | strong | safe:definition_terms:AHV-bbdfc9d9b74e | True |
| review_only_boundary_01 | review_only_boundary_guard | 神丹是什么意思 | weak_with_review_notice | - | True |
| review_only_boundary_02 | review_only_boundary_guard | 将军是什么意思 | weak_with_review_notice | - | True |
| review_only_boundary_03 | review_only_boundary_guard | 高是什么意思 | weak_with_review_notice | - | True |
| review_only_boundary_04 | review_only_boundary_guard | 顺是什么意思 | strong | safe:main_passages:ZJSHL-CH-011-P-0068<br>safe:main_passages:ZJSHL-CH-003-P-0054<br>safe:main_passages:ZJSHL-CH-004-P-0176 | True |
