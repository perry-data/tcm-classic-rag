# 第4章 系统设计证据映射表

本文件用于建立毕业论文第4章《系统设计》中各项设计主张与 `tcm-classic-rag` 仓库中真实实现的映射关系。

## 1. 架构与流程映射

| 论文小节 | 论文主张 | 对应代码/文件/接口/报告 | 状态 | 备注 |
|---|---|---|---|---|
| 4.2 总体架构 | 五层架构模型 | `backend/api/`, `backend/retrieval/`, `backend/answers/` | 已实现 | 逻辑分层清晰 |
| 4.3 离线构建 | 原始文本到 SQLite/FAISS | `scripts/build_v1_database.py`, `scripts/build_dense_index.py` | 已实现 | |
| 4.3.3 索引 | FTS5 Trigram 索引 | `backend/retrieval/hybrid.py` 中的 `SPARSE_FTS_TOKENIZER` | 已实现 | 使用 trigram 分词 |
| 4.3.4 Safe Dataset | 人工校验的安全数据集 | `data/processed/zjshl_dataset_v2/` | 已实现 | |
| 4.4 在线流程 | 意图识别 -> 检索 -> 门控 -> 生成 | `backend/answers/assembler.py` 中的 `assemble()` 方法 | 已实现 | 严格按此链路流转 |
| 4.5.3 RRF | 使用 RRF 融合分值 | `backend/retrieval/hybrid.py` 中的 `RRF_K` | 已实现 | |
| 4.5.3 重排序 | 使用 BGE Reranker | `backend/retrieval/hybrid.py` 中的 `DEFAULT_RERANK_MODEL` | 已实现 | |

## 2. 证据门控与回答模式映射

| 论文小节 | 论文主张 | 对应代码/文件/接口/报告 | 状态 | 备注 |
|---|---|---|---|---|
| 4.6.1 证据分层 | Primary/Secondary/Review | `backend/answers/assembler.py` 中的 `_build_evidence_item` | 已实现 | 明确区分角色 |
| 4.6.2 Strong | 强证据模式判定 | `_assemble_formula_effect_query` 等方法中的判定逻辑 | 已实现 | |
| 4.6.2 Weak | 弱证据提示模式 | `AnswerMode` = `weak_with_review_notice` | 已实现 | |
| 4.6.2 Refuse | 业务拒答模式 | `AnswerMode` = `refuse` | 已实现 | |
| 4.6.2 风险控制 | 拒答命中敏感词 | `_detect_policy_refusal` 方法 | 已实现 | |

## 3. 前后端交互与评测映射

| 论文小节 | 论文主张 | 对应代码/文件/接口/报告 | 状态 | 备注 |
|---|---|---|---|---|
| 4.7.2 引用溯源 | `[E1]` 标注与 ID 绑定 | `backend/answers/assembler.py` 中的 `_build_citations` | 已实现 | |
| 4.8.1 前端回退 | 放弃 React 采用原生 JS | `docs/patch_notes/react_backout_v1_patch_note.md` | 已执行 | 明确记载的回退操作 |
| 4.8.2 API 路径 | `/api/v1/answers` | `backend/api/minimal_api.py` | 已实现 | |
| 4.8.2 返回字段 | `answer_mode`, `citations` 等 | `EXPECTED_PAYLOAD_FIELDS` (minimal_api.py) | 已实现 | 字段一致 |
| 4.9.1 Goldset | ~150 条高质量评测集 | `artifacts/evaluation/goldset_v2_batchC_log.json` | 已完成 | 最终规模确认 |
| 4.9.2 评测指标 | Hit@K, Mode Match | `scripts/run_evaluator_v2.py` | 已实现 | |

## 4. 风险备注与说明

1. **前端技术栈**：开题报告中提到的 React + Tailwind 已在 `react_backout_v1` 任务中被回退，论文正文 4.8.1 节已正确处理为“工程折中”。
2. **评测集规模**：论文 4.9.1 节提到的 150 条为当前高质量核心集，符合真实仓库状态。
3. **回答生成**：LLM 仅负责 `answer_text` 生成，证据分层和回答模式判定完全由 `AnswerAssembler` 中的后端规则控制，论文表述必须严格遵守此边界。
