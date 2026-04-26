# Batch Upgrade Regression v1

- run_id: `ambiguous_high_value_evidence_upgrade_v1`
- generated_at_utc: `2026-04-24T02:14:03.099113+00:00`
- before_db: `/private/tmp/zjshl_v1_before_ambiguous_high_value_evidence_upgrade_v1.db`
- after_db: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/zjshl_v1.db`
- query_count: `45`

## Summary

- before strong/weak/refuse: `{"refuse": 3, "strong": 24, "weak": 18}`
- after strong/weak/refuse: `{"refuse": 1, "strong": 32, "weak": 12}`
- support_only_reduced_count: `20`
- new_safe_object_primary_hit_count: `20`
- forbidden_primary_total: `0`
- review_only_primary_conflict_count: `0`
- alias_risk_conflict_count: `0`
- formula_bad_anchor_top5_total: `0`
- regression_pass_count / fail_count: `45 / 0`

## Query Table

| category | query | before | after | primary_after | pass |
| --- | --- | --- | --- | --- | --- |
| candidate_A | 何谓太阳病 | strong | strong | safe:definition_terms:AHV-fdb12048d73e | True |
| candidate_A | 伤寒是什么 | strong | strong | safe:definition_terms:AHV-82d1c8a78473 | True |
| candidate_A | 温病是什么意思 | strong | strong | safe:definition_terms:AHV-65a3bdee145b | True |
| candidate_A | 暑病是什么意思 | strong | strong | safe:definition_terms:AHV-d1abf1c57ecf | True |
| candidate_A | 冬温是什么 | weak_with_review_notice | strong | safe:definition_terms:AHV-9dfd46e14608 | True |
| candidate_A | 时行寒疫是什么 | strong | strong | safe:definition_terms:AHV-bb8f9a64a54e | True |
| candidate_A | 刚痓是什么 | weak_with_review_notice | strong | safe:definition_terms:AHV-87d3ca263c08 | True |
| candidate_A | 柔痓是什么意思 | strong | strong | safe:definition_terms:AHV-cdac1a4b7e7b | True |
| candidate_A | 痓病是什么 | weak_with_review_notice | strong | safe:definition_terms:AHV-01cf7a0eba28 | True |
| candidate_A | 结脉是什么 | strong | strong | safe:definition_terms:AHV-bbdfc9d9b74e | True |
| candidate_A | 促脉是什么 | refuse | strong | safe:definition_terms:AHV-472e3287583d | True |
| candidate_A | 弦脉是什么 | strong | strong | safe:definition_terms:AHV-54c535ab7161 | True |
| candidate_A | 滑脉是什么意思 | weak_with_review_notice | strong | safe:definition_terms:AHV-5d33fe1b97eb | True |
| candidate_A | 革脉是什么 | refuse | strong | safe:definition_terms:AHV-6fb7ea26388a | True |
| candidate_A | 行尸是什么意思 | weak_with_review_notice | strong | safe:definition_terms:AHV-901247b4beaf | True |
| candidate_A | 内虚是什么意思 | strong | strong | safe:definition_terms:AHV-b52564cf7480 | True |
| candidate_A | 血崩是什么 | strong | strong | safe:definition_terms:AHV-439df1ff9f25 | True |
| candidate_A | 霍乱是什么 | strong | strong | safe:definition_terms:AHV-72cae785c0ac | True |
| candidate_A | 劳复是什么意思 | weak_with_review_notice | strong | safe:definition_terms:AHV-68ab3aae2083 | True |
| candidate_A | 食复是什么意思 | strong | strong | safe:definition_terms:AHV-8df0a4ec9de9 | True |
| candidate_B | 寸口卫气盛名曰高是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| candidate_B | 荣气盛名曰章是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| candidate_B | 高章相搏名曰纲是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| candidate_B | 卫气弱名曰惵是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| candidate_B | 荣气弱名曰卑是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| candidate_B | 卑相搏名曰损是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| candidate_B | 卫气和名曰缓是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| candidate_B | 荣气和名曰迟是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| candidate_C | 动是什么意思 | strong | strong | safe:main_passages:ZJSHL-CH-009-P-0159<br>safe:main_passages:ZJSHL-CH-015-P-0221<br>safe:main_passages:ZJSHL-CH-010-P-0170 | True |
| candidate_C | 两阳是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| candidate_C | 清邪中上是什么意思 | strong | strong | safe:main_passages:ZJSHL-CH-023-P-0046 | True |
| candidate_C | 寒格是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| gold_safe_definition | 发汗药是什么意思 | strong | strong | safe:definition_terms:DPO-c8ac10b5ac88 | True |
| gold_safe_definition | 坏病是什么 | strong | strong | safe:definition_terms:DPO-f2fb5cd46de2 | True |
| gold_safe_definition | 盗汗是什么意思 | strong | strong | safe:definition_terms:DPO-246b6bf4c029 | True |
| gold_safe_definition | 水结胸是什么 | strong | strong | safe:definition_terms:DPO-e8f5807c114a | True |
| gold_safe_definition | 四逆是什么意思 | strong | strong | safe:definition_terms:DPO-ce8ffb681e3f | True |
| formula_guard | 桂枝去芍药汤方的条文是什么？ | strong | strong | safe:main_passages:ZJSHL-CH-025-P-0005 | True |
| formula_guard | 桂枝去芍药加附子汤方的条文是什么？ | strong | strong | safe:main_passages:ZJSHL-CH-025-P-0006 | True |
| formula_guard | 四逆加人参汤方的条文是什么？ | strong | strong | safe:main_passages:ZJSHL-CH-029-P-0001 | True |
| formula_guard | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | strong | safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-025-P-0003 | True |
| formula_guard | 桂枝去桂加茯苓白术汤方的条文是什么？ | strong | strong | safe:main_passages:ZJSHL-CH-025-P-0013 | True |
| review_only_boundary | 神丹是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| review_only_boundary | 将军是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| review_only_boundary | 口苦病是什么意思 | refuse | refuse | - | True |
