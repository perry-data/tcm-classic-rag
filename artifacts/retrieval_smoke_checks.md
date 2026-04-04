# Retrieval Smoke Checks

## 运行命令

`python run_minimal_retrieval.py`

## 结论

- `strong_chunk_backref`: mode=`strong`, primary=3, secondary=3, risk=2, chunk_hits=2
- `weak_with_review_notice`: mode=`weak_with_review_notice`, primary=0, secondary=1, risk=2, chunk_hits=0
- `refuse_no_match`: mode=`refuse`, primary=0, secondary=0, risk=0, chunk_hits=0

## Strong Precision Patch

- query: `黄连汤方的条文是什么？`
- before_profile: `baseline`
- after_profile: `tight_primary`

### Primary Evidence Before Tight Filter

| record_id | chapter_id | topic_consistency | text_preview |
| --- | --- | --- | --- |
| safe:main_passages:ZJSHL-CH-009-P-0017 | ZJSHL-CH-009 | baseline_unchecked | 葛根半斤 甘草二两，炙。味甘平 黄芩二，赵本作「三」两。味苦寒 黄连三两。味苦寒 |
| safe:main_passages:ZJSHL-CH-009-P-0019 | ZJSHL-CH-009 | baseline_unchecked | 上四味，以水八升，先煮葛根，减二升，内诸药，煮取二升，去滓，分温再服。 |
| safe:main_passages:ZJSHL-CH-010-P-0145 | ZJSHL-CH-010 | baseline_unchecked | 黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 |

### Primary Evidence After Tight Filter

| record_id | chapter_id | topic_consistency | text_preview |
| --- | --- | --- | --- |
| safe:main_passages:ZJSHL-CH-010-P-0145 | ZJSHL-CH-010 | exact_formula_anchor | 黄连汤方：黄连味苦寒 甘草炙。味甘平 乾姜味辛热 桂枝去皮，各三两。味辛热 人参二两。 |
| safe:main_passages:ZJSHL-CH-010-P-0146 | ZJSHL-CH-010 | exact_formula_anchor | 味甘温 半夏半升，洗。味辛。医统本作甘，温 大枣十二枚，擘。味甘温 |
| safe:main_passages:ZJSHL-CH-010-P-0147 | ZJSHL-CH-010 | exact_formula_anchor | 上热者，泄之以苦，黄连之苦以降阳；下寒者，散之以辛，桂、姜、半夏之辛以升阴；脾欲缓，急食甘以缓之，人参、甘草、大枣之甘以益胃。 |

### Primary Evidence Diff

- removed_from_primary: `["safe:main_passages:ZJSHL-CH-009-P-0017", "safe:main_passages:ZJSHL-CH-009-P-0019"]`
- added_to_primary: `["safe:main_passages:ZJSHL-CH-010-P-0146", "safe:main_passages:ZJSHL-CH-010-P-0147"]`

## Example: strong_chunk_backref

- query: `黄连汤方的条文是什么？`
- mode: `strong`
- mode_reason: 基于主证据回答，并附带辅助说明
- runtime_risk_flags: `[]`

### Raw Candidates

| record_id | source_object | evidence_level | combined_score | matched_terms | topic_consistency | backref_target_type |
| --- | --- | --- | --- | --- | --- | --- |
| safe:chunks:ZJSHL-CK-F-0049 | chunks | C | 158.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | exact_formula_anchor | main_passages |
| safe:main_passages:ZJSHL-CH-010-P-0145 | main_passages | A | 157.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | exact_formula_anchor | none |
| full:passages:ZJSHL-CH-010-P-0145 | passages | C | 154.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | exact_formula_anchor | none |
| safe:chunks:ZJSHL-CK-F-0009 | chunks | C | 116.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | expanded_formula_anchor | main_passages |
| safe:main_passages:ZJSHL-CH-009-P-0016 | main_passages | B | 114.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | expanded_formula_anchor | none |
| full:passages:ZJSHL-CH-009-P-0016 | passages | C | 112.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | expanded_formula_anchor | none |

### Primary Evidence

| record_id | source_object | combined_score | topic_consistency | retrieval_paths |
| --- | --- | --- | --- | --- |
| safe:main_passages:ZJSHL-CH-010-P-0145 | main_passages | 159.0 | exact_formula_anchor | [{"type": "chunk_backref", "chunk_record_id": "safe:chunks:ZJSHL-CK-F-0049", "chunk_score": 158.5}, {"type": "direct"}] |
| safe:main_passages:ZJSHL-CH-010-P-0146 | main_passages | 159.0 | exact_formula_anchor | [{"type": "chunk_backref", "chunk_record_id": "safe:chunks:ZJSHL-CK-F-0049", "chunk_score": 158.5}] |
| safe:main_passages:ZJSHL-CH-010-P-0147 | main_passages | 159.0 | exact_formula_anchor | [{"type": "chunk_backref", "chunk_record_id": "safe:chunks:ZJSHL-CK-F-0049", "chunk_score": 158.5}] |

### Secondary Evidence

