# Tech Spec MVP Baseline v1

## 1. 文档定位

本文件定义当前仓库的正式技术基线，目标是回答两个问题：

1. 现在这套系统实际上是怎么跑起来的。
2. 后续 coding agent 如果继续开发，哪些入口、合同、数据边界不能误判。

本文件按“真实实现”书写，不按理想架构图书写。

## 2. 当前系统总览

### 2.1 正式运行链路

```text
data/raw/《注解伤寒论》.zip
        │
        ├─ scripts/check_dataset_acceptance.py
        │
data/processed/zjshl_dataset_v2/
        │
        ├─ scripts/build_mvp_safe_dataset.py
        │        └─ dist/zjshl_dataset_v2_mvp_safe.zip
        │
        ├─ build_mvp_database.py
        │        └─ artifacts/zjshl_mvp.db
        │
        ├─ build_dense_index.py
        │        ├─ artifacts/dense_chunks.faiss
        │        ├─ artifacts/dense_main_passages.faiss
        │        └─ artifacts/*_meta.json
        │
        ├─ run_hybrid_retrieval.py
        │
        ├─ run_answer_assembler.py
        │
        └─ app_minimal_api.py
                 ├─ POST /api/v1/answers
                 └─ GET / + /frontend/*
```

### 2.2 运行时核心文件

| 层 | 当前正式入口 | 说明 |
| --- | --- | --- |
| 数据验收 | `scripts/check_dataset_acceptance.py` | 检查原始 / 处理后数据是否满足构建前提 |
| safe 数据构建 | `scripts/build_mvp_safe_dataset.py` | 生成 MVP safe 数据包 |
| 数据库构建 | `build_mvp_database.py` | 生成 SQLite 与统一检索视图 |
| dense 索引构建 | `build_dense_index.py` | 基于数据库生成两套 FAISS 索引 |
| 检索 | `run_hybrid_retrieval.py` | 当前正式检索主入口 |
| 检索骨架 | `run_minimal_retrieval.py` | hybrid 直接复用的基础门控与分槽逻辑 |
| 回答编排 | `run_answer_assembler.py` | 当前正式 answer payload 入口 |
| HTTP API | `app_minimal_api.py` | 当前正式最小 API 与静态文件服务 |
| 前端 | `frontend/index.html` + `frontend/app.js` + `frontend/styles.css` | 同源单页消费层 |

## 3. 数据输入边界

### 3.1 当前正式输入源

| 路径 | 角色 | 备注 |
| --- | --- | --- |
| `data/raw/《注解伤寒论》.zip` | 原始回查源 | 上游源文件，主要用于数据验收与追溯 |
| `data/processed/zjshl_dataset_v2/` | full 数据目录 | 当前最重要的处理后数据底座 |
| `dist/zjshl_dataset_v2_mvp_safe.zip` | safe 数据包 | 当前数据库构建的 safe 输入 |
| `layered_enablement_policy.json` | 分层启用策略 | 决定 A/B/C/D 层级、禁用源和 answer mode 规则 |
| `database_schema_draft.json` | 数据库构建配置 | 决定表与视图生成口径 |

### 3.2 当前数据分层原则

`layered_enablement_policy.json` 是运行期策略源，关键约束如下：

- `safe_main_passages_primary`：A 层，可进入 `primary_evidence`
- `safe_main_passages_secondary`：B 层，只能进入 `secondary_evidence`
- `full_annotations_raw`：B 层，只能辅助展示，且需风险提示
- `full_passages_ledger`：C 层，只能作为 review / risk
- `ambiguous_related_material`：C 层，只能作为 review / risk
- `annotation_links`：D 层，当前完全禁用

### 3.3 safe 数据策略的当前实现

`scripts/build_mvp_safe_dataset.py` 的现行策略不是“追求完美修复”，而是“先隔离风险，再保住 MVP 可运行”：

- 清空 `annotation_links.json`
- 清空 `annotations.json` 中 `anchor_passage_id`
- 从 `main_passages.json` 排除 ambiguous 主条
- 将过短主条降级为非 primary
- 从 `chunks.json` 里排除 ambiguous-backed / 过短切片

这意味着当前数据底座是一个“保守启用”的研读系统，不是完整开放的全文知识库。

## 4. 数据库与检索视图

### 4.1 当前数据库文件

- 正式数据库：`artifacts/zjshl_mvp.db`

### 4.2 当前表与视图

根据实际数据库与构建报告，当前存在：

- `records_main_passages`
- `records_chunks`
- `records_annotations`
- `records_passages`
- `risk_registry_ambiguous`
- `record_chunk_passage_links`
- `vw_retrieval_records_unified`

### 4.3 当前规模

