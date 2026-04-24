# Data Plane Audit Regression v1

- generated_at_utc: `2026-04-22T14:34:04.834577+00:00`
- before_db: `/private/tmp/zjshl_v1_before_data_plane_audit_v1.db`
- after_db: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/zjshl_v1.db`

## Summary

- before mode_counts: `{"strong": 26, "weak_with_review_notice": 2}`
- after mode_counts: `{"refuse": 2, "strong": 23, "weak_with_review_notice": 3}`
- forbidden_primary before -> after: `0 -> 0`
- formula bad anchors top5 before -> after: `0 -> 0`
- learner_short strong before -> after: `8 -> 7`
- downgraded definition primary before -> after: `2 -> 0`
- ambiguous alias forced normalization before -> after: `1 -> 0`

## Query Table

| category | query | before | after | focus_before | focus_after | primary_after |
| --- | --- | --- | --- | --- | --- | --- |
| formula | 桂枝去芍药汤方的条文是什么？ | strong | strong | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0005 |
| formula | 桂枝去芍药加附子汤方的条文是什么？ | strong | strong | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0006 |
| formula | 四逆加人参汤方的条文是什么？ | strong | strong | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-029-P-0001 |
| formula | 四逆加猪胆汁汤方的条文是什么？ | strong | strong | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-029-P-0002 |
| formula | 桂枝去桂加茯苓白术汤方的条文是什么？ | strong | strong | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0013 |
| formula | 桂枝去芍药汤方和桂枝去芍药加附子汤方有什么不同？ | strong | strong | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0006<br>safe:main_passages:ZJSHL-CH-025-P-0005 |
| formula | 四逆汤方和四逆加人参汤方有什么不同？ | strong | strong | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-029-P-0001<br>safe:main_passages:ZJSHL-CH-008-P-0267<br>safe:main_passages:ZJSHL-CH-008-P-0268 |
| formula | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | strong | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-025-P-0003 |
| definition | 什么是风温 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-5df60e5f4e98 |
| definition | 什么是下药 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-033fc08d3b2a |
| definition | 什么是四逆 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-ce8ffb681e3f |
| definition | 什么是湿痹 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-b5650615b93f |
| definition | 什么是发汗药 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-c8ac10b5ac88 |
| definition | 什么是内烦 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-f3bab230a1db |
| definition | 什么是阳易 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-93241fa8b8b3 |
| definition | 什么是胆瘅 | strong | refuse | term_normalization | noise_stripped_query | - |
| learner_short | 睡着出汗是什么意思 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-246b6bf4c029 |
| learner_short | 四肢不温是什么 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-ce8ffb681e3f |
| learner_short | 泻下药是什么意思 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-033fc08d3b2a |
| learner_short | 时气是什么意思 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-2436635882e1 |
| learner_short | 气从少腹上冲是什么意思 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-e3ac03414a67 |
| learner_short | 表里两感是什么意思 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-3883d70fcc3a |
| learner_short | 水饮结胸是什么意思 | strong | strong | term_normalization | term_normalization | safe:definition_terms:DPO-e8f5807c114a |
| learner_short | 口苦病是什么意思 | strong | refuse | term_normalization | noise_stripped_query | - |
| review_only_boundary | 神丹是什么意思 | weak_with_review_notice | weak_with_review_notice | noise_stripped_query | noise_stripped_query | - |
| review_only_boundary | 将军是什么意思 | weak_with_review_notice | weak_with_review_notice | noise_stripped_query | noise_stripped_query | - |
| review_only_boundary | 两阳是什么意思 | strong | strong | noise_stripped_query | noise_stripped_query | safe:main_passages:ZJSHL-CH-009-P-0275<br>safe:main_passages:ZJSHL-CH-017-P-0049<br>safe:main_passages:ZJSHL-CH-009-P-0159 |
| alias_boundary | 阴阳易是什么意思 | strong | weak_with_review_notice | term_normalization | noise_stripped_query | - |
