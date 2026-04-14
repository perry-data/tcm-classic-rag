# 《伤寒论》RAG 数据库落库方案（MVP）

## 1. 本轮结论

本轮建议采用 `5 + 1 + 1(optional)` 结构：

1. `records_main_passages`
2. `records_chunks`
3. `records_annotations`
4. `records_passages`
5. `risk_registry_ambiguous`
6. `record_chunk_passage_links`
7. `disabled_annotation_links`（可选，仅审计留档，不进运行链路）

并额外设计一个逻辑统一检索视图：

- `vw_retrieval_records_unified`

这个视图不是新的事实表，只是把多源记录统一暴露成后续 BM25 / FTS / 规则检索可消费的同构结构。

## 2. 设计边界

本轮只把分层策略翻译成数据库结构，不包含：

- 建表 SQL
- 数据导入代码
- API
- 前端
- 向量检索

## 3. 冻结文件审计结论

本方案基于以下冻结文件：

- [06_layered_enablement_policy.md](/Users/man_ray/Projects/Python/tcm-classic-rag/docs/data/06_layered_enablement_policy.md)
- [layered_enablement_policy.json](/Users/man_ray/Projects/Python/tcm-classic-rag/config/layered_enablement_policy.json)
- [layered_field_mapping.md](/Users/man_ray/Projects/Python/tcm-classic-rag/docs/data/layered_field_mapping.md)
- [zjshl_dataset_v2_v1_safe.zip](/Users/man_ray/Projects/Python/tcm-classic-rag/dist/zjshl_dataset_v2_v1_safe.zip)
- `zjshl_dataset_v2.zip` 对应内容在当前工作区未见原始 zip；字段审计使用 [data/processed/zjshl_dataset_v2](/Users/man_ray/Projects/Python/tcm-classic-rag/data/processed/zjshl_dataset_v2) 作为 full 数据等价来源。

已核对到的关键事实：

- safe `main_passages` 共 777 条，其中 666 条可保留为 Level A，111 条被 safe 降级为 Level B。
- full `main_passages` 共 1212 条，safe `main_passages` 是其子集。
- safe `chunks` 共 583 条，full `chunks` 共 1119 条，safe `chunks` 是其子集。
- safe `chunks` 全部可以回指到 safe `main_passages`。
- 583 个 safe `chunks` 中有 67 个对应多个 `source_passage_ids`，因此需要单独关系表。
- full `annotations` 共 629 条，其中 619 条带 `anchor_passage_id`，但该挂接链本轮不得启用。
- full `passages` 共 1841 条，是全文总账层。
- `ambiguous_passages` 共 450 条，全部能在 full `passages` 中找到同 `passage_id`；其中 435 条对应 full `main_passages`，但与 safe `main_passages` 零重合。
- safe `chunks` 与 safe `main_passages` 和 `ambiguous_passages` 也零重合，因此风险层可以独立建模。

## 4. safe / full 双数据源如何落库

### 4.1 落库原则

最小实现不建议把 safe/full 两套文件完整双份落库，而建议按“策略实际启用对象”装载：

- 从 safe 落库：
  - `main_passages`
  - `chunks`
- 从 full 落库：
  - `annotations`
  - `passages`
  - `ambiguous_passages`
- 默认不落运行时表：
  - full `main_passages`
  - full `chunks`
  - safe `annotations`
  - safe `passages`
  - safe `ambiguous_passages`
- 默认不进入运行链路：
  - `annotation_links`

### 4.2 为什么不把 safe/full 全对象双份入库

原因有三点：

1. 策略并不要求 full `main_passages` 和 full `chunks` 作为独立检索对象启用。
2. safe 与 full 在 `annotations/passages` 上存在同 ID 但字段内容不同的情况，例如 `anchor_passage_id` 被 safe 清空、`passages.retrieval_primary` 被 safe 重写；若双份无节制入库，后续实现要处理大量无收益的重复记录。
3. 最小数据库实现的目标是承接策略，不是保留所有可能的数据演化形态。

