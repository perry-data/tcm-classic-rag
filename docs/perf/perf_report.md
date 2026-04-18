# `/api/v1/answers` Perf Report

## Scope

- Endpoint: `POST /api/v1/answers`
- Query set: 6 fixed regression queries, covering `strong` / `weak_with_review_notice` / `refuse` 各 2 条
- Main benchmark method: `scripts/bench_latency.py`
- Main runs:
  - baseline: old in-memory server on `:8010`, 5 rounds, 30 requests
  - after: optimized server on `:8012`, 5 rounds, 30 requests

## Query Set

| query_id | expected_mode | query |
| --- | --- | --- |
| `strong_formula_lookup` | `strong` | `黄连汤方的条文是什么？` |
| `strong_general_management` | `strong` | `太阳病应该怎么办？` |
| `weak_meaning_explanation` | `weak_with_review_notice` | `烧针益阳而损阴是什么意思？` |
| `weak_fragment_guidance` | `weak_with_review_notice` | `若噎者怎么办？` |
| `refuse_out_of_book` | `refuse` | `书中有没有提到量子纠缠？` |
| `refuse_personalized_treatment` | `refuse` | `我发烧了能不能用麻黄汤？` |

## End-to-End Before / After

| scenario | requests | p50 | p95 | max | mode_mismatch |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline (`8010`) | 30 | `9366.052 ms` | `16688.756 ms` | `17311.636 ms` | `0` |
| after (`8012`) | 30 | `8567.036 ms` | `12925.000 ms` | `13521.619 ms` | `0` |

### Improvement

- `p50`: `9366.052 -> 8567.036 ms` (`-8.5%`)
- `p95`: `16688.756 -> 12925.000 ms` (`-22.6%`)
- `max`: `17311.636 -> 13521.619 ms` (`-21.9%`)

## Stage Breakdown

分段计时来自优化后服务的 `Server-Timing` / JSONL perf log。为了看清真正的“慢在哪里”，下面按 **非 refuse 请求**（20/30 个）统计平均耗时和占比。

平均非 refuse 总耗时：`10186.530 ms`

| stage | avg ms | share |
| --- | ---: | ---: |
| `llm_generate` | `9623.476` | `94.47%` |
| `rerank_cross_encoder` | `544.263` | `5.34%` |
| `sparse_retrieval` | `5.034` | `0.05%` |
| `dense_embed` | `2.959` | `0.03%` |
| `evidence_gating` | `0.593` | `0.01%` |
| `dense_search_faiss` | `0.426` | `<0.01%` |
| `fusion_rrf` | `0.115` | `<0.01%` |
| `request_parse` | `0.036` | `<0.01%` |
| `response_build/serialize` | `0.014` | `<0.01%` |

结论：主瓶颈非常明确，是 `llm_generate`；第二名是 `rerank_cross_encoder`，但量级已经是次一级。

## Control Experiments

### 1. Disable LLM

`PERF_DISABLE_LLM=true`，5 rounds，30 requests

| scenario | p50 | p95 | max | note |
| --- | ---: | ---: | ---: | --- |
| hybrid + no LLM | `381.300 ms` | `1316.517 ms` | `1993.466 ms` | mode mismatch `0` |

结论：一旦移除 LLM，`p95` 从 `12.925 s` 级别直接掉到 `1.317 s`，说明端到端慢的第一名就是 LLM 生成。

### 2. Disable Rerank

`PERF_DISABLE_LLM=true PERF_DISABLE_RERANK=true`，5 rounds，30 requests

| scenario | p50 | p95 | max | note |
| --- | ---: | ---: | ---: | --- |
| hybrid + no LLM + no rerank | `4.592 ms` | `25.331 ms` | `156.616 ms` | mode mismatch `0` |

结论：在不走 LLM 的情况下，`rerank` 是 retrieval 链路里的主耗时来源。`hybrid + no LLM` 的平均延迟是 `452.765 ms`，关掉 rerank 后降到 `11.461 ms`。

### 3. Retrieval Mode Comparison

以下对照都带 `PERF_DISABLE_LLM=true`，目的是隔离 retrieval 本身的成本和稳定性。

| scenario | p50 | p95 | max | mode_mismatch |
| --- | ---: | ---: | ---: | ---: |
| hybrid + no LLM | `381.300 ms` | `1316.517 ms` | `1993.466 ms` | `0` |
| sparse + no LLM | `77.753 ms` | `1608.984 ms` | `2873.077 ms` | `0` |
| dense + no LLM | `391.387 ms` | `1712.510 ms` | `3996.228 ms` | `5` |

结论：

- `dense` 单跑并不比 `hybrid` 更快，且出现 `5/30` mode mismatch，典型是 `若噎者怎么办？` 从 `weak_with_review_notice` 掉成了 `refuse`。
- `sparse` 更快，但长尾仍然来自 rerank，且不能替代 hybrid 的召回覆盖。
- 这说明默认链路仍应保持 `hybrid`；性能优化应该优先打在 LLM 和 rerank，而不是直接砍掉 hybrid。

