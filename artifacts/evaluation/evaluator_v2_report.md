# Evaluator v2 Report

## 运行信息

- generated_at_utc: `2026-04-10T01:42:37.478887+00:00`
- runner_version: `evaluator_runner_v2_skeleton`
- runner_backend: `local_assembler`
- goldset: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/evaluation/goldset_v2_working_150.json`
- command: `python scripts/run_evaluator_v2.py --fail-on-evaluation-failure`
- notes: v2 keeps v1 enforced checks, adds retrieval diagnostics and failure taxonomy, and now carries a sampled answer_text review summary when the review artifact is present. Latency benchmark artifacts are still not included.

## 汇总

- total_questions: `150`
- mode_match_count: `150/150`
- citation_basic_pass_count: `120`
- failure_count: `0`
- all_checks_passed: `True`

## Retrieval Metrics

- top_k_values: `[1, 3, 5, 10]`

### Aggregate

| metric | K | hit_count | hit_rate |
| --- | ---: | ---: | ---: |
| `fused_hit_at_k` | 1 | 73 | 0.6083 |
| `fused_hit_at_k` | 3 | 109 | 0.9083 |
| `fused_hit_at_k` | 5 | 113 | 0.9417 |
| `fused_hit_at_k` | 10 | 119 | 0.9917 |
| `rerank_hit_at_k` | 1 | 58 | 0.4833 |
| `rerank_hit_at_k` | 3 | 107 | 0.8917 |
| `rerank_hit_at_k` | 5 | 114 | 0.95 |
| `rerank_hit_at_k` | 10 | 117 | 0.975 |

### By Question Type

| question_type | total | fused@1 | fused@3 | fused@5 | fused@10 | rerank@1 | rerank@3 | rerank@5 | rerank@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `comparison` | 30 | 26 (0.8667) | 30 (1.0) | 30 (1.0) | 30 (1.0) | 16 (0.5333) | 29 (0.9667) | 29 (0.9667) | 30 (1.0) |
| `general_overview` | 20 | 0 (0.0) | 9 (0.45) | 13 (0.65) | 19 (0.95) | 2 (0.1) | 15 (0.75) | 17 (0.85) | 19 (0.95) |
| `meaning_explanation` | 30 | 18 (0.6) | 30 (1.0) | 30 (1.0) | 30 (1.0) | 23 (0.7667) | 30 (1.0) | 30 (1.0) | 30 (1.0) |
| `refusal` | 30 | 0 (0.0) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 0 (0.0) |
| `source_lookup` | 40 | 29 (0.725) | 40 (1.0) | 40 (1.0) | 40 (1.0) | 17 (0.425) | 33 (0.825) | 38 (0.95) | 38 (0.95) |

### Rerank Delta

- count_with_gold_before_rerank: `120`
- improved_count: `19`
- unchanged_count: `71`
- worsened_count: `30`

## Answer_text Review

- enabled: `True`
- sample_count: `7`
- rubric_dimensions: `["clarity", "structure", "evidence_faithfulness", "mode_boundary_preservation"]`
- summary_notes: Sampled manual review on 7 current evaluator_v2 answers found 2 style-only answer_text_quality_issue candidates (eval_seed_q002 and eval_seed_q005) and 0 boundary-affecting candidates. Main gaps cluster in quote-heavy weak answers and broad general_overview answers whose structure is usable but still not compact enough. Source_lookup, comparison, and refuse samples are comparatively stable. This sample is sufficient to scope the next prompt/answer_text optimization pass, but not sufficient to claim full 150-sample quality improvements.
- artifact_path: `/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/evaluation/answer_text_review_report_v1.md`

## Failure Taxonomy

- items_with_failures: `3`

### Category Counts

| category | count |
| --- | ---: |
| `retrieval_failure` | 4 |
| `citation_failure` | 0 |
| `answer_mode_failure` | 0 |
| `evidence_layering_failure` | 0 |
| `unsupported_assertion_failure` | 0 |
| `answer_text_quality_issue` | 0 |
| `llm_runtime_issue` | 0 |
| `latency_issue` | 0 |

### Subcategory Counts

| subcategory | count |
| --- | ---: |
| `gold_miss_in_fused_topk` | 1 |
| `gold_miss_after_rerank` | 3 |
| `citation_not_in_gold` | 0 |
| `expected_weak_but_actual_strong` | 0 |
| `expected_refuse_but_not_refuse` | 0 |
| `mode_mismatch_other` | 0 |
| `primary_should_be_empty` | 0 |
| `evidence_should_be_zero` | 0 |
| `citations_should_be_zero` | 0 |
| `strong_without_gold_evidence` | 0 |
| `clarity_low` | 0 |
| `structure_low` | 0 |
| `evidence_faithfulness_low` | 0 |
| `mode_boundary_broken` | 0 |
| `llm_fallback_triggered` | 0 |
| `llm_validator_reject` | 0 |
| `latency_over_threshold` | 0 |

## 逐题结果

| question_id | type | expected | actual | mode | citations | fused_rank | rerank_rank | delta | taxonomy |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `eval_seed_q001` | `source_lookup` | `strong` | `strong` | PASS | 3 | 1 | 12 | 11 | 1 |
| `eval_seed_q002` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 5 | 1 | 1 | 0 | 0 |
| `eval_seed_q003` | `general_overview` | `strong` | `strong` | PASS | 3 | 5 | 3 | -2 | 0 |
| `eval_seed_q004` | `general_overview` | `strong` | `strong` | PASS | 3 | 9 | 2 | -7 | 0 |
| `eval_seed_q005` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | 2 | 3 | 1 | 0 |
| `eval_seed_q006` | `comparison` | `strong` | `strong` | PASS | 5 | 2 | 2 | 0 | 0 |
| `eval_seed_q007` | `comparison` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | 2 | 2 | 0 | 0 |
| `eval_seed_q008` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q009` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q010` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 3 | 2 | 0 |
| `eval_seed_q011` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q012` | `source_lookup` | `strong` | `strong` | PASS | 3 | 1 | 3 | 2 | 0 |
| `eval_seed_q013` | `source_lookup` | `strong` | `strong` | PASS | 3 | 1 | 3 | 2 | 0 |
| `eval_seed_q014` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q015` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q016` | `source_lookup` | `strong` | `strong` | PASS | 1 | 2 | 2 | 0 | 0 |
| `eval_seed_q017` | `source_lookup` | `strong` | `strong` | PASS | 1 | 2 | 2 | 0 | 0 |
| `eval_seed_q018` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q019` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q020` | `source_lookup` | `strong` | `strong` | PASS | 3 | 1 | 1 | 0 | 0 |
| `eval_seed_q021` | `source_lookup` | `strong` | `strong` | PASS | 1 | 2 | 2 | 0 | 0 |
| `eval_seed_q022` | `source_lookup` | `strong` | `strong` | PASS | 1 | 2 | 2 | 0 | 0 |
| `eval_seed_q023` | `source_lookup` | `strong` | `strong` | PASS | 3 | 1 | 14 | 13 | 1 |
| `eval_seed_q024` | `source_lookup` | `strong` | `strong` | PASS | 3 | 1 | 2 | 1 | 0 |
| `eval_seed_q025` | `source_lookup` | `strong` | `strong` | PASS | 3 | 1 | 1 | 0 | 0 |
| `eval_seed_q026` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 2 | 1 | 0 |
| `eval_seed_q027` | `source_lookup` | `strong` | `strong` | PASS | 1 | 2 | 4 | 2 | 0 |
| `eval_seed_q028` | `source_lookup` | `strong` | `strong` | PASS | 1 | 2 | 2 | 0 | 0 |
| `eval_seed_q029` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 3 | 1 | 1 | 0 | 0 |
| `eval_seed_q030` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | 1 | 1 | 0 | 0 |
| `eval_seed_q031` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | 1 | 1 | 0 | 0 |
| `eval_seed_q032` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q033` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | 1 | 1 | 0 | 0 |
| `eval_seed_q034` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | 2 | 1 | -1 | 0 |
| `eval_seed_q035` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | 2 | 1 | -1 | 0 |
| `eval_seed_q036` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | 2 | 1 | -1 | 0 |
| `eval_seed_q037` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q038` | `meaning_explanation` | `strong` | `strong` | PASS | 2 | 2 | 2 | 0 | 0 |
| `eval_seed_q039` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 5 | 1 | 1 | 0 | 0 |
| `eval_seed_q040` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | 1 | 1 | 0 | 0 |
| `eval_seed_q041` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 5 | 1 | 1 | 0 | 0 |
| `eval_seed_q042` | `general_overview` | `strong` | `strong` | PASS | 3 | 8 | 4 | -4 | 0 |
| `eval_seed_q043` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 8 | 3 | 2 | -1 | 0 |
| `eval_seed_q044` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 8 | 2 | 1 | -1 | 0 |
| `eval_seed_q045` | `general_overview` | `strong` | `strong` | PASS | 3 | 3 | 1 | -2 | 0 |
| `eval_seed_q046` | `general_overview` | `strong` | `strong` | PASS | 3 | 4 | 2 | -2 | 0 |
| `eval_seed_q047` | `general_overview` | `strong` | `strong` | PASS | 4 | 2 | 2 | 0 | 0 |
| `eval_seed_q048` | `general_overview` | `strong` | `strong` | PASS | 4 | 6 | 7 | 1 | 0 |
| `eval_seed_q049` | `general_overview` | `strong` | `strong` | PASS | 4 | 9 | 3 | -6 | 0 |
| `eval_seed_q050` | `general_overview` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 2 | 2 | 2 | 0 | 0 |
| `eval_seed_q051` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 6 | 5 | 0 |
| `eval_seed_q052` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q053` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q054` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 2 | 1 | 0 |
| `eval_seed_q055` | `comparison` | `strong` | `strong` | PASS | 4 | 2 | 2 | 0 | 0 |
| `eval_seed_q056` | `comparison` | `strong` | `strong` | PASS | 5 | 1 | 2 | 1 | 0 |
| `eval_seed_q057` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q058` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 2 | 1 | 0 |
| `eval_seed_q059` | `comparison` | `strong` | `strong` | PASS | 6 | 1 | 2 | 1 | 0 |
| `eval_seed_q060` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 2 | 1 | 0 |
| `eval_seed_q061` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q062` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q063` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q064` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q065` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q066` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q067` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q068` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q069` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q070` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q071` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q072` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q073` | `source_lookup` | `strong` | `strong` | PASS | 3 | 3 | 1 | -2 | 0 |
| `eval_seed_q074` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 2 | 1 | 0 |
| `eval_seed_q075` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 2 | 1 | 0 |
| `eval_seed_q076` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q077` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q078` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q079` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 4 | 3 | 0 |
| `eval_seed_q080` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 3 | 2 | 0 |
| `eval_seed_q081` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q082` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q083` | `comparison` | `strong` | `strong` | PASS | 5 | 1 | 2 | 1 | 0 |
| `eval_seed_q084` | `comparison` | `strong` | `strong` | PASS | 6 | 1 | 1 | 0 | 0 |
| `eval_seed_q085` | `comparison` | `strong` | `strong` | PASS | 5 | 1 | 1 | 0 | 0 |
| `eval_seed_q086` | `comparison` | `strong` | `strong` | PASS | 5 | 1 | 1 | 0 | 0 |
| `eval_seed_q087` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q088` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q089` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q090` | `comparison` | `strong` | `strong` | PASS | 5 | 1 | 1 | 0 | 0 |
| `eval_seed_q091` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q092` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q093` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 8 | 2 | 2 | 0 | 0 |
| `eval_seed_q094` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q095` | `general_overview` | `strong` | `strong` | PASS | 2 | 16 | 13 | -3 | 2 |
| `eval_seed_q096` | `general_overview` | `strong` | `strong` | PASS | 4 | 7 | 3 | -4 | 0 |
| `eval_seed_q097` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q098` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q099` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q100` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q101` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q102` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q103` | `source_lookup` | `strong` | `strong` | PASS | 1 | 2 | 2 | 0 | 0 |
| `eval_seed_q104` | `source_lookup` | `strong` | `strong` | PASS | 1 | 2 | 4 | 2 | 0 |
| `eval_seed_q105` | `source_lookup` | `strong` | `strong` | PASS | 1 | 2 | 2 | 0 | 0 |
| `eval_seed_q106` | `source_lookup` | `strong` | `strong` | PASS | 3 | 1 | 1 | 0 | 0 |
| `eval_seed_q107` | `source_lookup` | `strong` | `strong` | PASS | 1 | 1 | 1 | 0 | 0 |
| `eval_seed_q108` | `comparison` | `strong` | `strong` | PASS | 4 | 2 | 2 | 0 | 0 |
| `eval_seed_q109` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 2 | 1 | 0 |
| `eval_seed_q110` | `comparison` | `strong` | `strong` | PASS | 6 | 1 | 1 | 0 | 0 |
| `eval_seed_q111` | `comparison` | `strong` | `strong` | PASS | 5 | 1 | 1 | 0 | 0 |
| `eval_seed_q112` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q113` | `meaning_explanation` | `strong` | `strong` | PASS | 3 | 2 | 3 | 1 | 0 |
| `eval_seed_q114` | `meaning_explanation` | `strong` | `strong` | PASS | 3 | 2 | 1 | -1 | 0 |
| `eval_seed_q115` | `meaning_explanation` | `strong` | `strong` | PASS | 3 | 2 | 2 | 0 | 0 |
| `eval_seed_q116` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q117` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 6 | 1 | 1 | 0 | 0 |
| `eval_seed_q118` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q119` | `general_overview` | `strong` | `strong` | PASS | 4 | 2 | 2 | 0 | 0 |
| `eval_seed_q120` | `general_overview` | `strong` | `strong` | PASS | 2 | 2 | 2 | 0 | 0 |
| `eval_seed_q121` | `general_overview` | `strong` | `strong` | PASS | 3 | 6 | 2 | -4 | 0 |
| `eval_seed_q122` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q123` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q124` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q125` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q126` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q127` | `source_lookup` | `strong` | `strong` | PASS | 3 | 1 | 4 | 3 | 0 |
| `eval_seed_q128` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q129` | `source_lookup` | `strong` | `strong` | PASS | 1 | 1 | 1 | 0 | 0 |
| `eval_seed_q130` | `source_lookup` | `strong` | `strong` | PASS | 1 | 2 | 2 | 0 | 0 |
| `eval_seed_q131` | `source_lookup` | `strong` | `strong` | PASS | 2 | 1 | 4 | 3 | 0 |
| `eval_seed_q132` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q133` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 2 | 1 | 0 |
| `eval_seed_q134` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 1 | 0 | 0 |
| `eval_seed_q135` | `comparison` | `strong` | `strong` | PASS | 4 | 1 | 2 | 1 | 0 |
| `eval_seed_q136` | `comparison` | `strong` | `strong` | PASS | 5 | 1 | 1 | 0 | 0 |
| `eval_seed_q137` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | 2 | 2 | 0 | 0 |
| `eval_seed_q138` | `meaning_explanation` | `strong` | `strong` | PASS | 1 | 2 | 2 | 0 | 0 |
| `eval_seed_q139` | `meaning_explanation` | `strong` | `strong` | PASS | 3 | 3 | 1 | -2 | 0 |
| `eval_seed_q140` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 4 | 2 | 1 | -1 | 0 |
| `eval_seed_q141` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 2 | 1 | 1 | 0 | 0 |
| `eval_seed_q142` | `meaning_explanation` | `weak_with_review_notice` | `weak_with_review_notice` | PASS | 3 | 1 | 2 | 1 | 0 |
| `eval_seed_q143` | `general_overview` | `strong` | `strong` | PASS | 4 | 2 | 2 | 0 | 0 |
| `eval_seed_q144` | `general_overview` | `strong` | `strong` | PASS | 3 | 5 | 4 | -1 | 0 |
| `eval_seed_q145` | `general_overview` | `strong` | `strong` | PASS | 2 | 5 | 9 | 4 | 0 |
| `eval_seed_q146` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q147` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q148` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q149` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |
| `eval_seed_q150` | `refusal` | `refuse` | `refuse` | PASS | 0 | - | - | - | 0 |

## 失败样本

### eval_seed_q001

- query: 黄连汤方的条文是什么？
- question_type: `source_lookup`
- failed_checks: `[]`
- failure_taxonomy: `[{"category": "retrieval_failure", "subcategory": "gold_miss_after_rerank", "severity": "error", "notes": "Gold evidence not found after rerank within top 10."}]`

### eval_seed_q023

- query: 四逆汤方的条文是什么？
- question_type: `source_lookup`
- failed_checks: `[]`
- failure_taxonomy: `[{"category": "retrieval_failure", "subcategory": "gold_miss_after_rerank", "severity": "error", "notes": "Gold evidence not found after rerank within top 10."}]`

### eval_seed_q095

- query: 少阳病有哪些核心表现和处理边界？
- question_type: `general_overview`
- failed_checks: `[]`
- failure_taxonomy: `[{"category": "retrieval_failure", "subcategory": "gold_miss_in_fused_topk", "severity": "error", "notes": "Gold evidence not found in fused top 10."}, {"category": "retrieval_failure", "subcategory": "gold_miss_after_rerank", "severity": "error", "notes": "Gold evidence not found after rerank within top 10."}]`


## Scope Notes

- 本轮 v2 skeleton 保留了 v1 的 mode / citation / unsupported assertion 检查。
- 本轮已接入 retrieval 指标字段与 failure taxonomy 字段。
- `answer_text_quality_review` 已以 sampled manual review 形态接入，但仍属于诊断层，不影响 failure_count 或退出码。
- `latency_benchmark` 仍为后续轮次范围，本报告中未实际填充。