补充约束：

- 与 `ambiguous_passages` 关联的 full `main_passages/chunks` 不再以独立运行时表承接。
- 它们的风险回退角色统一由 `records_passages + risk_registry_ambiguous` 覆盖。

### 4.3 `dataset_variant` 的解释

`dataset_variant` 表示该条运行时记录实际来自哪一套导入源：

- `safe`
- `full`

它不是“风险等级”的别名。风险等级仍由 `evidence_level`、`display_allowed`、`risk_flag` 决定。

## 5. 统一字段约定

以下字段应作为所有运行时记录表的公共最小字段：

| 字段 | 说明 |
| --- | --- |
| `record_id` | 运行时主键，建议格式 `dataset_variant:source_object:source_record_id` |
| `source_record_id` | 原始对象主键，`passage_id` / `chunk_id` / `link_id` |
| `dataset_variant` | `safe` / `full` |
| `source_object` | `main_passages` / `chunks` / `annotations` / `passages` / `ambiguous_passages` / `annotation_links` |
| `source_type` | `main_text` / `chunk` / `annotation` / `ledger_text` / `risk_registry` / `link_relation` |
| `retrieval_allowed` | 是否允许进入召回 |
| `evidence_level` | `A` / `B` / `C` / `D` |
| `display_allowed` | `primary` / `secondary` / `risk_only` / `preview_only` / `false` |
| `risk_flag` | 建议用数组保存，可为空数组，也可包含 `annotation_unlinked` / `ambiguous_source` / `ledger_mixed_roles` / `strong_evidence_insufficient` |
| `requires_disclaimer` | 是否必须前台提示 |
| `default_weight_tier` | `highest` / `high` / `medium` / `medium_low` / `low` / `lowest` / `off` |
| `policy_source_id` | 对应 [layered_enablement_policy.json](/Users/man_ray/Projects/Python/tcm-classic-rag/config/layered_enablement_policy.json) 里的 `source_id` |
| `policy_version` | 建议固定为 `2026-04-02` 或等价策略版本号 |

说明：

- `risk_flag` 不建议做单值字符串，原因是 `records_passages` 可能同时带 `ledger_mixed_roles` 和 `ambiguous_source`。
- 所有可检索表都建议保存 `normalized_text`，即使原始对象未提供，也应在导入阶段生成。

## 6. 物理表设计

### 6.1 `records_main_passages`

用途：

- 主证据事实表。
- 同时承接 Level A 和 Level B。
- 也是 `chunks` 回指后的最终落点。

记录粒度：

- safe `main_passages` 一条原始记录对应一行。

数据来源：

- safe `main_passages.json`

主键：

- `record_id`

最小字段：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `record_id` | 派生 | `safe:main_passages:{passage_id}` |
| `source_record_id` | `passage_id` | 原始主键 |
| `passage_id` | 原始 | 显式保留，便于回指 |
| `dataset_variant` | 固定 | `safe` |
| `source_object` | 固定 | `main_passages` |
| `source_type` | 固定 | `main_text` |
| `book_id` | 原始 | 来源 |
| `chapter_id` | 原始 | 来源 |
| `chapter_name` | 原始 | 来源 |
| `chapter_type` | 原始 | 来源 |
| `passage_order_in_chapter` | 原始 | 章内排序 |
| `source_file` | 原始 | 来源文件 |
| `source_item_no` | 原始 | 来源序号 |
| `text` | 原始 | 原文文本字段 |
| `normalized_text` | 原始 | 检索文本字段 |
| `text_role` | 原始 | 原始角色 |
| `role_confidence` | 原始 | 原始置信度 |
| `anchor_passage_id` | 原始 | 原字段保留 |
| `retrieval_primary_raw` | 原始 `retrieval_primary` | 原始 safe 标记 |
| `retrieval_allowed` | 固定 | `true` |
| `evidence_level` | 派生 | `true -> A`，`false -> B` |
| `display_allowed` | 派生 | `A -> primary`，`B -> secondary` |
| `risk_flag` | 派生 | `A -> []`，`B -> ["short_text_demoted"]` |
| `requires_disclaimer` | 固定 | `false` |
| `default_weight_tier` | 派生 | `A -> high`，`B -> medium` |
| `policy_source_id` | 派生 | `safe_main_passages_primary` 或 `safe_main_passages_secondary` |

