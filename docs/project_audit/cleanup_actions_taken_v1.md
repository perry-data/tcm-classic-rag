# 本轮整理动作记录 v1

- 执行日期：2026-04-21
- 执行原则：只做低风险、可回溯整理；不删除核心文件；不修改后端/前端业务逻辑。

## 1. 已执行动作

### 1.1 建立项目体检入口

新增：

- `docs/project_audit/README.md`
- `docs/project_audit/project_health_check_v1.md`
- `docs/project_audit/file_cleanup_plan_v1.md`
- `docs/project_audit/directory_reorg_suggestion_v1.md`
- `docs/project_audit/cleanup_actions_taken_v1.md`

目的：把本轮体检结论、清理分级、目录整理建议和实际动作放到统一入口，避免散落在聊天记录里。

### 1.2 归档旧版清理盘点

移动：

| 原路径 | 新路径 |
| --- | --- |
| `docs/project/project_cleanup_plan.md` | `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/project_cleanup_plan_2026-04-04.md` |
| `docs/project/project_file_registry.json` | `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/project_file_registry_2026-04-04.json` |
| `docs/project/project_inventory.md` | `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/project_inventory_2026-04-04.md` |
| `docs/project/project_structure_snapshot.txt` | `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/project_structure_snapshot_2026-04-04.txt` |

原因：这组文件是 2026-04-04 的旧扫描结果，当前仓库结构已经变化；继续放在 `docs/project/` 容易被误读为当前状态。

### 1.3 隔离正式目录中的临时文件

移动并重命名：

| 原路径 | 新路径 |
| --- | --- |
| `docs/proposal/.!38916!221030147张前_开题报告.docx` | `docs/project_audit/archive/quarantine_temp_files_2026-04-21/word_temp_221030147_opening_report_2026-04-21.docx.tmp` |

原因：该文件是 Word/WPS 临时文件形态，且被 Git 跟踪；它不应与正式开题报告 `docs/proposal/221030147张前_开题报告.docx` 并列。

### 1.4 忽略本地 Playwright 快照目录

修改：

- `.gitignore` 增加 `.playwright-cli/`

原因：`.playwright-cli/` 是本地浏览器快照输出，不属于源码、数据、正式文档或论文资产；本轮没有移动已有快照，只阻止其继续出现在 Git 未跟踪列表里。

## 2. 明确未执行的动作

本轮没有执行：

- 没有删除任何核心源码、数据、评测文件或论文材料。
- 没有修改 `backend/answers/assembler.py`，该文件在本轮开始前已有既有改动。
- 没有修改 `answer_mode`、payload contract、检索主链路或 LLM 生成链路。
- 没有读取或修改 `.env` 内容。
- 没有移动 `.playwright-cli/` 里的现有快照文件。
- 没有清理 `artifacts/hf_cache/`、runtime DB、FAISS index、frontend dist。

## 3. 本轮产生的新目录

| 目录 | 用途 |
| --- | --- |
| `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/` | 旧版项目清理盘点归档 |
| `docs/project_audit/archive/quarantine_temp_files_2026-04-21/` | 明确临时文件的隔离区 |

## 4. 回溯方式

如果需要撤回本轮整理：

1. 将 `docs/project_audit/archive/previous_cleanup_inventory_2026-04-04/*` 移回 `docs/project/` 并恢复原文件名。
2. 将 `word_temp_221030147_opening_report_2026-04-21.docx.tmp` 移回 `docs/proposal/.!38916!221030147张前_开题报告.docx`。
3. 从 `.gitignore` 删除 `.playwright-cli/`。
4. 删除本轮新增的 `docs/project_audit/*_v1.md` 和 `docs/project_audit/README.md`。

这些动作均不涉及核心运行链路。
