# Dense Retrieval Plan

## 本轮实际落地

本轮已按 [dense_retrieval_upgrade_spec.md](/Users/man_ray/Projects/Python/tcm-classic-rag/dense_retrieval_upgrade_spec.md) 实现最小 Hybrid 检索闭环：

- dense index 构建：[build_dense_index.py](/Users/man_ray/Projects/Python/tcm-classic-rag/build_dense_index.py)
- hybrid retrieval：[run_hybrid_retrieval.py](/Users/man_ray/Projects/Python/tcm-classic-rag/run_hybrid_retrieval.py)
- dense index 产物：
  - [dense_chunks.faiss](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/dense_chunks.faiss)
  - [dense_chunks_meta.json](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/dense_chunks_meta.json)
  - [dense_main_passages.faiss](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/dense_main_passages.faiss)
  - [dense_main_passages_meta.json](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/dense_main_passages_meta.json)

## 模型与依赖

- embedding model: `BAAI/bge-small-zh-v1.5`
- rerank model: `BAAI/bge-reranker-base`
- vector index: `faiss-cpu`
- runtime env: 项目内 `.venv`
- cache dir: `artifacts/hf_cache`

## 检索链路

1. sparse recall
2. dense recall
3. RRF fusion
4. Cross-Encoder rerank
5. evidence gating
6. `strong / weak_with_review_notice / refuse`

## 实际索引范围

- dense chunks index: `records_chunks`
- dense main index: `records_main_passages`

未建立 dense index 的对象：

- `records_annotations`
- `records_passages`
- `risk_registry_ambiguous`

这些对象仍主要依赖 sparse 进入候选，再由现有分层逻辑落入 secondary / review。

## 融合参数

- sparse top-k: `20`
- dense chunks top-k: `20`
- dense main top-k: `12`
- fusion top-k: `24`
- RRF k: `60`
- rerank top-N: `18`

## 门控保持

以下规则已在 Hybrid 链路中保持：

- `annotation_links` 继续禁用
- `chunks` 只召回并回指，不直接作为 primary
- `annotations` 不能进入 primary
- `passages / ambiguous_passages` 不能进入 primary
- dense-only 命中的 A 级 `main_passages` 默认不能直接变 primary
- 方名类 query 继续保留 `exact / expanded / different_formula_anchor` 区分

## 当前最小验证

已覆盖 3 条冻结 query：

- `黄连汤方的条文是什么？`
- `烧针益阳而损阴是什么意思？`
- `书中有没有提到量子纠缠？`

对应结果见：

- [hybrid_retrieval_examples.json](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/hybrid_retrieval_examples.json)
- [hybrid_retrieval_smoke_checks.md](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/hybrid_retrieval_smoke_checks.md)