### 6.2 `records_chunks`

用途：

- 第一阶段召回骨架。
- 命中预览对象。
- 本身不作为最终主证据。

记录粒度：

- safe `chunks` 一条原始记录对应一行。

数据来源：

- safe `chunks.json`

主键：

- `record_id`

最小字段：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `record_id` | 派生 | `safe:chunks:{chunk_id}` |
| `source_record_id` | `chunk_id` | 原始主键 |
| `chunk_id` | 原始 | 显式保留 |
| `dataset_variant` | 固定 | `safe` |
| `source_object` | 固定 | `chunks` |
| `source_type` | 固定 | `chunk` |
| `book_id` | 原始 | 来源 |
| `chapter_id` | 原始 | 来源 |
| `chapter_name` | 原始 | 来源 |
| `chunk_type` | 原始 | 原始角色 |
| `retrieval_tier_raw` | 原始 `retrieval_tier` | 原字段保留 |
| `chunk_text` | 原始 | 原文文本字段 |
| `normalized_text` | 原始 | 检索文本字段 |
| `source_passage_ids_json` | 原始 | 保留原始数组 |
| `source_passage_count` | 派生 | 数组长度 |
| `retrieval_allowed` | 固定 | `true` |
| `evidence_level` | 固定 | `C` |
| `display_allowed` | 固定 | `preview_only` |
| `risk_flag` | 固定 | `[]` |
| `requires_disclaimer` | 固定 | `false` |
| `default_weight_tier` | 固定 | `highest` |
| `policy_source_id` | 固定 | `safe_chunks` |

强约束：

- `records_chunks` 命中后必须经 `record_chunk_passage_links` 回指到 `records_main_passages`。
- `chunks` 不允许直接进入 `primary_evidence`。

### 6.3 `record_chunk_passage_links`

用途：

- 解决 `chunks.source_passage_ids` 为多值数组的问题。
- 作为 `chunks -> main_passages` 的唯一运行时回指关系。

记录粒度：

- 一个 `chunk_id` 与一个 `passage_id` 的对应关系一行。

数据来源：

- safe `chunks.source_passage_ids`

主键：

- `link_id`

最小字段：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `link_id` | 派生 | 建议 `safe:chunks:{chunk_id}:{ordinal}` |
| `chunk_record_id` | 派生 | FK 到 `records_chunks.record_id` |
| `chunk_id` | 原始 | 冗余保留，便于排查 |
| `main_passage_record_id` | 派生 | FK 到 `records_main_passages.record_id` |
| `main_passage_id` | 原始 | 对应 `passage_id` |
| `link_order` | 派生 | 对应 `source_passage_ids` 顺序 |
| `backref_source` | 固定 | `source_passage_ids` |

说明：

- 本表是必需表，不建议只把 `source_passage_ids` 塞进 JSON 后在检索时临时拆解。

### 6.4 `records_annotations`

用途：

- 辅助证据表。
- 可检索、可展示，但只能按“注解原文片段”处理。

记录粒度：

- full `annotations` 一条原始记录对应一行。

数据来源：

- full `annotations.json`

主键：

- `record_id`

