# evaluator_v2 语义冻结 Patch Note

- 日期：2026-04-10
- 类型：documentation / schema alignment
- 对应轮次：评估优化第二步

## 1. 本轮做了什么

本轮只做“语义冻结 / 文档收口 / schema 对齐”，没有改 evaluator 主骨架逻辑。

新增文档：

1. `docs/evaluation/evaluator_v2_metric_semantics_v1.md`
2. `docs/evaluation/evaluator_v2_taxonomy_semantics_v1.md`
3. `docs/patch_notes/evaluator_v2_semantics_freeze_patch_note.md`

小幅更新：

1. `config/evaluation/evaluator_v2_metric_schema_draft.json`
2. `docs/evaluation/evaluation_failure_taxonomy_v1.md`

## 2. 这轮冻结了哪些口径

### 2.1 Retrieval 指标语义

已明确冻结：

1. `top_k_values` 是固定诊断窗口，不是业务主链参数
2. `fused_hit_at_k` 与 `rerank_hit_at_k` 的分母是“可评估题”，当前为 `120`
3. `by_question_type.count` 是题型总量，不是 Hit@K 分母
4. refusal 类全 0 表示“当前口径下不适用的占位结果”，不是异常
5. `rerank_rank_delta = best_after - best_before`
6. `improved / unchanged / worsened` 的统计口径已经固定

### 2.2 Taxonomy 语义

已明确冻结：

1. taxonomy 当前是诊断层 artifact
2. taxonomy 不等价于 v1 强失败
3. 可以出现 `all_checks_passed = true` 且 `items_with_failures > 0`
4. taxonomy 不影响 `--fail-on-evaluation-failure` 的退出逻辑
5. `category_counts` 与 `subcategory_counts` 按条目计数
6. `items_with_failures` 按题目去重计数

## 3. 对当前三个样本的正式解释

本轮把以下三条样本的读取方式冻结了：

1. `eval_seed_q001`
2. `eval_seed_q023`
3. `eval_seed_q095`

冻结结论如下：

1. `q001 / q023` 属于“fused 已命中，但 rerank 把 gold 挤出 top10”的代表样本
2. `q095` 属于“fused 阶段就没把 gold 拉进 top10，rerank 仅轻微改善但仍未进 top10”的代表样本
3. 三者都属于 retrieval 诊断信号，不等于 v1 强失败

## 4. schema / taxonomy 文档做了哪些最小纠偏

### 4.1 schema draft

本轮对 `config/evaluation/evaluator_v2_metric_schema_draft.json` 做了最小对齐：

1. 把 `answer_text_quality_review` 和 `latency_benchmark` 加入 root `required`
2. 把 `failure_taxonomy.artifact_path` 加入 `required`
3. 为 retrieval metrics 与 failure taxonomy 的关键字段补了 `description`

这样做的原因是：

1. 当前实际 report 已经稳定包含这些字段
2. 语义冻结后，schema 应与当前实际 report 结构更严格对齐

对既有 report 读取的影响：

1. 无影响
2. 当前已产出的 `evaluator_v2_report.json` 已满足新约束

### 4.2 taxonomy 文档

本轮只做了两处轻量收口：

1. 增加语义冻结参考文档链接
2. 明确写出 taxonomy 不影响 `--fail-on-evaluation-failure`

对既有 report 读取的影响：

1. 无影响

## 5. 本轮明确没做什么

以下内容本轮都没有做：

1. 没有改 retrieval 逻辑
2. 没有改 rerank 策略
3. 没有改 prompt
4. 没有改 goldset
5. 没有加 answer_text review 实评
6. 没有加 latency benchmark 实跑
7. 没有改前端 / API / payload contract
8. 没有把 taxonomy 接进退出码

## 6. 本轮完成后的意义

做完这一步以后，项目协调层已经可以稳定回答三件事：

1. `evaluator_v2` 现在量的是哪一层、分母是什么
2. taxonomy 到底算不算失败
3. 为什么 retrieval 优化 / answer_text review / latency 之前要先冻结口径

这意味着后续任何 retrieval 或 answer_text 结果，都可以回到同一把尺子上解释。
