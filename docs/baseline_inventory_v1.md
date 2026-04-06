# Baseline Inventory v1

## 1. 判定规则

本清单使用三类标签：

- `canonical`：当前正式基线。后续开发、审查、答辩、论文映射优先以这些对象为准。
- `supporting`：辅助参考、验证产物、现存扩展或上游源。可保留、可引用，但不是第一依据。
- `legacy / patch / historical`：历史方案、补丁记录、旧验证结果、盘点快照。不建议继续扩写为主线材料。

## 2. 当前正式基线清单

| 类别 | 路径 | 状态 | 说明 |
| --- | --- | --- | --- |
| 正式 PRD | `docs/PRD_mvp_baseline_v1.md` | `canonical` | 当前正式产品边界 |
| 正式技术规格 | `docs/tech_spec_mvp_baseline_v1.md` | `canonical` | 当前真实实现说明 |
| 正式仓库地图 | `docs/repo_map_v1.md` | `canonical` | 当前目录与角色划分 |
| 正式基线清单 | `docs/baseline_inventory_v1.md` | `canonical` | 本文件 |
| 正式变更流程 | `docs/change_workflow_v1.md` | `canonical` | 后续开发流程 |
| 正式整编方案 | `docs/cleanup_plan_v1.md` | `canonical` | 最小整理路线 |
| 正式数据底座 | `data/processed/zjshl_dataset_v2/` | `canonical` | 当前 full 数据目录 |
| 正式 safe 数据包 | `dist/zjshl_dataset_v2_mvp_safe.zip` | `canonical` | 当前 safe 数据基线 |
| 正式数据验收脚本 | `scripts/check_dataset_acceptance.py` | `canonical` | 当前构建链前置校验入口 |
| 正式 safe 构建脚本 | `scripts/build_mvp_safe_dataset.py` | `canonical` | 当前 safe 数据包构建入口 |
| 正式分层策略 | `layered_enablement_policy.json` | `canonical` | A/B/C/D 层级与禁用源策略 |
| 正式数据库构建配置 | `database_schema_draft.json` | `canonical` | 落库规则与结构口径 |
| 正式数据库脚本 | `build_mvp_database.py` | `canonical` | 当前 SQLite 构建入口 |
| 正式数据库文件 | `artifacts/zjshl_mvp.db` | `canonical` | 当前运行期数据库 |
| 正式 dense 构建脚本 | `build_dense_index.py` | `canonical` | 当前索引构建入口 |
| 正式 dense 运行资产 | `artifacts/dense_chunks.faiss` | `canonical` | runtime 必需，Git 忽略 |
| 正式 dense 运行资产 | `artifacts/dense_main_passages.faiss` | `canonical` | runtime 必需，Git 忽略 |
| 正式 retrieval 入口 | `run_hybrid_retrieval.py` | `canonical` | 当前主检索入口 |
| 正式 retrieval 骨架 | `run_minimal_retrieval.py` | `canonical` | hybrid 依赖的门控骨架 |
| 正式 answer 入口 | `run_answer_assembler.py` | `canonical` | 当前 answer payload 主入口 |
| 正式 API 入口 | `app_minimal_api.py` | `canonical` | 当前 HTTP 服务入口 |
| 正式 payload 合同 | `answer_payload_contract.md` | `canonical` | payload 顶层合同 |
| 正式 API 合同 | `minimal_api_contract.md` | `canonical` | HTTP 请求 / 响应合同 |
| 正式前端入口 | `frontend/index.html` | `canonical` | 当前 SPA 入口 |
| 正式前端逻辑 | `frontend/app.js` | `canonical` | 当前 payload 消费逻辑 |
| 正式前端样式 | `frontend/styles.css` | `canonical` | 当前前端样式 |
| 正式冻结样例 | `run_minimal_retrieval.py` 中 `DEFAULT_EXAMPLES` | `canonical` | 三条冻结样例来源 |
| 正式 API 验证基线 | `artifacts/api_smoke_checks.md` | `canonical` | 最小 HTTP 回归依据 |
| 正式 answer 验证基线 | `artifacts/hybrid_answer_smoke_checks.md` | `canonical` | answer payload 回归依据 |
| 正式 retrieval 验证基线 | `artifacts/hybrid_retrieval_smoke_checks.md` | `canonical` | hybrid retrieval 回归依据 |

## 3. Supporting 清单

