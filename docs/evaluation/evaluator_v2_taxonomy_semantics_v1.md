# evaluator_v2 Failure Taxonomy 语义 v1

- 文档版本：v1
- 文档日期：2026-04-10
- 文档定位：冻结 `evaluator_v2` 中 failure taxonomy 的读取与解释口径
- 配套文档：
  - `docs/evaluation/evaluation_failure_taxonomy_v1.md`
  - `docs/evaluation/evaluator_v2_metric_semantics_v1.md`

## 1. 结论先行

本轮必须冻结的结论只有四条：

1. taxonomy 当前是诊断层 artifact
2. taxonomy 不等价于 v1 强失败
3. 可以出现 `all_checks_passed = true` 且 `items_with_failures > 0`
4. taxonomy 当前不影响 `--fail-on-evaluation-failure` 的退出逻辑

这四条结论是后续 retrieval 优化、answer_text review、latency benchmark 和论文结果分析的共同前提。

## 2. taxonomy 在系统里的位置

`evaluator_v2` 目前有两层口径：

1. 强校验层
   - 延续 `evaluator_v1`
   - 负责决定当前主链是否回归
2. 诊断层
   - 新增的 retrieval metrics 和 failure taxonomy
   - 负责告诉我们哪里值得继续优化

taxonomy 属于第 2 层，不属于第 1 层。

因此：

1. `summary.failure_count` 看的是强校验层
2. `failure_taxonomy.items_with_failures` 看的是诊断层

这两个数可以不同，而且当前就确实不同。

## 3. 与 v1 强校验的关系

taxonomy 当前与以下 v1 强校验并行存在：

1. `mode_match`
2. `citation_basic_pass`
3. `unsupported_assertion_check`
4. refusal 边界相关空字段检查

正式关系如下：

1. taxonomy 可以复用这些检查的结果来打标签
2. 但 taxonomy 不会反向覆盖 v1 的 pass / fail 结论
3. `failure_count = 0` 只表示强校验层没发现问题
4. `items_with_failures > 0` 表示诊断层发现了值得继续跟踪的信号

所以当前报告里：

1. `failure_count = 0`
2. `items_with_failures = 3`

两者同时成立是正常的，不是冲突。

## 4. 退出码语义

taxonomy 当前不影响退出码。

正式冻结口径：

1. `--fail-on-evaluation-failure` 只看 v1 强校验是否通过
2. taxonomy 即便出现条目，也不会单独触发非零退出

因此：

1. taxonomy 是“提醒我们后面该优化哪里”
2. 不是“本轮 replay 必须判失败”

## 5. 一级分类定义

### 5.1 当前已自动接入的 category

#### `retrieval_failure`

含义：

在当前冻结的诊断窗口里，gold evidence 没有进入期望观察范围，或 rerank 使 gold 排位明显恶化。

#### `citation_failure`

含义：

最终输出中的 citation 未匹配 gold `record_id` 或 canonical `passage_id`。

#### `answer_mode_failure`

含义：

最终 `answer_mode` 与 gold 期望模式不一致。

#### `evidence_layering_failure`

含义：

在应为空、应拒答或应不输出证据的样本中，系统输出了不该出现的 evidence / citation / primary evidence。

#### `unsupported_assertion_failure`

含义：

最终回答触发了 v1 已定义的 unsupported assertion 边界规则。

### 5.2 当前已预留但未自动接入的 category

#### `answer_text_quality_issue`

预留给后续 answer_text review。

#### `llm_runtime_issue`

预留给后续 LLM runtime / validator / fallback 诊断。

#### `latency_issue`

预留给后续 latency mini-benchmark。

## 6. 二级分类定义

### 6.1 当前已启用的 subcategory

#### `gold_miss_in_fused_topk`

gold 未进入 fused top `K` 观察窗口。

#### `gold_miss_after_rerank`

gold 未进入 rerank top `K` 观察窗口。

#### `citation_not_in_gold`

citation 未匹配 gold `record_id` 或 canonical `passage_id`。

#### `expected_weak_but_actual_strong`

gold 期望 `weak_with_review_notice`，但实际给成 `strong`。

#### `expected_refuse_but_not_refuse`

gold 期望 `refuse`，但实际没有拒答。

#### `mode_mismatch_other`

除上述两类之外的其他 mode 错配。

