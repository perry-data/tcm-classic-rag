# Evaluator v1 Report

## 运行信息

- generated_at_utc: `2026-04-08T11:18:14.514482+00:00`
- runner_version: `evaluator_runner_v1`
- runner_backend: `local_assembler`
- entrypoint: `backend.answers.assembler.AnswerAssembler`
- goldset: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/evaluation/goldset_v2_working_102.json`
- command: `python scripts/run_evaluator_v1.py --goldset artifacts/evaluation/goldset_v2_working_102.json --report-json artifacts/evaluation/comparison_entity_fix_v1_eval_report.json --report-md artifacts/evaluation/comparison_entity_fix_v1_eval_report.md`
- replay_note: Default v1 path uses the local AnswerAssembler to run query -> hybrid retrieval -> evidence gating -> answer assembler without starting the HTTP transport adapter.

## 汇总

- total_questions: `102`
- mode_match_count: `97/102`
- mode_match_rate: `0.951`
- citation_check_required_basic_pass: `81/82`
- failure_count: `5`
- all_checks_passed: `False`
- type_counts: `{"comparison": 20, "general_overview": 14, "meaning_explanation": 18, "refusal": 20, "source_lookup": 30}`
- expected_mode_counts: `{"refuse": 20, "strong": 63, "weak_with_review_notice": 19}`
- actual_mode_counts: `{"refuse": 20, "strong": 60, "weak_with_review_notice": 22}`

## 题型统计

| question_type | total | mode_match | citation_required | citation_basic_pass | failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| `comparison` | 20 | 20 | 20 | 20 | 0 |
| `general_overview` | 14 | 12 | 14 | 13 | 2 |
| `meaning_explanation` | 18 | 17 | 18 | 18 | 1 |
| `refusal` | 20 | 20 | 0 | 0 | 0 |
| `source_lookup` | 30 | 28 | 30 | 30 | 2 |

## 逐题结果

| question_id | type | expected | actual | mode | citations | gold citation | primary empty | zero evidence | zero citations | unsupported |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `eval_seed_q001` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q002` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q003` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q004` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q005` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q006` | `comparison` | `strong` | `strong` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q007` | `comparison` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | PASS | PASS | PASS | PASS | PASS |
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
| `eval_seed_q029` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q030` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q031` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q032` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q033` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q034` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q035` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q036` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q037` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q038` | `meaning_explanation` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q039` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q040` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q041` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q042` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q043` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 8 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q044` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 8 | PASS | PASS | PASS | PASS | PASS |
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
| `eval_seed_q057` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
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
| `eval_seed_q073` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q074` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q075` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q076` | `source_lookup` | `strong` | `weak_with_review_notice` | FAIL | 8 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q077` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q078` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q079` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q080` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q081` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q082` | `source_lookup` | `strong` | `weak_with_review_notice` | FAIL | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q083` | `comparison` | `strong` | `strong` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q084` | `comparison` | `strong` | `strong` | PASS | 6 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q085` | `comparison` | `strong` | `strong` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q086` | `comparison` | `strong` | `strong` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q087` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q088` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q089` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q090` | `comparison` | `strong` | `strong` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q091` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q092` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q093` | `meaning_explanation` | `weak_with_review_notice` | `strong` | FAIL | 1 | PASS | FAIL | PASS | PASS | FAIL |
| `eval_seed_q094` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q095` | `general_overview` | `strong` | `weak_with_review_notice` | FAIL | 5 | FAIL | PASS | PASS | PASS | PASS |
| `eval_seed_q096` | `general_overview` | `strong` | `weak_with_review_notice` | FAIL | 8 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q097` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q098` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q099` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q100` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q101` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q102` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |

## 失败样本

### eval_seed_q076

- query: 麻黄杏仁甘草石膏汤方的条文是什么？
- question_type: `source_lookup`
- expected_mode: `strong`
- actual_mode: `weak_with_review_notice`
- failed_checks: `mode_match`
- unsupported_assertion_failure_reasons: `None`

### eval_seed_q082

- query: 麻子仁丸方的条文是什么？
- question_type: `source_lookup`
- expected_mode: `strong`
- actual_mode: `weak_with_review_notice`
- failed_checks: `mode_match`
- unsupported_assertion_failure_reasons: `None`

### eval_seed_q093

- query: 心下痞，按之濡是什么意思？
- question_type: `meaning_explanation`
- expected_mode: `weak_with_review_notice`
- actual_mode: `strong`
- failed_checks: `mode_match, primary_empty_check, unsupported_assertion_check`
- unsupported_assertion_failure_reasons: `expected_weak_but_actual_mode_strong, primary_evidence_should_be_empty`

### eval_seed_q095

- query: 少阳病有哪些核心表现和处理边界？
- question_type: `general_overview`
- expected_mode: `strong`
- actual_mode: `weak_with_review_notice`
- failed_checks: `mode_match, gold_citation_check`
- unsupported_assertion_failure_reasons: `None`

### eval_seed_q096

- query: 伤寒瘥后有哪些处理分支？
- question_type: `general_overview`
- expected_mode: `strong`
- actual_mode: `weak_with_review_notice`
- failed_checks: `mode_match`
- unsupported_assertion_failure_reasons: `None`


## Citation Required 明细

- `eval_seed_q001`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0145", "safe:main_passages:ZJSHL-CH-010-P-0146", "safe:main_passages:ZJSHL-CH-010-P-0147"]
- `eval_seed_q002`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0016", "safe:main_passages:ZJSHL-CH-009-P-0295", "safe:main_passages:ZJSHL-CH-010-P-0080", "full:passages:ZJSHL-CH-003-P-0016", "full:ambiguous_passages:ZJSHL-CH-003-P-0016"]
- `eval_seed_q003`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0195", "safe:main_passages:ZJSHL-CH-009-P-0002", "safe:main_passages:ZJSHL-CH-008-P-0220"]
- `eval_seed_q004`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0078", "safe:main_passages:ZJSHL-CH-014-P-0112", "safe:main_passages:ZJSHL-CH-014-P-0062"]
- `eval_seed_q005`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0207", "safe:main_passages:ZJSHL-CH-016-P-0009"]
- `eval_seed_q006`: PASS; matched=["safe:main_passages:ZJSHL-CH-025-P-0004", "safe:main_passages:ZJSHL-CH-025-P-0003", "safe:main_passages:ZJSHL-CH-008-P-0236", "full:passages:ZJSHL-CH-025-P-0003", "full:ambiguous_passages:ZJSHL-CH-009-P-0053"]
- `eval_seed_q007`: PASS; matched=["safe:main_passages:ZJSHL-CH-025-P-0005", "safe:main_passages:ZJSHL-CH-025-P-0006", "full:passages:ZJSHL-CH-025-P-0005", "full:ambiguous_passages:ZJSHL-CH-008-P-0238", "full:passages:ZJSHL-CH-025-P-0006", "full:ambiguous_passages:ZJSHL-CH-008-P-0238"]
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
- `eval_seed_q029`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0007", "safe:main_passages:ZJSHL-CH-006-P-0034", "full:passages:ZJSHL-CH-003-P-0007"]
- `eval_seed_q030`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0009", "safe:main_passages:ZJSHL-CH-003-P-0080", "full:passages:ZJSHL-CH-003-P-0009"]
- `eval_seed_q031`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0011", "safe:main_passages:ZJSHL-CH-003-P-0010", "full:passages:ZJSHL-CH-003-P-0011"]
- `eval_seed_q032`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0013", "full:annotations:ZJSHL-CH-004-P-0209", "full:passages:ZJSHL-CH-003-P-0013", "full:passages:ZJSHL-CH-004-P-0209"]
- `eval_seed_q033`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0015", "full:annotations:ZJSHL-CH-009-P-0302", "full:annotations:ZJSHL-CH-011-P-0103", "full:passages:ZJSHL-CH-003-P-0015", "full:passages:ZJSHL-CH-009-P-0302"]
- `eval_seed_q034`: PASS; matched=["safe:main_passages:ZJSHL-CH-003-P-0017"]
- `eval_seed_q035`: PASS; matched=["safe:main_passages:ZJSHL-CH-003-P-0019"]
- `eval_seed_q036`: PASS; matched=["safe:main_passages:ZJSHL-CH-003-P-0023"]
- `eval_seed_q037`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0027", "full:passages:ZJSHL-CH-003-P-0027"]
- `eval_seed_q038`: PASS; matched=["safe:main_passages:ZJSHL-CH-003-P-0031", "safe:main_passages:ZJSHL-CH-004-P-0130"]
- `eval_seed_q039`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0041", "safe:main_passages:ZJSHL-CH-003-P-0039", "safe:main_passages:ZJSHL-CH-023-P-0018", "full:passages:ZJSHL-CH-003-P-0041"]
- `eval_seed_q040`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0043", "safe:main_passages:ZJSHL-CH-003-P-0099", "safe:main_passages:ZJSHL-CH-003-P-0037", "full:passages:ZJSHL-CH-003-P-0043"]
- `eval_seed_q041`: PASS; matched=["full:annotations:ZJSHL-CH-003-P-0047", "safe:main_passages:ZJSHL-CH-003-P-0088", "full:passages:ZJSHL-CH-003-P-0047"]
- `eval_seed_q042`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0123", "safe:main_passages:ZJSHL-CH-011-P-0146", "safe:main_passages:ZJSHL-CH-011-P-0086"]
- `eval_seed_q043`: PASS; matched=["safe:main_passages:ZJSHL-CH-013-P-0008", "safe:main_passages:ZJSHL-CH-013-P-0018", "safe:main_passages:ZJSHL-CH-013-P-0002", "full:passages:ZJSHL-CH-013-P-0008"]
- `eval_seed_q044`: PASS; matched=["safe:main_passages:ZJSHL-CH-015-P-0193", "safe:main_passages:ZJSHL-CH-015-P-0232", "full:passages:ZJSHL-CH-015-P-0200", "full:ambiguous_passages:ZJSHL-CH-015-P-0200", "full:passages:ZJSHL-CH-015-P-0198"]
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
- `eval_seed_q056`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0267", "safe:main_passages:ZJSHL-CH-009-P-0130", "full:passages:ZJSHL-CH-009-P-0130", "full:ambiguous_passages:ZJSHL-CH-009-P-0128"]
- `eval_seed_q057`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0258", "safe:main_passages:ZJSHL-CH-008-P-0261", "safe:main_passages:ZJSHL-CH-008-P-0256", "safe:main_passages:ZJSHL-CH-008-P-0256"]
- `eval_seed_q058`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0159", "safe:main_passages:ZJSHL-CH-009-P-0175", "safe:main_passages:ZJSHL-CH-009-P-0173"]
- `eval_seed_q059`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0068", "safe:main_passages:ZJSHL-CH-027-P-0009", "full:passages:ZJSHL-CH-010-P-0068", "full:ambiguous_passages:ZJSHL-CH-010-P-0066", "full:passages:ZJSHL-CH-027-P-0009", "full:ambiguous_passages:ZJSHL-CH-010-P-0095"]
- `eval_seed_q060`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0165", "safe:main_passages:ZJSHL-CH-025-P-0012", "safe:main_passages:ZJSHL-CH-025-P-0012", "safe:main_passages:ZJSHL-CH-011-P-0104"]
- `eval_seed_q073`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0012", "safe:main_passages:ZJSHL-CH-009-P-0013"]
- `eval_seed_q074`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0017", "safe:main_passages:ZJSHL-CH-009-P-0019"]
- `eval_seed_q075`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0093", "safe:main_passages:ZJSHL-CH-009-P-0095"]
- `eval_seed_q076`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0100", "safe:main_passages:ZJSHL-CH-009-P-0102"]
- `eval_seed_q077`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0110", "safe:main_passages:ZJSHL-CH-009-P-0112"]
- `eval_seed_q078`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0120", "safe:main_passages:ZJSHL-CH-009-P-0122"]
- `eval_seed_q079`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0239", "safe:main_passages:ZJSHL-CH-009-P-0241"]
- `eval_seed_q080`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0261", "safe:main_passages:ZJSHL-CH-009-P-0263"]
- `eval_seed_q081`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0020", "safe:main_passages:ZJSHL-CH-010-P-0022"]
- `eval_seed_q082`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0172", "safe:main_passages:ZJSHL-CH-011-P-0174", "full:passages:ZJSHL-CH-011-P-0172"]
- `eval_seed_q083`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0004", "full:ambiguous_passages:ZJSHL-CH-009-P-0009"]
- `eval_seed_q084`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0093", "safe:main_passages:ZJSHL-CH-009-P-0130", "full:passages:ZJSHL-CH-009-P-0093", "full:ambiguous_passages:ZJSHL-CH-009-P-0090", "full:passages:ZJSHL-CH-009-P-0130", "full:ambiguous_passages:ZJSHL-CH-009-P-0128"]
- `eval_seed_q085`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0100", "safe:main_passages:ZJSHL-CH-025-P-0003", "safe:main_passages:ZJSHL-CH-009-P-0098", "full:passages:ZJSHL-CH-025-P-0003", "full:ambiguous_passages:ZJSHL-CH-009-P-0053"]
- `eval_seed_q086`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0110", "safe:main_passages:ZJSHL-CH-009-P-0120", "safe:main_passages:ZJSHL-CH-009-P-0118", "full:passages:ZJSHL-CH-009-P-0110", "full:ambiguous_passages:ZJSHL-CH-009-P-0108"]
- `eval_seed_q087`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0239", "safe:main_passages:ZJSHL-CH-009-P-0211"]
- `eval_seed_q088`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0020", "safe:main_passages:ZJSHL-CH-010-P-0031", "safe:main_passages:ZJSHL-CH-010-P-0017", "safe:main_passages:ZJSHL-CH-010-P-0029"]
- `eval_seed_q089`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0085", "safe:main_passages:ZJSHL-CH-027-P-0004", "safe:main_passages:ZJSHL-CH-010-P-0083", "safe:main_passages:ZJSHL-CH-010-P-0088"]
- `eval_seed_q090`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0124", "safe:main_passages:ZJSHL-CH-014-P-0129", "safe:main_passages:ZJSHL-CH-014-P-0122", "full:passages:ZJSHL-CH-014-P-0129", "full:ambiguous_passages:ZJSHL-CH-014-P-0127"]
- `eval_seed_q091`: PASS; matched=["full:annotations:ZJSHL-CH-009-P-0109", "full:passages:ZJSHL-CH-009-P-0108", "full:ambiguous_passages:ZJSHL-CH-009-P-0108", "full:passages:ZJSHL-CH-009-P-0109"]
- `eval_seed_q092`: PASS; matched=["full:annotations:ZJSHL-CH-009-P-0149", "full:passages:ZJSHL-CH-009-P-0148", "full:passages:ZJSHL-CH-009-P-0149", "full:ambiguous_passages:ZJSHL-CH-009-P-0148"]
- `eval_seed_q093`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0083"]
- `eval_seed_q094`: PASS; matched=["full:annotations:ZJSHL-CH-011-P-0103", "full:passages:ZJSHL-CH-011-P-0103"]
- `eval_seed_q095`: FAIL; matched=[]
- `eval_seed_q096`: PASS; matched=["full:passages:ZJSHL-CH-017-P-0054"]
