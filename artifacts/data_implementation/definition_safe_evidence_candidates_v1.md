# Definition Safe Evidence Candidates v1

## Current Support-Only Failure Surface

| query | previous mode | why weak | full passage support ids | candidate definition / explanation sentence |
| --- | --- | --- | --- | --- |
| 什么是发汗药 | weak_with_review_notice | primary_eligible 为空，关键句只在 support/review 的 full:passages 中 | full:passages:ZJSHL-CH-006-P-0120<br>full:passages:ZJSHL-CH-010-P-0137 | 发汗药，须温暖服者，易为发散也。 |
| 发汗药是什么意思 | weak_with_review_notice | primary_eligible 为空，关键句只在 support/review 的 full:passages 中 | full:passages:ZJSHL-CH-006-P-0127<br>full:passages:ZJSHL-CH-006-P-0120<br>full:passages:ZJSHL-CH-006-P-0126<br>full:passages:ZJSHL-CH-006-P-0119 | 发汗药，须温暖服者，易为发散也。 |
| 坏病是什么 | weak_with_review_notice | primary_eligible 为空，关键句只在 support/review 的 full:passages 中 | full:passages:ZJSHL-CH-008-P-0227<br>full:passages:ZJSHL-CH-008-P-0226 | 太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。 |
| 坏病是什么意思 | weak_with_review_notice | primary_eligible 为空，关键句只在 support/review 的 full:passages 中 | full:passages:ZJSHL-CH-008-P-0227<br>full:passages:ZJSHL-CH-008-P-0226 | 太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。 |

## Promotion Registry

| concept_id | term | type | primary support passage | source layer | safe primary | primary sentence | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEF-FAHAN-YAO | 发汗药 | therapeutic_category | ZJSHL-CH-006-P-0127 | passages / C | yes | 发汗药，须温暖服者，易为发散也。 | 从 full:passages 中抽出定义/解释句与归类句；原 full passage 仍不进入 primary。 |
| DEF-XIA-YAO | 下药 | therapeutic_category | ZJSHL-CH-006-P-0120 | passages / C | yes | 承气汤者，下药也。 | 仅提升直接归类句；泛化解释仍需下一轮补充。 |
| DEF-HUAI-BING | 坏病 | disease_state_term | ZJSHL-CH-008-P-0227 | passages / C | yes | 太阳病，三日中，曾经发汗、吐下、温针，虚其正气，病仍不解者，谓之坏病，言为医所坏病也。 | 抽出“谓之坏病/此为坏病”的定义句，避免整段 full passage 越权。 |
| DEF-YANG-JIE | 阳结 | pulse_pattern_term | ZJSHL-CH-003-P-0004 | main_passages / A | yes | 其脉浮而数，能食，不大便者，此为实，名曰阳结也。 | 已有 safe main 主证据；纳入 registry 作为概念对象对照。 |
| DEF-YIN-JIE | 阴结 | pulse_pattern_term | ZJSHL-CH-003-P-0004 | main_passages / A | yes | 其脉沉而迟，不能食，身体重，大便反硬，名曰阴结也。 | 已有 safe main 主证据；纳入 registry 作为概念对象对照。 |
| DEF-SHEN-DAN | 神丹 | drug_name_term | ZJSHL-CH-006-P-0118 | passages / C | no | 神丹者，发汗之药也。 | 当前依据主要来自 annotation/full passage 对照层；本轮登记但不提升。 |

## Non-Promotion Rule

- `full:passages:*` remains risk/support-only in the original runtime tables.
- Only rows with `is_safe_primary_candidate=1` are exposed through `retrieval_ready_definition_view`.
- `DEF-SHEN-DAN` is deliberately registered but not exposed as primary because the current source is still review-only.
