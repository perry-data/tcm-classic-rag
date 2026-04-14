# FTS5 / BM25 Patch Note

## 本轮新增

- 为 SQLite 数据库补齐正式稀疏检索虚表：`retrieval_sparse_fts`
- sparse layer 从“统一视图 + lexical matcher”切换到 `SQLite FTS5 + bm25()`
- FTS5 sparse recall 已接入当前 hybrid retrieval 主链
- 新增 FTS5/BM25 对比产物与 smoke checks

## 关键文件

- [hybrid.py](/Users/man_ray/Projects/Python/tcm-classic-rag/backend/retrieval/hybrid.py)
- [build_v1_database.py](/Users/man_ray/Projects/Python/tcm-classic-rag/scripts/build_v1_database.py)
- [technical_design_v1.md](/Users/man_ray/Projects/Python/tcm-classic-rag/docs/final/technical_design_v1.md)
- [system_spec_v1.md](/Users/man_ray/Projects/Python/tcm-classic-rag/docs/final/system_spec_v1.md)

## 实现说明

- 建库阶段会创建 `retrieval_sparse_fts`，tokenizer 使用 `trigram`
- 运行时若当前库缺失该虚表，`HybridRetrievalEngine` 会自动补建并回填
- sparse 查询先做 query focus 提取，再生成 FTS `MATCH` 表达式
- 稀疏排序正式使用 SQLite `bm25()`；`text_match_score` 保留用于 topic consistency 和 gating 收口
- sparse 结果仍按既有 `SOURCE_BUDGETS`、RRF、rerank、evidence gating 继续流转

## 兼容性说明

- 未改 API 路由
- 未改请求体
- 未改 answer payload 顶层字段
- 未改 evidence gating 规则
- `chunks` 仍只负责召回与回指，不直接进入 `primary_evidence`
- 对不足 3 字的极短 focus query，保留 lexical fallback 作为兜底

## 本轮输出

- [fts5_retrieval_examples.json](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/fts5_retrieval_examples.json)
- [fts5_smoke_checks.md](/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/fts5_smoke_checks.md)

## 本地运行说明

- `./.venv/bin/python -m backend.retrieval.hybrid`
- `./.venv/bin/python scripts/build_v1_database.py`
