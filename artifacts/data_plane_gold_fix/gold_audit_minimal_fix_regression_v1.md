# Gold Audit Minimal Fix Regression v1

- generated_at_utc: `2026-04-24T00:17:15.554261+00:00`
- before_db: `/tmp/zjshl_v1_before_gold_audit_minimal_fix_v1.db`
- after_db: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/zjshl_v1.db`

## Summary

- forbidden_primary before -> after: `0 -> 0`
- 胆瘅 risk alias count before -> after: `2 -> 0`
- 胆瘅 learner lexicon risk count before -> after: `0 -> 0`
- 胆瘅 definition primary conflicts before -> after: `0 -> 0`
- formula strong before -> after: `2/2 -> 2/2`
- formula bad anchors top5 before -> after: `0 -> 0`
- gold-safe definition hit before -> after: `2 -> 2`
- 发汗药 target hit before -> after: `4 -> 4`

## Query Table

| category | query | before_mode | after_mode | before_focus | after_focus | before_target_hit | after_target_hit | primary_after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fahan | 什么是发汗药 | strong | strong | term_normalization | term_normalization | True | True | ["safe:definition_terms:DPO-c8ac10b5ac88"] |
| fahan | 发汗药是什么意思 | strong | strong | term_normalization | term_normalization | True | True | ["safe:definition_terms:DPO-c8ac10b5ac88"] |
| fahan | 发汗药是干什么的 | strong | strong | term_normalization | term_normalization | True | True | ["safe:definition_terms:DPO-c8ac10b5ac88"] |
| fahan | 发汗的药是什么意思 | strong | strong | term_normalization | term_normalization | True | True | ["safe:definition_terms:DPO-c8ac10b5ac88"] |
| dandan | 什么是胆瘅 | refuse | refuse | noise_stripped_query | noise_stripped_query | False | False | - |
| dandan | 胆瘅是什么意思 | weak_with_review_notice | weak_with_review_notice | noise_stripped_query | noise_stripped_query | False | False | - |
| dandan_alias | 口苦病是什么意思 | refuse | refuse | noise_stripped_query | noise_stripped_query | False | False | - |
| dandan_alias | 胆瘅病是什么意思 | refuse | refuse | noise_stripped_query | noise_stripped_query | False | False | - |
| formula | 桂枝汤方的条文是什么？ | strong | strong | noise_stripped_query | noise_stripped_query | False | False | ["safe:main_passages:ZJSHL-CH-008-P-0217", "safe:main_passages:ZJSHL-CH-016-P-0034", "safe:main_passages:ZJSHL-CH-008-P-0219"] |
| formula | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | strong | noise_stripped_query | noise_stripped_query | False | False | ["safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-025-P-0003"] |
| gold_safe_definition | 什么是下药 | strong | strong | term_normalization | term_normalization | True | True | ["safe:definition_terms:DPO-033fc08d3b2a"] |
| gold_safe_definition | 什么是四逆 | strong | strong | term_normalization | term_normalization | True | True | ["safe:definition_terms:DPO-ce8ffb681e3f"] |
