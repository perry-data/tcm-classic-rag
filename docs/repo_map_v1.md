# Repo Map v1

## 1. 结论先行

当前仓库不是“代码太多”，而是“不同阶段的正式入口、补丁说明、验证产物、盘点文档和空壳脚手架混在同一层级”。真正需要长期保留并继续依赖的文件并不多，主要集中在：

- 数据构建链
- 检索 / 回答 / API / 前端主链
- policy / contract / baseline docs
- 关键 smoke / examples 产物

## 2. 当前目录树

以下目录树只展开到关键层级，并标明当前建议状态。

```text
tcm-classic-rag/
├── app_minimal_api.py                         [canonical]
├── run_answer_assembler.py                    [canonical]
├── run_hybrid_retrieval.py                    [canonical]
├── run_minimal_retrieval.py                   [canonical dependency]
├── build_mvp_database.py                      [canonical]
├── build_dense_index.py                       [canonical]
├── answer_payload_contract.md                 [canonical]
├── minimal_api_contract.md                    [canonical]
├── layered_enablement_policy.json             [canonical]
├── database_schema_draft.json                 [canonical]
├── data/
│   ├── raw/《注解伤寒论》.zip                  [supporting source]
│   ├── processed/zjshl_dataset_v2/            [canonical upstream dataset]
│   ├── indexes/                               [empty placeholder]
│   └── sqlite/                                [empty placeholder]
├── dist/
│   └── zjshl_dataset_v2_mvp_safe.zip          [canonical data artifact]
├── artifacts/
│   ├── zjshl_mvp.db                           [canonical runtime artifact]
│   ├── dense_chunks.faiss                     [canonical runtime artifact, ignored]
│   ├── dense_main_passages.faiss              [canonical runtime artifact, ignored]
│   ├── dense_*_meta.json                      [supporting]
│   ├── database_*                             [supporting]
│   ├── hybrid_retrieval_*                     [supporting baseline validation]
│   ├── hybrid_answer_*                        [supporting baseline validation]
│   ├── api_*                                  [supporting baseline validation]
│   ├── retrieval_* / answer_*                 [historical baseline]
│   ├── comparison_* / general_question_*      [supporting extension validation]
│   └── hf_cache/                              [local cache, ignored]
├── frontend/
│   ├── index.html                             [canonical]
│   ├── app.js                                 [canonical]
│   ├── styles.css                             [canonical]
│   └── README.md                              [empty placeholder]
├── scripts/
│   ├── check_dataset_acceptance.py            [canonical]
│   └── build_mvp_safe_dataset.py              [canonical]
├── docs/
│   ├── 01_scope_freeze.md                     [supporting]
│   ├── 03_dataset_acceptance_report.md        [supporting]
│   ├── 05_dataset_patch_note.md               [supporting]
│   ├── 06_layered_enablement_policy.md        [supporting]
│   ├── 07_database_schema_plan.md             [supporting]
│   ├── PRD_mvp_baseline_v1.md                 [canonical]
│   ├── tech_spec_mvp_baseline_v1.md           [canonical]
│   ├── repo_map_v1.md                         [canonical]
│   ├── baseline_inventory_v1.md               [canonical]
│   ├── change_workflow_v1.md                  [canonical]
│   └── cleanup_plan_v1.md                     [canonical]
├── reports/                                   [supporting generated reports]
├── backend/                                   [historical scaffold, empty]
├── project_inventory.md                       [historical inventory]
├── project_cleanup_plan.md                    [historical inventory]
├── project_structure_snapshot.txt             [historical inventory]
├── project_file_registry.json                 [historical inventory]
├── comparison_patch_note.md                   [patch / extension note]
├── general_question_patch_note.md             [patch / extension note]
├── hybrid_retrieval_patch_note.md             [patch note]
├── hybrid_answer_assembler_patch_note.md      [patch note]
├── minimal_api_patch_note.md                  [patch note]
├── frontend_mvp_spec.md                       [supporting]
├── frontend_debug_report.md                   [historical / supporting]
├── dense_retrieval_plan.md                    [supporting]
├── dense_retrieval_upgrade_spec.md            [historical spec]
├── retrieval_upgrade_decision_log.md          [historical]
├── retrieval_upgrade_options.json             [historical]
├── embedding_selection_note.md                [historical]
├── run_comparison_checks.py                   [supporting extension]
├── run_general_question_checks.py             [supporting extension]
└── general_question_strategy.py               [supporting runtime extension]
```

## 3. 关键目录 / 文件用途

### 3.1 正式运行层

| 路径 | 用途 | 当前判断 |
| --- | --- | --- |
| `app_minimal_api.py` | HTTP API 和静态文件服务入口 | 当前正式 API 主入口 |
| `run_answer_assembler.py` | 统一 answer payload 编排 | 当前正式 answer 主入口 |
| `run_hybrid_retrieval.py` | hybrid 检索主入口 | 当前正式 retrieval 主入口 |
| `run_minimal_retrieval.py` | minimal 检索骨架与 gating 逻辑 | 不是对外主入口，但仍是正式依赖 |
| `frontend/` | 前端单页 | 当前正式前端入口 |

### 3.2 数据与构建层

