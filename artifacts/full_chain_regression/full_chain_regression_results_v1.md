# Full Chain Regression Results v1

- run_id: `full_chain_production_like_regression_v1`
- query_count: `120`
- run_mode_count: `3`

## Mode Status

| mode | status | reason |
| --- | --- | --- |
| A_data_plane_baseline | completed |  |
| B_retrieval_rerank | completed |  |
| C_production_like_full_chain | completed |  |

## Metrics

| metric | value |
| --- | --- |
| query_count | 120 |
| run_mode_count | 3 |
| completed_modes | ["A_data_plane_baseline", "B_retrieval_rerank", "C_production_like_full_chain"] |
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
| failure_type_counts | {"answer_mode_calibration_error": 12, "assembler_slot_error": 3, "citation_error": 3, "data_layer_bad_alias": 6, "negative_query_false_positive": 1, "rerank_regression": 2, "retrieval_miss": 3, "review_only_boundary_error": 7} |
| p0_repair_count | 4 |
| p1_repair_count | 3 |
| p2_observation_count | 8 |
| latency_p50_by_mode | {"A_data_plane_baseline": 39.291, "B_retrieval_rerank": 586.909, "C_production_like_full_chain": 8654.537} |
| latency_p95_by_mode | {"A_data_plane_baseline": 473.935, "B_retrieval_rerank": 1660.059, "C_production_like_full_chain": 21417.208} |

## Failed Records

| mode | query_id | category | answer_mode | failure_type | reasons |
| --- | --- | --- | --- | --- | --- |
| A_data_plane_baseline | ahv2_canonical_02 | ahv2_canonical | strong | assembler_slot_error | canonical definition primary does not contain expected concept |
| A_data_plane_baseline | cross_batch_adversarial_10 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| A_data_plane_baseline | cross_batch_adversarial_12 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| A_data_plane_baseline | cross_batch_adversarial_15 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| A_data_plane_baseline | cross_batch_adversarial_18 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| A_data_plane_baseline | formula_04 | formula | strong | citation_error | fail: strong citations are not limited to primary evidence |
| A_data_plane_baseline | formula_07 | formula | strong | data_layer_bad_alias | fail: strong citations are not limited to primary evidence; formula normalization/raw candidates missed one or more expected formulas |
| A_data_plane_baseline | formula_18 | formula | strong | data_layer_bad_alias | fail: strong citations are not limited to primary evidence; formula normalization/raw candidates missed one or more expected formulas |
| A_data_plane_baseline | learner_short_21 | learner_short_normal | refuse | retrieval_miss | normal learner query refused instead of offering a conservative book-grounded answer |
| A_data_plane_baseline | review_only_boundary_08 | review_only_support_boundary | strong | review_only_boundary_error | review-only/support-only boundary query produced strong answer; review-only/support-only surface appears in primary evidence |
| A_data_plane_baseline | review_only_boundary_10 | review_only_support_boundary | strong | review_only_boundary_error | review-only/support-only boundary query produced strong answer |
| B_retrieval_rerank | ahv2_canonical_02 | ahv2_canonical | strong | assembler_slot_error | canonical definition primary does not contain expected concept |
| B_retrieval_rerank | cross_batch_adversarial_10 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| B_retrieval_rerank | cross_batch_adversarial_12 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| B_retrieval_rerank | cross_batch_adversarial_15 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| B_retrieval_rerank | cross_batch_adversarial_18 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| B_retrieval_rerank | formula_04 | formula | strong | citation_error | fail: strong citations are not limited to primary evidence |
| B_retrieval_rerank | formula_07 | formula | strong | data_layer_bad_alias | fail: strong citations are not limited to primary evidence; formula normalization/raw candidates missed one or more expected formulas |
| B_retrieval_rerank | formula_18 | formula | strong | data_layer_bad_alias | fail: strong citations are not limited to primary evidence; formula normalization/raw candidates missed one or more expected formulas |
| B_retrieval_rerank | learner_short_21 | learner_short_normal | refuse | retrieval_miss | normal learner query refused instead of offering a conservative book-grounded answer |
| B_retrieval_rerank | review_only_boundary_04 | review_only_support_boundary | strong | rerank_regression | review-only/support-only boundary query produced strong answer; review-only/support-only surface appears in primary evidence; B mode failed while A mode passed for the same query |
| B_retrieval_rerank | review_only_boundary_08 | review_only_support_boundary | strong | review_only_boundary_error | review-only/support-only boundary query produced strong answer; review-only/support-only surface appears in primary evidence |
| B_retrieval_rerank | review_only_boundary_10 | review_only_support_boundary | strong | review_only_boundary_error | review-only/support-only boundary query produced strong answer; review-only/support-only surface appears in primary evidence |
| B_retrieval_rerank | negative_modern_09 | negative_modern_unrelated | strong | rerank_regression | negative/modern unrelated query produced strong answer; negative/modern unrelated query has primary evidence; B mode failed while A mode passed for the same query |
| C_production_like_full_chain | ahv2_canonical_02 | ahv2_canonical | strong | assembler_slot_error | canonical definition primary does not contain expected concept |
| C_production_like_full_chain | cross_batch_adversarial_10 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| C_production_like_full_chain | cross_batch_adversarial_12 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| C_production_like_full_chain | cross_batch_adversarial_15 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| C_production_like_full_chain | cross_batch_adversarial_18 | cross_batch_adversarial | strong | answer_mode_calibration_error | strong comparison/relationship answer lacks primary coverage for both sides |
| C_production_like_full_chain | formula_04 | formula | strong | citation_error | fail: strong citations are not limited to primary evidence |
| C_production_like_full_chain | formula_07 | formula | strong | data_layer_bad_alias | fail: strong citations are not limited to primary evidence; formula normalization/raw candidates missed one or more expected formulas |
| C_production_like_full_chain | formula_18 | formula | strong | data_layer_bad_alias | fail: strong citations are not limited to primary evidence; formula normalization/raw candidates missed one or more expected formulas |
| C_production_like_full_chain | learner_short_21 | learner_short_normal | refuse | retrieval_miss | normal learner query refused instead of offering a conservative book-grounded answer |
| C_production_like_full_chain | review_only_boundary_04 | review_only_support_boundary | strong | review_only_boundary_error | review-only/support-only boundary query produced strong answer; review-only/support-only surface appears in primary evidence |
| C_production_like_full_chain | review_only_boundary_08 | review_only_support_boundary | strong | review_only_boundary_error | review-only/support-only boundary query produced strong answer; review-only/support-only surface appears in primary evidence |
| C_production_like_full_chain | review_only_boundary_10 | review_only_support_boundary | strong | review_only_boundary_error | review-only/support-only boundary query produced strong answer; review-only/support-only surface appears in primary evidence |
| C_production_like_full_chain | negative_modern_09 | negative_modern_unrelated | strong | negative_query_false_positive | negative/modern unrelated query produced strong answer; negative/modern unrelated query has primary evidence |
