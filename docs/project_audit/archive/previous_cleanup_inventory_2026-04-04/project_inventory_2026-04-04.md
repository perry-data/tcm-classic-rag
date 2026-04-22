# Project Inventory

## Scope

- 扫描时间：`2026-04-04T19:30:22+08:00`
- 项目根目录：`/Users/man_ray/Projects/Python/tcm-classic-rag`
- 范围：扫描当前工作区全部项目对象，排除 `.git/` 内部文件。
- 展开策略：`.venv/`、`venv/`、`artifacts/hf_cache/`、`__pycache__/`、`scripts/__pycache__/`、`data/indexes/`、`outputs/` 仅按目录 bundle 记录，不逐个展开内部文件。

## Summary

- 登记对象：`98`（文件 `91`，目录 bundle `7`）
- 估算总量：`3.1 GB`
- Git 跟踪对象：`86`
- Git 忽略对象：`12`

| 类别 | 说明 | 对象数 |
| --- | --- | --- |
| A | 当前核心运行文件 | 24 |
| B | 当前有效的验证与说明文件 | 25 |
| C | 可重建产物 | 3 |
| D | 缓存 / 本地依赖 / 不应提交 | 4 |
| E | 历史遗留但可能仍需保留 | 8 |
| F | 明显的清理候选 | 34 |

## Current Mainline

当前主链路按真实文件关系可归纳为：

1. `dataset_acceptance`
   - entry: `scripts/check_dataset_acceptance.py`
   - inputs: `data/raw/《注解伤寒论》.zip, data/processed/zjshl_dataset_v2/`
   - outputs: `docs/03_dataset_acceptance_report.md, reports/dataset_acceptance_summary.json, reports/dataset_issue_list.csv`
2. `safe_dataset_build`
   - entry: `scripts/build_v1_safe_dataset.py`
   - inputs: `data/processed/zjshl_dataset_v2/`
   - outputs: `dist/zjshl_dataset_v2_v1_safe.zip, docs/05_dataset_patch_note.md, reports/dataset_patch_summary.json`
3. `database_build`
   - entry: `build_v1_database.py`
   - inputs: `dist/zjshl_dataset_v2_v1_safe.zip, data/processed/zjshl_dataset_v2/, database_schema_draft.json, layered_enablement_policy.json`
   - outputs: `artifacts/zjshl_v1.db, artifacts/database_build_report.md, artifacts/database_counts.json, artifacts/database_smoke_checks.md`
4. `dense_index_build`
   - entry: `build_dense_index.py`
   - inputs: `artifacts/zjshl_v1.db`
   - outputs: `artifacts/dense_chunks.faiss, artifacts/dense_chunks_meta.json, artifacts/dense_main_passages.faiss, artifacts/dense_main_passages_meta.json, artifacts/dense_index_build_report.md, artifacts/hf_cache/`
5. `retrieval_baseline`
   - entry: `run_minimal_retrieval.py`
   - inputs: `artifacts/zjshl_v1.db, layered_enablement_policy.json`
   - outputs: `artifacts/retrieval_examples.json, artifacts/retrieval_smoke_checks.md`
6. `retrieval_current`
   - entry: `run_hybrid_retrieval.py`
   - inputs: `run_minimal_retrieval.py, artifacts/zjshl_v1.db, artifacts/dense_chunks.faiss, artifacts/dense_main_passages.faiss, artifacts/hf_cache/`
   - outputs: `artifacts/hybrid_retrieval_examples.json, artifacts/hybrid_retrieval_smoke_checks.md`
7. `answer_current`
   - entry: `run_answer_assembler.py`
   - inputs: `run_hybrid_retrieval.py, answer_payload_contract.md`
   - outputs: `artifacts/hybrid_answer_examples.json, artifacts/hybrid_answer_smoke_checks.md`

当前最重要的 examples / smoke checks：

- `artifacts/database_smoke_checks.md`
- `artifacts/hybrid_retrieval_examples.json`
- `artifacts/hybrid_retrieval_smoke_checks.md`
- `artifacts/hybrid_answer_examples.json`
- `artifacts/hybrid_answer_smoke_checks.md`

已确认的替代关系：

