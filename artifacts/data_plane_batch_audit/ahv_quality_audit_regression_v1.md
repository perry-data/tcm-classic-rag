# AHV Quality Audit Regression v1

- run_id: `batch_upgrade_quality_audit_v1`
- generated_at_utc: `2026-04-24T02:13:20.899626+00:00`
- query_count: `34`

## Summary

- audited_ahv_object_count: `20`
- keep_safe_primary_count: `20`
- adjusted_object_count: `18`
- downgraded_object_count: `0`
- alias_adjusted_count: `5`
- before strong/weak/refuse: `{"refuse": 2, "strong": 30, "weak": 2}`
- after strong/weak/refuse: `{"refuse": 2, "strong": 30, "weak": 2}`
- forbidden_primary_total: `0`
- review_only_primary_conflict_count: `0`
- ahv_primary_hit_count / miss_count: `20 / 0`
- formula_bad_anchor_top5_total: `0`
- regression_pass_count / fail_count: `34 / 0`

## Query Table

| category | query | before | after | primary_after | pass |
| --- | --- | --- | --- | --- | --- |
| ahv_object | 何谓太阳病 | strong | strong | safe:definition_terms:AHV-fdb12048d73e | True |
| ahv_object | 伤寒是什么 | strong | strong | safe:definition_terms:AHV-82d1c8a78473 | True |
| ahv_object | 温病是什么意思 | strong | strong | safe:definition_terms:AHV-65a3bdee145b | True |
| ahv_object | 暑病是什么意思 | strong | strong | safe:definition_terms:AHV-d1abf1c57ecf | True |
| ahv_object | 冬温是什么 | strong | strong | safe:definition_terms:AHV-9dfd46e14608 | True |
| ahv_object | 时行寒疫是什么 | strong | strong | safe:definition_terms:AHV-bb8f9a64a54e | True |
| ahv_object | 刚痓是什么 | strong | strong | safe:definition_terms:AHV-87d3ca263c08 | True |
| ahv_object | 柔痓是什么意思 | strong | strong | safe:definition_terms:AHV-cdac1a4b7e7b | True |
| ahv_object | 痓病是什么 | strong | strong | safe:definition_terms:AHV-01cf7a0eba28 | True |
| ahv_object | 结脉是什么 | strong | strong | safe:definition_terms:AHV-bbdfc9d9b74e | True |
| ahv_object | 促脉是什么 | strong | strong | safe:definition_terms:AHV-472e3287583d | True |
| ahv_object | 弦脉是什么 | strong | strong | safe:definition_terms:AHV-54c535ab7161 | True |
| ahv_object | 滑脉是什么意思 | strong | strong | safe:definition_terms:AHV-5d33fe1b97eb | True |
| ahv_object | 革脉是什么 | strong | strong | safe:definition_terms:AHV-6fb7ea26388a | True |
| ahv_object | 行尸是什么意思 | strong | strong | safe:definition_terms:AHV-901247b4beaf | True |
| ahv_object | 内虚是什么意思 | strong | strong | safe:definition_terms:AHV-b52564cf7480 | True |
| ahv_object | 血崩是什么 | strong | strong | safe:definition_terms:AHV-439df1ff9f25 | True |
| ahv_object | 霍乱是什么 | strong | strong | safe:definition_terms:AHV-72cae785c0ac | True |
| ahv_object | 劳复是什么意思 | strong | strong | safe:definition_terms:AHV-68ab3aae2083 | True |
| ahv_object | 食复是什么意思 | strong | strong | safe:definition_terms:AHV-8df0a4ec9de9 | True |
| gold_safe_definition_guard | 下药是什么意思 | strong | strong | safe:definition_terms:DPO-033fc08d3b2a | True |
| gold_safe_definition_guard | 四逆是什么意思 | strong | strong | safe:definition_terms:DPO-ce8ffb681e3f | True |
| gold_safe_definition_guard | 盗汗是什么意思 | strong | strong | safe:definition_terms:DPO-246b6bf4c029 | True |
| gold_safe_definition_guard | 水结胸是什么 | strong | strong | safe:definition_terms:DPO-e8f5807c114a | True |
| gold_safe_definition_guard | 坏病是什么 | strong | strong | safe:definition_terms:DPO-f2fb5cd46de2 | True |
| formula_guard | 桂枝去芍药汤方的条文是什么？ | strong | strong | safe:main_passages:ZJSHL-CH-025-P-0005 | True |
| formula_guard | 桂枝去芍药加附子汤方的条文是什么？ | strong | strong | safe:main_passages:ZJSHL-CH-025-P-0006 | True |
| formula_guard | 四逆加人参汤方的条文是什么？ | strong | strong | safe:main_passages:ZJSHL-CH-029-P-0001 | True |
| formula_guard | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | strong | safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-025-P-0003 | True |
| formula_guard | 桂枝去桂加茯苓白术汤方的条文是什么？ | strong | strong | safe:main_passages:ZJSHL-CH-025-P-0013 | True |
| review_only_boundary_guard | 神丹是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| review_only_boundary_guard | 将军是什么意思 | weak_with_review_notice | weak_with_review_notice | - | True |
| review_only_boundary_guard | 口苦病是什么意思 | refuse | refuse | - | True |
| review_only_boundary_guard | 胆瘅病是什么意思 | refuse | refuse | - | True |
