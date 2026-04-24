# Small Gold Audit Regression v1

- generated_at_utc: `2026-04-23T01:12:04.679074+00:00`
- mode_counts: `{"refuse": 3, "strong": 23, "weak_with_review_notice": 3}`
- category_mode_counts: `{"definition": {"strong": 8}, "formula": {"strong": 8}, "learner_short": {"refuse": 1, "strong": 6, "weak_with_review_notice": 1}, "review_only_boundary": {"refuse": 2, "strong": 1, "weak_with_review_notice": 2}}`
- forbidden primary total: `0`
- formula strong: `8 / 8`
- formula bad anchors top5 total: `0`
- review-only / not-ready definition primary conflicts: `0`
- gold safe primary hits: `13 / 13`

| category | query | answer_mode | focus | target | verdict | target_hit | primary_ids |
| --- | --- | --- | --- | --- | --- | --- | --- |
| formula | 乌梅丸方的条文是什么？ | strong | noise_stripped_query |  |  | false | safe:main_passages:ZJSHL-CH-015-P-0221<br>safe:main_passages:ZJSHL-CH-015-P-0222 |
| formula | 旋复代赭石汤方的条文是什么？ | strong | noise_stripped_query |  |  | false | safe:main_passages:ZJSHL-CH-010-P-0106 |
| formula | 栀子浓朴汤方的条文是什么？ | strong | noise_stripped_query |  |  | false | safe:main_passages:ZJSHL-CH-009-P-0170 |
| formula | 桂枝甘草龙骨牡蛎汤方的条文是什么？ | strong | noise_stripped_query |  |  | false | safe:main_passages:ZJSHL-CH-009-P-0298 |
| formula | 茵陈蒿汤方的条文是什么？ | strong | noise_stripped_query |  |  | false | safe:main_passages:ZJSHL-CH-011-P-0141 |
| formula | 麻黄附子甘草汤方的条文是什么？ | strong | noise_stripped_query |  |  | false | safe:main_passages:ZJSHL-CH-014-P-0069 |
| formula | 桂枝去芍药汤方和桂枝去芍药加附子汤方有什么不同？ | strong | noise_stripped_query |  |  | false | safe:main_passages:ZJSHL-CH-025-P-0006<br>safe:main_passages:ZJSHL-CH-025-P-0005 |
| formula | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | noise_stripped_query |  |  | false | safe:main_passages:ZJSHL-CH-025-P-0004<br>safe:main_passages:ZJSHL-CH-025-P-0003 |
| definition | 什么是下药 | strong | term_normalization | 下药 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-033fc08d3b2a |
| definition | 什么是两感 | strong | term_normalization | 两感 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-3883d70fcc3a |
| definition | 什么是四逆 | strong | term_normalization | 四逆 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-ce8ffb681e3f |
| definition | 什么是发汗药 | strong | term_normalization | 发汗药 | gold_needs_sentence_reselection | true | safe:definition_terms:DPO-c8ac10b5ac88 |
| definition | 什么是湿痹 | strong | term_normalization | 湿痹 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-b5650615b93f |
| definition | 什么是结阴 | strong | term_normalization | 结阴 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-35a45498ed5c |
| definition | 什么是阳易 | strong | term_normalization | 阳易 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-93241fa8b8b3 |
| definition | 什么是内烦 | strong | term_normalization | 内烦 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-f3bab230a1db |
| learner_short | 泻下药是什么意思 | strong | term_normalization | 下药 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-033fc08d3b2a |
| learner_short | 表里两感是什么意思 | strong | term_normalization | 两感 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-3883d70fcc3a |
| learner_short | 四肢不温是什么 | strong | term_normalization | 四逆 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-ce8ffb681e3f |
| learner_short | 睡着出汗是什么意思 | strong | term_normalization | 盗汗 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-246b6bf4c029 |
| learner_short | 时气是什么意思 | strong | term_normalization | 时行之气 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-2436635882e1 |
| learner_short | 水饮结胸是什么意思 | strong | term_normalization | 水结胸 | gold_safe_primary_but_medium | true | safe:definition_terms:DPO-e8f5807c114a |
| learner_short | 阴阳易是什么意思 | weak_with_review_notice | noise_stripped_query |  |  | false | - |
| learner_short | 口苦病是什么意思 | refuse | noise_stripped_query | 胆瘅 | gold_review_only | false | - |
| review_only_boundary | 神丹是什么意思 | weak_with_review_notice | noise_stripped_query | 神丹 | gold_review_only | false | - |
| review_only_boundary | 将军是什么意思 | weak_with_review_notice | noise_stripped_query | 将军 | gold_review_only | false | - |
| review_only_boundary | 两阳是什么意思 | strong | noise_stripped_query | 两阳 | gold_not_ready_for_promotion | false | safe:main_passages:ZJSHL-CH-009-P-0275<br>safe:main_passages:ZJSHL-CH-017-P-0049<br>safe:main_passages:ZJSHL-CH-009-P-0159 |
| review_only_boundary | 什么是胆瘅 | refuse | noise_stripped_query | 胆瘅 | gold_review_only | false | - |
| review_only_boundary | 口苦病是什么意思 | refuse | noise_stripped_query | 胆瘅 | gold_review_only | false | - |
