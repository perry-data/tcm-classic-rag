# Backend Freeze Spec

## 1. 文档目标

本文件用于封板当前《伤寒论》RAG 后端的最小闭环，并明确：

- 当前后端已经完成了什么
- 哪些行为现在视为冻结
- 哪些行为后续仍允许微调
- 前端未来应依赖的稳定边界是什么

本轮封板只覆盖后端业务闭环，不开始前端开发，不做 UI，不引入新的数据库结构，不重做 dense retrieval。

## 2. 当前后端组成

当前后端已经完成以下组成部分，并且它们共同构成可交付给前端的后端最小闭环：

- Hybrid retrieval
- dense retrieval + RRF + Cross-Encoder rerank
- evidence gating
- answer assembler
- `strong` / `weak_with_review_notice` / `refuse`
- answer payload contract

对应当前实现与产物：

- 检索主脚本：`run_hybrid_retrieval.py`
- 检索样例：`artifacts/hybrid_retrieval_examples.json`
- 检索 smoke check：`artifacts/hybrid_retrieval_smoke_checks.md`
- 回答组装主脚本：`run_answer_assembler.py`
- 回答样例：`artifacts/hybrid_answer_examples.json`
- 回答 smoke check：`artifacts/hybrid_answer_smoke_checks.md`
- payload 合同：`answer_payload_contract.md`
- dense 升级说明：`dense_retrieval_upgrade_spec.md`
- dense 落地说明：`dense_retrieval_plan.md`

## 3. 当前后端已经完成了什么

当前后端已经完成的，不需要前端再等待的能力如下：

- 用户 query 已可进入 Hybrid 检索链路，而不是只走旧的 sparse-only 最小检索。
- Hybrid 检索已包含 sparse recall、dense chunks recall、dense main_passages recall、RRF fusion、Cross-Encoder rerank。
- dense 检索当前已经落在 `records_chunks` 与 `records_main_passages` 双索引上。
- dense 命中 `chunks` 后，已经会回指到 `main_passages`，而不是让 `chunks` 直接充当主证据。
- evidence gating 仍然是最终分层裁决器，dense / rerank 只增强召回和排序，不越级决定主证据。
- answer assembler 已能把检索结果稳定组装成统一 answer payload。
- answer payload 已固定输出三模式：`strong`、`weak_with_review_notice`、`refuse`。
- 三个冻结样例已经具备稳定预期：
  - `黄连汤方的条文是什么？` -> `strong`
  - `烧针益阳而损阴是什么意思？` -> `weak_with_review_notice`
  - `书中有没有提到量子纠缠？` -> `refuse`

## 4. 当前后端的最小闭环定义

当前后端的最小闭环固定定义为：

`query -> hybrid retrieval -> evidence gating -> answer assembler -> stable payload`

进一步拆开就是：

1. 前端或调用方只提交一个用户问题 `query`。
2. Hybrid retrieval 负责 sparse + dense 召回、RRF 融合、Cross-Encoder rerank。
3. evidence gating 负责把候选严格分入 `primary_evidence`、`secondary_evidence`、`review_materials`。
4. answer assembler 负责输出稳定的 answer payload，而不是输出松散调试对象。
5. 前端未来只依赖稳定 payload，不依赖内部检索 trace、阈值或候选排序细节。

## 5. 已冻结行为

以下行为从本轮开始视为冻结，前端和后续后端工作都应以此为边界：

- `annotation_links` 继续禁用。
- `chunks` 不直接进入 `primary_evidence`。
- `annotations` 不进入 `primary_evidence`。
- `passages / ambiguous_passages` 不进入 `primary_evidence`。
- `strong / weak_with_review_notice / refuse` 三模式保留。
- answer payload 顶层字段合同保持稳定。
- 黄连汤方主证据精度补丁保持不回归。

进一步明确为：

- `primary_evidence` 的业务语义冻结为“主证据”，当前只允许合规 `main_passages` 进入。
- `secondary_evidence` 的业务语义冻结为“补充依据”，当前允许来自降级后的 `main_passages` 与 `annotations`。
- `review_materials` 的业务语义冻结为“核对材料”，当前承载 `passages` 与 `ambiguous_passages`。
- `weak_with_review_notice` 模式下 `primary_evidence` 必须为空。
- `refuse` 模式必须输出统一拒答结构，不得伪造正文答案。
- `citations` 在 `strong` 模式主要来自 `primary_evidence`；在 `weak_with_review_notice` 模式来自 `secondary_evidence + review_materials`；在 `refuse` 模式为空。
- `display_sections` 的 section 语义和字段映射保持稳定，供前端决定显示顺序与可见性。
- 顶层字段名冻结为：
  - `query`
  - `answer_mode`
  - `answer_text`
  - `primary_evidence`
  - `secondary_evidence`
  - `review_materials`
  - `disclaimer`
  - `review_notice`
  - `refuse_reason`
  - `suggested_followup_questions`
  - `citations`
  - `display_sections`

## 6. 允许后续微调的行为

以下项目后续仍允许微调，但前提是不能破坏上一节的冻结边界，也不能改变前端依赖的最小合同：

- dense 阈值
- rerank 阈值
- sparse top-k
- dense top-k
- fusion top-k
- rerank top-N
- dense-only final gate 的数值阈值
- `secondary_evidence` / `review_materials` 的候选数量上限
- `answer_text`、`disclaimer`、`review_notice`、`refuse_reason`、`suggested_followup_questions` 的文案微调
- `title` / `snippet` 的截断长度或轻量清洗策略
- rerank 设备选择，例如 `cpu` / `mps`

这些微调允许发生，因为它们不应改变：

- 三模式分类本身
- 证据分层语义
- 顶层 payload 字段
- 前端依赖的显示区块语义

## 7. 明确不在本轮封板范围内的内容

以下内容不属于本轮冻结对象，也不应在本轮启动：

- 前端页面
- UI 设计
- 复杂 HTTP API 实现
- answer payload 合同重构
- 数据库 schema 变更
- 多书扩展
- LLM 生成式回答
- 恢复 `annotation_links`

## 8. 对前端的稳定交付边界

前端未来应依赖的不是检索内部实现，而是“最小输入 + 稳定 payload 输出”：

- 最小输入：`query`
- 稳定输出：answer payload
- 业务裁决字段：`answer_mode`
- 展示编排字段：`display_sections`
- 主证据展示字段：`primary_evidence`
- 辅助 / 核对展示字段：`secondary_evidence`、`review_materials`

前端不应依赖以下内部细节：

- dense / sparse 的具体分数
- RRF 常数
- rerank 原始分数
- 具体候选召回路径
- 内部 trace 或 debug 字段
- 当前候选数量恰好等于多少

## 9. 当前是否已经稳定到可以交给前端

结论：

- 从业务闭环与 payload 合同角度看，当前后端已经稳定到可以交给前端做接口联调和页面开发。
- 从工程形态看，当前稳定的是“后端业务闭环 + 文档化 contract”，不是“完整 HTTP 服务实现”。

因此，开始前端开发的前提不是继续改检索逻辑，而是满足以下两点：

1. `backend_acceptance_checklist.md` 中的冻结样例与通用验收项全部通过。
2. 前端只依赖 `minimal_api_contract.md` 中定义的最小接口，不擅自绑定内部检索细节。

如果后续需要补一个薄的 HTTP 封装层，它应当只是 transport adapter，不应改变本文件定义的冻结行为。
