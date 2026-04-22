# Markdown 清理判断规则 v1

- 执行日期：2026-04-21
- 范围：仅处理 `.md` 文件。
- 本轮不处理：Python、TS、JSON、DB、PNG、ZIP、DOCX、源码目录、数据目录、配置目录。

## 1. 固定边界

以下 Markdown 本轮不进入清理候选：

| 范围 | 规则 |
| --- | --- |
| `README.md` | 项目入口说明，必须保留在 Git |
| `docs/contracts/*` | payload / API 合同，必须保留在 Git |
| `docs/final/*` | 答辩和论文可引用正式文档，必须保留在 Git |
| `backend/`、`frontend/src/`、`scripts/`、`config/`、`data/` | 本轮禁止触碰这些目录下的文件 |
| 当前仍被论文、评测、设计文档直接引用的 Markdown | 必须保留或只做归档，不移出 Git |

## 2. 分类规则

| 类别 | 含义 | 使用条件 |
| --- | --- | --- |
| `KEEP_GIT` | 继续保留在 Git | 正式依据、评测报告、实验 before/after、设计规格、部署说明、仍被引用的补丁记录 |
| `ARCHIVE_IN_GIT` | 留在 Git，但放入归档区 | 已过期但仍有历史解释价值的旧审计、旧方案、旧结构快照 |
| `LOCAL_ONLY` | 从 Git 移出，只在本地保留 | 未被当前文档引用、主要服务 LLM/coding agent 工作流的阶段性 patch note、demo 说明、临时验收说明 |
| `DELETE_SAFE` | 低风险，可删除 | 只有在确认可重建、无引用、无证据价值时使用；本轮未使用 |

## 3. 必须保留的 Markdown

必须保留在 Git 的 Markdown 包括：

1. 合同与正式文档：`README.md`、`docs/contracts/*`、`docs/final/*`。
2. 评测与实验唯一证据：`artifacts/evaluation/*.md`、`artifacts/experiments/*.md`。
3. 数据、检索、回答、评测、部署的主说明：`docs/data/*`、`docs/evaluation/*`、`docs/specs/*`、`docs/design/*`、`docs/setup/*`。
4. 项目审计主文件：`docs/project_audit/*_v1.md`。
5. 当前仍被多个文档引用的少量 patch note，例如 `modelstudio_qwen_plus_*`、`frontend_react_refactor_v1.md`、`v1_0_seal_patch_note.md`。

## 4. 更适合归档的 Markdown

适合 `ARCHIVE_IN_GIT` 的 Markdown：

1. 旧版项目盘点、旧 cleanup plan、旧结构快照。
2. 已被当前实现取代，但仍能解释历史决策的技术方案。
3. 已归档到 `docs/archive/` 或 `docs/project_audit/archive/` 的历史材料。

## 5. 不应该继续进入 Git 的 Markdown

适合 `LOCAL_ONLY` 的 Markdown：

1. 只服务一次 coding agent 轮次的 patch note。
2. 未被当前 README/docs/artifacts 引用的 demo 说明。
3. 已有正式设计文档、评测报告或 audit 文件覆盖的阶段性说明。
4. 前端临时验收说明、传输热修 demo、旧 UI demo 等。

本轮把这类文件移动到：

`outputs/markdown_local_only_2026-04-21/`

该目录已被既有 `.gitignore` 的 `outputs/` 规则忽略，因此文件本地保留，但不再进入 Git。

## 6. 删除规则

本轮不做 Markdown 永久删除。后续只有同时满足以下条件，才可标记为 `DELETE_SAFE`：

1. 原文件不再被任何当前文档引用。
2. 有更完整的新文件替代。
3. 不是评测、实验或论文证据唯一来源。
4. 删除前已经在 registry 中登记。
5. 删除动作写入 actions 文件并给出回滚方式。
