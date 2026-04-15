# 第4章 事实核验矩阵 (v2)

本矩阵记录了毕业论文第4章中所有关键技术主张的真实性核验情况。

| 论文主张 | 是否可写 | 证据文件 | 证据位置/函数/字段 | 推荐写法 | 禁止写法 |
|---|---|---|---|---|---|
| 混合检索架构 | 可写 | `backend/retrieval/hybrid.py` | `HybridRetrievalEngine` | 结合 FTS5 (BM25) 与 FAISS (BGE) | 仅使用向量检索 |
| RRF 融合算法 | 可写 | `backend/retrieval/hybrid.py` | `RRF_K = 60` | 采用倒数排名融合 (RRF) 统一分值 | 简单加权融合 |
| BGE 重排序 | 可写 | `backend/retrieval/hybrid.py` | `DEFAULT_RERANK_MODEL` | 使用 BGE Reranker 进行重排序 | 仅依赖初筛得分 |
| 证据门控机制 | 可写 | `backend/answers/assembler.py` | `_assemble_formula_effect_query` | 基于后端规则判定回答模式 | LLM 决定可靠性 |
| 回答模式分层 | 可写 | `backend/answers/assembler.py` | `strong/weak/refuse` | 包含强依据、弱依据及拒答模式 | 只有一种回答方式 |
| 引用联动交互 | 可写 | `frontend/app.js` | `renderAnswer` (隐含), `citations` 字段 | 前端支持引用编号与证据卡片联动 | 仅文本展示引用 |
| 会话持久化存储 | 可写 | `backend/chat_history/store.py` | `class ConversationStore` | 支持会话持久化存储与历史搜索 | 仅单次对话 |
| 异体字映射 | **可保守写** | `backend/answers/assembler.py` | `FORMULA_VARIANT_REPLACEMENTS` | 针对核心方药名建立替换映射 | “古医药异体字库” |
| 数据记录规模 | **可保守写** | `artifacts/database_counts.json` | `records_chunks: 583` | 包含 4000 余条统一检索记录 | “40,000+ 语义片段” |
| Goldset 规模 | 可写 | `artifacts/evaluation/evaluator_v2_report.md` | `total_questions: 150` | 构建了 150 条高质量黄金测试集 | “250 条专家标注” |
| 前端技术栈 | 可写 | `frontend/app.js` | 源码内容 | 原生 JavaScript 驱动的单页应用 | React + Tailwind |
| API 接口路径 | 可写 | `backend/api/minimal_api.py` | `API_PATH = "/api/v1/answers"` | 核心接口为 `/api/v1/answers` | 虚构的 `/query` 接口 |