来自 `artifacts/database_counts.json` 的当前基线计数：

| 对象 | 数量 |
| --- | --- |
| `records_main_passages` | 777 |
| `records_chunks` | 583 |
| `records_annotations` | 629 |
| `records_passages` | 1841 |
| `risk_registry_ambiguous` | 450 |
| `record_chunk_passage_links` | 676 |
| `vw_retrieval_records_unified` | 4280 |

补充统计：

- A 层 `main_passages`: 666
- B 层 `main_passages`: 111
- 多 passage chunk: 67
- unified view 中 `annotation_links`: 0

### 4.4 当前 unified view 的作用

`vw_retrieval_records_unified` 是检索统一入口。当前 sparse 检索、dense 索引构建和后续 evidence gating 都围绕该视图展开。

重要事实：

- `chunks` 可被召回，但不能直接进入 `primary_evidence`
- `annotation_links` 不会进入 unified view
- `record_chunk_passage_links` 承担 chunk -> main passage 回指关系

## 5. 当前检索链路

### 5.1 请求建模

`run_hybrid_retrieval.py` 在 `run_minimal_retrieval.py` 的骨架上构造请求对象，关键字段包括：

- `query_text`
- `query_text_normalized`
- `query_theme`
- `precision_profile=tight_primary`
- `allow_levels=["A","B","C"]`
- `blocked_sources=["annotation_links"]`
- `scope_filters.book_id="ZJSHL"`

### 5.2 sparse 阶段

在 unified view 上做词面匹配，核心行为：

- 归一化 query
- 提取 query terms
- 计算 `text_match_score`
- 叠加 `weight_bonus`
- 应用 topic consistency / precision adjustment
- 依据 `SOURCE_BUDGETS` 和 `SPARSE_TOP_K=20` 保留结果

### 5.3 dense 阶段

当前有两套 dense 索引：

- `artifacts/dense_chunks.faiss`
- `artifacts/dense_main_passages.faiss`

当前 embedding / rerank 模型常量：

- embedding: `BAAI/bge-small-zh-v1.5`
- rerank: `BAAI/bge-reranker-base`

dense 检索参数：

- `DENSE_CHUNK_TOP_K=20`
- `DENSE_MAIN_TOP_K=12`

### 5.4 fusion 阶段

hybrid 检索把三路候选合并：

- sparse
- dense_chunks
- dense_main_passages

融合方式是 RRF：

- `FUSION_TOP_K=24`
- `RRF_K=60`

### 5.5 rerank 阶段

对 fused top N 候选做 cross-encoder rerank：

- `RERANK_TOP_N=18`
- 使用 sigmoid 后的 `rerank_score`
- 再结合 `rrf_score`、`sparse_score`、`dense_rank_score`、`weight_bonus` 生成最终 `combined_score`

### 5.6 final candidate gate

最终候选不会直接按分数进入证据槽位，还要通过最终门控：

- dense-only 候选需要额外阈值
- 方名 query 下，dense-only 候选必须满足 `exact_formula_anchor`
- 对 query topic mismatch 的候选，允许保留，但会降级到 secondary / review

## 6. Evidence Gating

当前系统最关键的不是“召回多少”，而是“召回后如何分槽”。实际规则如下：

| 来源 | 进入检索 | 可进入 `primary_evidence` | 可进入 `secondary_evidence` | 可进入 `review_materials` |
| --- | --- | --- | --- | --- |
| `chunks` | 是 | 否 | 否，需先回指 | 否 |
| `safe main_passages` A 层 | 是 | 是 | 主题偏移时可降级 | 否 |
| `safe main_passages` B 层 | 是 | 否 | 是 | 否 |
| `annotations` | 是 | 否 | 是 | 否 |
| `passages` | 是 | 否 | 否 | 是 |
| `ambiguous_passages` | 是 | 否 | 否 | 是 |
| `annotation_links` | 否 | 否 | 否 | 否 |

补充说明：

- `chunks` 只是召回骨架，命中后必须回指 `main_passages`
- `A` 层主条若主题不一致，会被打上 `topic_mismatch_demoted` 并降级
- `passages` 和 `ambiguous_passages` 只承担人工核对材料角色

## 7. Answer Assembler

### 7.1 当前正式入口

- 正式入口：`run_answer_assembler.py`

### 7.2 当前真实调度顺序

`AnswerAssembler.assemble()` 的当前真实顺序是：

1. 尝试识别 comparison query
2. 尝试识别 general question
3. 回退到标准 single-query path

但本基线 v1 的正式承诺只覆盖第 3 条标准路径。前两条属于现存扩展实现，不应在后续文档中被自动升级为正式范围。

### 7.3 标准路径的输出规则

