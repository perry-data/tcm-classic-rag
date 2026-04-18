# Evaluator v1 Report

## 运行信息

- generated_at_utc: `2026-04-18T09:18:33.415368+00:00`
- runner_version: `evaluator_runner_v1`
- runner_backend: `local_assembler`
- entrypoint: `backend.answers.assembler.AnswerAssembler`
- goldset: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/evaluation/goldset_v1_seed.json`
- command: `python scripts/run_evaluator_v1.py --report-json artifacts/evaluation/evaluator_v1_perf_regression.json --report-md artifacts/evaluation/evaluator_v1_perf_regression.md`
- replay_note: Default v1 path uses the local AnswerAssembler to run query -> hybrid retrieval -> evidence gating -> answer assembler without starting the HTTP transport adapter.

## 汇总

- total_questions: `72`
- mode_match_count: `64/72`
- mode_match_rate: `0.8889`
- citation_check_required_basic_pass: `58/58`
- failure_count: `8`
- all_checks_passed: `False`
- type_counts: `{"comparison": 12, "general_overview": 12, "meaning_explanation": 14, "refusal": 14, "source_lookup": 20}`
- expected_mode_counts: `{"refuse": 14, "strong": 43, "weak_with_review_notice": 15}`
- actual_mode_counts: `{"refuse": 14, "strong": 51, "weak_with_review_notice": 7}`

## 题型统计

| question_type | total | mode_match | citation_required | citation_basic_pass | failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| `comparison` | 12 | 12 | 12 | 12 | 0 |
| `general_overview` | 12 | 12 | 12 | 12 | 0 |
| `meaning_explanation` | 14 | 6 | 14 | 14 | 8 |
| `refusal` | 14 | 14 | 0 | 0 | 0 |
| `source_lookup` | 20 | 20 | 20 | 20 | 0 |

## 逐题结果

| question_id | type | expected | actual | mode | citations | gold citation | primary empty | zero evidence | zero citations | unsupported |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `eval_seed_q001` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q002` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 10 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q003` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q004` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q005` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q006` | `comparison` | `strong` | `strong` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q007` | `comparison` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q008` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q009` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q010` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q011` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q012` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q013` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q014` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q015` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q016` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q017` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q018` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q019` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q020` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q021` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q022` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q023` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q024` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q025` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q026` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q027` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q028` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q029` | `meaning_explanation` | `weak_with_review_notice` | `strong` | FAIL | 1 | PASS | FAIL | PASS | PASS | FAIL |
| `eval_seed_q030` | `meaning_explanation` | `weak_with_review_notice` | `strong` | FAIL | 1 | PASS | FAIL | PASS | PASS | FAIL |
| `eval_seed_q031` | `meaning_explanation` | `weak_with_review_notice` | `strong` | FAIL | 1 | PASS | FAIL | PASS | PASS | FAIL |
| `eval_seed_q032` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 8 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q033` | `meaning_explanation` | `weak_with_review_notice` | `strong` | FAIL | 1 | PASS | FAIL | PASS | PASS | FAIL |
| `eval_seed_q034` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q035` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q036` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q037` | `meaning_explanation` | `weak_with_review_notice` | `strong` | FAIL | 1 | PASS | FAIL | PASS | PASS | FAIL |
| `eval_seed_q038` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q039` | `meaning_explanation` | `weak_with_review_notice` | `strong` | FAIL | 1 | PASS | FAIL | PASS | PASS | FAIL |
| `eval_seed_q040` | `meaning_explanation` | `weak_with_review_notice` | `strong` | FAIL | 1 | PASS | FAIL | PASS | PASS | FAIL |
| `eval_seed_q041` | `meaning_explanation` | `weak_with_review_notice` | `strong` | FAIL | 1 | PASS | FAIL | PASS | PASS | FAIL |
| `eval_seed_q042` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q043` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 7 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q044` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 7 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q045` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q046` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q047` | `general_overview` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q048` | `general_overview` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q049` | `general_overview` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q050` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q051` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q052` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q053` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q054` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q055` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q056` | `comparison` | `strong` | `strong` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q057` | `comparison` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q058` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q059` | `comparison` | `strong` | `strong` | PASS | 6 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q060` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q061` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q062` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q063` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q064` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q065` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q066` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q067` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q068` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q069` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q070` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q071` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q072` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |

