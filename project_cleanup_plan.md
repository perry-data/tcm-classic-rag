# Project Cleanup Plan

## This Round

- 本轮只做识别和方案输出，没有执行任何不可逆删除。
- 判断原则：不确定是否可删时，优先保守到 `archive` 或 `keep`。
- `.git/` 内部对象未纳入清理建议。

## Current Mainline Conclusion

- 当前检索主入口：`run_hybrid_retrieval.py`。
- 当前回答编排主入口：`run_answer_assembler.py`。
- 当前 retrieval 基础骨架：`run_minimal_retrieval.py`，被 hybrid 直接复用，不可误删。
- 当前数据准备主链：`scripts/check_dataset_acceptance.py` -> `scripts/build_mvp_safe_dataset.py` -> `build_mvp_database.py` -> `build_dense_index.py`。
- 当前最重要的 examples / smoke checks：`artifacts/database_smoke_checks.md`、`artifacts/hybrid_retrieval_examples.json`、`artifacts/hybrid_retrieval_smoke_checks.md`、`artifacts/hybrid_answer_examples.json`、`artifacts/hybrid_answer_smoke_checks.md`。
- 已被新文件替代的旧结果：`artifacts/answer_examples.json` / `artifacts/answer_smoke_checks.md` 被 `artifacts/hybrid_answer_*` 替代；`artifacts/retrieval_*` 仍可作为 minimal 基线，但不再是当前主验证结果。

## Keep

| 路径 / 文件组 | 分类 | 附加标记 | 原因 |
| --- | --- | --- | --- |
| `answer_payload_contract.md` | A | - | 回答 payload 合同文件；当前 answer assembler 需要保持兼容。 |
| `build_dense_index.py` | A | - | 当前 dense index 构建入口。 |
| `build_mvp_database.py` | A | - | 当前 SQLite 落库入口。 |
| `database_schema_draft.json` | A | - | 数据库构建脚本当前读取的 schema/source-resolution 配置。 |
| `dense_retrieval_plan.md` | B | - | 当前有效的说明、验证样例或报告。 |
| `hybrid_answer_assembler_patch_note.md` | B | - | 当前有效的说明、验证样例或报告。 |
| `hybrid_retrieval_patch_note.md` | B | - | 当前有效的说明、验证样例或报告。 |
| `layered_enablement_policy.json` | A | - | 运行时策略源文件。 |
| `retrieval_precision_patch_note.md` | B | - | 当前有效的说明、验证样例或报告。 |
| `run_answer_assembler.py` | A | - | 当前回答编排主入口。 |
| `run_hybrid_retrieval.py` | A | - | 当前检索主入口。 |
| `run_minimal_retrieval.py` | A | - | 当前 minimal 检索基线与 hybrid 检索共享骨架；虽不是主入口，但仍是运行时依赖。 |
| `.gitignore` | A | - | 当前版本控制忽略规则；决定缓存/索引/环境目录是否入库。 |
| `artifacts/database_build_report.md` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/database_counts.json` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/database_smoke_checks.md` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/dense_chunks_meta.json` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/dense_index_build_report.md` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/dense_main_passages_meta.json` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/hybrid_answer_examples.json` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/hybrid_answer_smoke_checks.md` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/hybrid_retrieval_examples.json` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/hybrid_retrieval_smoke_checks.md` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/zjshl_mvp.db` | C | rebuildable_artifact | 当前仍在使用的运行产物；可重建，但本轮不建议移除。 |
| `data/processed/zjshl_dataset_v2/README_parse_report_v2.md` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/aliases.json` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/ambiguous_passages.json` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/annotation_links.json` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/annotations.json` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/books.json` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/chapter_stats.json` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/chapters.json` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/chunks.json` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/main_passages.json` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/passages.json` | A | - | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/raw/《注解伤寒论》.zip` | A | - | 原始回查底座。 |
| `dist/zjshl_dataset_v2_mvp_safe.zip` | A | rebuildable_artifact | 当前 safe 数据包基线。 |
| `docs/01_scope_freeze.md` | B | - | 当前有效的说明、验证样例或报告。 |
| `docs/03_dataset_acceptance_report.md` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `docs/05_dataset_patch_note.md` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `docs/06_layered_enablement_policy.md` | B | - | 当前有效的说明、验证样例或报告。 |
| `docs/07_database_schema_plan.md` | B | - | 当前有效的说明、验证样例或报告。 |
| `docs/layered_field_mapping.md` | B | - | 当前有效的说明、验证样例或报告。 |
| `docs/layered_usage_examples.md` | B | - | 当前有效的说明、验证样例或报告。 |
| `docs/minimal_retrieval_input_plan.md` | B | - | 当前有效的说明、验证样例或报告。 |
| `reports/dataset_acceptance_summary.json` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `reports/dataset_issue_list.csv` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `reports/dataset_patch_summary.json` | B | rebuildable_artifact | 当前有效的验证产物；可由脚本重建。 |
| `scripts/build_mvp_safe_dataset.py` | A | - | 当前 safe 数据包构建入口。 |
| `scripts/check_dataset_acceptance.py` | A | - | 当前数据验收入口。 |

## Archive

| 路径 / 文件组 | 分类 | 可参考的新文件 | 原因 |
| --- | --- | --- | --- |
| `dense_retrieval_upgrade_spec.md` | E | dense_retrieval_plan.md, hybrid_retrieval_patch_note.md | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `embedding_selection_note.md` | E | dense_retrieval_plan.md, retrieval_upgrade_options.json, code constants | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `retrieval_upgrade_decision_log.md` | E | dense_retrieval_plan.md, hybrid_retrieval_patch_note.md, code constants | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `retrieval_upgrade_options.json` | E | run_hybrid_retrieval.py, build_dense_index.py | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `artifacts/answer_examples.json` | E | artifacts/hybrid_answer_examples.json | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `artifacts/answer_smoke_checks.md` | E | artifacts/hybrid_answer_smoke_checks.md | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `artifacts/retrieval_examples.json` | E | artifacts/hybrid_retrieval_examples.json | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `artifacts/retrieval_smoke_checks.md` | E | artifacts/hybrid_retrieval_smoke_checks.md | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |

## Candidate Delete

| 路径 / 文件组 | 附加标记 | 原因 |
| --- | --- | --- |
| `README.md` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `outputs` | ignore_from_git | 空输出目录占位；当前没有活跃产物写入这里。 |
| `venv` | ignore_from_git, rebuildable_artifact | 旧虚拟环境，占位功能已被 .venv/ 覆盖。 |
| `.DS_Store` | ignore_from_git | 系统生成垃圾文件；可直接清理，并应继续忽略。 |
| `.claude/.DS_Store` | ignore_from_git | 系统生成垃圾文件；可直接清理，并应继续忽略。 |
| `backend/app/api/annotation.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/api/passage.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/api/search.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/core/config.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/core/database.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/main.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/retrieval/alias_expand.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/retrieval/fts_search.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/retrieval/rank_fusion.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/schemas/passage.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/schemas/search.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/services/annotation_service.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/services/passage_service.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/requirements.txt` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/scripts/build_fts.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/scripts/import_sqlite.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/scripts/inspect_dataset.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/scripts/search_demo.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/tests/test_passage.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/tests/test_search.py` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `data/.DS_Store` | ignore_from_git | 系统生成垃圾文件；可直接清理，并应继续忽略。 |
| `data/indexes` | ignore_from_git | 空索引占位目录；当前实际索引产物写在 artifacts/。 |
| `data/sqlite/.gitkeep` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `docs/api_design.md` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `docs/data_schema.md` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `docs/dev_log.md` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `docs/parsing_notes.md` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `frontend/README.md` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `notebooks/.gitkeep` | - | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |

