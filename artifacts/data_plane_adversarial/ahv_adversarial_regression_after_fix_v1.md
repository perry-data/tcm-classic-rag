# AHV Adversarial Regression v1

- run_label: `after_fix`
- generated_at_utc: `2026-04-24T05:23:09.536577+00:00`
- db_path: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/zjshl_v1.db`
- total_query_count: `87`
- pass_count / fail_count: `87 / 0`
- wrong_ahv_primary_hit_count: `0`
- wrong_term_normalization_count: `0`
- disabled_alias_still_hit_count: `0`
- partial_word_false_positive_count: `0`
- non_definition_intent_hijack_count: `0`
- negative_sample_false_positive_count: `0`
- forbidden_primary_total: `0`
- review_only_primary_conflict_count: `0`
- formula_bad_anchor_top5_total: `0`
- ahv_canonical_guard_pass_count: `20`

## Failures

- none

## Query Results

| query_id | query_type | query | answer_mode | focus | primary_ids | pass |
| --- | --- | --- | --- | --- | --- | --- |
| ahv_canonical_01 | ahv_canonical_guard | 何谓太阳病 | strong | term_normalization | safe:definition_terms:AHV-fdb12048d73e | True |
| ahv_canonical_02 | ahv_canonical_guard | 伤寒是什么 | strong | term_normalization | safe:definition_terms:AHV-82d1c8a78473 | True |
| ahv_canonical_03 | ahv_canonical_guard | 温病是什么意思 | strong | term_normalization | safe:definition_terms:AHV-65a3bdee145b | True |
| ahv_canonical_04 | ahv_canonical_guard | 暑病是什么意思 | strong | term_normalization | safe:definition_terms:AHV-d1abf1c57ecf | True |
| ahv_canonical_05 | ahv_canonical_guard | 冬温是什么 | strong | term_normalization | safe:definition_terms:AHV-9dfd46e14608 | True |
| ahv_canonical_06 | ahv_canonical_guard | 时行寒疫是什么 | strong | term_normalization | safe:definition_terms:AHV-bb8f9a64a54e | True |
| ahv_canonical_07 | ahv_canonical_guard | 刚痓是什么 | strong | term_normalization | safe:definition_terms:AHV-87d3ca263c08 | True |
| ahv_canonical_08 | ahv_canonical_guard | 柔痓是什么意思 | strong | term_normalization | safe:definition_terms:AHV-cdac1a4b7e7b | True |
| ahv_canonical_09 | ahv_canonical_guard | 痓病是什么 | strong | term_normalization | safe:definition_terms:AHV-01cf7a0eba28 | True |
| ahv_canonical_10 | ahv_canonical_guard | 结脉是什么 | strong | term_normalization | safe:definition_terms:AHV-bbdfc9d9b74e | True |
| ahv_canonical_11 | ahv_canonical_guard | 促脉是什么 | strong | term_normalization | safe:definition_terms:AHV-472e3287583d | True |
| ahv_canonical_12 | ahv_canonical_guard | 弦脉是什么 | strong | term_normalization | safe:definition_terms:AHV-54c535ab7161 | True |
| ahv_canonical_13 | ahv_canonical_guard | 滑脉是什么意思 | strong | term_normalization | safe:definition_terms:AHV-5d33fe1b97eb | True |
| ahv_canonical_14 | ahv_canonical_guard | 革脉是什么 | strong | term_normalization | safe:definition_terms:AHV-6fb7ea26388a | True |
| ahv_canonical_15 | ahv_canonical_guard | 行尸是什么意思 | strong | term_normalization | safe:definition_terms:AHV-901247b4beaf | True |
| ahv_canonical_16 | ahv_canonical_guard | 内虚是什么意思 | strong | term_normalization | safe:definition_terms:AHV-b52564cf7480 | True |
| ahv_canonical_17 | ahv_canonical_guard | 血崩是什么 | strong | term_normalization | safe:definition_terms:AHV-439df1ff9f25 | True |
| ahv_canonical_18 | ahv_canonical_guard | 霍乱是什么 | strong | term_normalization | safe:definition_terms:AHV-72cae785c0ac | True |
| ahv_canonical_19 | ahv_canonical_guard | 劳复是什么意思 | strong | term_normalization | safe:definition_terms:AHV-68ab3aae2083 | True |
| ahv_canonical_20 | ahv_canonical_guard | 食复是什么意思 | strong | term_normalization | safe:definition_terms:AHV-8df0a4ec9de9 | True |
| similar_01 | similar_concept_false_trigger | 春温病是什么意思 | refuse | noise_stripped_query | - | True |
| similar_02 | similar_concept_false_trigger | 寒疫病是什么意思 | refuse | noise_stripped_query | - | True |
| similar_03 | similar_concept_false_trigger | 痉是什么意思 | weak_with_review_notice | noise_stripped_query | - | True |
| similar_04 | similar_concept_false_trigger | 痓是什么意思 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-007-P-0155<br>safe:main_passages:ZJSHL-CH-007-P-0159 | True |
| similar_05 | similar_concept_false_trigger | 刚痓和柔痓有什么不同 | refuse | noise_stripped_query | - | True |
| similar_06 | similar_concept_false_trigger | 柔痓和痓病是一回事吗 | refuse | noise_stripped_query | - | True |
| similar_07 | similar_concept_false_trigger | 痉病和痓病是同一个词吗 | refuse | noise_stripped_query | - | True |
| similar_08 | similar_concept_false_trigger | 结是什么意思 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-010-P-0123<br>safe:main_passages:ZJSHL-CH-010-P-0170 | True |
| similar_09 | similar_concept_false_trigger | 结脉和促脉有什么区别 | refuse | noise_stripped_query | - | True |
| similar_10 | similar_concept_false_trigger | 促是什么意思 | weak_with_review_notice | noise_stripped_query | - | True |
| similar_11 | similar_concept_false_trigger | 滑脉和革脉有什么不同 | refuse | noise_stripped_query | - | True |
| similar_12 | similar_concept_false_trigger | 滑象是什么意思 | refuse | noise_stripped_query | - | True |
| similar_13 | similar_concept_false_trigger | 革象是什么意思 | refuse | noise_stripped_query | - | True |
| similar_14 | similar_concept_false_trigger | 劳复和食复一样吗 | refuse | noise_stripped_query | - | True |
| similar_15 | similar_concept_false_trigger | 劳病是什么意思 | refuse | noise_stripped_query | - | True |
| similar_16 | similar_concept_false_trigger | 食病是什么意思 | weak_with_review_notice | noise_stripped_query | - | True |
| similar_17 | similar_concept_false_trigger | 伤寒和温病有什么区别 | refuse | noise_stripped_query | - | True |
| similar_18 | similar_concept_false_trigger | 伤寒和暑病有什么区别 | refuse | noise_stripped_query | - | True |
| similar_19 | similar_concept_false_trigger | 伤寒和冬温有什么区别 | refuse | noise_stripped_query | - | True |
| similar_20 | similar_concept_false_trigger | 太阳病和伤寒是一回事吗 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-008-P-0193<br>safe:main_passages:ZJSHL-CH-009-P-0002<br>safe:main_passages:ZJSHL-CH-008-P-0195 | True |
| disabled_alias_01 | disabled_alias_recheck | 春温是什么意思 | weak_with_review_notice | noise_stripped_query | - | True |
| disabled_alias_02 | disabled_alias_recheck | 暑病者是什么意思 | weak_with_review_notice | noise_stripped_query | - | True |
| disabled_alias_03 | disabled_alias_recheck | 寒疫是什么意思 | weak_with_review_notice | noise_stripped_query | - | True |
| disabled_alias_04 | disabled_alias_recheck | 劳动病是什么 | weak_with_review_notice | noise_stripped_query | - | True |
| disabled_alias_05 | disabled_alias_recheck | 强食复病是什么意思 | refuse | noise_stripped_query | - | True |
| partial_word_01 | partial_word_literal_similarity | 太阳是什么意思 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-008-P-0217 | True |
| partial_word_02 | partial_word_literal_similarity | 寒是什么意思 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022<br>safe:main_passages:ZJSHL-CH-011-P-0209 | True |
| partial_word_03 | partial_word_literal_similarity | 温是什么意思 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-027-P-0011<br>safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-009-P-0022 | True |
| partial_word_04 | partial_word_literal_similarity | 暑是什么意思 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-006-P-0004<br>safe:main_passages:ZJSHL-CH-006-P-0012<br>safe:main_passages:ZJSHL-CH-006-P-0024 | True |
| partial_word_05 | partial_word_literal_similarity | 弦是什么意思 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-011-P-0068<br>safe:main_passages:ZJSHL-CH-009-P-0239<br>safe:main_passages:ZJSHL-CH-009-P-0211 | True |
| partial_word_06 | partial_word_literal_similarity | 滑是什么意思 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-008-P-0217<br>safe:main_passages:ZJSHL-CH-015-P-0221<br>safe:main_passages:ZJSHL-CH-011-P-0109 | True |
| partial_word_07 | partial_word_literal_similarity | 革是什么意思 | weak_with_review_notice | noise_stripped_query | - | True |
| partial_word_08 | partial_word_literal_similarity | 劳是什么意思 | weak_with_review_notice | noise_stripped_query | - | True |
| partial_word_09 | partial_word_literal_similarity | 食是什么意思 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-010-P-0123<br>safe:main_passages:ZJSHL-CH-015-P-0221 | True |
| partial_word_10 | partial_word_literal_similarity | 复是什么意思 | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-009-P-0298<br>safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-008-P-0217 | True |
| non_definition_01 | non_definition_intent | 太阳病有哪些方？ | weak_with_review_notice | noise_stripped_query | - | True |
| non_definition_02 | non_definition_intent | 伤寒怎么治疗？ | refuse | noise_stripped_query | - | True |
| non_definition_03 | non_definition_intent | 温病与伤寒如何区分？ | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-007-P-0155 | True |
| non_definition_04 | non_definition_intent | 霍乱用什么方？ | refuse | noise_stripped_query | - | True |
| non_definition_05 | non_definition_intent | 劳复应该怎么处理？ | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-017-P-0048<br>safe:main_passages:ZJSHL-CH-017-P-0049 | True |
| non_definition_06 | non_definition_intent | 食复怎么治？ | refuse | noise_stripped_query | - | True |
| non_definition_07 | non_definition_intent | 结脉有什么方？ | refuse | noise_stripped_query | - | True |
| non_definition_08 | non_definition_intent | 革脉预后如何？ | refuse | noise_stripped_query | - | True |
| negative_01 | negative_unrelated | 太阳能是什么意思 | refuse | noise_stripped_query | - | True |
| negative_02 | negative_unrelated | 食物中毒是什么意思 | refuse | noise_stripped_query | - | True |
| negative_03 | negative_unrelated | 劳动合同是什么 | refuse | noise_stripped_query | - | True |
| negative_04 | negative_unrelated | 皮革是什么 | refuse | noise_stripped_query | - | True |
| negative_05 | negative_unrelated | 滑雪是什么意思 | refuse | noise_stripped_query | - | True |
| negative_06 | negative_unrelated | 内虚拟机是什么 | refuse | noise_stripped_query | - | True |
| negative_07 | negative_unrelated | 霍乱疫苗是什么 | refuse | noise_stripped_query | - | True |
| negative_08 | negative_unrelated | 暑假是什么 | refuse | noise_stripped_query | - | True |
| negative_09 | negative_unrelated | 温度是什么意思 | refuse | noise_stripped_query | - | True |
| negative_10 | negative_unrelated | 复习是什么意思 | refuse | noise_stripped_query | - | True |
| formula_guard_01 | formula_guard | 桂枝去芍药汤方的条文是什么？ | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0005 | True |
| formula_guard_02 | formula_guard | 桂枝去芍药加附子汤方的条文是什么？ | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0006 | True |
| formula_guard_03 | formula_guard | 四逆加人参汤方的条文是什么？ | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-029-P-0001 | True |
| formula_guard_04 | formula_guard | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-025-P-0003 | True |
| formula_guard_05 | formula_guard | 桂枝去桂加茯苓白术汤方的条文是什么？ | strong | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0013 | True |
| gold_safe_definition_01 | gold_safe_definition_guard | 下药是什么意思 | strong | term_normalization | safe:definition_terms:DPO-033fc08d3b2a | True |
| gold_safe_definition_02 | gold_safe_definition_guard | 四逆是什么意思 | strong | term_normalization | safe:definition_terms:DPO-ce8ffb681e3f | True |
| gold_safe_definition_03 | gold_safe_definition_guard | 盗汗是什么意思 | strong | term_normalization | safe:definition_terms:DPO-246b6bf4c029 | True |
| gold_safe_definition_04 | gold_safe_definition_guard | 水结胸是什么 | strong | term_normalization | safe:definition_terms:DPO-e8f5807c114a | True |
| gold_safe_definition_05 | gold_safe_definition_guard | 坏病是什么 | strong | term_normalization | safe:definition_terms:DPO-f2fb5cd46de2 | True |
| review_only_boundary_01 | review_only_boundary_guard | 神丹是什么意思 | weak_with_review_notice | noise_stripped_query | - | True |
| review_only_boundary_02 | review_only_boundary_guard | 将军是什么意思 | weak_with_review_notice | noise_stripped_query | - | True |
| review_only_boundary_03 | review_only_boundary_guard | 口苦病是什么意思 | refuse | noise_stripped_query | - | True |
| review_only_boundary_04 | review_only_boundary_guard | 胆瘅病是什么意思 | refuse | noise_stripped_query | - | True |