最小字段：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `record_id` | 派生 | `full:annotations:{passage_id}` |
| `source_record_id` | `passage_id` | 原始主键 |
| `annotation_id` | 原始 `passage_id` | 可与 `source_record_id` 相同 |
| `passage_id` | 原始 | 保留原字段 |
| `dataset_variant` | 固定 | `full` |
| `source_object` | 固定 | `annotations` |
| `source_type` | 固定 | `annotation` |
| `book_id` | 原始 | 来源 |
| `chapter_id` | 原始 | 来源 |
| `chapter_name` | 原始 | 来源 |
| `chapter_type` | 原始 | 来源 |
| `passage_order_in_chapter` | 原始 | 来源 |
| `source_file` | 原始 | 来源文件 |
| `source_item_no` | 原始 | 来源序号 |
| `text` | 原始 | 原文文本字段 |
| `normalized_text` | 原始 | 检索文本字段 |
| `text_role` | 原始 | 原始角色 |
| `role_confidence` | 原始 | 原始置信度 |
| `source_anchor_passage_id` | 原始 `anchor_passage_id` | 只保留作审计，不作为运行时 join 键 |
| `retrieval_primary_raw` | 原始 `retrieval_primary` | 原字段保留 |
| `retrieval_allowed` | 固定 | `true` |
| `evidence_level` | 固定 | `B` |
| `display_allowed` | 固定 | `secondary` |
| `risk_flag` | 固定 | `["annotation_unlinked"]` |
| `requires_disclaimer` | 固定 | `true` |
| `default_weight_tier` | 固定 | `medium_low` |
| `policy_source_id` | 固定 | `full_annotations_raw` |
| `linkage_enabled` | 固定 | `false` |

强约束：

- 即使 `source_anchor_passage_id` 非空，也不得自动挂接正文，不得自动升格为主证据。

### 6.5 `records_passages`

用途：

- 全量总账兜底表。
- 只承担 Level C 候选召回、上下文回查与风险模式补充。

记录粒度：

- full `passages` 一条原始记录对应一行。

数据来源：

- full `passages.json`

主键：

- `record_id`

最小字段：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `record_id` | 派生 | `full:passages:{passage_id}` |
| `source_record_id` | `passage_id` | 原始主键 |
| `passage_id` | 原始 | 原始主键 |
| `dataset_variant` | 固定 | `full` |
| `source_object` | 固定 | `passages` |
| `source_type` | 固定 | `ledger_text` |
| `book_id` | 原始 | 来源 |
| `chapter_id` | 原始 | 来源 |
| `chapter_name` | 原始 | 来源 |
| `chapter_type` | 原始 | 来源 |
| `passage_order_in_chapter` | 原始 | 来源 |
| `source_file` | 原始 | 来源文件 |
| `source_item_no` | 原始 | 来源序号 |
| `text` | 原始 | 原文文本字段 |
| `normalized_text` | 原始 | 检索文本字段 |
| `text_role` | 原始 | 原始角色 |
| `role_confidence` | 原始 | 原始置信度 |
| `source_anchor_passage_id` | 原始 `anchor_passage_id` | 原字段保留，不启用自动证据链 |
| `retrieval_primary_raw` | 原始 `retrieval_primary` | 原字段保留，仅审计 |
| `retrieval_allowed` | 固定 | `true` |
| `evidence_level` | 固定 | `C` |
| `display_allowed` | 固定 | `risk_only` |
| `risk_flag` | 派生 | 默认 `["ledger_mixed_roles"]`；若命中 ambiguous，再叠加 `ambiguous_source` |
| `requires_disclaimer` | 固定 | `true` |
| `default_weight_tier` | 固定 | `low` |
| `policy_source_id` | 固定 | `full_passages_ledger` |
| `ambiguous_registry_hit` | 派生 | 是否在 `risk_registry_ambiguous` 中存在同 `passage_id` |

强约束：

- `records_passages` 不能直接升格为主证据。

### 6.6 `risk_registry_ambiguous`

用途：

- 风险登记表。
- 承接 `ambiguous_passages` 的文本检索和风险标签判断。

记录粒度：

- full `ambiguous_passages` 一条原始记录对应一行。

数据来源：

- full `ambiguous_passages.json`

主键：

- `record_id`