## 失败样本

### eval_seed_q029

- query: 一阴一阳谓之道是什么意思？
- question_type: `meaning_explanation`
- expected_mode: `weak_with_review_notice`
- actual_mode: `strong`
- failed_checks: `mode_match, primary_empty_check, unsupported_assertion_check`
- unsupported_assertion_failure_reasons: `expected_weak_but_actual_mode_strong, primary_evidence_should_be_empty`

### eval_seed_q030

- query: 阳为气，阴为血是什么意思？
- question_type: `meaning_explanation`
- expected_mode: `weak_with_review_notice`
- actual_mode: `strong`
- failed_checks: `mode_match, primary_empty_check, unsupported_assertion_check`
- unsupported_assertion_failure_reasons: `expected_weak_but_actual_mode_strong, primary_evidence_should_be_empty`

### eval_seed_q031

- query: 脉沉者知荣血内微是什么意思？
- question_type: `meaning_explanation`
- expected_mode: `weak_with_review_notice`
- actual_mode: `strong`
- failed_checks: `mode_match, primary_empty_check, unsupported_assertion_check`
- unsupported_assertion_failure_reasons: `expected_weak_but_actual_mode_strong, primary_evidence_should_be_empty`

### eval_seed_q033

- query: 荣气微者加烧针是什么意思？
- question_type: `meaning_explanation`
- expected_mode: `weak_with_review_notice`
- actual_mode: `strong`
- failed_checks: `mode_match, primary_empty_check, unsupported_assertion_check`
- unsupported_assertion_failure_reasons: `expected_weak_but_actual_mode_strong, primary_evidence_should_be_empty`

### eval_seed_q037

- query: 绵绵者连绵而软是什么意思？
- question_type: `meaning_explanation`
- expected_mode: `weak_with_review_notice`
- actual_mode: `strong`
- failed_checks: `mode_match, primary_empty_check, unsupported_assertion_check`
- unsupported_assertion_failure_reasons: `expected_weak_but_actual_mode_strong, primary_evidence_should_be_empty`

### eval_seed_q039

- query: 弦则为减减则为寒是什么意思？
- question_type: `meaning_explanation`
- expected_mode: `weak_with_review_notice`
- actual_mode: `strong`
- failed_checks: `mode_match, primary_empty_check, unsupported_assertion_check`
- unsupported_assertion_failure_reasons: `expected_weak_but_actual_mode_strong, primary_evidence_should_be_empty`

### eval_seed_q040

- query: 浮为阳紧为阴是什么意思？
- question_type: `meaning_explanation`
- expected_mode: `weak_with_review_notice`
- actual_mode: `strong`
- failed_checks: `mode_match, primary_empty_check, unsupported_assertion_check`
- unsupported_assertion_failure_reasons: `expected_weak_but_actual_mode_strong, primary_evidence_should_be_empty`

### eval_seed_q041

- query: 阳胜则热阴胜则寒是什么意思？
- question_type: `meaning_explanation`
- expected_mode: `weak_with_review_notice`
- actual_mode: `strong`
- failed_checks: `mode_match, primary_empty_check, unsupported_assertion_check`
- unsupported_assertion_failure_reasons: `expected_weak_but_actual_mode_strong, primary_evidence_should_be_empty`


## Citation Required 明细

