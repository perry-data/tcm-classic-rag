# Evaluator v1 Report

## 运行信息

- generated_at_utc: `2026-04-07T07:35:45.840470+00:00`
- runner_version: `evaluator_runner_v1`
- runner_backend: `local_assembler`
- entrypoint: `backend.answers.assembler.AnswerAssembler`
- goldset: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/evaluation/goldset_v1_seed.json`
- command: `python scripts/run_evaluator_v1.py`
- replay_note: Default v1 path uses the local AnswerAssembler to run query -> hybrid retrieval -> evidence gating -> answer assembler without starting the HTTP transport adapter.

## 汇总

- total_questions: `9`
- mode_match_count: `9/9`
- mode_match_rate: `1.0`
- citation_check_required_basic_pass: `6/7`
- failure_count: `1`
- all_checks_passed: `False`
- type_counts: `{"comparison": 2, "general_overview": 3, "meaning_explanation": 1, "refusal": 2, "source_lookup": 1}`
- expected_mode_counts: `{"refuse": 2, "strong": 4, "weak_with_review_notice": 3}`
- actual_mode_counts: `{"refuse": 2, "strong": 4, "weak_with_review_notice": 3}`

## 题型统计

| question_type | total | mode_match | citation_required | citation_basic_pass | failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| `comparison` | 2 | 2 | 2 | 2 | 0 |
| `general_overview` | 3 | 3 | 3 | 2 | 1 |
| `meaning_explanation` | 1 | 1 | 1 | 1 | 0 |
| `refusal` | 2 | 2 | 0 | 0 | 0 |
| `source_lookup` | 1 | 1 | 1 | 1 | 0 |

## 逐题结果

| question_id | type | expected | actual | mode | citations | gold citation | primary empty | zero evidence | zero citations | unsupported |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `eval_seed_q001` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q002` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q003` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q004` | `general_overview` | `strong` | `strong` | PASS | 3 | FAIL | PASS | PASS | PASS | FAIL |
| `eval_seed_q005` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q006` | `comparison` | `strong` | `strong` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q007` | `comparison` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q008` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q009` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |

## 失败样本

### eval_seed_q004

- query: 少阴病应该怎么办？
- question_type: `general_overview`
- expected_mode: `strong`
- actual_mode: `strong`
- failed_checks: `gold_citation_check, unsupported_assertion_check`
- unsupported_assertion_failure_reasons: `strong_without_gold_citation`


## Citation Required 明细

- `eval_seed_q001`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0145", "safe:main_passages:ZJSHL-CH-010-P-0146", "safe:main_passages:ZJSHL-CH-010-P-0147"]
- `eval_seed_q002`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0016", "safe:main_passages:ZJSHL-CH-009-P-0295", "safe:main_passages:ZJSHL-CH-010-P-0080", "full:passages:ZJSHL-CH-003-P-0016", "full:ambiguous_passages:ZJSHL-CH-003-P-0016"]
- `eval_seed_q003`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0195", "safe:main_passages:ZJSHL-CH-009-P-0002", "safe:main_passages:ZJSHL-CH-008-P-0220"]
- `eval_seed_q004`: FAIL; matched=[]
- `eval_seed_q005`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0207", "safe:main_passages:ZJSHL-CH-016-P-0009", "safe:main_passages:ZJSHL-CH-014-P-0058", "safe:main_passages:ZJSHL-CH-009-P-0312"]
- `eval_seed_q006`: PASS; matched=["safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-025-P-0003", "safe:main_passages:ZJSHL-CH-008-P-0236", "full:passages:ZJSHL-CH-025-P-0003"]
- `eval_seed_q007`: PASS; matched=["safe:main_passages:ZJSHL-CH-025-P-0005", "safe:main_passages:ZJSHL-CH-025-P-0006", "full:passages:ZJSHL-CH-025-P-0005", "full:ambiguous_passages:ZJSHL-CH-008-P-0238", "full:passages:ZJSHL-CH-025-P-0006", "full:ambiguous_passages:ZJSHL-CH-008-P-0238"]