- `run_hybrid_retrieval.py` 相对于 `run_minimal_retrieval.py`：hybrid 检索是当前主入口，但它直接复用 minimal 检索骨架和 gating 逻辑，minimal 仍属于现行依赖。
- `artifacts/hybrid_retrieval_examples.json` 相对于 `artifacts/retrieval_examples.json`：hybrid 产物是当前主检索验证结果；minimal 产物保留为基线对照。
- `artifacts/hybrid_answer_examples.json` 相对于 `artifacts/answer_examples.json`：answer 产物已迁移到 hybrid 命名；旧 answer_* 文件只保留历史参考意义。
- `dense_retrieval_plan.md` 相对于 `dense_retrieval_upgrade_spec.md`：spec 已落地为当前实现；plan + patch note 更接近现状。
- `.venv` 相对于 `venv`：.venv/ 已被文档和脚本明确视为当前运行环境；venv/ 为旧环境残留。
- `scripts/build_v1_safe_dataset.py` 相对于 `docs/05_dataset_patch_note.md`：safe 包、补丁说明和 patch summary 都由该脚本生成。
- `scripts/check_dataset_acceptance.py` 相对于 `docs/03_dataset_acceptance_report.md`：验收报告和 issue list 都可由该脚本重建。

## Full Inventory By Directory

### ROOT

- 对象数：`20`
- 体积合计：`30.2 MB`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `README.md` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `__pycache__` | 165.6 KB | D | ignore_from_git | bundle:5 files<br>git:ignored | Python 编译缓存，可随时删除后重新生成。 |
| `answer_payload_contract.md` | 4.4 KB | A | keep | git:tracked | 回答 payload 合同文件；当前 answer assembler 需要保持兼容。 |
| `build_dense_index.py` | 8.9 KB | A | keep | git:tracked | 当前 dense index 构建入口。 |
| `build_v1_database.py` | 46.3 KB | A | keep | git:tracked | 当前 SQLite 落库入口。 |
| `database_schema_draft.json` | 15.5 KB | A | keep | git:tracked | 数据库构建脚本当前读取的 schema/source-resolution 配置。 |
| `dense_retrieval_plan.md` | 2.5 KB | B | keep | git:tracked | 当前有效的说明、验证样例或报告。 |
| `dense_retrieval_upgrade_spec.md` | 7.3 KB | E | archive | git:tracked<br>newer:dense_retrieval_plan.md, hybrid_retrieval_patch_note.md | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `embedding_selection_note.md` | 1.4 KB | E | archive | git:tracked<br>newer:dense_retrieval_plan.md, retrieval_upgrade_options.json, code constants | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `hybrid_answer_assembler_patch_note.md` | 1.1 KB | B | keep | git:tracked | 当前有效的说明、验证样例或报告。 |
| `hybrid_retrieval_patch_note.md` | 2.0 KB | B | keep | git:tracked | 当前有效的说明、验证样例或报告。 |
| `layered_enablement_policy.json` | 8.8 KB | A | keep | git:tracked | 运行时策略源文件。 |
| `outputs` | 0 B | F | candidate_delete | bundle:1 files<br>empty<br>git:ignored | 空输出目录占位；当前没有活跃产物写入这里。 |
| `retrieval_precision_patch_note.md` | 1.4 KB | B | keep | git:tracked | 当前有效的说明、验证样例或报告。 |
| `retrieval_upgrade_decision_log.md` | 1.3 KB | E | archive | git:tracked<br>newer:dense_retrieval_plan.md, hybrid_retrieval_patch_note.md, code constants | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `retrieval_upgrade_options.json` | 830 B | E | archive | git:tracked<br>newer:run_hybrid_retrieval.py, build_dense_index.py | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `run_answer_assembler.py` | 22.8 KB | A | keep | git:tracked | 当前回答编排主入口。 |
| `run_hybrid_retrieval.py` | 31.5 KB | A | keep | git:tracked | 当前检索主入口。 |
| `run_minimal_retrieval.py` | 36.2 KB | A | keep | git:tracked | 当前 minimal 检索基线与 hybrid 检索共享骨架；虽不是主入口，但仍是运行时依赖。 |
| `venv` | 29.8 MB | F | candidate_delete | bundle:862 files<br>git:ignored<br>newer:.venv | 旧虚拟环境，占位功能已被 .venv/ 覆盖。 |

### .hidden