- `eval_seed_q001`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0145", "safe:main_passages:ZJSHL-CH-010-P-0146", "safe:main_passages:ZJSHL-CH-010-P-0147"]
- `eval_seed_q002`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0016", "safe:main_passages:ZJSHL-CH-009-P-0295", "safe:main_passages:ZJSHL-CH-010-P-0080", "full:passages:ZJSHL-CH-003-P-0016"]
- `eval_seed_q003`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0195", "safe:main_passages:ZJSHL-CH-009-P-0002", "safe:main_passages:ZJSHL-CH-008-P-0220"]
- `eval_seed_q004`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0078", "safe:main_passages:ZJSHL-CH-014-P-0112", "safe:main_passages:ZJSHL-CH-014-P-0062"]
- `eval_seed_q005`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0207", "safe:main_passages:ZJSHL-CH-016-P-0009"]
- `eval_seed_q006`: PASS; matched=["safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-025-P-0003", "safe:main_passages:ZJSHL-CH-008-P-0236", "full:passages:ZJSHL-CH-025-P-0003", "full:passages:ZJSHL-CH-009-P-0053"]
- `eval_seed_q007`: PASS; matched=["safe:main_passages:ZJSHL-CH-025-P-0005", "safe:main_passages:ZJSHL-CH-025-P-0006", "full:passages:ZJSHL-CH-025-P-0005", "full:passages:ZJSHL-CH-008-P-0238", "full:passages:ZJSHL-CH-025-P-0006"]
- `eval_seed_q010`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0217", "safe:main_passages:ZJSHL-CH-008-P-0219"]
- `eval_seed_q011`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0004", "safe:main_passages:ZJSHL-CH-009-P-0006"]
- `eval_seed_q012`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0023", "safe:main_passages:ZJSHL-CH-009-P-0025"]
- `eval_seed_q013`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0033", "safe:main_passages:ZJSHL-CH-009-P-0034", "safe:main_passages:ZJSHL-CH-009-P-0035"]
- `eval_seed_q014`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0040", "safe:main_passages:ZJSHL-CH-009-P-0043"]
- `eval_seed_q015`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0211", "safe:main_passages:ZJSHL-CH-009-P-0213"]
- `eval_seed_q016`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0250"]
- `eval_seed_q017`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0138"]
- `eval_seed_q018`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0165", "safe:main_passages:ZJSHL-CH-010-P-0167"]
- `eval_seed_q019`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0068", "safe:main_passages:ZJSHL-CH-011-P-0070"]
- `eval_seed_q020`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0071", "safe:main_passages:ZJSHL-CH-011-P-0072", "safe:main_passages:ZJSHL-CH-011-P-0073"]
- `eval_seed_q021`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0109"]
- `eval_seed_q022`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0141"]
- `eval_seed_q023`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0267", "safe:main_passages:ZJSHL-CH-008-P-0268", "safe:main_passages:ZJSHL-CH-008-P-0269"]
- `eval_seed_q024`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0258", "safe:main_passages:ZJSHL-CH-008-P-0259", "safe:main_passages:ZJSHL-CH-008-P-0260"]
- `eval_seed_q025`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0261", "safe:main_passages:ZJSHL-CH-008-P-0262", "safe:main_passages:ZJSHL-CH-008-P-0263"]
- `eval_seed_q026`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0264", "safe:main_passages:ZJSHL-CH-008-P-0266"]
- `eval_seed_q027`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0105"]
- `eval_seed_q028`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0068"]
- `eval_seed_q029`: PASS; matched=["full:passages:ZJSHL-CH-003-P-0007"]
- `eval_seed_q030`: PASS; matched=["full:passages:ZJSHL-CH-003-P-0009"]
- `eval_seed_q031`: PASS; matched=["full:passages:ZJSHL-CH-003-P-0011"]
- `eval_seed_q032`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0013", "full:annotations:ZJSHL-CH-004-P-0209", "full:passages:ZJSHL-CH-003-P-0013", "full:passages:ZJSHL-CH-004-P-0209"]
- `eval_seed_q033`: PASS; matched=["full:passages:ZJSHL-CH-003-P-0015"]
- `eval_seed_q034`: PASS; matched=["full:passages:ZJSHL-CH-003-P-0018"]
- `eval_seed_q035`: PASS; matched=["full:passages:ZJSHL-CH-003-P-0020"]
- `eval_seed_q036`: PASS; matched=["safe:main_passages:ZJSHL-CH-003-P-0023"]
- `eval_seed_q037`: PASS; matched=["full:passages:ZJSHL-CH-003-P-0027"]
- `eval_seed_q038`: PASS; matched=["safe:main_passages:ZJSHL-CH-003-P-0031"]
- `eval_seed_q039`: PASS; matched=["full:passages:ZJSHL-CH-003-P-0041"]
- `eval_seed_q040`: PASS; matched=["full:passages:ZJSHL-CH-003-P-0043"]
- `eval_seed_q041`: PASS; matched=["full:passages:ZJSHL-CH-003-P-0047"]
- `eval_seed_q042`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0123", "safe:main_passages:ZJSHL-CH-011-P-0146", "safe:main_passages:ZJSHL-CH-011-P-0086"]
- `eval_seed_q043`: PASS; matched=["safe:main_passages:ZJSHL-CH-013-P-0008", "safe:main_passages:ZJSHL-CH-013-P-0018", "safe:main_passages:ZJSHL-CH-013-P-0002", "full:passages:ZJSHL-CH-013-P-0008"]
- `eval_seed_q044`: PASS; matched=["safe:main_passages:ZJSHL-CH-015-P-0193", "safe:main_passages:ZJSHL-CH-015-P-0232", "full:passages:ZJSHL-CH-015-P-0200", "full:passages:ZJSHL-CH-015-P-0198"]
- `eval_seed_q045`: PASS; matched=["safe:main_passages:ZJSHL-CH-006-P-0012", "safe:main_passages:ZJSHL-CH-009-P-0173", "safe:main_passages:ZJSHL-CH-009-P-0320"]
- `eval_seed_q046`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0193", "safe:main_passages:ZJSHL-CH-008-P-0215", "safe:main_passages:ZJSHL-CH-010-P-0075"]
- `eval_seed_q047`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0195", "safe:main_passages:ZJSHL-CH-008-P-0193", "safe:main_passages:ZJSHL-CH-009-P-0002", "safe:main_passages:ZJSHL-CH-008-P-0220"]
- `eval_seed_q048`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0123", "safe:main_passages:ZJSHL-CH-011-P-0146", "safe:main_passages:ZJSHL-CH-011-P-0086", "safe:main_passages:ZJSHL-CH-011-P-0101"]
- `eval_seed_q049`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0078", "safe:main_passages:ZJSHL-CH-014-P-0112", "safe:main_passages:ZJSHL-CH-014-P-0062", "safe:main_passages:ZJSHL-CH-014-P-0072"]
- `eval_seed_q050`: PASS; matched=["safe:main_passages:ZJSHL-CH-016-P-0002", "safe:main_passages:ZJSHL-CH-016-P-0004"]
- `eval_seed_q051`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0217", "safe:main_passages:ZJSHL-CH-009-P-0004"]
- `eval_seed_q052`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0022", "safe:main_passages:ZJSHL-CH-009-P-0033", "safe:main_passages:ZJSHL-CH-009-P-0077", "safe:main_passages:ZJSHL-CH-009-P-0036"]
- `eval_seed_q053`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0068", "safe:main_passages:ZJSHL-CH-011-P-0071"]
- `eval_seed_q054`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0211", "safe:main_passages:ZJSHL-CH-009-P-0250"]
- `eval_seed_q055`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0138", "safe:main_passages:ZJSHL-CH-011-P-0109"]
- `eval_seed_q056`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0267", "safe:main_passages:ZJSHL-CH-009-P-0130", "full:passages:ZJSHL-CH-009-P-0130", "full:passages:ZJSHL-CH-009-P-0128"]
- `eval_seed_q057`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0258", "safe:main_passages:ZJSHL-CH-008-P-0261", "safe:main_passages:ZJSHL-CH-008-P-0256"]
- `eval_seed_q058`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0159", "safe:main_passages:ZJSHL-CH-009-P-0175", "safe:main_passages:ZJSHL-CH-009-P-0173"]
- `eval_seed_q059`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0068", "safe:main_passages:ZJSHL-CH-027-P-0009", "full:passages:ZJSHL-CH-010-P-0068", "full:passages:ZJSHL-CH-010-P-0066", "full:passages:ZJSHL-CH-027-P-0009", "full:passages:ZJSHL-CH-010-P-0095"]
- `eval_seed_q060`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0165", "safe:main_passages:ZJSHL-CH-025-P-0012", "safe:main_passages:ZJSHL-CH-011-P-0104"]
