# Retrieval Smoke Checks

## 运行命令

`python run_minimal_retrieval.py`

## 结论

- `strong_chunk_backref`: mode=`strong`, primary=3, secondary=1, risk=2, chunk_hits=2
- `weak_with_review_notice`: mode=`weak_with_review_notice`, primary=0, secondary=1, risk=2, chunk_hits=0
- `refuse_no_match`: mode=`refuse`, primary=0, secondary=0, risk=0, chunk_hits=0

## Example: strong_chunk_backref

- query: `黄连汤方的条文是什么？`
- mode: `strong`
- mode_reason: 基于主证据回答，并附带辅助说明
- runtime_risk_flags: `[]`

### Raw Candidates

| record_id | source_object | evidence_level | combined_score | matched_terms | backref_target_type |
| --- | --- | --- | --- | --- | --- |
| safe:chunks:ZJSHL-CK-F-0009 | chunks | C | 134.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | main_passages |
| safe:chunks:ZJSHL-CK-F-0049 | chunks | C | 134.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | main_passages |
| safe:main_passages:ZJSHL-CH-010-P-0145 | main_passages | A | 133.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | none |
| safe:main_passages:ZJSHL-CH-009-P-0016 | main_passages | B | 132.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | none |
| full:passages:ZJSHL-CH-009-P-0016 | passages | C | 130.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | none |
| full:passages:ZJSHL-CH-010-P-0145 | passages | C | 130.5 | ["黄连汤方", "连汤方", "黄连汤", "汤方", "连汤", "黄连"] | none |

### Primary Evidence

| record_id | source_object | combined_score | retrieval_paths |
| --- | --- | --- | --- |
| safe:main_passages:ZJSHL-CH-009-P-0017 | main_passages | 135.0 | [{"type": "chunk_backref", "chunk_record_id": "safe:chunks:ZJSHL-CK-F-0009", "chunk_score": 134.5}] |
| safe:main_passages:ZJSHL-CH-009-P-0019 | main_passages | 135.0 | [{"type": "chunk_backref", "chunk_record_id": "safe:chunks:ZJSHL-CK-F-0009", "chunk_score": 134.5}] |
| safe:main_passages:ZJSHL-CH-010-P-0145 | main_passages | 135.0 | [{"type": "chunk_backref", "chunk_record_id": "safe:chunks:ZJSHL-CK-F-0049", "chunk_score": 134.5}, {"type": "direct"}] |

### Secondary Evidence

| record_id | source_object | combined_score | risk_flag |
| --- | --- | --- | --- |
| safe:main_passages:ZJSHL-CH-009-P-0016 | main_passages | 135.0 | ["short_text_demoted"] |

### Risk Materials

| record_id | source_object | combined_score | risk_flag |
| --- | --- | --- | --- |
| full:passages:ZJSHL-CH-009-P-0016 | passages | 130.5 | ["ledger_mixed_roles"] |
| full:passages:ZJSHL-CH-010-P-0145 | passages | 130.5 | ["ledger_mixed_roles"] |

### Chunk Hits

| chunk_record_id | chunk_score | linked_main_passages |
| --- | --- | --- |
| safe:chunks:ZJSHL-CK-F-0009 | 134.5 | [{"main_passage_record_id": "safe:main_passages:ZJSHL-CH-009-P-0016", "passage_id": "ZJSHL-CH-009-P-0016", "evidence_level": "B", "display_allowed": "secondary"}, {"main_passage_record_id": "safe:main_passages:ZJSHL-CH-009-P-0017", "passage_id": "ZJSHL-CH-009-P-0017", "evidence_level": "A", "display_allowed": "primary"}, {"main_passage_record_id": "safe:main_passages:ZJSHL-CH-009-P-0019", "passage_id": "ZJSHL-CH-009-P-0019", "evidence_level": "A", "display_allowed": "primary"}] |
| safe:chunks:ZJSHL-CK-F-0049 | 134.5 | [{"main_passage_record_id": "safe:main_passages:ZJSHL-CH-010-P-0145", "passage_id": "ZJSHL-CH-010-P-0145", "evidence_level": "A", "display_allowed": "primary"}, {"main_passage_record_id": "safe:main_passages:ZJSHL-CH-010-P-0146", "passage_id": "ZJSHL-CH-010-P-0146", "evidence_level": "A", "display_allowed": "primary"}, {"main_passage_record_id": "safe:main_passages:ZJSHL-CH-010-P-0147", "passage_id": "ZJSHL-CH-010-P-0147", "evidence_level": "A", "display_allowed": "primary"}, {"main_passage_record_id": "safe:main_passages:ZJSHL-CH-010-P-0148", "passage_id": "ZJSHL-CH-010-P-0148", "evidence_level": "A", "display_allowed": "primary"}] |

## Example: weak_with_review_notice

- query: `烧针益阳而损阴是什么意思？`
- mode: `weak_with_review_notice`
- mode_reason: 仅命中辅助或风险材料，以下内容需核对
- runtime_risk_flags: `["strong_evidence_insufficient", "annotation_unlinked", "ledger_mixed_roles", "ambiguous_source"]`

### Raw Candidates

| record_id | source_object | evidence_level | combined_score | matched_terms | backref_target_type |
| --- | --- | --- | --- | --- | --- |
| full:annotations:ZJSHL-CH-003-P-0016 | annotations | B | 192.0 | ["烧针益阳而损阴", "烧针益阳", "益阳而损", "针益阳而", "阳而损阴", "烧针益", "益阳而", "而损阴", "针益阳", "阳而损", "损阴", "烧针"] | none |
| full:passages:ZJSHL-CH-003-P-0016 | passages | C | 191.0 | ["烧针益阳而损阴", "烧针益阳", "益阳而损", "针益阳而", "阳而损阴", "烧针益", "益阳而", "而损阴", "针益阳", "阳而损", "损阴", "烧针"] | none |
| full:ambiguous_passages:ZJSHL-CH-003-P-0016 | ambiguous_passages | C | 190.0 | ["烧针益阳而损阴", "烧针益阳", "益阳而损", "针益阳而", "阳而损阴", "烧针益", "益阳而", "而损阴", "针益阳", "阳而损", "损阴", "烧针"] | passages |

### Primary Evidence

_no rows_

### Secondary Evidence

| record_id | source_object | combined_score | risk_flag |
| --- | --- | --- | --- |
| full:annotations:ZJSHL-CH-003-P-0016 | annotations | 192.0 | ["annotation_unlinked"] |

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
