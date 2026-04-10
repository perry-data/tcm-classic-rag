# Optimization Matrix v1 Patch Note

## 1. 本轮新增了什么

本轮没有改业务代码，没有启动新的优化实现主线，而是先把“后续优化该怎么排、先做什么、哪些现在不值得做”正式收束成文档。

新增文件：

1. `docs/project_optimization/optimization_matrix_v1.md`
   - 基于当前稳定系统状态，建立五大优化维度的系统矩阵。
   - 覆盖检索质量、生成质量、前端展示、性能、评估体系五个方向。
   - 每个维度都补齐当前现状、痛点、可做动作、预期收益、风险、实现成本、论文收益与答辩收益。
2. `docs/project_optimization/optimization_priority_decision_v1.md`
   - 在矩阵基础上，正式给出 P0 / P1 / P2 排序。
   - 明确“第一轮唯一优化目标”只能选一个，并给出排序理由。
   - 说明当前不值得优先做的优化项。
3. `docs/patch_notes/optimization_matrix_v1_patch_note.md`
   - 记录本轮范围、判断依据与结论摘要。

## 2. 为什么现在先做优化矩阵

原因有三点：

1. 当前系统已经具备稳定基线，不再处于“先把链路跑通再说”的阶段。
2. 150 条 evaluator v1、qwen-plus live validation、主链闭环已经足以支撑“开始做优化排序”。
3. 如果不先明确优先级，后续很容易同时碰 retrieval、prompt、前端、性能，导致系统收口失焦。

所以，本轮先做的不是代码优化，而是**优化决策收束**。

## 3. 本轮依据的稳定基线

本轮判断默认承接以下已完成状态：

1. retrieval / rerank / evidence gating / answer assembler / minimal API / frontend MVP 已稳定。
2. `goldset_v2_working_150.json` 已形成，`evaluator_v1` 回放结果为：
   - `total_questions = 150`
   - `mode_match = 150/150`
   - `citation_check_required_basic_pass = 120/120`
   - `failure_count = 0`
3. `qwen-plus` live validation 已成功：
   - 4 条 non-refuse 样例真实走到 LLM 返回
   - `refuse` 继续按设计跳过 LLM
   - `answer_mode`、evidence、citations 不变

这意味着当前最需要解决的已经不是“系统能不能工作”，而是“下一步该优先优化哪一层”。

## 4. 本轮结论摘要

### 4.1 五大优化维度的排序

本轮给出的正式排序是：

1. P0：评估体系优化
2. P1：检索质量优化
3. P1：Prompt / 生成质量优化
4. P2：性能优化
5. P2：前端展示优化

### 4.2 第一轮唯一优化目标

本轮明确只选一个：

> 第一轮唯一优化目标：**评估优化**

原因不是“评估最炫”，而是：

1. 它风险最低，不破坏当前稳定主链。
2. 它论文收益最高，直接服务第 4 章。
3. 它能为 retrieval / generation / performance 后续优化建立统一尺子。
4. 没有更细评估前，直接做其他主线都容易变成盲调。

### 4.3 当前不值得优先做的项

本轮明确认为以下事项不值得现在优先推进：

1. React + Tailwind 前端重写
2. 多步 Prompt 编排
3. 多书扩展
4. 在评估尺子未升级前继续把 goldset 从 150 往 200-250 堆量
5. 生产级性能 / 并发 / 部署优化
6. 改 payload contract 或 evidence 分层规则

这些事项的共同问题是：

- 收益不够集中
- 容易破坏稳定性
- 不利于论文收口
- 更适合写进展望而不是当前主线

## 5. 本轮未做什么

本轮明确没有做以下事情：

1. 没有改 retrieval、rerank、gating、answer assembler。
2. 没有改 Minimal API 和 frontend 逻辑。
3. 没有改 `answer_mode`、evidence slots、citations、payload contract。
4. 没有启动任何新的多线优化实现。
5. 没有写论文正文。

## 6. 本轮正式意义

本轮完成后，项目新增了三项正式成果：

1. 有了一份可复用的系统优化矩阵。
2. 有了一份明确的优先级与唯一主线决策文档。
3. 后续每一轮优化都可以围绕“先评估、再单线推进、最后回归验证”的方式收束，而不是回到发散扩功能的状态。
