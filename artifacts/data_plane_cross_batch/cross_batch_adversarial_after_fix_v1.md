# Cross-Batch AHV Adversarial Regression v1

- run_label: `after_fix`
- total_query_count: `120`
- strong / weak / refuse: `75 / 14 / 31`
- regression_pass_count / regression_fail_count: `120 / 0`
- wrong_ahv_primary_hit_count: `0`
- wrong_term_normalization_count: `0`
- non_definition_intent_hijack_count: `0`
- comparison_primary_hijack_count: `0`
- forbidden_primary_total: `0`
- review_only_primary_conflict_count: `0`
- formula_bad_anchor_top5_total: `0`
- ahv_v1_guard_pass_count: `20` / `20`
- ahv2_guard_pass_count: `20` / `20`

## Failures

- none

## Query Results

| query_id | query_type | query | mode | matched_ahv_terms | primary_ids | pass |
| --- | --- | --- | --- | --- | --- | --- |
| ahv_v1_canonical_01 | ahv_v1_canonical_guard | 何谓太阳病 | strong | 太阳病 | safe:definition_terms:AHV-fdb12048d73e | True |
| ahv_v1_canonical_02 | ahv_v1_canonical_guard | 伤寒是什么 | strong | 伤寒 | safe:definition_terms:AHV-82d1c8a78473 | True |
| ahv_v1_canonical_03 | ahv_v1_canonical_guard | 温病是什么意思 | strong | 温病 | safe:definition_terms:AHV-65a3bdee145b | True |
| ahv_v1_canonical_04 | ahv_v1_canonical_guard | 暑病是什么意思 | strong | 暑病 | safe:definition_terms:AHV-d1abf1c57ecf | True |
| ahv_v1_canonical_05 | ahv_v1_canonical_guard | 冬温是什么 | strong | 冬温 | safe:definition_terms:AHV-9dfd46e14608 | True |
| ahv_v1_canonical_06 | ahv_v1_canonical_guard | 时行寒疫是什么 | strong | 时行寒疫 | safe:definition_terms:AHV-bb8f9a64a54e | True |
| ahv_v1_canonical_07 | ahv_v1_canonical_guard | 刚痓是什么 | strong | 刚痓 | safe:definition_terms:AHV-87d3ca263c08 | True |
| ahv_v1_canonical_08 | ahv_v1_canonical_guard | 柔痓是什么意思 | strong | 柔痓 | safe:definition_terms:AHV-cdac1a4b7e7b | True |
| ahv_v1_canonical_09 | ahv_v1_canonical_guard | 痓病是什么 | strong | 痓病 | safe:definition_terms:AHV-01cf7a0eba28 | True |
| ahv_v1_canonical_10 | ahv_v1_canonical_guard | 结脉是什么 | strong | 结脉 | safe:definition_terms:AHV-bbdfc9d9b74e | True |
| ahv_v1_canonical_11 | ahv_v1_canonical_guard | 促脉是什么 | strong | 促脉 | safe:definition_terms:AHV-472e3287583d | True |
| ahv_v1_canonical_12 | ahv_v1_canonical_guard | 弦脉是什么 | strong | 弦脉 | safe:definition_terms:AHV-54c535ab7161 | True |
| ahv_v1_canonical_13 | ahv_v1_canonical_guard | 滑脉是什么意思 | strong | 滑脉 | safe:definition_terms:AHV-5d33fe1b97eb | True |
| ahv_v1_canonical_14 | ahv_v1_canonical_guard | 革脉是什么 | strong | 革脉 | safe:definition_terms:AHV-6fb7ea26388a | True |
| ahv_v1_canonical_15 | ahv_v1_canonical_guard | 行尸是什么意思 | strong | 行尸 | safe:definition_terms:AHV-901247b4beaf | True |
| ahv_v1_canonical_16 | ahv_v1_canonical_guard | 内虚是什么意思 | strong | 内虚 | safe:definition_terms:AHV-b52564cf7480 | True |
| ahv_v1_canonical_17 | ahv_v1_canonical_guard | 血崩是什么 | strong | 血崩 | safe:definition_terms:AHV-439df1ff9f25 | True |
| ahv_v1_canonical_18 | ahv_v1_canonical_guard | 霍乱是什么 | strong | 霍乱 | safe:definition_terms:AHV-72cae785c0ac | True |
| ahv_v1_canonical_19 | ahv_v1_canonical_guard | 劳复是什么意思 | strong | 劳复 | safe:definition_terms:AHV-68ab3aae2083 | True |
| ahv_v1_canonical_20 | ahv_v1_canonical_guard | 食复是什么意思 | strong | 食复 | safe:definition_terms:AHV-8df0a4ec9de9 | True |
| ahv2_canonical_01 | ahv2_canonical_guard | 荣气微是什么意思 | strong | 荣气微 | safe:definition_terms:AHV2-850318ee8950 | True |
| ahv2_canonical_02 | ahv2_canonical_guard | 卫气衰是什么意思 | strong | 卫气衰 | safe:definition_terms:AHV2-81a12b6da994 | True |
| ahv2_canonical_03 | ahv2_canonical_guard | 阳气微是什么意思 | strong | 阳气微 | safe:definition_terms:AHV2-767dfa46f2b1 | True |
| ahv2_canonical_04 | ahv2_canonical_guard | 亡血是什么意思 | strong | 亡血 | safe:definition_terms:AHV2-7882ca0aa96a | True |
| ahv2_canonical_05 | ahv2_canonical_guard | 平脉是什么意思 | strong | 平脉 | safe:definition_terms:AHV2-310eca701a93 | True |
| ahv2_canonical_06 | ahv2_canonical_guard | 数脉是什么意思 | strong | 数脉 | safe:definition_terms:AHV2-f9e89349db80 | True |
| ahv2_canonical_07 | ahv2_canonical_guard | 毛脉是什么意思 | strong | 毛脉 | safe:definition_terms:AHV2-5f24c7010fec | True |
| ahv2_canonical_08 | ahv2_canonical_guard | 纯弦脉是什么意思 | strong | 纯弦脉 | safe:definition_terms:AHV2-92d765f487d4 | True |
| ahv2_canonical_09 | ahv2_canonical_guard | 残贼是什么意思 | strong | 残贼 | safe:definition_terms:AHV2-dac342243a2d | True |
| ahv2_canonical_10 | ahv2_canonical_guard | 八邪是什么意思 | strong | 八邪 | safe:definition_terms:AHV2-c29e7aff2765 | True |
| ahv2_canonical_11 | ahv2_canonical_guard | 湿家是什么意思 | strong | 湿家 | safe:definition_terms:AHV2-1e3cd430a062 | True |
| ahv2_canonical_12 | ahv2_canonical_guard | 风湿是什么意思 | strong | 风湿 | safe:definition_terms:AHV2-f5bd47a65fa0 | True |
| ahv2_canonical_13 | ahv2_canonical_guard | 水逆是什么意思 | strong | 水逆 | safe:definition_terms:AHV2-1da410fb57b4 | True |
| ahv2_canonical_14 | ahv2_canonical_guard | 半表半里证是什么意思 | strong | 半表半里证 | safe:definition_terms:AHV2-aa28a21f86c8 | True |
| ahv2_canonical_15 | ahv2_canonical_guard | 过经是什么意思 | strong | 过经 | safe:definition_terms:AHV2-dbeb47457236 | True |
| ahv2_canonical_16 | ahv2_canonical_guard | 结胸是什么意思 | strong | 结胸 | safe:definition_terms:AHV2-0f3d2d43c342 | True |
| ahv2_canonical_17 | ahv2_canonical_guard | 阳明病是什么 | strong | 阳明病 | safe:definition_terms:AHV2-5a00f10e6dee | True |
| ahv2_canonical_18 | ahv2_canonical_guard | 太阴病是什么 | strong | 太阴病 | safe:definition_terms:AHV2-8709f78f1237 | True |
| ahv2_canonical_19 | ahv2_canonical_guard | 少阴病是什么 | strong | 少阴病 | safe:definition_terms:AHV2-9f641a6ecc7d | True |
| ahv2_canonical_20 | ahv2_canonical_guard | 厥阴病是什么 | strong | 厥阴病 | safe:definition_terms:AHV2-7b2df4caf446 | True |
| conflict_01 | cross_batch_concept_conflict | 太阳病和阳明病有什么区别 | strong | - | safe:main_passages:ZJSHL-CH-011-P-0010<br>safe:main_passages:ZJSHL-CH-006-P-0076<br>safe:main_passages:ZJSHL-CH-011-P-0054 | True |
| conflict_02 | cross_batch_concept_conflict | 伤寒和温病有什么区别 | refuse | - | - | True |
| conflict_03 | cross_batch_concept_conflict | 伤寒和暑病是一回事吗 | refuse | - | - | True |
| conflict_04 | cross_batch_concept_conflict | 刚痓和柔痓有什么不同 | refuse | - | - | True |
| conflict_05 | cross_batch_concept_conflict | 痓病和刚痓是什么关系 | refuse | - | - | True |
| conflict_06 | cross_batch_concept_conflict | 结脉和促脉有什么区别 | refuse | - | - | True |
| conflict_07 | cross_batch_concept_conflict | 弦脉和纯弦脉有什么区别 | strong | - | safe:main_passages:ZJSHL-CH-004-P-0184 | True |
| conflict_08 | cross_batch_concept_conflict | 滑脉和数脉有什么区别 | refuse | - | - | True |
| conflict_09 | cross_batch_concept_conflict | 劳复和食复一样吗 | refuse | - | - | True |
| conflict_10 | cross_batch_concept_conflict | 结胸和水逆有什么不同 | refuse | - | - | True |
| conflict_11 | cross_batch_concept_conflict | 半表半里证和结胸有什么关系 | strong | - | safe:main_passages:ZJSHL-CH-010-P-0005 | True |
| conflict_12 | cross_batch_concept_conflict | 水逆和水结胸是一回事吗 | weak_with_review_notice | - | - | True |
| conflict_13 | cross_batch_concept_conflict | 少阴病和厥阴病有什么区别 | strong | - | safe:main_passages:ZJSHL-CH-006-P-0076<br>safe:main_passages:ZJSHL-CH-015-P-0198<br>safe:main_passages:ZJSHL-CH-014-P-0095 | True |
| conflict_14 | cross_batch_concept_conflict | 太阴病和阳明病有什么区别 | strong | - | safe:main_passages:ZJSHL-CH-006-P-0076<br>safe:main_passages:ZJSHL-CH-013-P-0008<br>safe:main_passages:ZJSHL-CH-011-P-0054 | True |
| conflict_15 | cross_batch_concept_conflict | 温病和暑病有什么关系 | refuse | - | - | True |
| conflict_16 | cross_batch_concept_conflict | 冬温和温病是一回事吗 | refuse | - | - | True |
| conflict_17 | cross_batch_concept_conflict | 时行寒疫和伤寒有什么不同 | strong | - | safe:main_passages:ZJSHL-CH-006-P-0024<br>safe:main_passages:ZJSHL-CH-009-P-0320<br>safe:main_passages:ZJSHL-CH-009-P-0322 | True |
| conflict_18 | cross_batch_concept_conflict | 平脉和数脉有什么区别 | refuse | - | - | True |
| conflict_19 | cross_batch_concept_conflict | 毛脉和革脉有什么区别 | refuse | - | - | True |
| conflict_20 | cross_batch_concept_conflict | 残贼和八邪有什么关系 | refuse | - | - | True |
| conflict_21 | cross_batch_concept_conflict | 湿家和风湿有什么区别 | weak_with_review_notice | - | - | True |
| conflict_22 | cross_batch_concept_conflict | 阳气微和内虚有什么关系 | refuse | - | - | True |
| conflict_23 | cross_batch_concept_conflict | 亡血和血崩是一回事吗 | refuse | - | - | True |
| conflict_24 | cross_batch_concept_conflict | 过经和劳复有什么不同 | strong | - | safe:main_passages:ZJSHL-CH-017-P-0049<br>safe:main_passages:ZJSHL-CH-017-P-0050<br>safe:main_passages:ZJSHL-CH-009-P-0159 | True |
| conflict_25 | cross_batch_concept_conflict | 太阳病和少阴病怎样区分 | strong | - | safe:main_passages:ZJSHL-CH-006-P-0076<br>safe:main_passages:ZJSHL-CH-014-P-0095<br>safe:main_passages:ZJSHL-CH-014-P-0112 | True |
| non_definition_01 | non_definition_intent | 阳明病用什么方 | weak_with_review_notice | - | - | True |
| non_definition_02 | non_definition_intent | 少阴病怎么治 | strong | - | safe:main_passages:ZJSHL-CH-014-P-0095<br>safe:main_passages:ZJSHL-CH-014-P-0112<br>safe:main_passages:ZJSHL-CH-014-P-0045 | True |
| non_definition_03 | non_definition_intent | 厥阴病有哪些方 | weak_with_review_notice | - | - | True |
| non_definition_04 | non_definition_intent | 霍乱用什么方 | refuse | - | - | True |
| non_definition_05 | non_definition_intent | 结胸怎么治 | refuse | - | - | True |
| non_definition_06 | non_definition_intent | 水逆用什么方 | refuse | - | - | True |
| non_definition_07 | non_definition_intent | 伤寒怎么治疗 | refuse | - | - | True |
| non_definition_08 | non_definition_intent | 温病怎么治 | refuse | - | - | True |
| non_definition_09 | non_definition_intent | 劳复应该怎么处理 | strong | - | safe:main_passages:ZJSHL-CH-017-P-0048<br>safe:main_passages:ZJSHL-CH-017-P-0049 | True |
| non_definition_10 | non_definition_intent | 食复应该怎么处理 | weak_with_review_notice | - | - | True |
| non_definition_11 | non_definition_intent | 弦脉预后如何 | refuse | - | - | True |
| non_definition_12 | non_definition_intent | 革脉说明什么 | refuse | - | - | True |
| non_definition_13 | non_definition_intent | 结脉有什么方 | refuse | - | - | True |
| non_definition_14 | non_definition_intent | 太阳病的条文是什么 | strong | - | safe:main_passages:ZJSHL-CH-008-P-0193<br>safe:main_passages:ZJSHL-CH-009-P-0002<br>safe:main_passages:ZJSHL-CH-008-P-0220 | True |
| non_definition_15 | non_definition_intent | 阳明病的条文是什么 | strong | - | safe:main_passages:ZJSHL-CH-011-P-0054<br>safe:main_passages:ZJSHL-CH-011-P-0012<br>safe:main_passages:ZJSHL-CH-011-P-0038 | True |
| non_definition_16 | non_definition_intent | 太阴病的病机是什么 | strong | - | safe:main_passages:ZJSHL-CH-013-P-0008<br>safe:main_passages:ZJSHL-CH-006-P-0076 | True |
| non_definition_17 | non_definition_intent | 半表半里证用什么方 | weak_with_review_notice | - | - | True |
| non_definition_18 | non_definition_intent | 风湿如何治疗 | strong | - | safe:main_passages:ZJSHL-CH-010-P-0149<br>safe:main_passages:ZJSHL-CH-010-P-0157 | True |
| non_definition_19 | non_definition_intent | 亡血怎么处理 | strong | - | safe:main_passages:ZJSHL-CH-010-P-0125<br>safe:main_passages:ZJSHL-CH-003-P-0048 | True |
| non_definition_20 | non_definition_intent | 过经之后用什么方 | refuse | - | - | True |
| negative_alias_01 | alias_partial_negative | 温是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-027-P-0011<br>safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022 | True |
| negative_alias_02 | alias_partial_negative | 寒是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-011-P-0209 | True |
| negative_alias_03 | alias_partial_negative | 阳是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-009-P-0022 | True |
| negative_alias_04 | alias_partial_negative | 阴是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-008-P-0217<br>safe:main_passages:ZJSHL-CH-014-P-0119 | True |
| negative_alias_05 | alias_partial_negative | 数是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-008-P-0217<br>safe:main_passages:ZJSHL-CH-010-P-0113 | True |
| negative_alias_06 | alias_partial_negative | 毛是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-004-P-0191<br>safe:main_passages:ZJSHL-CH-004-P-0193<br>safe:main_passages:ZJSHL-CH-004-P-0227 | True |
| negative_alias_07 | alias_partial_negative | 纯是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-004-P-0184<br>safe:main_passages:ZJSHL-CH-004-P-0203<br>safe:main_passages:ZJSHL-CH-004-P-0205 | True |
| negative_alias_08 | alias_partial_negative | 弦是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-011-P-0068<br>safe:main_passages:ZJSHL-CH-009-P-0239<br>safe:main_passages:ZJSHL-CH-009-P-0211 | True |
| negative_alias_09 | alias_partial_negative | 水是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-027-P-0011<br>safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022 | True |
| negative_alias_10 | alias_partial_negative | 过是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-008-P-0264<br>safe:main_passages:ZJSHL-CH-003-P-0115<br>safe:main_passages:ZJSHL-CH-004-P-0134 | True |
| negative_alias_11 | alias_partial_negative | 半表是什么意思 | weak_with_review_notice | - | - | True |
| negative_alias_12 | alias_partial_negative | 复习是什么意思 | refuse | - | - | True |
| negative_alias_13 | alias_partial_negative | 劳动是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-017-P-0050<br>safe:main_passages:ZJSHL-CH-017-P-0049 | True |
| negative_alias_14 | alias_partial_negative | 食物是什么意思 | refuse | - | - | True |
| negative_alias_15 | alias_partial_negative | 太阳能是什么意思 | refuse | - | - | True |
| negative_alias_16 | alias_partial_negative | 阳明山是什么 | refuse | - | - | True |
| negative_alias_17 | alias_partial_negative | 少阴影是什么意思 | refuse | - | - | True |
| negative_alias_18 | alias_partial_negative | 太阴历是什么 | refuse | - | - | True |
| negative_alias_19 | alias_partial_negative | 厥是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-015-P-0253<br>safe:main_passages:ZJSHL-CH-010-P-0123<br>safe:main_passages:ZJSHL-CH-008-P-0217 | True |
| negative_alias_20 | alias_partial_negative | 八邪游戏是什么 | refuse | - | - | True |
| review_only_01 | review_only_rejected_guard | 神丹是什么意思 | weak_with_review_notice | - | - | True |
| review_only_02 | review_only_rejected_guard | 将军是什么意思 | weak_with_review_notice | - | - | True |
| review_only_03 | review_only_rejected_guard | 两阳是什么意思 | weak_with_review_notice | - | - | True |
| review_only_04 | review_only_rejected_guard | 胆瘅是什么意思 | weak_with_review_notice | - | - | True |
| review_only_05 | review_only_rejected_guard | 火劫发汗是什么意思 | weak_with_review_notice | - | - | True |
| review_only_06 | review_only_rejected_guard | 肝乘脾是什么意思 | weak_with_review_notice | - | - | True |
| review_only_07 | review_only_rejected_guard | 反是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-008-P-0217<br>safe:main_passages:ZJSHL-CH-025-P-0007 | True |
| review_only_08 | review_only_rejected_guard | 复是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-009-P-0298<br>safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-008-P-0217 | True |
| review_only_09 | review_only_rejected_guard | 寒格是什么意思 | weak_with_review_notice | - | - | True |
| review_only_10 | review_only_rejected_guard | 清邪中上是什么意思 | strong | - | safe:main_passages:ZJSHL-CH-023-P-0046 | True |
| formula_guard_01 | formula_guard | 桂枝去芍药汤方的条文是什么？ | strong | - | safe:main_passages:ZJSHL-CH-025-P-0005 | True |
| formula_guard_02 | formula_guard | 桂枝去芍药加附子汤方的条文是什么？ | strong | - | safe:main_passages:ZJSHL-CH-025-P-0006 | True |
| formula_guard_03 | formula_guard | 四逆加人参汤方的条文是什么？ | strong | - | safe:main_passages:ZJSHL-CH-029-P-0001 | True |
| formula_guard_04 | formula_guard | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | - | safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-025-P-0003 | True |
| formula_guard_05 | formula_guard | 桂枝去桂加茯苓白术汤方的条文是什么？ | strong | - | safe:main_passages:ZJSHL-CH-025-P-0013 | True |
