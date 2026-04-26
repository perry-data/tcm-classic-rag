# Formula Medium Span Fix Regression v1

- generated_at_utc: `2026-04-24T00:48:06.303096+00:00`
- before_db: `/tmp/zjshl_v1_before_formula_medium_span_fix_v1.db`
- after_db: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/zjshl_v1.db`

## Summary

- exact formula strong before -> after: `6/6 -> 6/6`
- comparison strong before -> after: `2/2 -> 2/2`
- forbidden primary before -> after: `0 -> 0`
- primary non-safe-main before -> after: `0 -> 0`
- bad anchors top5 before -> after: `0 -> 0`
- target high count before -> after: `0 -> 4`

## Query Table

| category | query | before_mode | after_mode | primary_after | safe_main_after | bad_anchor_after |
| --- | --- | --- | --- | --- | --- | --- |
| formula_exact | 乌梅丸方的条文是什么？ | strong | strong | ["safe:main_passages:ZJSHL-CH-015-P-0221", "safe:main_passages:ZJSHL-CH-015-P-0222"] | True | 0 |
| formula_exact | 旋复代赭石汤方的条文是什么？ | strong | strong | ["safe:main_passages:ZJSHL-CH-010-P-0106"] | True | 0 |
| formula_exact | 栀子浓朴汤方的条文是什么？ | strong | strong | ["safe:main_passages:ZJSHL-CH-009-P-0170"] | True | 0 |
| formula_exact | 桂枝甘草龙骨牡蛎汤方的条文是什么？ | strong | strong | ["safe:main_passages:ZJSHL-CH-009-P-0298"] | True | 0 |
| formula_exact | 茵陈蒿汤方的条文是什么？ | strong | strong | ["safe:main_passages:ZJSHL-CH-011-P-0141"] | True | 0 |
| formula_exact | 麻黄附子甘草汤方的条文是什么？ | strong | strong | ["safe:main_passages:ZJSHL-CH-014-P-0069"] | True | 0 |
| formula_comparison | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | strong | strong | ["safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-025-P-0003"] | True | 0 |
| formula_comparison | 桂枝去芍药汤方和桂枝去芍药加附子汤方有什么不同？ | strong | strong | ["safe:main_passages:ZJSHL-CH-025-P-0006", "safe:main_passages:ZJSHL-CH-025-P-0005", "safe:main_passages:ZJSHL-CH-009-P-0278"] | True | 0 |
