# evaluator_v2 主骨架 Patch Note

- 日期：2026-04-09
- 类型：evaluation tooling / report artifact
- 对应轮次：评估优化第一步

## 1. 本轮目标

本轮只实现 `evaluator_v2` 主骨架，不做 retrieval 调优、不做 prompt 调优、不做人评 review、不做 latency benchmark。

实现目标固定为四件事：

1. 在 `run_evaluator_v1.py` 基础上扩出 `run_evaluator_v2.py`
2. 接入 retrieval 指标字段
3. 接入 failure taxonomy 字段
4. 输出 v2 JSON / Markdown 报告

## 2. 本轮新增内容

### 2.1 新增 `scripts/run_evaluator_v2.py`

实现方式不是重写评估链，而是复用 v1 主体并做最小扩展：

1. 继续复用 goldset 150 的 replay 方式
2. 继续复用 local assembler / API 双入口
3. 继续复用 v1 的 mode / citation / unsupported assertion / refusal 边界检查
4. 在评估结果外层补充 retrieval metrics 与 failure taxonomy

### 2.2 新增 retrieval 指标字段

本轮已实际接入以下字段：

1. `top_k_values`
2. `aggregate.fused_hit_at_k`
3. `aggregate.rerank_hit_at_k`
4. `by_question_type`
5. `rerank_delta_summary`

其中：

1. `Hit@K` 固定使用 `K = 1, 3, 5, 10`
2. 支持按 `source_lookup / meaning_explanation / general_overview / comparison / refusal` 五类题型汇总
3. 支持比较 fused 阶段与 rerank 阶段 gold rank 的变化

### 2.3 新增 failure taxonomy 字段

本轮已实际接入以下字段：

1. `category_counts`
2. `subcategory_counts`
3. `items_with_failures`

并新增文档：

1. `docs/evaluation/evaluation_failure_taxonomy_v1.md`

用于冻结 taxonomy 的类别语义、计数规则与当前轮次边界。

### 2.4 新增 v2 报告产物

本轮新增：

1. `artifacts/evaluation/evaluator_v2_report.json`
2. `artifacts/evaluation/evaluator_v2_report.md`

报告结构已尽量对齐：

1. `config/evaluation/evaluator_v2_metric_schema_draft.json`

## 3. 与 v1 的差异

相对 `evaluator_v1`，本轮的核心变化不是更换评估对象，而是把“最终 payload 校验器”扩成“带 retrieval 诊断的评估报告器”。

具体差异如下：

1. v1 主要回答：系统有没有回归
2. v2 skeleton 新增回答：检索链哪一层更值得先优化、失败样本主要集中在哪

本轮依然保留 v1 的正式边界，不改变以下事实：

1. 主链业务逻辑未改
2. payload contract 未改
3. goldset 未扩
4. `summary.failure_count` 仍然沿用 v1 强校验口径

## 4. 本轮实际运行结果

本轮已完成对 `goldset_v2_working_150.json` 的 full 150 回放，并成功产出 v2 JSON / Markdown 报告。

结果摘要如下：

1. `total_questions = 150`
2. `mode_match_count = 150`
3. `citation_basic_pass_count = 120`
4. `failure_count = 0`
5. `all_checks_passed = true`

retrieval 诊断摘要如下：

1. fused `Hit@10 = 119 / 120 = 0.9917`
2. rerank `Hit@10 = 117 / 120 = 0.9750`
3. rerank delta：`improved = 19`，`unchanged = 71`，`worsened = 30`

failure taxonomy 摘要如下：

1. `items_with_failures = 3`
2. `retrieval_failure = 4`
3. 其余 category 当前均为 `0`

对应样本主要是：

1. `eval_seed_q001`
2. `eval_seed_q023`
3. `eval_seed_q095`

这里需要特别说明：

这些 taxonomy 条目当前是“检索诊断信号”，不是本轮 v1 强校验失败，因此不会把本次 replay 判为失败退出。

## 5. 本轮明确没做什么

以下内容本轮明确没有实现，并且属于刻意留白：

1. 没有做人评 `answer_text review`
2. 没有做 `latency mini-benchmark`
3. 没有做 retrieval 参数调优
4. 没有做 prompt 调优
5. 没有改前端
6. 没有改业务主链

## 6. 已知边界

本轮 v2 skeleton 仍然有三条明确边界：

1. `failure_taxonomy` 目前只接入自动可判定项，answer_text / latency / llm runtime 相关类别仍是预留位
2. taxonomy 当前用于诊断与统计，不直接进入退出码判定
3. schema draft 已与当前报告结构对齐，但仍保留后续扩展空间

## 7. 下一步建议

如果继续按 `evaluation_upgrade_task_breakdown_v1.md` 推进，下一步应做的是：

1. 冻结 retrieval 指标与 taxonomy 语义
2. 在此基础上再进入 answer_text review 与 latency benchmark
