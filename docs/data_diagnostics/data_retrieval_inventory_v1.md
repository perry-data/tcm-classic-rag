# 数据底座与检索对象盘点 v1

生成时间：2026-04-21

本报告只整理底层数据、检索对象、证据对象和链路诊断信息。未修改 prompt、前端、API、answer_mode、payload contract，也未把 commentarial 提升为 primary_evidence。

## 1. Runtime 数据总览

当前运行时核心库是 `artifacts/zjshl_v1.db`。检索入口不是直接读原始 JSON，而是读 SQLite 视图 `vw_retrieval_records_unified`，再由 FTS5、FAISS、RRF、rerank 和 evidence gating 继续处理。

| 对象 | 行数 | 当前角色 | 参与检索 | 可进入证据槽 | 备注 |
| --- | ---: | --- | --- | --- | --- |
| `records_main_passages` | 777 | canonical 主文本运行时表 | 是，FTS；是，dense main | `primary_evidence` 或 `secondary_evidence` | A 级 666 条可 primary；B 级 111 条只 secondary |
| `records_chunks` | 583 | recall chunk | 是，FTS；是，dense chunks | 不直接进入证据槽 | 通过 `record_chunk_passage_links` 回指 main_passages |
| `records_annotations` | 629 | 成无己注解 raw 辅助层 | 是，FTS | `secondary_evidence` | `linkage_enabled=0`，不走 annotation_links 挂接 |
| `records_passages` | 1841 | full ledger / risk-only 核对层 | 是，FTS | `review_materials` | C 级，`display_allowed=risk_only` |
| `risk_registry_ambiguous` | 450 | ambiguous risk registry | 是，FTS | `review_materials` | C 级，低权重、需免责声明 |
| `record_chunk_passage_links` | 676 | chunk -> main passage 回指关系 | 间接参与 | 间接影响证据槽 | chunk 命中后回填 canonical passage |
| `retrieval_sparse_fts` | 4280 | FTS5/BM25 虚表 | 是，sparse top-k | 否 | tokenizer 为 `trigram` |
| `vw_retrieval_records_unified` | 4280 | retrieval-facing 统一视图 | 是，运行时入口 | 否 | 不包含 annotation_links |

Dense index 当前只覆盖两类对象：

| FAISS / meta | 记录数 | 覆盖对象 |
| --- | ---: | --- |
| `artifacts/dense_chunks.faiss` / `dense_chunks_meta.json` | 583 | `records_chunks` |
| `artifacts/dense_main_passages.faiss` / `dense_main_passages_meta.json` | 777 | `records_main_passages` |

因此，`annotations`、`passages`、`ambiguous_passages` 参与 sparse/FTS 和后续融合，但不进入 dense FAISS index。

## 2. 原始 JSON 与运行时入库情况

| 原始数据文件 | 原始行数 | 运行时使用情况 |
| --- | ---: | --- |
| `books.json` | 1 | 只做数据说明/来源元数据，不进入检索 |
| `chapters.json` | 29 | `chapter_id/chapter_name/chapter_type/order` 被写入多张表，其中 chapter_name 参与展示 |
| `main_passages.json` | 1212 | safe runtime DB 入库 777 条 main_passages |
| `chunks.json` | 1119 | safe runtime DB 入库 583 条 chunks |
| `annotations.json` | 629 | 入库为 `records_annotations`，只做 secondary |
| `passages.json` | 1841 | 入库为 `records_passages`，只做 risk/review |
| `ambiguous_passages.json` | 450 | 入库为 `risk_registry_ambiguous` |
| `aliases.json` | 46 | 当前只在构建/验收层出现，未进入 runtime retrieval normalization |
| `annotation_links.json` | 619 | 当前运行时禁用，不进入 unified view |

## 3. 当前真正的检索单元

当前在线链路实际检索单元有四类：

1. `records_chunks`
   - `retrieval_text = chunk_text`
   - sparse 和 dense 都可召回
   - `evidence_level=C`，`display_allowed=preview_only`
   - 命中后通过 `record_chunk_passage_links` 找回 main_passages，chunk 本身不展示为 primary

2. `records_main_passages`
   - canonical-first 的核心检索单元
   - sparse 和 dense 都可召回
   - A 级可 primary，B 级只 secondary

3. `records_annotations`
   - 成无己注解 raw 辅助材料
   - sparse 可召回
   - 固定 secondary，不参与 primary

4. `records_passages` / `risk_registry_ambiguous`
   - full ledger 和 ambiguous 材料
   - sparse 可召回
   - 固定 review/risk，不进入 primary/secondary 主结论

commentarial layer 的 711 个讲稿单元不进入 `vw_retrieval_records_unified`，它们由 `backend/commentarial/layer.py` 单独路由和展示，属于 payload 里的 `commentarial` extension，不属于 primary/secondary/review 三个 evidence slot。

## 4. 当前真正的证据单元

| 证据槽 | 可进入对象 | 当前规则 |
| --- | --- | --- |
| `primary_evidence` | A 级 `main_passages` | 必须是 canonical 主文本且通过 topic/formula gate |
| `secondary_evidence` | B 级 `main_passages`、`annotations`、被降级的 main backref | 辅助解释，不作为主结论 |
| `review_materials` | `records_passages`、`risk_registry_ambiguous` | 风险核对材料 |
| `citations` | strong 引 primary；weak 引 secondary + review；refuse 为空 | citation 跟随证据槽，不单独从 commentarial 取 |
| `commentarial` | commentarial units | 独立 extension，不进入 confidence gate |

## 5. 当前真正进入链路的 metadata

已经实际进入检索、过滤、排序或展示的字段：

