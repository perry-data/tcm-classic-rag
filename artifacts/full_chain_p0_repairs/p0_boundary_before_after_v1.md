# P0 Boundary Before / After v1

- before_failure_count: `10`
- after_failure_count: `0`

## Before

| mode | query | answer_mode | failure_type | primary_ids |
| --- | --- | --- | --- | --- |
| A_data_plane_baseline | 两阳是什么意思？ | weak_with_review_notice | none |  |
| A_data_plane_baseline | 清邪中上是什么意思？ | strong | review_only_boundary_error | safe:main_passages:ZJSHL-CH-023-P-0046 |
| A_data_plane_baseline | 反是什么意思？ | strong | review_only_boundary_error | safe:main_passages:ZJSHL-CH-009-P-0159, safe:main_passages:ZJSHL-CH-008-P-0217, safe:main_passages:ZJSHL-CH-025-P-0007 |
| A_data_plane_baseline | 白虎是什么意思？ | weak_with_review_notice | none |  |
| B_retrieval_rerank | 两阳是什么意思？ | strong | rerank_regression | safe:main_passages:ZJSHL-CH-009-P-0275, safe:main_passages:ZJSHL-CH-017-P-0049, safe:main_passages:ZJSHL-CH-017-P-0050 |
| B_retrieval_rerank | 清邪中上是什么意思？ | strong | review_only_boundary_error | safe:main_passages:ZJSHL-CH-023-P-0046 |
| B_retrieval_rerank | 反是什么意思？ | strong | review_only_boundary_error | safe:main_passages:ZJSHL-CH-003-P-0090, safe:main_passages:ZJSHL-CH-025-P-0007, safe:main_passages:ZJSHL-CH-009-P-0159 |
| B_retrieval_rerank | 白虎是什么意思？ | strong | rerank_regression | safe:main_passages:ZJSHL-CH-011-P-0104, safe:main_passages:ZJSHL-CH-010-P-0128, safe:main_passages:ZJSHL-CH-010-P-0165 |
| C_production_like_full_chain | 两阳是什么意思？ | strong | review_only_boundary_error | safe:main_passages:ZJSHL-CH-009-P-0275, safe:main_passages:ZJSHL-CH-017-P-0049, safe:main_passages:ZJSHL-CH-017-P-0050 |
| C_production_like_full_chain | 清邪中上是什么意思？ | strong | review_only_boundary_error | safe:main_passages:ZJSHL-CH-023-P-0046 |
| C_production_like_full_chain | 反是什么意思？ | strong | review_only_boundary_error | safe:main_passages:ZJSHL-CH-003-P-0090, safe:main_passages:ZJSHL-CH-025-P-0007, safe:main_passages:ZJSHL-CH-009-P-0159 |
| C_production_like_full_chain | 白虎是什么意思？ | strong | negative_query_false_positive | safe:main_passages:ZJSHL-CH-011-P-0104, safe:main_passages:ZJSHL-CH-010-P-0128, safe:main_passages:ZJSHL-CH-010-P-0165 |

## After

| mode | query | answer_mode | pass | primary_ids | secondary_count | review_count |
| --- | --- | --- | --- | --- | --- | --- |
| A_data_plane_baseline | 清邪中上是什么意思？ | weak_with_review_notice | True |  | 4 | 2 |
| A_data_plane_baseline | 反是什么意思？ | weak_with_review_notice | True |  | 14 | 0 |
| A_data_plane_baseline | 两阳是什么意思？ | weak_with_review_notice | True |  | 14 | 1 |
| A_data_plane_baseline | 白虎是什么意思？ | refuse | True |  | 0 | 0 |
| B_retrieval_rerank | 清邪中上是什么意思？ | weak_with_review_notice | True |  | 4 | 2 |
| B_retrieval_rerank | 反是什么意思？ | weak_with_review_notice | True |  | 14 | 0 |
| B_retrieval_rerank | 两阳是什么意思？ | weak_with_review_notice | True |  | 13 | 0 |
| B_retrieval_rerank | 白虎是什么意思？ | refuse | True |  | 0 | 0 |
| C_production_like_full_chain | 清邪中上是什么意思？ | weak_with_review_notice | True |  | 4 | 2 |
| C_production_like_full_chain | 反是什么意思？ | weak_with_review_notice | True |  | 14 | 0 |
| C_production_like_full_chain | 两阳是什么意思？ | weak_with_review_notice | True |  | 13 | 0 |
| C_production_like_full_chain | 白虎是什么意思？ | refuse | True |  | 0 | 0 |