| 类别 | 路径 | 状态 | 说明 |
| --- | --- | --- | --- |
| 原始输入源 | `data/raw/《注解伤寒论》.zip` | `supporting` | 上游原始文件，主要用于追溯和验收 |
| 数据验收报告 | `docs/03_dataset_acceptance_report.md` | `supporting` | 验收说明，可重建 |
| 数据补丁说明 | `docs/05_dataset_patch_note.md` | `supporting` | safe 策略说明，可重建 |
| 分层策略说明 | `docs/06_layered_enablement_policy.md` | `supporting` | policy 的说明文档 |
| 数据库方案说明 | `docs/07_database_schema_plan.md` | `supporting` | 数据库与表视图说明 |
| 范围冻结说明 | `docs/01_scope_freeze.md` | `supporting` | MVP 范围冻结背景 |
| 前端规格说明 | `frontend_mvp_spec.md` | `supporting` | 前端同源消费说明 |
| dense 方案说明 | `dense_retrieval_plan.md` | `supporting` | dense 检索实现说明 |
| 数据库统计 | `artifacts/database_counts.json` | `supporting` | 当前数据库规模快照 |
| 数据库构建报告 | `artifacts/database_build_report.md` | `supporting` | 当前落库结果说明 |
| 数据库 smoke | `artifacts/database_smoke_checks.md` | `supporting` | 数据层验证产物 |
| dense meta | `artifacts/dense_chunks_meta.json` | `supporting` | dense 索引元数据 |
| dense meta | `artifacts/dense_main_passages_meta.json` | `supporting` | dense 索引元数据 |
| dense 构建报告 | `artifacts/dense_index_build_report.md` | `supporting` | dense 构建验证产物 |
| hybrid retrieval examples | `artifacts/hybrid_retrieval_examples.json` | `supporting` | 当前主检索示例 |
| hybrid answer examples | `artifacts/hybrid_answer_examples.json` | `supporting` | 当前主回答示例 |
| API examples | `artifacts/api_examples.json` | `supporting` | API 示例产物 |
| comparison check 脚本 | `run_comparison_checks.py` | `supporting` | 现存扩展验证，不纳入 MVP 正式基线 |
| general check 脚本 | `run_general_question_checks.py` | `supporting` | 现存扩展验证，不纳入 MVP 正式基线 |
| general strategy | `general_question_strategy.py` | `supporting` | 当前 answer assembler 的扩展依赖 |
| comparison smoke/examples | `artifacts/comparison_*` | `supporting` | 扩展能力验证，不是正式验收基线 |
| general smoke/examples | `artifacts/general_question_*` | `supporting` | 扩展能力验证，不是正式验收基线 |

## 4. Legacy / Patch / Historical 清单

| 类别 | 路径 | 状态 | 说明 |
| --- | --- | --- | --- |
| 旧 retrieval 验证 | `artifacts/retrieval_examples.json` | `legacy / historical` | 已被 `hybrid_retrieval_*` 取代 |
| 旧 retrieval 验证 | `artifacts/retrieval_smoke_checks.md` | `legacy / historical` | 已被 `hybrid_retrieval_*` 取代 |
| 旧 answer 验证 | `artifacts/answer_examples.json` | `legacy / historical` | 已被 `hybrid_answer_*` 取代 |
| 旧 answer 验证 | `artifacts/answer_smoke_checks.md` | `legacy / historical` | 已被 `hybrid_answer_*` 取代 |
| 根目录 patch note | `hybrid_retrieval_patch_note.md` | `patch` | 保留，但不应继续充当主规格 |
| 根目录 patch note | `hybrid_answer_assembler_patch_note.md` | `patch` | 保留，但不应继续充当主规格 |
| 根目录 patch note | `minimal_api_patch_note.md` | `patch` | 保留，但不应继续充当主规格 |
| 根目录 patch note | `retrieval_precision_patch_note.md` | `patch` | 保留，但不应继续充当主规格 |
| 扩展 patch note | `comparison_patch_note.md` | `patch` | 现存扩展记录，不纳入正式范围 |
| 扩展 patch note | `general_question_patch_note.md` | `patch` | 现存扩展记录，不纳入正式范围 |
| 历史检索 spec | `dense_retrieval_upgrade_spec.md` | `historical` | 已被当前实现和 plan 替代 |
| 历史决策记录 | `retrieval_upgrade_decision_log.md` | `historical` | 保留追溯，不再扩写 |
| 历史选项记录 | `retrieval_upgrade_options.json` | `historical` | 保留追溯，不再扩写 |
| 历史嵌入说明 | `embedding_selection_note.md` | `historical` | 保留追溯，不再扩写 |
| 历史盘点文档 | `project_inventory.md` | `historical` | 已被本轮 repo map / inventory 替代 |
| 历史盘点文档 | `project_cleanup_plan.md` | `historical` | 已被本轮 cleanup plan 替代 |
| 历史盘点文档 | `project_structure_snapshot.txt` | `historical` | 快照留档，不再当主入口 |
| 历史盘点文档 | `project_file_registry.json` | `historical` | 快照留档，不再当主入口 |
| 空壳 scaffold | `backend/` 下空文件 | `historical scaffold` | 当前不参与运行，不应误当主入口 |

## 5. 当前不再建议继续扩写的旧文件类别

后续不建议继续把新增内容写到以下类别中：

- 根目录 patch note
- 根目录临时 spec / alignment note / decision log
- 旧版 `artifacts/retrieval_*` 与 `artifacts/answer_*`
- `project_*` 盘点文件
- `backend/` 空壳 scaffold
- 零字节占位文档

## 6. 当前正式基线到底是什么

一句话版：

当前正式基线是“基于 `data/processed/zjshl_dataset_v2/` 与 `dist/zjshl_dataset_v2_mvp_safe.zip` 构建出的 `artifacts/zjshl_mvp.db` 和 dense 索引，再由 `run_hybrid_retrieval.py`、`run_answer_assembler.py`、`app_minimal_api.py`、`frontend/` 组成的单书、三模式、证据分层的最小闭环”。

后续如果新增功能，必须在这条基线上做变更，而不是重新发明一套入口。