### 4. Keep-Alive Comparison

为了单独看 HTTP 连接复用，补了一个 `PERF_ENABLE_LLM_KEEPALIVE=false` 对照。两边都使用新代码，并对齐到 3 rounds（18 requests）。

| scenario | p50 | p95 | max |
| --- | ---: | ---: | ---: |
| keepalive on (`8012`, rounds 1-3) | `8619.099 ms` | `13016.377 ms` | `13521.619 ms` |
| keepalive off (`8017`, 3 rounds) | `9052.161 ms` | `14606.489 ms` | `19617.817 ms` |

结论：连接复用对中位数提升有限，但能稳定压缩长尾，尤其是 `max` 和 `p95`。

## Root Cause Summary

1. 慢的第一名：`llm_generate`
   - 非 refuse 请求平均占比 `94.47%`
   - `PERF_DISABLE_LLM=true` 后，`p95` 从 `12925.000 ms` 掉到 `1316.517 ms`

2. 慢的第二名：`rerank_cross_encoder`
   - 非 refuse 请求平均占比 `5.34%`
   - 在不走 LLM 时，关掉 rerank 可把平均延迟从 `452.765 ms` 压到 `11.461 ms`

3. 旧链路里还有一个隐性放大器：**LLM 首次生成经常因为段落格式未过校验而触发第二次调用**
   - 优化前的单请求日志里，`黄连汤方的条文是什么？` 曾出现两次 LLM 调用，单次 `ttfb_ms` 约 `7.5s + 8.4s`
   - 优化后同类请求可在首次生成即通过，样本延迟从 `16.7s` 级降到 `8.1s` 级

## Implemented Optimizations

### 1. Request-Scoped Perf Tracing

- 新增 `backend/perf.py`
- 每个请求生成 `request_id`
- 分段计时覆盖：
  - `request_parse`
  - `sparse_retrieval`
  - `dense_embed`
  - `dense_search_faiss`
  - `fusion_rrf`
  - `rerank_cross_encoder`
  - `evidence_gating`
  - `llm_generate`
  - `response_build/serialize`
- 输出：
  - JSONL: `artifacts/perf/request_timings.jsonl`
  - Response headers: `X-Request-Id`, `Server-Timing`

### 2. LLM Keep-Alive + Request Metrics

- `ModelStudioLLMClient` 从“每次请求新建 `urllib` 连接”改为“按线程复用 `http.client.(HTTPS)Connection`”
- 新增 per-call metrics：
  - `ttfb_ms`
  - `total_ms`
  - `status_code`
- 开关：
  - `PERF_ENABLE_LLM_KEEPALIVE=true|false`

### 3. Avoid Unnecessary Second LLM Call

- 新增 `normalize_answer_text_paragraphs()`
- 在 LLM 输出进入 validator 前，自动把“只有一个大段但句子结构完整”的结果整理为短段落
- 目的不是改内容，只是避免因格式问题触发第二次 LLM 调用

### 4. Dense Query Vector Reuse + LRU Cache

- 之前对 `dense_chunks` 和 `dense_main_passages` 会各算一次 embedding
- 现在同一请求只算一次 query embedding，然后复用到两次 FAISS search
- 额外增加最近查询的 embedding LRU cache
- 开关：
  - `PERF_ENABLE_QUERY_EMBED_CACHE=true|false`
  - `PERF_QUERY_EMBED_CACHE_SIZE`

### 5. Measurement / Tuning Flags

- `PERF_DISABLE_LLM=true|false`
- `PERF_DISABLE_RERANK=true|false`
- `PERF_RETRIEVAL_MODE=hybrid|sparse|dense`
- `PERF_RERANK_TOP_N`

## Regression

### Fixed Perf Query Set

- baseline: `mode_mismatch_count=0`
- after: `mode_mismatch_count=0`

### Evaluator V1

运行结果：

- report: `artifacts/evaluation/evaluator_v1_perf_regression.json`
- markdown: `artifacts/evaluation/evaluator_v1_perf_regression.md`

摘要：

- `mode_match_count`: `64/72`
- `citation_basic_pass_count`: `58/58`
- `failure_count`: `8`

与仓库原有 `artifacts/evaluation/evaluator_v1_report.json` 对比，摘要完全一致；这 8 个失败样本本来就存在，全部集中在 `meaning_explanation` 类型，没有因为本轮性能改动新增回归。

## Artifacts

- `scripts/bench_latency.py`
- `artifacts/perf/latency_baseline.json`
- `artifacts/perf/latency_after.json`
- `artifacts/perf/latency_disable_llm.json`
- `artifacts/perf/latency_disable_llm_disable_rerank.json`
- `artifacts/perf/latency_sparse_no_llm.json`
- `artifacts/perf/latency_dense_no_llm.json`
- `artifacts/perf/latency_no_keepalive.json`
- `artifacts/perf/request_timings.jsonl`
- `artifacts/evaluation/evaluator_v1_perf_regression.json`
- `artifacts/evaluation/evaluator_v1_perf_regression.md`