## Ignore From Git

| 路径 / 文件组 | 附加标记 | 原因 |
| --- | --- | --- |
| `__pycache__` | candidate_delete | Python 编译缓存，可随时删除后重新生成。 |
| `.venv` | rebuildable_artifact | 当前项目默认运行环境；本地保留即可，不应提交 Git。 |
| `artifacts/dense_chunks.faiss` | rebuildable_artifact | 当前 dense 检索索引文件；可重建，且已被 .gitignore 排除。 |
| `artifacts/dense_main_passages.faiss` | rebuildable_artifact | 当前 dense 检索索引文件；可重建，且已被 .gitignore 排除。 |
| `artifacts/hf_cache` | rebuildable_artifact | 本地 Hugging Face 模型缓存，体积大，可按需重建。 |
| `scripts/__pycache__` | candidate_delete | 脚本编译缓存，可随时删除后重新生成。 |

## Rebuildable Artifact Notes

- `dist/zjshl_dataset_v2_mvp_safe.zip` 可由 `scripts/build_mvp_safe_dataset.py` 重建。
- `artifacts/zjshl_mvp.db`、`artifacts/database_*` 可由 `build_mvp_database.py` 重建。
- `artifacts/dense_chunks.faiss`、`artifacts/dense_main_passages.faiss`、对应 meta/report，以及 `artifacts/hf_cache/` 可由 `build_dense_index.py` 和模型下载过程重建。
- `artifacts/retrieval_*` 可由 `run_minimal_retrieval.py` 重建。
- `artifacts/hybrid_retrieval_*` 可由 `run_hybrid_retrieval.py` 重建。
- `artifacts/hybrid_answer_*` 可由 `run_answer_assembler.py` 重建。
- `docs/03_dataset_acceptance_report.md`、`reports/dataset_acceptance_summary.json`、`reports/dataset_issue_list.csv` 可由 `scripts/check_dataset_acceptance.py` 重建。
- `docs/05_dataset_patch_note.md`、`reports/dataset_patch_summary.json` 可由 `scripts/build_mvp_safe_dataset.py` 重建。

## Lowest-Risk Cleanup Targets For Next Round

1. 先清理系统垃圾与缓存：`.DS_Store`、`__pycache__/`、`scripts/__pycache__/`。
2. 再处理重复环境：保留 `.venv/`，把 `venv/` 列为待删。
3. 若只做归档不删除，可先把旧结果 `artifacts/answer_*`、`artifacts/retrieval_*` 和历史方案文档移入待归档区。
4. 最后再评估空占位文件：`backend/` 空文件、`frontend/README.md`、空 `docs/*.md`、`README.md`、`notebooks/.gitkeep`、`data/sqlite/.gitkeep`。

## Caution

- `run_minimal_retrieval.py`、`layered_enablement_policy.json`、`database_schema_draft.json`、`data/processed/zjshl_dataset_v2/`、`dist/zjshl_dataset_v2_mvp_safe.zip`、`artifacts/zjshl_mvp.db` 不能被误判为旧文件。
- `artifacts/dense_chunks.faiss` / `artifacts/dense_main_passages.faiss` 虽是可重建索引，但当前 hybrid 检索依赖它们；若未来要清理，应先确认重建路径可随时复现。
- `backend/` 虽然现在是空壳，但删除前最好先确认你是否还想保留未来 API 目录骨架。
