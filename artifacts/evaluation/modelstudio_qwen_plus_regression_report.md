# Evaluator v1 Report

## 运行信息

- generated_at_utc: `2026-04-09T08:06:55.759058+00:00`
- runner_version: `evaluator_runner_v1`
- runner_backend: `local_assembler`
- entrypoint: `backend.answers.assembler.AnswerAssembler`
- goldset: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/evaluation/goldset_v2_working_150.json`
- command: `python scripts/run_evaluator_v1.py --goldset artifacts/evaluation/goldset_v2_working_150.json --report-json artifacts/evaluation/modelstudio_qwen_plus_regression_report.json --report-md artifacts/evaluation/modelstudio_qwen_plus_regression_report.md --fail-on-evaluation-failure`
- replay_note: Default v1 path uses the local AnswerAssembler to run query -> hybrid retrieval -> evidence gating -> answer assembler without starting the HTTP transport adapter.

## 汇总

- total_questions: `150`
- mode_match_count: `150/150`
- mode_match_rate: `1.0`
- citation_check_required_basic_pass: `120/120`
- failure_count: `0`
- all_checks_passed: `True`
- type_counts: `{"comparison": 30, "general_overview": 20, "meaning_explanation": 30, "refusal": 30, "source_lookup": 40}`
- expected_mode_counts: `{"refuse": 30, "strong": 95, "weak_with_review_notice": 25}`
- actual_mode_counts: `{"refuse": 30, "strong": 95, "weak_with_review_notice": 25}`

## 题型统计

| question_type | total | mode_match | citation_required | citation_basic_pass | failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| `comparison` | 30 | 30 | 30 | 30 | 0 |
| `general_overview` | 20 | 20 | 20 | 20 | 0 |
| `meaning_explanation` | 30 | 30 | 30 | 30 | 0 |
| `refusal` | 30 | 30 | 0 | 0 | 0 |
| `source_lookup` | 40 | 40 | 40 | 40 | 0 |

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
| `eval_seed_q076` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q077` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q078` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q079` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q080` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q081` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q082` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
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
| `eval_seed_q093` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 8 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q094` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q095` | `general_overview` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q096` | `general_overview` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q097` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q098` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q099` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q100` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q101` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q102` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q103` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q104` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q105` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q106` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q107` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q108` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q109` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q110` | `comparison` | `strong` | `strong` | PASS | 6 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q111` | `comparison` | `strong` | `strong` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q112` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q113` | `meaning_explanation` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q114` | `meaning_explanation` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q115` | `meaning_explanation` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q116` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q117` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q118` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q119` | `general_overview` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q120` | `general_overview` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q121` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q122` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q123` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q124` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q125` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q126` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q127` | `source_lookup` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q128` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q129` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q130` | `source_lookup` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q131` | `source_lookup` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q132` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q133` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q134` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q135` | `comparison` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q136` | `comparison` | `strong` | `strong` | PASS | 5 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q137` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q138` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q139` | `meaning_explanation` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q140` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q141` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q142` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q143` | `general_overview` | `strong` | `strong` | PASS | 4 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q144` | `general_overview` | `strong` | `strong` | PASS | 3 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q145` | `general_overview` | `strong` | `strong` | PASS | 2 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q146` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q147` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q148` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q149` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |
| `eval_seed_q150` | `refusal` | `refuse` | `refuse` | PASS | 0 | PASS | PASS | PASS | PASS | PASS |

## 失败样本

_No failed samples._

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
- `eval_seed_q082`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0172", "safe:main_passages:ZJSHL-CH-011-P-0174"]
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
- `eval_seed_q093`: PASS; matched=["full:annotations:ZJSHL-CH-010-P-0084", "safe:main_passages:ZJSHL-CH-010-P-0083", "full:passages:ZJSHL-CH-010-P-0083", "full:passages:ZJSHL-CH-010-P-0084"]
- `eval_seed_q094`: PASS; matched=["full:annotations:ZJSHL-CH-011-P-0103", "full:passages:ZJSHL-CH-011-P-0103"]
- `eval_seed_q095`: PASS; matched=["safe:main_passages:ZJSHL-CH-012-P-0219", "safe:main_passages:ZJSHL-CH-012-P-0215"]
- `eval_seed_q096`: PASS; matched=["safe:main_passages:ZJSHL-CH-017-P-0063", "safe:main_passages:ZJSHL-CH-017-P-0048", "safe:main_passages:ZJSHL-CH-017-P-0056", "safe:main_passages:ZJSHL-CH-017-P-0061"]
- `eval_seed_q103`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0145"]
- `eval_seed_q104`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0125"]
- `eval_seed_q105`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0140"]
- `eval_seed_q106`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0153", "safe:main_passages:ZJSHL-CH-010-P-0154", "safe:main_passages:ZJSHL-CH-010-P-0156"]
- `eval_seed_q107`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0134"]
- `eval_seed_q108`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0140", "safe:main_passages:ZJSHL-CH-027-P-0011", "safe:main_passages:ZJSHL-CH-027-P-0011", "safe:main_passages:ZJSHL-CH-010-P-0142"]
- `eval_seed_q109`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0153", "safe:main_passages:ZJSHL-CH-010-P-0159", "safe:main_passages:ZJSHL-CH-010-P-0149"]
- `eval_seed_q110`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0064", "safe:main_passages:ZJSHL-CH-014-P-0069", "full:passages:ZJSHL-CH-014-P-0064", "full:passages:ZJSHL-CH-014-P-0069"]
- `eval_seed_q111`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0134", "safe:main_passages:ZJSHL-CH-014-P-0081", "full:passages:ZJSHL-CH-014-P-0134"]
- `eval_seed_q112`: PASS; matched=["safe:main_passages:ZJSHL-CH-009-P-0315", "safe:main_passages:ZJSHL-CH-009-P-0322", "safe:main_passages:ZJSHL-CH-009-P-0318", "safe:main_passages:ZJSHL-CH-009-P-0320"]
- `eval_seed_q113`: PASS; matched=["safe:main_passages:ZJSHL-CH-003-P-0004"]
- `eval_seed_q114`: PASS; matched=["safe:main_passages:ZJSHL-CH-003-P-0006"]
- `eval_seed_q115`: PASS; matched=["safe:main_passages:ZJSHL-CH-017-P-0049"]
- `eval_seed_q116`: PASS; matched=["full:annotations:ZJSHL-CH-010-P-0136", "full:passages:ZJSHL-CH-010-P-0136", "full:passages:ZJSHL-CH-009-P-0210", "full:ambiguous_passages:ZJSHL-CH-009-P-0210"]
- `eval_seed_q117`: PASS; matched=["full:passages:ZJSHL-CH-010-P-0026", "full:ambiguous_passages:ZJSHL-CH-010-P-0026"]
- `eval_seed_q118`: PASS; matched=["full:annotations:ZJSHL-CH-015-P-0279", "full:passages:ZJSHL-CH-015-P-0277"]
- `eval_seed_q119`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0002", "safe:main_passages:ZJSHL-CH-010-P-0008", "safe:main_passages:ZJSHL-CH-010-P-0029", "safe:main_passages:ZJSHL-CH-009-P-0312"]
- `eval_seed_q120`: PASS; matched=["safe:main_passages:ZJSHL-CH-008-P-0215", "safe:main_passages:ZJSHL-CH-010-P-0075"]
- `eval_seed_q121`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0099", "safe:main_passages:ZJSHL-CH-014-P-0105", "safe:main_passages:ZJSHL-CH-004-P-0165"]
- `eval_seed_q127`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0170", "safe:main_passages:ZJSHL-CH-010-P-0171", "safe:main_passages:ZJSHL-CH-010-P-0173"]
- `eval_seed_q128`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0158", "safe:main_passages:ZJSHL-CH-011-P-0160"]
- `eval_seed_q129`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0074"]
- `eval_seed_q130`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0090"]
- `eval_seed_q131`: PASS; matched=["safe:main_passages:ZJSHL-CH-015-P-0309", "safe:main_passages:ZJSHL-CH-015-P-0311"]
- `eval_seed_q132`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0010", "safe:main_passages:ZJSHL-CH-010-P-0020", "safe:main_passages:ZJSHL-CH-010-P-0008", "safe:main_passages:ZJSHL-CH-010-P-0017"]
- `eval_seed_q133`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0074", "safe:main_passages:ZJSHL-CH-014-P-0090", "safe:main_passages:ZJSHL-CH-014-P-0072", "safe:main_passages:ZJSHL-CH-014-P-0093"]
- `eval_seed_q134`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0101", "safe:main_passages:ZJSHL-CH-014-P-0109", "safe:main_passages:ZJSHL-CH-014-P-0099", "safe:main_passages:ZJSHL-CH-014-P-0105"]
- `eval_seed_q135`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0150", "safe:main_passages:ZJSHL-CH-008-P-0267"]
- `eval_seed_q136`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0170", "safe:main_passages:ZJSHL-CH-009-P-0105", "safe:main_passages:ZJSHL-CH-010-P-0168", "full:passages:ZJSHL-CH-009-P-0105", "full:ambiguous_passages:ZJSHL-CH-009-P-0103"]
- `eval_seed_q137`: PASS; matched=["safe:main_passages:ZJSHL-CH-003-P-0002"]
- `eval_seed_q138`: PASS; matched=["safe:main_passages:ZJSHL-CH-004-P-0178"]
- `eval_seed_q139`: PASS; matched=["safe:main_passages:ZJSHL-CH-016-P-0002"]
- `eval_seed_q140`: PASS; matched=["full:annotations:ZJSHL-CH-004-P-0181", "safe:main_passages:ZJSHL-CH-004-P-0180", "full:passages:ZJSHL-CH-004-P-0181", "full:passages:ZJSHL-CH-004-P-0180"]
- `eval_seed_q141`: PASS; matched=["full:annotations:ZJSHL-CH-004-P-0179", "full:passages:ZJSHL-CH-004-P-0179"]
- `eval_seed_q142`: PASS; matched=["full:annotations:ZJSHL-CH-010-P-0004", "safe:main_passages:ZJSHL-CH-010-P-0005", "full:passages:ZJSHL-CH-010-P-0004"]
- `eval_seed_q143`: PASS; matched=["safe:main_passages:ZJSHL-CH-010-P-0083", "safe:main_passages:ZJSHL-CH-010-P-0088", "safe:main_passages:ZJSHL-CH-010-P-0111", "safe:main_passages:ZJSHL-CH-010-P-0090"]
- `eval_seed_q144`: PASS; matched=["safe:main_passages:ZJSHL-CH-011-P-0202", "safe:main_passages:ZJSHL-CH-009-P-0318", "safe:main_passages:ZJSHL-CH-009-P-0233"]
- `eval_seed_q145`: PASS; matched=["safe:main_passages:ZJSHL-CH-014-P-0093", "safe:main_passages:ZJSHL-CH-015-P-0232"]
