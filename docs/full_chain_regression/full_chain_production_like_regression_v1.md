# Full Chain Production-like Regression v1

## Scope

This run evaluates whether prior data-plane upgrades still hold after rerank, assembler slotting, citations, and LLM answer_text rendering. It does not add AHV3 objects, change prompts, change frontend code, change API payload contract, or reopen raw full passages into primary evidence.

## Mode Completion

| mode | status | reason |
| --- | --- | --- |
| A_data_plane_baseline | completed |  |
| B_retrieval_rerank | completed |  |
| C_production_like_full_chain | completed |  |

## Quantitative Metrics

| metric | value |
| --- | --- |
| query_count | 120 |
| run_mode_count | 3 |
| pass_count_by_mode | {"A_data_plane_baseline": 109, "B_retrieval_rerank": 107, "C_production_like_full_chain": 107} |
| fail_count_by_mode | {"A_data_plane_baseline": 11, "B_retrieval_rerank": 13, "C_production_like_full_chain": 13} |
| forbidden_primary_total | 0 |
| formula_bad_anchor_total | 0 |
| review_only_primary_conflict_total | 0 |
| wrong_definition_primary_total | 0 |
| non_definition_intent_hijack_total | 0 |
| rerank_regression_count | 2 |
| llm_faithfulness_error_count | 0 |
| answer_mode_calibration_error_count | 12 |
| citation_error_count | 3 |
| p0_repair_count | 4 |
| p1_repair_count | 3 |
| latency_p50_by_mode | {"A_data_plane_baseline": 39.291, "B_retrieval_rerank": 586.909, "C_production_like_full_chain": 8654.537} |
| latency_p95_by_mode | {"A_data_plane_baseline": 473.935, "B_retrieval_rerank": 1660.059, "C_production_like_full_chain": 21417.208} |

## Major Failure Types

| failure_type | count |
| --- | --- |
| answer_mode_calibration_error | 12 |
| assembler_slot_error | 3 |
| citation_error | 3 |
| data_layer_bad_alias | 6 |
| negative_query_false_positive | 1 |
| rerank_regression | 2 |
| retrieval_miss | 3 |
| review_only_boundary_error | 7 |

## P0 Immediate Data-layer Repairs

| query_id | mode | failure_type | query | next_action |
| --- | --- | --- | --- | --- |
| review_only_boundary_08 | C_production_like_full_chain | review_only_boundary_error | 清邪中上是什么意思？ | Audit term_alias_registry and learner_query_normalization_lexicon for active review-only surfaces; keep object out of retrieval_ready_definition_view. |
| review_only_boundary_10 | C_production_like_full_chain | review_only_boundary_error | 反是什么意思？ | Audit term_alias_registry and learner_query_normalization_lexicon for active review-only surfaces; keep object out of retrieval_ready_definition_view. |
| review_only_boundary_04 | C_production_like_full_chain | review_only_boundary_error | 两阳是什么意思？ | Audit term_alias_registry and learner_query_normalization_lexicon for active review-only surfaces; keep object out of retrieval_ready_definition_view. |
| negative_modern_09 | C_production_like_full_chain | negative_query_false_positive | 白虎是什么意思？ | Add or tighten alias/intent guard so modern false-friend query does not select book primary evidence. |

## P1 Next Batch Data-layer Repairs

| query_id | mode | failure_type | query | next_action |
| --- | --- | --- | --- | --- |
| formula_07 | C_production_like_full_chain | data_layer_bad_alias | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | Audit exact alias coverage for the expected formula/definition object without adding broad contains surfaces. |
| formula_18 | C_production_like_full_chain | data_layer_bad_alias | 麻黄汤方和桂枝汤方的区别是什么？ | Audit exact alias coverage for the expected formula/definition object without adding broad contains surfaces. |
| learner_short_21 | C_production_like_full_chain | retrieval_miss | 干呕是什么意思？ | Check whether a learner-safe definition/explanation object exists; if not, queue object/span audit rather than reopening raw full passages. |

## P2 Observations

| query_id | mode | failure_type | query | next_action |
| --- | --- | --- | --- | --- |
| ahv2_canonical_02 | C_production_like_full_chain | assembler_slot_error | 少阴病是什么意思 | Manual audit: inspect primary/secondary/review slots and decide whether this is data-layer, rerank, assembler, or LLM work. |
| cross_batch_adversarial_10 | C_production_like_full_chain | answer_mode_calibration_error | 半表半里证和过经有什么不同 | Manual audit: inspect primary/secondary/review slots and decide whether this is data-layer, rerank, assembler, or LLM work. |
| cross_batch_adversarial_12 | C_production_like_full_chain | answer_mode_calibration_error | 荣气微和卫气衰有什么区别 | Manual audit: inspect primary/secondary/review slots and decide whether this is data-layer, rerank, assembler, or LLM work. |
| cross_batch_adversarial_15 | C_production_like_full_chain | answer_mode_calibration_error | 霍乱和伤寒有什么区别 | Manual audit: inspect primary/secondary/review slots and decide whether this is data-layer, rerank, assembler, or LLM work. |
| cross_batch_adversarial_18 | C_production_like_full_chain | answer_mode_calibration_error | 痓病和太阳病有什么不同 | Manual audit: inspect primary/secondary/review slots and decide whether this is data-layer, rerank, assembler, or LLM work. |
| formula_04 | C_production_like_full_chain | citation_error | 白虎汤方和白虎加人参汤方的区别是什么？ | Inspect citation slot normalization for this branch; do not change evidence eligibility until citation mismatch is localized. |
| review_only_boundary_04 | B_retrieval_rerank | rerank_regression | 两阳是什么意思？ | Compare A/B raw and rerank top candidates; preserve safe object priority through rerank or assembler slot selection. |
| negative_modern_09 | B_retrieval_rerank | rerank_regression | 白虎是什么意思？ | Compare A/B raw and rerank top candidates; preserve safe object priority through rerank or assembler slot selection. |

## Artifact Index

- `artifacts/full_chain_regression/full_chain_query_set_v1.json`
- `artifacts/full_chain_regression/full_chain_regression_results_v1.json`
- `artifacts/full_chain_regression/full_chain_failure_cases_v1.json`
- `artifacts/full_chain_regression/data_layer_repair_queue_v1.json`
- `artifacts/full_chain_regression/latency_snapshot_v1.json`
