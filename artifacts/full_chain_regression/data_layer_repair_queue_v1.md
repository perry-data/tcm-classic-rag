# Data Layer Repair Queue v1

- p0_repair_count: `4`
- p1_repair_count: `3`
- p2_observation_count: `8`

## P0

| query_id | mode | failure_type | query | next_action |
| --- | --- | --- | --- | --- |
| review_only_boundary_08 | C_production_like_full_chain | review_only_boundary_error | 清邪中上是什么意思？ | Audit term_alias_registry and learner_query_normalization_lexicon for active review-only surfaces; keep object out of retrieval_ready_definition_view. |
| review_only_boundary_10 | C_production_like_full_chain | review_only_boundary_error | 反是什么意思？ | Audit term_alias_registry and learner_query_normalization_lexicon for active review-only surfaces; keep object out of retrieval_ready_definition_view. |
| review_only_boundary_04 | C_production_like_full_chain | review_only_boundary_error | 两阳是什么意思？ | Audit term_alias_registry and learner_query_normalization_lexicon for active review-only surfaces; keep object out of retrieval_ready_definition_view. |
| negative_modern_09 | C_production_like_full_chain | negative_query_false_positive | 白虎是什么意思？ | Add or tighten alias/intent guard so modern false-friend query does not select book primary evidence. |

## P1

| query_id | mode | failure_type | query | next_action |
| --- | --- | --- | --- | --- |
| formula_07 | C_production_like_full_chain | data_layer_bad_alias | 桂枝加附子汤方和桂枝加厚朴杏子汤方的区别是什么？ | Audit exact alias coverage for the expected formula/definition object without adding broad contains surfaces. |
| formula_18 | C_production_like_full_chain | data_layer_bad_alias | 麻黄汤方和桂枝汤方的区别是什么？ | Audit exact alias coverage for the expected formula/definition object without adding broad contains surfaces. |
| learner_short_21 | C_production_like_full_chain | retrieval_miss | 干呕是什么意思？ | Check whether a learner-safe definition/explanation object exists; if not, queue object/span audit rather than reopening raw full passages. |

## P2

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