最小字段：

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `record_id` | 派生 | `full:ambiguous_passages:{passage_id}` |
| `source_record_id` | `passage_id` | 原始主键 |
| `passage_id` | 原始 | 风险主键 |
| `dataset_variant` | 固定 | `full` |
| `source_object` | 固定 | `ambiguous_passages` |
| `source_type` | 固定 | `risk_registry` |
| `chapter_id` | 原始 | 来源 |
| `source_file` | 原始 | 来源文件 |
| `source_item_no` | 原始 | 来源序号 |
| `text` | 原始 | 原文文本字段 |
| `normalized_text` | 派生 | 对 `text` 做同规则规范化 |
| `text_role` | 原始 | 原始角色 |
| `retrieval_allowed` | 固定 | `true` |
| `evidence_level` | 固定 | `C` |
| `display_allowed` | 固定 | `risk_only` |
| `risk_flag` | 固定 | `["ambiguous_source"]` |
| `requires_disclaimer` | 固定 | `true` |
| `default_weight_tier` | 固定 | `lowest` |
| `policy_source_id` | 固定 | `ambiguous_related_material` |
| `linked_passage_record_id` | 派生 | FK 到 `records_passages.record_id` |
| `linked_passage_id` | 派生 | 对应 full `passages.passage_id` |

强约束：

- 该表只承担风险召回与风险判断，不承担主证据职责。

### 6.7 `disabled_annotation_links`（可选）

用途：

- 如果下一轮实现希望把 `annotation_links` 留档进库，可用此表隔离保存。

记录粒度：

- full `annotation_links` 一条原始记录对应一行。

是否必需：

- 否。最小实现可以完全不导入该对象。

若导入，最小字段：

| 字段 | 说明 |
| --- | --- |
| `record_id` | `full:annotation_links:{link_id}` |
| `source_record_id` | 原始 `link_id` |
| `dataset_variant` | `full` |
| `source_object` | `annotation_links` |
| `source_type` | `link_relation` |
| `from_passage_id` | 原始 |
| `to_passage_id` | 原始 |
| `relation` | 原始 |
| `confidence` | 原始 |
| `retrieval_allowed` | `false` |
| `evidence_level` | `D` |
| `display_allowed` | `false` |
| `risk_flag` | `["disabled_link_layer"]` |
| `requires_disclaimer` | `false` |
| `default_weight_tier` | `off` |

强约束：

- 不进统一检索视图。
- 不建运行时 join。
- 不参与证据链拼接。

## 7. 是否需要统一检索视图

需要。

建议设计逻辑视图 `vw_retrieval_records_unified`，统一暴露所有 `retrieval_allowed = true` 的运行时记录，供后续：

- BM25
- SQLite FTS
- 规则检索
- 混合排序

使用。

### 7.1 视图来源

视图只 union 以下来源：

- `records_chunks`
- `records_main_passages`
- `records_annotations`
- `records_passages`
- `risk_registry_ambiguous`

视图明确排除：

- `disabled_annotation_links`
- 任何 `retrieval_allowed = false`

### 7.2 视图最小字段

| 字段 | 说明 |
| --- | --- |
| `retrieval_entry_id` | 通常等于 `record_id` |
| `record_table` | 原表名 |
| `record_id` | 原表主键 |
| `source_record_id` | 原始对象主键 |
| `dataset_variant` | safe / full |
| `source_object` | 原始对象类型 |
| `source_type` | 业务角色 |
| `retrieval_text` | 对 chunks 取 `chunk_text`，其他取 `text` |
| `normalized_text` | 检索标准文本 |
| `book_id` | 可空 |
| `chapter_id` | 可空 |
| `chapter_name` | 可空 |
| `evidence_level` | A / B / C |
| `display_allowed` | primary / secondary / risk_only / preview_only |
| `risk_flag` | 风险标签数组 |
| `requires_disclaimer` | 是否前台提示 |
| `default_weight_tier` | 权重层级 |
| `policy_source_id` | 策略来源 |
| `backref_target_type` | `main_passages` / `passages` / `none` |
| `backref_target_ids_json` | 例如 chunk 对应的 safe `passage_id` 列表 |

### 7.3 视图的职责边界

该视图只负责统一检索入口，不负责替代事实表。

后续如果需要 FTS/BM25 的物理索引表，可以从该视图再派生，例如：