| record_id | source_object | combined_score | topic_consistency | risk_flag |
| --- | --- | --- | --- | --- |
| safe:main_passages:ZJSHL-CH-009-P-0017 | main_passages | 117.0 | expanded_formula_anchor | ["topic_mismatch_demoted"] |
| safe:main_passages:ZJSHL-CH-009-P-0019 | main_passages | 117.0 | expanded_formula_anchor | ["topic_mismatch_demoted"] |
| safe:main_passages:ZJSHL-CH-009-P-0016 | main_passages | 117.0 | expanded_formula_anchor | ["short_text_demoted"] |

### Risk Materials

| record_id | source_object | combined_score | risk_flag |
| --- | --- | --- | --- |
| full:passages:ZJSHL-CH-010-P-0145 | passages | 154.5 | ["ledger_mixed_roles"] |
| full:passages:ZJSHL-CH-009-P-0016 | passages | 112.5 | ["ledger_mixed_roles"] |

### Chunk Hits

| chunk_record_id | chunk_score | topic_consistency | linked_main_passages |
| --- | --- | --- | --- |
| safe:chunks:ZJSHL-CK-F-0049 | 158.5 | exact_formula_anchor | [{"main_passage_record_id": "safe:main_passages:ZJSHL-CH-010-P-0145", "passage_id": "ZJSHL-CH-010-P-0145", "evidence_level": "A", "display_allowed": "primary"}, {"main_passage_record_id": "safe:main_passages:ZJSHL-CH-010-P-0146", "passage_id": "ZJSHL-CH-010-P-0146", "evidence_level": "A", "display_allowed": "primary"}, {"main_passage_record_id": "safe:main_passages:ZJSHL-CH-010-P-0147", "passage_id": "ZJSHL-CH-010-P-0147", "evidence_level": "A", "display_allowed": "primary"}, {"main_passage_record_id": "safe:main_passages:ZJSHL-CH-010-P-0148", "passage_id": "ZJSHL-CH-010-P-0148", "evidence_level": "A", "display_allowed": "primary"}] |
| safe:chunks:ZJSHL-CK-F-0009 | 116.5 | expanded_formula_anchor | [{"main_passage_record_id": "safe:main_passages:ZJSHL-CH-009-P-0016", "passage_id": "ZJSHL-CH-009-P-0016", "evidence_level": "B", "display_allowed": "secondary"}, {"main_passage_record_id": "safe:main_passages:ZJSHL-CH-009-P-0017", "passage_id": "ZJSHL-CH-009-P-0017", "evidence_level": "A", "display_allowed": "primary"}, {"main_passage_record_id": "safe:main_passages:ZJSHL-CH-009-P-0019", "passage_id": "ZJSHL-CH-009-P-0019", "evidence_level": "A", "display_allowed": "primary"}] |

## Example: weak_with_review_notice

- query: `烧针益阳而损阴是什么意思？`
- mode: `weak_with_review_notice`
- mode_reason: 仅命中辅助或风险材料，以下内容需核对
- runtime_risk_flags: `["strong_evidence_insufficient", "annotation_unlinked", "ledger_mixed_roles", "ambiguous_source"]`

### Raw Candidates

| record_id | source_object | evidence_level | combined_score | matched_terms | topic_consistency | backref_target_type |
| --- | --- | --- | --- | --- | --- | --- |
| full:annotations:ZJSHL-CH-003-P-0016 | annotations | B | 192.0 | ["烧针益阳而损阴", "烧针益阳", "益阳而损", "针益阳而", "阳而损阴", "烧针益", "益阳而", "而损阴", "针益阳", "阳而损", "损阴", "烧针"] | neutral | none |
| full:passages:ZJSHL-CH-003-P-0016 | passages | C | 191.0 | ["烧针益阳而损阴", "烧针益阳", "益阳而损", "针益阳而", "阳而损阴", "烧针益", "益阳而", "而损阴", "针益阳", "阳而损", "损阴", "烧针"] | neutral | none |
| full:ambiguous_passages:ZJSHL-CH-003-P-0016 | ambiguous_passages | C | 190.0 | ["烧针益阳而损阴", "烧针益阳", "益阳而损", "针益阳而", "阳而损阴", "烧针益", "益阳而", "而损阴", "针益阳", "阳而损", "损阴", "烧针"] | neutral | passages |

### Primary Evidence

_no rows_

### Secondary Evidence

| record_id | source_object | combined_score | topic_consistency | risk_flag |
| --- | --- | --- | --- | --- |
| full:annotations:ZJSHL-CH-003-P-0016 | annotations | 192.0 | neutral | ["annotation_unlinked"] |

### Risk Materials

| record_id | source_object | combined_score | risk_flag |
| --- | --- | --- | --- |
| full:passages:ZJSHL-CH-003-P-0016 | passages | 191.0 | ["ledger_mixed_roles", "ambiguous_source"] |
| full:ambiguous_passages:ZJSHL-CH-003-P-0016 | ambiguous_passages | 190.0 | ["ambiguous_source"] |

### Chunk Hits

_no rows_

## Example: refuse_no_match

- query: `书中有没有提到量子纠缠？`
- mode: `refuse`
- mode_reason: 未找到足以支撑回答的依据，建议缩小问题范围或改问具体条文
- runtime_risk_flags: `[]`

### Raw Candidates

_no rows_

### Primary Evidence

_no rows_

### Secondary Evidence

_no rows_

### Risk Materials

_no rows_

### Chunk Hits

_no rows_
