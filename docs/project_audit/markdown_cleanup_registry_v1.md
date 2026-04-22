# Markdown 清理登记表 v1

- 扫描日期：2026-04-21
- 扫描对象：项目中的 Markdown 文件。
- 登记范围：非核心 Markdown。已排除 `README.md`、`docs/contracts/*`、`docs/final/*`、`backend/`、`frontend/src/`、`scripts/`、`config/`、`data/`。
- 执行方式：先按引用关系和文件职责分类，再对低风险阶段性文件执行 `LOCAL_ONLY` 移动。

## 1. 分类汇总

| 类别 | 数量 | 说明 |
| --- | ---: | --- |
| `LOCAL_ONLY` | 58 | 已移到 `outputs/markdown_local_only_2026-04-21/`，本地保留，不再进入 Git |
| `DELETE_SAFE` | 0 | 本轮未永久删除 Markdown |
| `ARCHIVE_IN_GIT` | 5+ | 历史方案/旧盘点，保留在 Git 归档区 |
| `KEEP_GIT` | 其余非核心 md | 评测、实验、设计、部署、项目审计等仍保留在 Git |

## 2. LOCAL_ONLY 明细

| 路径 | 文件作用判断 | 当前状态判断 | 建议类别 | 理由 |
| --- | --- | --- | --- | --- |
| `artifacts/demo/definition_outline_query_hotfix_demo.md` | 阶段性 demo 验证说明 | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 未被当前 README/docs/artifacts 引用，属于阶段性 agent 验证材料 |
| `artifacts/demo/formula_effect_query_hotfix_demo.md` | 阶段性 demo 验证说明 | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 未被当前 README/docs/artifacts 引用，属于阶段性 agent 验证材料 |
| `artifacts/demo/frontend_second_submit_hang_hotfix_demo.md` | 阶段性 demo 验证说明 | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 未被当前 README/docs/artifacts 引用，属于阶段性 agent 验证材料 |
| `artifacts/demo/frontend_streaming_ux_demo.md` | 阶段性 demo 验证说明 | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 未被当前 README/docs/artifacts 引用，属于阶段性 agent 验证材料 |
| `artifacts/demo/frontend_transport_hotfix_demo.md` | 阶段性 demo 验证说明 | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 未被当前 README/docs/artifacts 引用，属于阶段性 agent 验证材料 |
| `artifacts/demo/frontend_uiux_round2_demo.md` | 阶段性 demo 验证说明 | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 未被当前 README/docs/artifacts 引用，属于阶段性 agent 验证材料 |
| `artifacts/frontend_mvp_examples.md` | 前端阶段性样例 | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 已有正式前端说明和截图验收材料覆盖，原文件未被引用 |
| `artifacts/frontend_uiux_polish_v1/acceptance_summary.md` | 前端 UI/UX 阶段性验收说明 | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 非正式依据，截图资产仍保留，原 md 未被引用 |
| `docs/notes/comparison_patch_note.md` | 早期阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 早期 notes 噪音，未被当前文档引用 |
| `docs/notes/frontend_fix_patch_note.md` | 早期阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 早期 notes 噪音，未被当前文档引用 |
| `docs/notes/fts5_bm25_patch_note.md` | 早期阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 早期 notes 噪音，未被当前文档引用 |
| `docs/notes/general_question_patch_note.md` | 早期阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 早期 notes 噪音，未被当前文档引用 |
| `docs/notes/minimal_api_patch_note.md` | 早期阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 早期 notes 噪音，未被当前文档引用 |
| `docs/notes/proposal_alignment_note.md` | 早期阶段性 proposal 对齐 note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | 已有 `docs/project_audit/proposal_vs_actual_gap_audit_v1.md` 覆盖主审计口径 |
| `docs/patch_notes/comparison_entity_fix_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/comparison_reannotation_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，评测/指南主证据仍保留 |
| `docs/patch_notes/definition_outline_query_hotfix_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/definition_query_priority_boundary_tuning_v1.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，设计文档仍保留 |
| `docs/patch_notes/evaluation_upgrade_spec_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，`docs/evaluation/evaluation_upgrade_spec_v1.md` 仍保留 |
| `docs/patch_notes/evaluator_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，评测入口和报告仍保留 |
| `docs/patch_notes/evaluator_v2_answer_text_review_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，评测报告仍保留 |
| `docs/patch_notes/evaluator_v2_semantics_freeze_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，语义文档仍保留 |
| `docs/patch_notes/evaluator_v2_skeleton_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，v2 评测报告仍保留 |
| `docs/patch_notes/fahan_controlled_replay_v1.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，实验产物仍保留 |
| `docs/patch_notes/formula_effect_boundary_tuning_v1.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，实验/设计主文件仍保留 |
| `docs/patch_notes/formula_effect_bulk_audit_decision_v1.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，bulk audit summary 仍保留 |
| `docs/patch_notes/formula_effect_cross_chapter_bridge_patch_v1.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，设计和 before/after 仍保留 |
| `docs/patch_notes/formula_effect_query_hotfix_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/formula_effect_short_tail_fragment_patch_v1.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，设计和 before/after 仍保留 |
| `docs/patch_notes/formula_effect_title_or_composition_patch_v1.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，设计和 before/after 仍保留 |
| `docs/patch_notes/frontend_layout_refactor_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/frontend_minimal_chat_layout_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/frontend_second_submit_hang_hotfix_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/frontend_streaming_ux_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/frontend_transport_disconnect_hotfix_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/frontend_transport_hotfix_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/frontend_uiux_polish_v1.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/frontend_uiux_round2_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/general_overview_finish_fix_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，分析/评测主文件仍保留 |
| `docs/patch_notes/general_overview_reannotation_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，reannotation 报告仍保留 |
| `docs/patch_notes/goldset_expand_60_80_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，当前 goldset 主版本仍保留 |
| `docs/patch_notes/goldset_independence_review_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，independence review 主文件仍保留 |
| `docs/patch_notes/goldset_v2_batchA_failure_triage_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，triage 主文件仍保留 |
| `docs/patch_notes/goldset_v2_batchA_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，Batch A 报告仍保留 |
| `docs/patch_notes/goldset_v2_batchB_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，Batch B 报告仍保留 |
| `docs/patch_notes/llm_generation_scope_decision_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，scope decision 主文件仍保留 |
| `docs/patch_notes/meaning_explanation_boundary_fix_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，分析/评测主文件仍保留 |
| `docs/patch_notes/meaning_explanation_reannotation_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，reannotation 报告仍保留 |
| `docs/patch_notes/minimal_llm_api_integration_spec_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，integration spec 主文件仍保留 |
| `docs/patch_notes/minimal_llm_api_openrouter_qwen_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/optimization_matrix_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，optimization matrix 主文件仍保留 |
| `docs/patch_notes/proposal_vs_actual_gap_audit_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，project audit 主文件仍保留 |
| `docs/patch_notes/q004_reannotation_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，q004 reannotation 报告仍保留 |
| `docs/patch_notes/q004_review_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，保留本地回查即可 |
| `docs/patch_notes/refusal_policy_fix_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，分析/评测主文件仍保留 |
| `docs/patch_notes/source_lookup_promotion_fix_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，分析/评测主文件仍保留 |
| `docs/patch_notes/source_lookup_reannotation_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，source lookup reannotation 报告仍保留 |
| `docs/patch_notes/system_completion_audit_v1_patch_note.md` | 阶段性 patch note | 已移到 outputs 本地忽略区，Git 中删除，内容本地保留 | LOCAL_ONLY | patch note 未被当前文档引用，system completion audit 主文件仍保留 |

## 3. ARCHIVE_IN_GIT 明细

| 路径 | 文件作用判断 | 当前状态判断 | 建议类别 | 理由 |
| --- | --- | --- | --- | --- |
| `docs/archive/dense_retrieval_upgrade_spec.md` | 旧检索升级方案 | 已在 archive 目录 | ARCHIVE_IN_GIT | 历史方案，当前实现已有更新文档和代码落地 |
| `docs/archive/embedding_selection_note.md` | 旧 embedding 选择说明 | 已在 archive 目录 | ARCHIVE_IN_GIT | 历史决策材料，保留归档即可 |
| `docs/archive/retrieval_upgrade_decision_log.md` | 旧 retrieval 决策记录 | 已在 archive 目录 | ARCHIVE_IN_GIT | 历史决策材料，保留归档即可 |
| `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/project_cleanup_plan_2026-04-04.md` | 旧项目清理计划 | 已归入 project audit archive | ARCHIVE_IN_GIT | 2026-04-04 旧快照，不代表当前状态 |
| `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/project_inventory_2026-04-04.md` | 旧项目 inventory | 已归入 project audit archive | ARCHIVE_IN_GIT | 2026-04-04 旧快照，不代表当前状态 |

## 4. KEEP_GIT 明细

以下非核心 Markdown 本轮只登记，不移动、不删除。

| 路径 | 文件作用判断 | 当前状态判断 | 建议类别 | 理由 |
| --- | --- | --- | --- | --- |
| `GEMINI.md` | agent 辅助说明 | 仍可服务协作上下文 | KEEP_GIT | 根层说明，体量小 |
| `artifacts/api_smoke_checks.md` | API smoke 验证产物 | 当前验证证据 | KEEP_GIT | 支撑系统可运行性 |
| `artifacts/commentarial_api_smoke_checks.md` | 注解 API smoke 验证产物 | 当前验证证据 | KEEP_GIT | 支撑 commentarial 相关能力 |
| `artifacts/commentarial_demo_summary.md` | 注解 demo 汇总 | 当前验证证据 | KEEP_GIT | 仍有复现/答辩参考价值 |
| `artifacts/commentarial_eval_snapshot.md` | 注解评估快照 | 当前验证证据 | KEEP_GIT | 评测快照不删除 |
| `artifacts/commentarial_formula_precision_snapshot.md` | 注解方剂精度快照 | 当前验证证据 | KEEP_GIT | 评测快照不删除 |
| `artifacts/commentarial_route_v2_snapshot.md` | 注解 route v2 快照 | 当前验证证据 | KEEP_GIT | 评测快照不删除 |
| `artifacts/comparison_smoke_checks.md` | comparison smoke 验证 | 当前验证证据 | KEEP_GIT | 功能 smoke 证据 |
| `artifacts/database_build_report.md` | 数据库构建报告 | 当前构建证据 | KEEP_GIT | 可支撑论文数据层 |
| `artifacts/database_smoke_checks.md` | 数据库 smoke 验证 | 当前构建证据 | KEEP_GIT | 可支撑论文数据层 |
| `artifacts/dense_index_build_report.md` | dense index 构建报告 | 当前构建证据 | KEEP_GIT | 可支撑检索层 |
| `artifacts/evaluation/answer_text_review_report_v1.md` | answer text 评审报告 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/comparison_entity_fix_v1_eval_report.md` | comparison entity 评测报告 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/comparison_reannotation_eval_report.md` | comparison reannotation 评测报告 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/evaluation_seed_smoke_checks.md` | seed smoke 验证 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/evaluator_v1_perf_regression.md` | evaluator v1 性能回归报告 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/evaluator_v1_report.md` | evaluator v1 报告 | 当前评测证据 | KEEP_GIT | 主评测报告 |
| `artifacts/evaluation/evaluator_v2_report.md` | evaluator v2 报告 | 当前评测证据 | KEEP_GIT | 主评测报告 |
| `artifacts/evaluation/general_overview_finish_fix_v1_eval_report.md` | general overview 修复评测 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/general_overview_reannotation_eval_report.md` | general overview reannotation 评测 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/goldset_v2_batchA_eval_report.md` | goldset batch A 报告 | 当前评测证据 | KEEP_GIT | batch 评测证据 |
| `artifacts/evaluation/goldset_v2_batchB_eval_report.md` | goldset batch B 报告 | 当前评测证据 | KEEP_GIT | batch 评测证据 |
| `artifacts/evaluation/goldset_v2_batchC_eval_report.md` | goldset batch C 报告 | 当前评测证据 | KEEP_GIT | batch 评测证据 |
| `artifacts/evaluation/meaning_explanation_boundary_fix_v1_eval_report.md` | meaning explanation 修复评测 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/meaning_explanation_reannotation_eval_report.md` | meaning explanation reannotation 评测 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/minimal_llm_api_regression_report.md` | minimal LLM API 回归报告 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/modelstudio_qwen_plus_regression_report.md` | Model Studio 回归报告 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/q004_reannotation_eval_report.md` | q004 reannotation 评测 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/refusal_policy_fix_v1_eval_report.md` | refusal policy 修复评测 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/source_lookup_promotion_fix_v1_eval_report.md` | source lookup promotion 评测 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/evaluation/source_lookup_reannotation_eval_report.md` | source lookup reannotation 评测 | 当前评测证据 | KEEP_GIT | 评测报告不删除 |
| `artifacts/experiments/definition_query_primary_prioritization_before_after_v1.md` | definition query before/after | 当前实验证据 | KEEP_GIT | before/after 证据不删除 |
| `artifacts/experiments/definition_query_priority_regression_report_v1.md` | definition query 回归报告 | 当前实验证据 | KEEP_GIT | 实验报告不删除 |
| `artifacts/experiments/fahan_controlled_replay_before_after_v1.md` | 发汗 controlled replay before/after | 当前实验证据 | KEEP_GIT | before/after 证据不删除 |
| `artifacts/experiments/formula_effect_before_after_v1.md` | formula_effect before/after | 当前实验证据 | KEEP_GIT | before/after 证据不删除 |
| `artifacts/experiments/formula_effect_bulk_audit_summary_v1.md` | formula_effect bulk audit summary | 当前实验证据 | KEEP_GIT | 实验报告不删除 |
| `artifacts/experiments/formula_effect_cross_chapter_bridge_before_after_v1.md` | formula_effect bridge before/after | 当前实验证据 | KEEP_GIT | before/after 证据不删除 |
| `artifacts/experiments/formula_effect_short_tail_fragment_before_after_v1.md` | formula_effect short-tail before/after | 当前实验证据 | KEEP_GIT | before/after 证据不删除 |
| `artifacts/experiments/formula_effect_title_or_composition_before_after_v1.md` | formula_effect title/composition before/after | 当前实验证据 | KEEP_GIT | before/after 证据不删除 |
| `artifacts/fts5_smoke_checks.md` | FTS5 smoke 验证 | 当前验证证据 | KEEP_GIT | 检索层 smoke 证据 |
| `artifacts/general_question_smoke_checks.md` | general question smoke 验证 | 当前验证证据 | KEEP_GIT | 策略层 smoke 证据 |
| `artifacts/generation_alignment_v1/generation_alignment_v1_report.md` | generation alignment 报告 | 当前验证证据 | KEEP_GIT | 生成质量回归证据 |
| `artifacts/hybrid_answer_smoke_checks.md` | hybrid answer smoke 验证 | 当前验证证据 | KEEP_GIT | 主链路 smoke 证据 |
| `artifacts/hybrid_retrieval_smoke_checks.md` | hybrid retrieval smoke 验证 | 当前验证证据 | KEEP_GIT | 主链路 smoke 证据 |
| `artifacts/llm_api_smoke_checks.md` | LLM API smoke 验证 | 当前验证证据 | KEEP_GIT | API 验证证据 |
| `artifacts/llm_api_smoke_checks_modelstudio.md` | Model Studio smoke 验证 | 当前验证证据 | KEEP_GIT | LLM 接入验证证据 |
| `artifacts/llm_api_smoke_checks_modelstudio_live.md` | Model Studio live smoke 验证 | 当前验证证据 | KEEP_GIT | live 验证证据 |
| `artifacts/retrieval_smoke_checks.md` | retrieval smoke 验证 | 当前验证证据 | KEEP_GIT | 检索基线证据 |
| `docs/evaluation/*` | 评测规范、标注准则、reannotation 报告 | 当前评测依据 | KEEP_GIT | 论文/答辩和评测复现依赖 |
| `docs/design/*` | 设计说明和策略文档 | 当前设计依据 | KEEP_GIT | 不作为阶段性噪音处理 |
| `docs/specs/*` | 规格、计划、验收 checklist | 当前规格依据 | KEEP_GIT | 不作为阶段性噪音处理 |
| `docs/data/*` | 数据层报告和策略说明 | 当前数据依据 | KEEP_GIT | 数据构建和论文可引用 |
| `docs/analysis/*` | 修复分析报告 | 当前分析依据 | KEEP_GIT | 与对应评测报告互补 |
| `docs/project_audit/*_v1.md` | 项目审计与清理报告 | 当前清理依据 | KEEP_GIT | 本轮新增交付物 |
| `docs/setup/*` | 部署和本地开发说明 | 当前运行依据 | KEEP_GIT | 用户和答辩演示可能直接使用 |
| `docs/review/*` | 人工 review 计划/报告 | 当前复核依据 | KEEP_GIT | 不删除唯一复核记录 |
| `docs/perf/perf_report.md` | 性能报告 | 当前测试依据 | KEEP_GIT | 性能测试证据 |
| `docs/system_completion_audit_v1.md` | 系统完成度审计 | 当前审计依据 | KEEP_GIT | 毕设收口材料 |

## 5. DELETE_SAFE 明细

无。

本轮没有永久删除 Markdown。
