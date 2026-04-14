# MVP 数据库构建报告

## 运行命令

`python build_v1_database.py --safe-source dist/zjshl_dataset_v2_v1_safe.zip --full-source data/processed/zjshl_dataset_v2`

## 输入源

- safe 数据源：`/Users/man_ray/Projects/Python/tcm-classic-rag/dist/zjshl_dataset_v2_v1_safe.zip`（zip）
- full 数据源：`/Users/man_ray/Projects/Python/tcm-classic-rag/data/processed/zjshl_dataset_v2`（directory）
- 当前工作区未检测到 `dist/zjshl_dataset_v2.zip`；本次构建使用目录输入 `/Users/man_ray/Projects/Python/tcm-classic-rag/data/processed/zjshl_dataset_v2` 作为 full 数据源。

## 输出

- 数据库文件：`/Users/man_ray/Projects/Python/tcm-classic-rag/artifacts/zjshl_v1.db`
- policy version：`2026-04-02`
- schema draft version：`2026-04-03`

## 必需对象检查

- 已创建六张必需表：`records_main_passages`、`records_chunks`、`records_annotations`、`records_passages`、`risk_registry_ambiguous`、`record_chunk_passage_links`。
- 已创建视图：`vw_retrieval_records_unified`。
- 未创建 `disabled_annotation_links` 运行时表。这是有意决策，原因是本轮要求默认不启用 `annotation_links`。

## 表级统计

- `records_main_passages`: 777
- `records_chunks`: 583
- `records_annotations`: 629
- `records_passages`: 1841
- `risk_registry_ambiguous`: 450
- `record_chunk_passage_links`: 676
- `vw_retrieval_records_unified`: 4280

## 关键校验

- `record_chunk_passage_links` 行数：676
- 多 passage chunk 数：67
- `annotation_links` 出现在 unified view 的行数：0
- chunk 主证据违规数：0
- annotation 辅助证据违规数：0
- passages 风险层违规数：0
- ambiguous 风险层违规数：0

## 与文档/JSON 的实现决策说明

- 字段与分层规则以冻结策略文件和 `database_schema_draft.json` 为准实现。
- `policy_version` 使用 `layered_enablement_policy.json.version`，而不是 schema draft 文件自身版本号。
- `risk_registry_ambiguous.normalized_text` 由原始 `text` 生成，因为源对象本身不带该字段。
- unified view 中 chunk 的 `backref_target_ids_json` 直接使用 `records_chunks.source_passage_ids_json`；真实回指关系仍由 `record_chunk_passage_links` 承担并在 smoke check 中验证。
- 未发现需要违背冻结策略的实现冲突。