#### `primary_should_be_empty`

`primary_evidence` 本应为空，但实际不为空。

#### `evidence_should_be_zero`

evidence 槽位本应为空，但实际不为空。

#### `citations_should_be_zero`

citation 列表本应为空，但实际不为空。

#### `strong_without_gold_evidence`

回答给出 `strong` 结论，但没有对应 gold evidence 支撑。

#### `mode_boundary_broken`

已确认属于 mode / boundary 破坏，但还不适合细分到更具体二级类的兜底标签。

### 6.2 当前只保留结构、不参与实际判定的 subcategory

以下 subcategory 已保留在 schema / report 中，但本轮仍为预留位：

1. `clarity_low`
2. `structure_low`
3. `evidence_faithfulness_low`
4. `llm_fallback_triggered`
5. `llm_validator_reject`
6. `latency_over_threshold`

## 7. 计数规则

### 7.1 `category_counts`

计数规则：

1. 按 taxonomy 条目计数
2. 不按题目去重
3. 同一题如果同时命中两个 retrieval subcategory，就会给 `retrieval_failure` 贡献 `2`

### 7.2 `subcategory_counts`

计数规则：

1. 按 taxonomy 条目计数
2. 不按题目去重
3. 每个 subcategory 命中一次就加 `1`

### 7.3 `items_with_failures`

计数规则：

1. 按题目去重
2. 只要一题至少命中一个 taxonomy 条目，就计为 `1`
3. 同一题即便命中多个条目，也只记一次

## 8. 如何解读当前结果

当前报告摘要是：

1. `failure_count = 0`
2. `items_with_failures = 3`
3. `category_counts.retrieval_failure = 4`

正式解释是：

1. 当前主链没有 mode / citation / unsupported assertion 回归
2. 但有 3 道题在 retrieval 诊断窗口上出现了值得关注的信号
3. 这 3 道题一共贡献了 4 个 taxonomy 条目

所以：

1. 题目数是 `3`
2. taxonomy 条目数是 `4`
3. 这两者不需要相等

## 9. 对当前三个样本的固定口径

### 9.1 `eval_seed_q001`

它被记入 taxonomy 的原因：

1. fused 阶段 gold rank 是 `1`
2. rerank 后 gold rank 变成 `12`
3. 因而命中 `gold_miss_after_rerank`

它属于：

1. rerank 问题
2. 不是 fused 问题

它目前不等于 v1 强失败，因为：

1. `mode_match = true`
2. citation 仍通过 gold 检查
3. unsupported assertion 仍通过

对下一步 retrieval 优化的意义：

1. 这是优先检查 rerank 负迁移的代表样本

### 9.2 `eval_seed_q023`

它被记入 taxonomy 的原因：

1. fused 阶段 gold rank 是 `1`
2. rerank 后 gold rank 变成 `14`
3. 因而命中 `gold_miss_after_rerank`

它属于：

1. rerank 问题
2. 不是 fused 问题

它目前不等于 v1 强失败，因为：

1. 最终回答仍通过 mode/citation/unsupported assertion 强校验

对下一步 retrieval 优化的意义：

1. 它和 `q001` 一起构成“fused 已好，但 rerank 拖后腿”的稳定样本组

### 9.3 `eval_seed_q095`

它被记入 taxonomy 的原因：

1. fused top10 没命中 gold
2. rerank top10 也没命中 gold
3. 所以同时命中 `gold_miss_in_fused_topk` 和 `gold_miss_after_rerank`

它属于：

1. fused 问题优先
2. rerank 只有轻微改善，但没有把问题修回来

它目前不等于 v1 强失败，因为：

1. 最终回答仍通过 mode/citation/unsupported assertion 强校验
2. 说明 gold 仍可在更靠后的候选中被利用

对下一步 retrieval 优化的意义：

1. 这是优先检查 fused 召回与 general query 路径的代表样本

## 10. 为什么这一步先于 retrieval 优化 / answer_text review / latency

因为如果 taxonomy 语义不先冻结，后面三条线都会缺一把稳定的尺子：

1. retrieval 优化会不知道“improved”到底在说什么
2. answer_text review 会缺少与检索诊断的共同语言
3. latency benchmark 会和失败样本分析脱节

所以这一步的价值不是“多做一个文档”，而是把后续所有结果解释锁定到同一套口径上。
