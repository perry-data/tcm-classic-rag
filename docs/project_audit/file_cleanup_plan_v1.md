# 文件清理分级计划 v1

- 扫描日期：2026-04-21
- 原则：先登记、再隔离、最后才考虑删除；不确定用途的文件不删。

## A 类：确认安全，可整理 / 移动 / 归档

这些对象不属于运行主链路，或已经确认是历史盘点/临时文件；本轮已处理其中一部分。

| 路径 / 文件组 | 当前判断 | 本轮动作 / 后续动作 |
| --- | --- | --- |
| `docs/project/project_cleanup_plan.md` | 旧版清理计划，内容与当前结构不一致 | 已移动到 `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/` |
| `docs/project/project_file_registry.json` | 旧版文件登记表，作为历史证据保留即可 | 已移动到 `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/` |
| `docs/project/project_inventory.md` | 旧版 inventory，部分路径已过期 | 已移动到 `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/` |
| `docs/project/project_structure_snapshot.txt` | 旧版结构快照 | 已移动到 `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/` |
| `docs/proposal/.!38916!221030147张前_开题报告.docx` | Word/WPS 临时文件，且不应和正式开题报告并列 | 已移动到 `docs/project_audit/archive/quarantine_temp_files_2026-04-21/` |
| `.playwright-cli/` | 本地 Playwright 快照输出 | 已加入 `.gitignore`；不移动现有文件 |
| `__pycache__/`、`*.pyc` | Python 可重建缓存 | 后续可直接清理；本轮未删 |
| `.DS_Store` | macOS 系统垃圾文件 | 后续可直接清理；本轮未删 |
| `thesis_private/assembled/~$*.docx`、`_template_probe/~$*.docx` | Word 临时锁文件 | 后续可在确认 Word 已关闭后清理 |

## B 类：高疑似无用 / 可重建，但本轮不直接删

这些对象可能很占空间或像历史产物，但仍可能用于复现、论文证据或本地运行，因此本轮只登记。

| 路径 / 文件组 | 疑点 | 建议 |
| --- | --- | --- |
| `artifacts/hf_cache/` | 约 1.1G，属于模型缓存，不入 Git | 磁盘紧张时可删除，删除后需重新下载模型 |
| `artifacts/runtime/chat_history_v1.db` | 本地聊天历史 runtime DB | 不提交；清理前先确认是否要保留演示历史 |
| `artifacts/chat_history_v1.db` | 另一个本地聊天 DB | 先确认实际服务读取路径，再决定保留或归档 |
| `frontend/dist/` | 可由 `npm run build` 重建 | 若部署依赖本地 dist，先重建验证后再清理 |
| `artifacts/route_a_before_results.json`、`artifacts/route_a_after_results.json` | route A 实验产物，已被 `.gitignore` 列为 runtime output | 后续确认对应实验已结束后归档或删除 |
| `artifacts/evaluation/goldset_v2_working_102.json`、`126.json` | 旧阶段 goldset | 不删；可移入 `artifacts/evaluation/archive/` 并保留 150 为当前主版本 |
| `artifacts/evaluation/*_reannotated.json` 与 `*_reannotation_*` | reannotation 中间版本多 | 不删；可按 question family 分 archive |
| `artifacts/frontend_*_v1/` | 前端截图验收产物 | 论文/验收可能引用，不删；可统一放 `artifacts/frontend/` |
| `artifacts/experiments/formula_effect_*` | formula_effect 实验与 before/after 多 | 可复现实验链路，不删；后续可补索引说明 |
| `reports/*.json`、`reports/*.csv` | 与 `docs/data/`、`artifacts/` 有交叉 | 先确认是否由脚本重建，再决定是否迁入 `artifacts/reports/` |
| `thesis_private/assembled/_render_check_word/` | docx 渲染检查截图 | 论文成稿前有用；后续论文定稿后再清理 |
| `thesis_private/assembled/_template_probe/` | 模板探针产物 | 高疑似临时，但与 docx 格式验证有关，暂不删 |
| `data/processed/commentarial_layer_round3/commentarial_handoff_bundle/` | 一次性交接包 | 当前仍可能是 commentarial 数据证据，不动 |
| `scripts/run_formula_effect_*_fix_v1.py` | 一次性 replay/fix 脚本 | 虽像临时脚本，但被相关实验链路复用；暂留在 `scripts/` |

## C 类：核心文件，禁止本轮触碰

这些文件属于运行、合同、数据源或验证主链路。清理轮不应移动、删除或顺手重构。

| 路径 / 文件组 | 原因 |
| --- | --- |
| `backend/api/minimal_api.py` | API 和同源服务入口 |
| `backend/retrieval/hybrid.py`、`backend/retrieval/minimal.py` | 检索主链路 |
| `backend/answers/assembler.py` | 回答编排主入口；本轮开始前已有未提交改动，禁止混改 |
| `backend/llm/prompt_builder.py`、`backend/llm/validator.py`、`backend/llm/client.py` | LLM 生成与校验链路 |
| `backend/chat_history/store.py` | 历史会话存储语义 |
| `backend/strategies/general_question.py` | 总括类问题策略 |
| `backend/checks/*.py` | 回归检查入口 |
| `frontend/src/*`、`frontend/package.json`、`frontend/vite.config.ts` | 前端源码和构建配置 |
| `scripts/build_v1_database.py`、`scripts/build_dense_index.py` | 数据库和 FAISS 索引构建入口 |
| `scripts/run_evaluator_v1.py`、`scripts/run_evaluator_v2.py` | 当前评测入口 |
| `scripts/dev.py`、`scripts/bootstrap_windows.ps1` | 本地开发/Windows 启动入口 |
| `config/*.json`、`config/evaluation/*.json`、`config/controlled_replay/*.json` | 运行和评测配置 |
| `data/raw/《注解伤寒论》.zip` | 原始数据源 |
| `data/processed/zjshl_dataset_v2/` | 当前 full 数据底座 |
| `dist/zjshl_dataset_v2_v1_safe.zip` | 当前 safe 数据包交付物 |
| `docs/contracts/*`、`docs/final/*`、`README.md` | 合同与正式说明 |
| `.env`、`.env.example` | 敏感/环境配置；本轮不读取、不修改内容 |

## 后续清理优先级

1. 先清理本地垃圾：`.DS_Store`、`__pycache__/`、`*.pyc`、Word `~$*.docx`。
2. 再整理 `artifacts/`：按 `runtime/`、`evaluation/`、`experiments/`、`frontend/`、`archive/` 分层。
3. 再整理 `docs/`：给 `patch_notes/`、`evaluation/`、`thesis/` 补索引，避免靠文件名猜版本。
4. 最后才评估可重建大文件：`artifacts/hf_cache/`、FAISS 索引、runtime DB、前端构建产物。
