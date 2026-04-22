# Formula Object Upgrade v1

## Scope

本轮只改数据层、retrieval/runtime normalization 和验证脚本：

- 不改 prompt。
- 不改前端。
- 不改 API payload contract。
- 不改 answer_mode 定义。
- 不改 commentarial layer 主逻辑。
- 不把 commentarial 提升为 primary。
- 不重开 safe dataset 边界。

## Implemented Runtime Objects

### formula_canonical_registry

构建脚本：`scripts/data_implementation/build_formula_registry_v1.py`

落库位置：`artifacts/zjshl_v1.db`

字段包含：

- `formula_id`
- `canonical_name`
- `normalized_name`
- `primary_formula_passage_id`
- `chapter_id`
- `formula_span_start_passage_id`
- `formula_span_end_passage_id`
- `composition_passage_ids_json`
- `decoction_passage_ids_json`
- `usage_context_passage_ids_json`
- `source_confidence`
- `is_active`

本轮额外保留 `source_passage_ids_json` 与 `chapter_ids_json`，用于 runtime 快速判断 passage 是否落在同一 formula span 内。

当前构建结果：

- formula rows: 106
- source_confidence high: 92
- source_confidence medium: 14

### formula_alias_registry

构建脚本将方剂 alias 数据化，并接入 runtime normalization。

覆盖内容：

- canonical 方名。
- `汤/汤方`、`散/散方`、`丸/丸方` 等 `方` 后缀变体。
- `data/processed/zjshl_dataset_v2/aliases.json` 中现有方剂条目。
- `浓朴/厚朴`、`杏子/杏仁`、`乾/干` 等常见自动变体。

自动生成 alias 明确标记：

- `is_auto_generated=1`
- `source=auto:*`
- `confidence` 低于 canonical/source alias

歧义 normalized alias 会被标记为 `needs_manual_review=1` 并降到 runtime 阈值以下，不作为人工确认 alias 混入 runtime。

当前构建结果：

- alias rows: 232
- canonical: 106
- suffix/source suffix variants: 106
- orthographic variants: 20
- aliases.json formula aliases: 16

### retrieval_ready_formula_view

`retrieval_ready_formula_view` 是本轮新增的运行时检索对象，一行对应一个 `formula_id`。

字段包含：

- `formula_id`
- `canonical_name`
- `normalized_name`
- `alias_text`
- `formula_name_text`
- `composition_text`
- `decoction_text`
- `usage_context_text`
- `neighbor_context_text`
- `retrieval_text`
- `primary_formula_passage_id`
- `formula_span_start_passage_id`
- `formula_span_end_passage_id`
- `source_passage_ids_json`
- `chapter_ids_json`
- `allowed_evidence_level`
- `source_confidence`

`retrieval_text` 由标准方名、alias、组成、煎服法、使用语境和必要邻接上下文拼接。核心正文只来自 safe `records_main_passages`，不把 `records_passages` / `ambiguous_passages` 作为 formula view 正文来源。

## Runtime Wiring

修改位置：

- `backend/retrieval/minimal.py`
- `backend/retrieval/hybrid.py`

新增行为：

1. `FormulaRuntimeIndex` 从 SQLite 的 `formula_canonical_registry`、`formula_alias_registry`、`retrieval_ready_formula_view` 加载运行时索引。
2. query 入口先做 formula normalization。
3. 单方题命中 `target_formula_id`。
4. 比较题命中 `left_formula_id` / `right_formula_id`。
5. 命中 formula_id 后显式召回 `retrieval_ready_formula_view`，不再只依赖 FTS 分词碰撞。
6. target formula object / same formula span 加权。
7. different / expanded formula anchor 在 formula query 下被 final gate 过滤或降权，不再进入 top candidates。
8. formula object 本身只作为 retrieval candidate；最终 primary evidence 仍回填 safe `records_main_passages`，payload evidence slot 不新增 `formulas` 类型。

可关闭开关：

- `TCM_DISABLE_FORMULA_OBJECT_RETRIEVAL=1`

回归脚本用该开关生成 before，对照默认启用后的 after。

## Regression

脚本：

- `scripts/data_implementation/run_formula_runtime_regression_v1.py`

产物：

- `artifacts/data_implementation/formula_runtime_regression_v1.json`
- `artifacts/data_implementation/formula_runtime_regression_v1.md`

回放设置：

- 来源：`artifacts/data_diagnostics/suspected_failure_pool_v1.json`
- 样本数：15
- engine：hybrid
- `PERF_RETRIEVAL_MODE=sparse`
- `PERF_DISABLE_RERANK=1`
- `PERF_DISABLE_LLM=1`

核心结果：

- top-5 bad formula anchors: 11 -> 0
- expanded_formula_anchor: 10 -> 0
- formula_cross_target_candidates triggers: 8 -> 0
- high_risk_candidate_dominance triggers: 9 -> 1
- top-5 risk candidates: 27 -> 15
- primary formula object backrefs: 0 -> 20
- after 中 9 条 exact、6 条 comparison 均命中 formula_id。

## primary/full:passages Contradiction

结论：不是 suspected pool 导出错，也不是离线脚本把 evidence slot 记错。当前线上装配链路确实会在 definition priority 分支中把 `full:passages:*` 放进 payload `primary_evidence`。

核查证据：

- `suspected_failure_pool_v1.json` 中有 3 条 `current_output_summary.primary_record_ids` 为 `full:passages:*`。
- 当前 runtime 复跑同三条 query，payload 仍出现 `full:passages:*` primary。
- 直接调用 retrieval 时，`primary_evidence` 仍是 safe `main_passages`，说明越界发生在 AnswerAssembler 的 definition priority 装配层，而不是 retrieval evidence gate。
- 具体原因在 `config/controlled_replay/definition_query_priority_rules_v1.json`：`primary_source_allowlist` 包含 `passages`，且 `source_object_bonus` 给了 `passages` 正分。`backend/answers/assembler.py` 的 `_assemble_definition_priority_query()` 会从 raw candidates 中按该规则重选 primary。

本轮未修复该问题，因为它属于 definition query / assembler evidence-slot 规则，不属于本轮冻结的方剂对象改造范围。下一轮应单独处理：把 definition priority 的 primary allowlist 收紧到 `main_passages`，或明确将 `passages` 只允许进 secondary/review。