| 路径 | 用途 | 当前判断 |
| --- | --- | --- |
| `scripts/check_dataset_acceptance.py` | 数据验收 | 正式构建链入口 |
| `scripts/build_mvp_safe_dataset.py` | safe 数据包构建 | 正式构建链入口 |
| `build_mvp_database.py` | SQLite 构建 | 正式构建链入口 |
| `build_dense_index.py` | dense 索引构建 | 正式构建链入口 |
| `data/processed/zjshl_dataset_v2/` | full 数据底座 | 正式上游数据目录 |
| `dist/zjshl_dataset_v2_mvp_safe.zip` | safe 数据包 | 正式中间基线 |
| `artifacts/zjshl_mvp.db` | 运行期数据库 | 正式运行产物 |

### 3.3 合同与策略层

| 路径 | 用途 | 当前判断 |
| --- | --- | --- |
| `answer_payload_contract.md` | payload 顶层与槽位合同 | 正式合同 |
| `minimal_api_contract.md` | API 请求 / 响应合同 | 正式合同 |
| `layered_enablement_policy.json` | 数据分层与模式策略 | 正式策略源 |
| `database_schema_draft.json` | 落库口径 | 正式构建配置 |

## 4. 哪些是当前正式文件

当前应继续作为正式依据的，只有以下几类：

1. 正式运行入口
   - `app_minimal_api.py`
   - `run_answer_assembler.py`
   - `run_hybrid_retrieval.py`
   - `run_minimal_retrieval.py`
   - `frontend/index.html`
   - `frontend/app.js`
   - `frontend/styles.css`
2. 正式数据 / 构建入口
   - `scripts/check_dataset_acceptance.py`
   - `scripts/build_mvp_safe_dataset.py`
   - `build_mvp_database.py`
   - `build_dense_index.py`
   - `data/processed/zjshl_dataset_v2/`
   - `dist/zjshl_dataset_v2_mvp_safe.zip`
   - `artifacts/zjshl_mvp.db`
3. 正式合同 / 策略
   - `answer_payload_contract.md`
   - `minimal_api_contract.md`
   - `layered_enablement_policy.json`
   - `database_schema_draft.json`
4. 正式基线文档
   - 本轮新增的 `docs/*_v1.md`

## 5. 哪些是中间产物 / 历史产物 / 补丁记录 / 示例产物

### 5.1 中间产物或可重建产物

- `artifacts/zjshl_mvp.db`
- `artifacts/dense_chunks.faiss`
- `artifacts/dense_main_passages.faiss`
- `artifacts/*_meta.json`
- `artifacts/*_smoke_checks.md`
- `artifacts/*_examples.json`
- `reports/*.json`
- `reports/*.csv`

这些文件很重要，但它们属于“验证 / 运行产物”，不是主叙事文档。

### 5.2 补丁记录

以下文件应保留，但不应继续充当主入口文档：

- `hybrid_retrieval_patch_note.md`
- `hybrid_answer_assembler_patch_note.md`
- `minimal_api_patch_note.md`
- `retrieval_precision_patch_note.md`
- `comparison_patch_note.md`
- `general_question_patch_note.md`
- `frontend_fix_patch_note.md`

### 5.3 历史 / 盘点类文档

以下文件已被本轮基线文档替代为主依据：

- `project_inventory.md`
- `project_cleanup_plan.md`
- `project_structure_snapshot.txt`
- `project_file_registry.json`

它们仍可留存，但不建议继续作为正式入口。

### 5.4 历史 / 被替代的验证产物

- `artifacts/retrieval_examples.json`
- `artifacts/retrieval_smoke_checks.md`
- `artifacts/answer_examples.json`
- `artifacts/answer_smoke_checks.md`

这些文件仍有参考价值，但已被 `hybrid_*` 同名产物取代为主验证结果。

## 6. 哪些文件后续应优先保留

后续若只能优先守住一批文件，应优先保留：

- 正式运行入口
- `layered_enablement_policy.json`
- `database_schema_draft.json`
- `data/processed/zjshl_dataset_v2/`
- `dist/zjshl_dataset_v2_mvp_safe.zip`
- `artifacts/zjshl_mvp.db`
- `artifacts/hybrid_retrieval_smoke_checks.md`
- `artifacts/hybrid_answer_smoke_checks.md`
- `artifacts/api_smoke_checks.md`
- 本轮新增的 6 份基线文档

## 7. 哪些文件不建议继续作为主入口

以下对象后续不建议继续作为“主入口”或“正式依据”：

- 根目录散落的 patch note
- `project_inventory.md` / `project_cleanup_plan.md` / `project_structure_snapshot.txt`
- `artifacts/retrieval_*` / `artifacts/answer_*` 旧基线产物
- `backend/` 下的空壳 scaffold
- 零字节占位文件：
  - `README.md`
  - `frontend/README.md`
  - `docs/api_design.md`
  - `docs/data_schema.md`
  - `docs/dev_log.md`
  - `docs/parsing_notes.md`

## 8. 当前文件夹混乱的根因

根因可以概括为四点：

1. 阶段性 patch / spec / note 直接堆在根目录，没有进入统一文档层。
2. generated artifacts 很多，但“运行基线”和“验证产物”没有明确分层。
3. 历史盘点文件已经出现，但没有成为正式基线文档，导致“盘点又盘点”。
4. 旧 scaffold 和空文件仍留在仓库可见面，增加认知噪音。

因此，本轮最关键的不是继续加功能，而是先把“什么算正式”写清楚。
