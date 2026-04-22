# 分段延迟拆解快照 v1

生成时间：2026-04-21

本快照引用已有运行记录 `artifacts/perf/latency_after.json`，该记录生成于 `2026-04-18T09:15:07.149616+00:00`，label 为 `after`，共 6 个 query、5 轮、30 次请求，mode mismatch 为 0。

本轮新增的 `query_trace_bundle_v1.json` 是离线诊断导出，默认关闭 LLM，避免把生成质量混入数据层诊断；下面的 LLM 延迟来自 `latency_after.json` 的真实 API benchmark。

## 1. 分段统计

| stage | count | avg_ms | p50_ms | p95_ms | max_ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| retrieval total without gating | 25 | 522.174 | 502.690 | 804.399 | 1309.056 |
| sparse / FTS5 BM25 | 25 | 4.178 | 1.339 | 15.764 | 16.171 |
| dense embed | 4 | 17.580 | 17.181 | 23.821 | 24.823 |
| dense search / FAISS | 25 | 0.426 | 0.375 | 0.870 | 1.294 |
| fusion / RRF | 25 | 0.109 | 0.097 | 0.222 | 0.267 |
| rerank / CrossEncoder | 25 | 514.648 | 500.701 | 774.083 | 1278.641 |
| evidence gating | 25 | 0.477 | 0.249 | 1.241 | 2.394 |
| llm_generate | 20 | 9623.476 | 8797.182 | 12379.763 | 12810.039 |
| response build / serialize | 30 | 0.011 | 0.011 | 0.021 | 0.022 |
| total | 30 | 6855.763 | 8561.555 | 12921.985 | 13517.629 |

说明：

- `dense_embed` count 为 4，是因为 query embedding cache 命中后不会重复记录 dense embed。
- `llm_generate` count 为 20，是因为 refuse 请求跳过 LLM。
- `retrieval total without gating` 是 sparse + dense_embed + dense_search + fusion + rerank 的合计，不包含 evidence_gating。

## 2. 事实结论

1. 非 LLM 检索链路中，rerank 是主要耗时，平均 514.648 ms。
2. sparse、FAISS search、RRF、evidence gating 都是毫秒级或亚毫秒级，不是当前主耗时。
3. LLM generate 平均 9623.476 ms，远高于检索链路，是端到端延迟的主导项。
4. response build / serialize 平均 0.011 ms，不构成瓶颈。
5. 若只讨论数据层优化，优先目标不应是 response serialize，而应是减少无效候选、降低 rerank 负担、增强 alias/topic 召回稳定性。

## 3. 与本轮诊断的关系

本轮新增脚本 `scripts/data_diagnostics/export_query_traces.py` 对 12 条代表 query 记录了 offline perf trace、sparse top-k、dense top-k、fusion top-k、rerank top-k、final slots 与 gate/demotion signals。

原始链路样例保存在：

- `artifacts/data_diagnostics/query_trace_bundle_v1.json`

该 artifact 适合下一轮定位“哪个 query 在哪个阶段偏掉”，不替代真实 API benchmark。
