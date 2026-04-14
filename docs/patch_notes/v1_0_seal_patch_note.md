# V1.0 毕业设计演示版封板增强 Patch Note

- 日期：2026-04-14
- 版本：V1.0 (Defense-ready)

## 1. 核心变更摘要

本轮工作的核心目标是将系统从“原型 MVP”状态正式封板为“毕业设计演示版 V1.0”，确保所有对外口径一致，并补齐答辩所需的关键材料。

## 2. 去 MVP 标签与口径同步

- **口径统一**：将 `README.md`、`PRD_v1.md`、`technical_design_v1.md`、`system_spec_v1.md` 中的“MVP/原型”等词汇统一替换为“V1.0 毕业设计演示版”。
- **文件重命名**：
  - `zjshl_mvp.db` -> `zjshl_v1.db`
  - `build_mvp_database.py` -> `build_v1_database.py`
  - `build_mvp_safe_dataset.py` -> `build_v1_safe_dataset.py`
  - `zjshl_dataset_v2_mvp_safe.zip` -> `zjshl_dataset_v2_v1_safe.zip`
- **实现对齐**：在文档中明确反映了 **LLM 接入 (Qwen-plus)** 和 **历史会话记录 (ConversationStore)** 已完整实现并接通这一事实。

## 3. 答辩材料补齐

- **对齐检查表**：新增 `docs/final/proposal_alignment_v1.md`，逐条对照开题报告目标，证明系统已达标。
- **结构图件**：在 `docs/figures/` 目录下新增 Mermaid 格式的系统功能结构图与系统架构结构图。
- **运行手册**：新增 `docs/final/defense_runbook_v1.md`，提供一键启动与演示指南。

## 4. 工作区与代码卫生

- **数据库路径优化**：
  - 将运行时生成的 `chat_history_v1.db` 移至 `artifacts/runtime/` 目录。
  - 更新 `.gitignore` 以彻底忽略所有运行时生成的数据库工件。
- **旧命令清理**：清理了所有对不存在的 `app_minimal_api.py` 的引用，统一至 `backend.api.minimal_api`。
- **代码一致性**：更新了 `ConversationStore` 的默认数据库路径。

## 5. 验收状态

- **仓库对外口径**：已统一为 V1.0 演示版。
- **开题对齐**：核心 RAG 链路已落地，差异点已记录并合理解释。
- **运行稳定性**：API 与前端同源链路测试通过，支持 LLM 改写与流式输出。

---
*注：本版本为毕业设计最终演示版，后续变更应遵循 V1.0 封板约束。*
