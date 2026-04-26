# Latency Snapshot v1

| mode | count | p50_ms | p95_ms | max_ms |
| --- | --- | --- | --- | --- |
| A_data_plane_baseline | 120 | 39.291 | 473.935 | 635.489 |
| B_retrieval_rerank | 120 | 586.909 | 1660.059 | 2789.551 |
| C_production_like_full_chain | 120 | 8654.537 | 21417.208 | 26527.032 |

## Stage P50

### A_data_plane_baseline

| stage | p50_ms |
| --- | --- |
| evidence_gating | 0.077 |
| fusion_rrf | 0.011 |
| response_build/serialize | 0.003 |
| sparse_retrieval | 3.893 |

### B_retrieval_rerank

| stage | p50_ms |
| --- | --- |
| dense_embed | 6.12 |
| dense_search_faiss | 0.113 |
| evidence_gating | 0.301 |
| fusion_rrf | 0.048 |
| rerank_cross_encoder | 490.51 |
| response_build/serialize | 0.004 |
| sparse_retrieval | 5.219 |

### C_production_like_full_chain

| stage | p50_ms |
| --- | --- |
| dense_embed | 6.395 |
| dense_search_faiss | 0.117 |
| evidence_gating | 0.284 |
| fusion_rrf | 0.053 |
| llm_generate | 8442.114 |
| rerank_cross_encoder | 448.002 |
| response_build/serialize | 0.015 |
| sparse_retrieval | 4.976 |
