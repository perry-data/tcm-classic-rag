# Hybrid Retrieval Patch Note

## 本轮新增

- 新建项目虚拟环境：`.venv`
- 接入 `faiss-cpu`
- 接入本地 embedding 模型 `BAAI/bge-small-zh-v1.5`
- 接入本地 Cross-Encoder `BAAI/bge-reranker-base`
- 实现 dense index 构建
- 实现 sparse + dense + RRF + rerank 的 Hybrid retrieval

## 关键文件

- [build_dense_index.py](/Users/man_ray/Projects/Python/tcm-classic-rag/scripts/build_dense_index.py)
- [hybrid.py](/Users/man_ray/Projects/Python/tcm-classic-rag/backend/retrieval/hybrid.py)
- [dense_retrieval_plan.md](/Users/man_ray/Projects/Python/tcm-classic-rag/docs/specs/dense_retrieval_plan.md)

## 行为变化

- 检索不再只有 sparse lexical 路径
- 新增 dense recall 之后，候选先经 RRF 融合，再经 Cross-Encoder 重排序
- 最终仍回到原有 evidence gating

## 精度与门控

为了避免 dense / rerank 把语义相近但不该入主证据的内容抬进 `primary_evidence`，本轮额外加了两层收口：

- 对方名类 query，增加 `different_formula_anchor` 和 `formula_query_off_topic`
- 对 dense-only 命中，增加最终准入 gate：
  - 方名类 query：只有 `exact_formula_anchor` 可继续进入最终池
  - generic query：dense-only 候选需满足更高 `dense_score / rerank_score` 阈值

## 当前结果

- `黄连汤方的条文是什么？` 仍为 `strong`
- `primary_evidence` 未回归混入“葛根黄芩黄连汤方”相关主条
- `烧针益阳而损阴是什么意思？` 仍为 `weak_with_review_notice`
- `书中有没有提到量子纠缠？` 仍为 `refuse`

## 兼容性说明

- 未修改数据库 schema
- 未修改 answer payload 合同
- 未恢复 `annotation_links`
- 未扩展到前端 / API / 多书 / LLM 生成

## 本地运行说明

推荐命令：

- `./.venv/bin/python scripts/build_dense_index.py`
- `./.venv/bin/python -m backend.retrieval.hybrid`

模型缓存位于：

- `artifacts/hf_cache`

当前脚本已支持优先使用本地 snapshot 路径加载缓存模型，减少重复联网依赖。
