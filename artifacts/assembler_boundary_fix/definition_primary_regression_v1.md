# Definition Primary Boundary Regression v1

- generated_at_utc: `2026-04-22T11:52:30.642754+00:00`
- definition_queries: `8`
- formula_queries: `8`
- definition_primary_forbidden_total: `0`
- definition_support_full_passages_count: `8`
- formula_primary_safe_main_all: `True`
- formula_strong_count: `8`
- formula_top5_bad_formula_anchor_total: `0`
- primary_formula_backref_total: `11`

## Definition / Meaning Queries

| query | mode | primary clean | primary ids | secondary/review full:passages | route |
| --- | --- | --- | --- | --- | --- |
| 什么是发汗药 | weak_with_review_notice | True | - | full:passages:ZJSHL-CH-006-P-0120<br>full:passages:ZJSHL-CH-010-P-0137 | what_is |
| 发汗药是什么意思 | weak_with_review_notice | True | - | full:passages:ZJSHL-CH-006-P-0127<br>full:passages:ZJSHL-CH-006-P-0120<br>full:passages:ZJSHL-CH-006-P-0126<br>full:passages:ZJSHL-CH-006-P-0119 | what_means |
| 阳结是什么 | strong | True | safe:main_passages:ZJSHL-CH-003-P-0017 | full:passages:ZJSHL-CH-003-P-0004<br>full:passages:ZJSHL-CH-003-P-0005 | what_is |
| 阳结是什么意思 | strong | True | safe:main_passages:ZJSHL-CH-003-P-0017 | full:passages:ZJSHL-CH-003-P-0004<br>full:passages:ZJSHL-CH-003-P-0018<br>full:passages:ZJSHL-CH-003-P-0005<br>full:passages:ZJSHL-CH-010-P-0019 | what_means |
| 坏病是什么 | weak_with_review_notice | True | - | full:passages:ZJSHL-CH-008-P-0227<br>full:passages:ZJSHL-CH-008-P-0226 | what_is |
| 坏病是什么意思 | weak_with_review_notice | True | - | full:passages:ZJSHL-CH-008-P-0227<br>full:passages:ZJSHL-CH-008-P-0226 | what_means |
| 承气汤是下药吗 | strong | True | safe:main_passages:ZJSHL-CH-015-P-0316<br>safe:main_passages:ZJSHL-CH-009-P-0261<br>safe:main_passages:ZJSHL-CH-011-P-0071 | full:passages:ZJSHL-CH-009-P-0134<br>full:passages:ZJSHL-CH-015-P-0316 | category_membership_yesno |
| 桂枝汤是什么药 | strong | True | safe:main_passages:ZJSHL-CH-008-P-0217<br>safe:main_passages:ZJSHL-CH-016-P-0034<br>safe:main_passages:ZJSHL-CH-008-P-0220 | full:passages:ZJSHL-CH-016-P-0034<br>full:passages:ZJSHL-CH-008-P-0220 | category_membership_open |

## Formula Regression Queries

| query | mode | formula norm | primary safe main | bad anchors top5 | formula backrefs |
| --- | --- | --- | --- | --- | --- |
| 葛根黄芩黄连汤方的条文是什么？ | strong | exact | True | 0 | 0 |
| 麻黄汤方的条文是什么？ | strong | exact | True | 0 | 1 |
| 大青龙汤方的条文是什么？ | strong | exact | True | 0 | 1 |
| 猪苓汤方的条文是什么？ | strong | exact | True | 0 | 1 |
| 甘草乾姜汤方和芍药甘草汤方的区别是什么？ | strong | comparison | True | 0 | 2 |
| 栀子豉汤方和栀子乾姜汤方有什么不同？ | strong | comparison | True | 0 | 2 |
| 白虎汤方和白虎加人参汤方的区别是什么？ | strong | comparison | True | 0 | 2 |
| 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | comparison | True | 0 | 2 |

## Failed Conditions

- none
