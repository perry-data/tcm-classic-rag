# System Completion Audit v1 Patch Note

## 本轮目的

本轮不扩功能、不补算法专题，只对照开题报告、三份正式主文档与当前主仓库实物，完成一次“面向论文与答辩”的系统完成度核查。

## 新增 / 修改文件

新增：

- `docs/system_completion_audit_v1.md`
- `docs/patch_notes/system_completion_audit_v1_patch_note.md`
- `artifacts/system_completion_audit/system_completion_matrix_v1.json`

## 核查结论摘要

本轮核查结论可以概括为三点：

1. 当前主系统闭环已经具备可写论文、可演示、可答辩基础。
2. 主链完成度高于正式主文档当前口径，尤其体现在 `chat history v1` 已回流主仓库、`qwen-plus` 最小真实接入已落地。
3. 当前最大的风险不是“功能没做出来”，而是“正式文档、论文口径和结构图还没有完全同步到当前实现”。

分模块判断摘要：

- 已完成：数据底座、检索链路、证据溯源、回答生成、LLM provider 接入、API、前端
- 部分完成：评估与测试、运行与部署、文档完备度
- 不纳入当前答辩范围：会话/history 作为附加实现，不计入冻结主链

## chat history / 一致性核查结果

本轮没有发现“chat history v1 未回流主仓库”的情况。

相反，当前主仓库已核验到：

- `backend/chat_history/store.py`
- `backend/api/minimal_api.py` 中的 conversations 系列接口
- `frontend/app.js` 中的 conversation/history 逻辑

因此，真实结论应为：

- `chat history v1` 已回流主仓库代码并接通前后端
- 但它不属于当前冻结答辩主链，不建议在论文中抬升为主系统范围

同时发现两个相关不一致点：

1. `artifacts/chat_history_v1.db` 当前是工作区未跟踪文件，不计为稳定版本化交付物。
2. 正式主文档与前端 spec 仍把 history 视为“不做”或未同步到当前实现。

## 其他关键不一致点

1. 正式主文档与 README 仍把真实 LLM 接入表述为“未接入”，但主仓库已有 `backend/llm/`、`.env.example` 和 `qwen-plus` live smoke artifact。
2. 若干 smoke artifact 仍引用不存在的 `app_minimal_api.py`。
3. 仓库中未核验到正式系统功能结构图 / 系统架构结构图文件。

## 建议下一轮唯一目标

下一轮只建议执行：

**论文/答辩口径与结构图封板 v1**

原因：

- 这是当前最重要的 P0 级收口目标。
- 若不先补齐，后续无论写论文还是准备答辩，都会反复遇到“代码与文档口径不一致”的问题。