标准路径会把 retrieval 结果组织成统一 payload，顶层字段固定为：

- `query`
- `answer_mode`
- `answer_text`
- `primary_evidence`
- `secondary_evidence`
- `review_materials`
- `disclaimer`
- `review_notice`
- `refuse_reason`
- `suggested_followup_questions`
- `citations`
- `display_sections`

### 7.4 三种 answer mode

| mode | 触发条件 | 输出要求 |
| --- | --- | --- |
| `strong` | 存在 `primary_evidence` | 以主依据组织 `answer_text` |
| `weak_with_review_notice` | 无主依据，但有辅助或风险材料 | 必须显式提示“需核对” |
| `refuse` | 无可用证据 | 必须给出拒答原因与改问建议 |

### 7.5 当前 answer text 生成方式

当前 answer text 不是 LLM 自由生成，而是模板化文本组织：

- `strong`：列出前 3 条主依据摘要
- `weak_with_review_notice`：给出“证据不足”引导，并引用首条辅助 / 风险材料
- `refuse`：输出统一拒答文案

这也是当前系统可控、可复现、可审查的重要前提。

## 8. API Contract

### 8.1 正式 HTTP 入口

- `POST /api/v1/answers`

### 8.2 请求体

```json
{
  "query": "黄连汤方的条文是什么？"
}
```

当前只有一个正式输入字段：`query`

### 8.3 响应体

直接返回 answer payload 本体，不额外包 `data`。

### 8.4 错误处理

当前 transport 语义：

- `200`：成功返回 payload，包括 `refuse`
- `400`：请求体非法
- `500`：服务内部失败

## 9. 前端消费关系

### 9.1 同源关系

`app_minimal_api.py` 同时承担静态文件服务：

- `GET /` -> `frontend/index.html`
- `GET /frontend/app.js`
- `GET /frontend/styles.css`
- `POST /api/v1/answers`

### 9.2 前端依赖边界

`frontend/app.js` 当前只依赖 payload 顶层稳定字段，不依赖：

- retrieval trace
- dense / sparse 分数
- rerank 中间结果
- 数据库内部结构

前端还会主动校验顶层字段齐全性，缺字段即报错。

## 10. 关键运行链路

### 10.1 构建链路

```bash
./.venv/bin/python scripts/check_dataset_acceptance.py
./.venv/bin/python scripts/build_mvp_safe_dataset.py
./.venv/bin/python build_mvp_database.py
./.venv/bin/python build_dense_index.py
```

### 10.2 运行链路

```bash
./.venv/bin/python app_minimal_api.py --host 127.0.0.1 --port 8000
```

浏览器入口：

- `http://127.0.0.1:8000/`

## 11. 当前已知限制

1. 单书固定，`scope_filters.book_id` 实际写死为 `ZJSHL`。
2. 当前回答是模板化编排，不做开放式生成。
3. query understanding 主要依赖启发式规则，而不是统一语义规划层。
4. dense 检索依赖本地缓存模型与 FAISS 索引。
5. `annotation_links` 当前完全禁用，不能当作遗漏功能随手恢复。
6. `backend/` 目录存在大量空壳文件，但不参与当前运行。
7. `run_answer_assembler.py` 已含 comparison / general 分支，这会让“代码能力”大于“正式基线”；后续必须靠变更流程维持边界。

## 12. 回归测试基线

### 12.1 当前正式回归样例

| Query | 期望模式 | 说明 |
| --- | --- | --- |
| `黄连汤方的条文是什么？` | `strong` | 强证据直答样例 |
| `烧针益阳而损阴是什么意思？` | `weak_with_review_notice` | 强证据不足样例 |
| `书中有没有提到量子纠缠？` | `refuse` | 书内无依据样例 |

### 12.2 当前正式 smoke 基线

| 产物 | 作用 |
| --- | --- |
| `artifacts/database_smoke_checks.md` | 校验数据库结构与 gating 约束 |
| `artifacts/hybrid_retrieval_smoke_checks.md` | 校验 hybrid 检索与 evidence gating |
| `artifacts/hybrid_answer_smoke_checks.md` | 校验 payload 结构与三模式 |
| `artifacts/api_smoke_checks.md` | 校验 `POST /api/v1/answers` |

### 12.3 当前必须保持的关键不变量

- `annotation_links` 不得泄漏进 unified view、raw candidates、evidence slots
- `chunks` 不得直接进入 `primary_evidence`
- `strong` 的 `primary_evidence` 必须仍然只来自 `main_passages`
- `黄连汤方` 的 strong 主证据不能把 `葛根黄芩黄连汤方` 重新拉回 primary
- 顶层 payload 字段顺序与字段集应保持稳定
