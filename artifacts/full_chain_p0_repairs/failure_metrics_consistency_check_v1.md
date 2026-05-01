# Failure Metrics Consistency Check v1

- consistent: `True`
- results_fail_record_count: `37`
- failure_cases_failure_count: `37`
- results_metric_failure_type_total: `37`
- failure_cases_type_total: `37`
- missing_or_none_failure_type_count: `0`
- finding: JSON artifacts are internally consistent at 37 failures; the apparent mismatch came from reading partial failure-type metrics instead of summing failure_type_counts.

## Failure Type Counts

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