| 字段 | 作用 |
| --- | --- |
| `record_id`, `record_table`, `source_object` | 运行时对象识别、budget、证据槽归类 |
| `retrieval_text`, `normalized_text` | FTS、lexical score、dense embedding 输入 |
| `chapter_id`, `chapter_name` | 展示、上下文补齐、部分 scope 诊断 |
| `evidence_level`, `display_allowed` | evidence gating 主边界 |
| `risk_flag`, `requires_disclaimer` | weak/review 风险标签、提示语 |
| `default_weight_tier`, `policy_source_id` | sparse/fusion 权重、source budget |
| `backref_target_ids_json`, `record_chunk_passage_links` | chunk 命中后回指 canonical passage |
| `source_passage_count` | chunk 统计与回指检查 |
| `retrieval_primary_raw` | build 阶段决定 A/B 层，runtime 主要通过 `evidence_level` 使用 |
| `ambiguous_registry_hit`, `linked_passage_id` | ambiguous/risk 表构建和诊断 |

运行时计算出来但不落表的 metadata：

| 计算字段 | 作用 |
| --- | --- |
| `query_theme` | 区分 formula_name vs generic |
| `topic_consistency` | exact_formula_anchor、different_formula_anchor 等 |
| `primary_allowed`, `primary_block_reason` | primary gate / demotion |
| `stage_sources`, `stage_ranks` | sparse/dense/fusion 来源诊断 |
| `sparse_score`, `dense_score`, `rrf_score`, `rerank_score`, `combined_score` | 排序链路诊断 |

## 6. 目前“存着但没有充分使用”的 metadata

这些字段已经存在，但没有作为稳定的数据层 registry 或 runtime ranking/filtering 的一等输入：

| 字段/文件 | 现状 | 可优化方向 |
| --- | --- | --- |
| `aliases.json` | 46 条，构建/验收层可见；runtime 检索未直接加载 | 建成 `learner_query_normalization_lexicon` / alias FTS 扩展 |
| `source_file`, `source_item_no` | 入库但 unified view 不暴露 | 用于更自然 citation label、同源窗口、人工复核 |
| `text_role`, `role_confidence` | 入库但 runtime 排序不直接用 | 用于区分方名、组成、煎服法、注解、泛论 |
| `passage_order_in_chapter` | 入库，少量上下文补齐用 | 可建 canonical neighbor windows |
| `anchor_passage_id`, `source_anchor_passage_id` | 入库但 annotation_links 禁用后作用弱 | 可作为未来修复后的安全对齐字段 |
| `retrieval_tier_raw` | chunk 表保留，当前 chunk 均为 primary tier | 可拆分 chunk 召回权重 |
| `chapter_type` | 入库但不参与 routing/gating | 可避免 preface/appendix/音释误入主候选 |
| commentarial `commentary_functions`, `comparison_focus`, `selection_flag`, `teaching_points` | 文件中存在，runtime 部分评分用，但没有规范 scope registry | 建 `unit_scope_type` 和 `commentarial_alignment_registry` |

## 7. chunk 策略清单

当前 runtime chunk 类型只有两类：

| chunk_type | count | avg_len | min_len | max_len | 当前作用 |
| --- | ---: | ---: | ---: | ---: | --- |
| `main_text` | 474 | 58.6 | 20 | 469 | canonical 片段召回，回指 main_passages |
| `formula_bundle` | 109 | 99.7 | 25 | 413 | 方剂/煎服法召回，回指 main_passages |

chunk 当前固定为：

- `evidence_level=C`
- `display_allowed=preview_only`
- `default_weight_tier=highest`
- `policy_source_id=safe_chunks`
- 可参与 sparse/dense/fusion/rerank
- 不直接展示为 primary/secondary/review
- 通过 backref 将 linked main_passages 放入 primary 或 secondary

实际风险：chunk 权重高，能提升召回，但如果 chunk 回指范围不够精细，后续候选里容易出现相邻方、连续方文、同章风险材料混杂。

## 8. commentarial 与 canonical 对齐现状

commentarial bundle 当前有：

- 711 个讲稿单元
- 831 条 resolved anchor links
- anchor_type：exact 549、theme 97、multi 59、excerpt 6
- 刘渡舟 438 单元，郝万山 273 单元
- `never_use_in_primary=711`
- `use_for_confidence_gate=0`
- `needs_manual_anchor_review=60`
- `needs_manual_content_review=6`
- resolved status 中 `theme_only_no_passage_resolution=97`

这说明 commentarial 层已经有初步结构化锚点，但还不够支撑稳定的数据层优化：

1. 已有“单元到 canonical passage”的 anchor 信息，但没有进入主 SQLite schema。
2. 有 `commentary_functions`，但缺少面向检索展示的 `unit_scope_type`：single_formula / comparison / broad_discussion / incidental_mention。
3. 有 named/comparison/meta eligibility，但没有把“顺带提及”和“主讲对象”分开。
4. theme-only 单元 97 条，只适合学习视角，不适合作为具体方剂/条文问题的默认证据补充。
5. 当前 commentarial extension 与 primary/secondary/review 是分离的，符合冻结边界；下一轮只能增强对齐/筛选，不应提升其证据层级。

## 9. 结论

当前系统真正的检索底座是 `vw_retrieval_records_unified + retrieval_sparse_fts + dense_chunks/dense_main FAISS`。真正的证据底座是 canonical main_passages A/B、annotations B、passages/ambiguous C 三层。最明显的数据层缺口不是“没有检索”，而是缺少稳定 registry：方剂规范表、别名归一表、主题/概念标签、commentarial scope 类型、canonical 邻接窗口和 retrieval-ready denormalized views。