- 对象数：`4`
- 体积合计：`809.8 MB`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `.DS_Store` | 6.0 KB | F | candidate_delete | git:ignored | 系统生成垃圾文件；可直接清理，并应继续忽略。 |
| `.claude/.DS_Store` | 6.0 KB | F | candidate_delete | git:ignored | 系统生成垃圾文件；可直接清理，并应继续忽略。 |
| `.gitignore` | 362 B | A | keep | git:tracked | 当前版本控制忽略规则；决定缓存/索引/环境目录是否入库。 |
| `.venv` | 809.8 MB | D | ignore_from_git | bundle:33631 files<br>git:ignored | 当前项目默认运行环境；本地保留即可，不应提交 Git。 |

### artifacts

- 对象数：`18`
- 体积合计：`2.3 GB`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `artifacts/answer_examples.json` | 17.9 KB | E | archive | git:tracked<br>newer:artifacts/hybrid_answer_examples.json | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `artifacts/answer_smoke_checks.md` | 10.9 KB | E | archive | git:tracked<br>newer:artifacts/hybrid_answer_smoke_checks.md | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `artifacts/database_build_report.md` | 2.3 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/database_counts.json` | 1.3 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/database_smoke_checks.md` | 6.4 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/dense_chunks.faiss` | 1.1 MB | C | ignore_from_git | git:ignored | 当前 dense 检索索引文件；可重建，且已被 .gitignore 排除。 |
| `artifacts/dense_chunks_meta.json` | 269.2 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/dense_index_build_report.md` | 657 B | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/dense_main_passages.faiss` | 1.5 MB | C | ignore_from_git | git:ignored | 当前 dense 检索索引文件；可重建，且已被 .gitignore 排除。 |
| `artifacts/dense_main_passages_meta.json` | 358.7 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/hf_cache` | 2.3 GB | D | ignore_from_git | bundle:46 files<br>git:ignored | 本地 Hugging Face 模型缓存，体积大，可按需重建。 |
| `artifacts/hybrid_answer_examples.json` | 21.2 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/hybrid_answer_smoke_checks.md` | 12.5 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/hybrid_retrieval_examples.json` | 89.2 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/hybrid_retrieval_smoke_checks.md` | 28.1 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `artifacts/retrieval_examples.json` | 39.1 KB | E | archive | git:tracked<br>newer:artifacts/hybrid_retrieval_examples.json | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `artifacts/retrieval_smoke_checks.md` | 8.6 KB | E | archive | git:tracked<br>newer:artifacts/hybrid_retrieval_smoke_checks.md | 已有更新实现或更新命名文件；当前更适合作为历史参考。 |
| `artifacts/zjshl_v1.db` | 3.8 MB | C | keep | git:tracked | 当前仍在使用的运行产物；可重建，但本轮不建议移除。 |

### backend

- 对象数：`20`
- 体积合计：`0 B`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `backend/app/api/annotation.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/api/passage.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/api/search.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/core/config.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/core/database.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/main.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/retrieval/alias_expand.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/retrieval/fts_search.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/retrieval/rank_fusion.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/schemas/passage.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/schemas/search.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/services/annotation_service.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/app/services/passage_service.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/requirements.txt` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/scripts/build_fts.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/scripts/import_sqlite.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/scripts/inspect_dataset.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/scripts/search_demo.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/tests/test_passage.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `backend/tests/test_search.py` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |

### data

- 对象数：`15`
- 体积合计：`4.2 MB`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `data/.DS_Store` | 6.0 KB | F | candidate_delete | git:ignored | 系统生成垃圾文件；可直接清理，并应继续忽略。 |
| `data/indexes` | 0 B | F | candidate_delete | bundle:1 files<br>empty<br>git:ignored<br>newer:artifacts/dense_chunks.faiss, artifacts/dense_main_passages.faiss | 空索引占位目录；当前实际索引产物写在 artifacts/。 |
| `data/processed/zjshl_dataset_v2/README_parse_report_v2.md` | 1.5 KB | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/aliases.json` | 7.7 KB | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/ambiguous_passages.json` | 179.9 KB | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/annotation_links.json` | 111.1 KB | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/annotations.json` | 544.0 KB | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/books.json` | 504 B | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/chapter_stats.json` | 6.1 KB | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/chapters.json` | 12.9 KB | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/chunks.json` | 782.2 KB | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/main_passages.json` | 969.1 KB | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/processed/zjshl_dataset_v2/passages.json` | 1.5 MB | A | keep | git:tracked | 当前 full 数据底座目录；safe 包、数据库和验收都依赖这些文件。 |
| `data/raw/《注解伤寒论》.zip` | 130.1 KB | A | keep | git:tracked | 原始回查底座。 |
| `data/sqlite/.gitkeep` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |

### dist

- 对象数：`1`
- 体积合计：`415.6 KB`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `dist/zjshl_dataset_v2_v1_safe.zip` | 415.6 KB | A | keep | git:tracked | 当前 safe 数据包基线。 |

### docs

- 对象数：`12`
- 体积合计：`72.0 KB`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `docs/01_scope_freeze.md` | 8.2 KB | B | keep | git:tracked | 当前有效的说明、验证样例或报告。 |
| `docs/03_dataset_acceptance_report.md` | 10.4 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `docs/05_dataset_patch_note.md` | 3.6 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `docs/06_layered_enablement_policy.md` | 11.2 KB | B | keep | git:tracked | 当前有效的说明、验证样例或报告。 |
| `docs/07_database_schema_plan.md` | 20.7 KB | B | keep | git:tracked | 当前有效的说明、验证样例或报告。 |
| `docs/api_design.md` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `docs/data_schema.md` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `docs/dev_log.md` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |
| `docs/layered_field_mapping.md` | 6.2 KB | B | keep | git:tracked | 当前有效的说明、验证样例或报告。 |
| `docs/layered_usage_examples.md` | 4.1 KB | B | keep | git:tracked | 当前有效的说明、验证样例或报告。 |
| `docs/minimal_retrieval_input_plan.md` | 7.5 KB | B | keep | git:tracked | 当前有效的说明、验证样例或报告。 |
| `docs/parsing_notes.md` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |

### frontend

- 对象数：`1`
- 体积合计：`0 B`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `frontend/README.md` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |

### notebooks

- 对象数：`1`
- 体积合计：`0 B`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `notebooks/.gitkeep` | 0 B | F | candidate_delete | empty<br>git:tracked | 零字节占位文件；当前仓库内没有实现内容，也没有被其他文件引用。 |

### reports

- 对象数：`3`
- 体积合计：`5.4 KB`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `reports/dataset_acceptance_summary.json` | 974 B | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `reports/dataset_issue_list.csv` | 3.0 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |
| `reports/dataset_patch_summary.json` | 1.4 KB | B | keep | git:tracked | 当前有效的验证产物；可由脚本重建。 |

### scripts

- 对象数：`3`
- 体积合计：`126.0 KB`

| 路径 | 大小 | 分类 | 建议 | 状态 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `scripts/__pycache__` | 66.0 KB | D | ignore_from_git | bundle:2 files<br>git:ignored | 脚本编译缓存，可随时删除后重新生成。 |
| `scripts/build_v1_safe_dataset.py` | 17.9 KB | A | keep | git:tracked | 当前 safe 数据包构建入口。 |
| `scripts/check_dataset_acceptance.py` | 42.1 KB | A | keep | git:tracked | 当前数据验收入口。 |

## Key Findings

- `run_hybrid_retrieval.py` 是当前检索主入口，但它明确依赖 `run_minimal_retrieval.py` 中的基础检索骨架，因此 minimal 不能被当作已废弃脚本。
- `run_answer_assembler.py` 当前默认输出 `artifacts/hybrid_answer_examples.json` 和 `artifacts/hybrid_answer_smoke_checks.md`，旧 `answer_*` 产物不再是当前默认结果。
- `backend/` 整体为零字节占位文件，当前不构成可运行 API。
- `frontend/README.md` 为空，当前没有活跃前端实现。
- `.venv/` 是当前文档和脚本指向的运行环境；`venv/` 是重复旧环境。
- `artifacts/hf_cache/` 和 `.venv/` 是体积最大的本地目录，属于典型缓存/依赖对象。
- `artifacts/zjshl_v1.db`、`dist/zjshl_dataset_v2_v1_safe.zip`、`artifacts/hybrid_*`、`artifacts/database_*` 都可重建，但当前仍承担运行或验证角色，不能粗暴当垃圾删。