- `fts_retrieval_records`

但它应是索引副本，不应成为新的真值表。

## 8. 最小检索流设计

### 8.1 第一阶段优先检索哪些对象

第一阶段检索优先顺序应与策略文件一致：

1. safe `chunks`
2. safe `main_passages` Level A
3. safe `main_passages` Level B
4. full `annotations`
5. full `passages`
6. `ambiguous_passages`

数据库实现上建议直接对 `vw_retrieval_records_unified` 取候选，但排序时先按 `default_weight_tier`，再按文本匹配分数。

### 8.2 `chunks` 命中后如何回指 `main_passages`

流程：

1. 命中 `records_chunks`
2. 用 `record_chunk_passage_links` 找到一个或多个 `main_passage_id`
3. 读取对应 `records_main_passages`
4. 以 `records_main_passages` 作为后续证据筛选对象
5. chunk 本身只保留为命中预览或调试痕迹

结论：

- `chunks` 不能直接充当 `primary_evidence`
- `chunks` 的业务价值是“先命中、再回指”

### 8.3 `annotations` 如何作为辅助材料进入结果集

规则：

- `records_annotations` 可直接参与检索。
- 命中后进入 `secondary_evidence` 候选池。
- 即使 `source_anchor_passage_id` 非空，也不与正文自动拼接。
- 展示时必须带 `annotation_unlinked` 风险提示。

### 8.4 `passages` 和 `ambiguous_passages` 如何只承担兜底/风险角色

规则：

- `records_passages` 只进入 `risk_materials` 候选池。
- `risk_registry_ambiguous` 只进入 `risk_materials` 与风险判断池。
- 二者都不允许直接升格为 `primary_evidence`。
- 若 `records_passages.passage_id` 同时存在于 `risk_registry_ambiguous`，则该 passage 至少附加 `ambiguous_source` 风险标记。

### 8.5 `annotation_links` 如何在数据库层保持禁用

最低要求：

- 不进 `vw_retrieval_records_unified`
- 不作为 join 来源
- 不参与证据链生成
- 不被任何“正文-注解自动关联”逻辑读取

建议做法二选一：

1. MVP 完全不导入
2. 如需审计，导入 `disabled_annotation_links`，但强制 `retrieval_allowed = false`

## 9. 不同回答模式对数据库结果的要求

### 9.1 Strong 模式

数据库结果至少满足：

- `primary_evidence_count >= 1`
- 该主证据必须来自 `records_main_passages`
- 如果主证据来自 chunk 命中，也必须先完成 `chunk -> main_passages` 回指后才能计入

允许附带：

- `secondary_evidence` 中的 safe Level B 主条
- `secondary_evidence` 中的 full `annotations`

### 9.2 Weak + Review 模式

数据库结果至少满足：

- `primary_evidence_count = 0`
- `secondary_evidence_count >= 1` 或 `risk_material_count >= 1`

最少返回内容：

- 至少一条 `secondary_evidence` 或 `risk_materials`
- 必须附加 `strong_evidence_insufficient`
- 若使用 `annotations`，同时附加 `annotation_unlinked`
- 若使用 `passages/ambiguous`，附加对应风险标签

### 9.3 Refuse 模式

数据库结果层的触发条件：

- `primary_evidence_count = 0`
- `secondary_evidence_count = 0`
- `risk_material_count = 0`

也就是：

- 检索后没有任何 `retrieval_allowed = true` 的合格记录进入结果槽位
- 或只有被过滤掉的禁用层记录

## 10. 下一轮最小数据库实现可直接照此落地

下一轮实现时，只需照本方案完成：

1. 五张事实表落库
2. 一张 chunk 回指关系表落库
3. 一张统一检索视图
4. 可选一张禁用链接隔离表

只要这些结构落好，就已经足以支撑：

- 最小 BM25 / FTS 检索入口
- `chunks -> main_passages` 回指
- A/B/C 分层筛选
- strong / weak_with_review_notice / refuse 三种回答模式判定
