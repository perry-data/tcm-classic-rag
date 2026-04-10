# evaluator_v2 Retrieval 指标语义 v1

- 文档版本：v1
- 文档日期：2026-04-10
- 文档定位：冻结 `evaluator_v2` 中 retrieval 指标的读取口径
- 适用产物：
  - `scripts/run_evaluator_v2.py`
  - `artifacts/evaluation/evaluator_v2_report.json`
  - `artifacts/evaluation/evaluator_v2_report.md`
  - `config/evaluation/evaluator_v2_metric_schema_draft.json`

## 1. 这份文档回答什么

本文件只回答一件事：

`evaluator_v2` 现在到底在量什么，以及这些 retrieval 指标应该怎么读。

它不涉及：

1. retrieval 参数调优
2. rerank 策略改造
3. prompt 调优
4. answer_text review
5. latency benchmark

## 2. 读取前提

`evaluator_v2` 的 retrieval 指标是“诊断层指标”，不是业务主链的直接评分器。

它的主要用途是：

1. 给后续 retrieval 优化提供 before / after 基线
2. 给 taxonomy 提供结构化上下文
3. 给论文中的检索层分析提供稳定口径

因此，这些指标要和 `summary` 一起读，而不是替代 `summary`。

推荐读取顺序：

1. 先看 `summary`
2. 再看 `retrieval_metrics.aggregate`
3. 再看 `retrieval_metrics.by_question_type`
4. 最后看 `rerank_delta_summary` 与具体失败样本

## 3. 适用范围与分母

### 3.1 什么题会进入 retrieval 指标分母

retrieval 指标的分母不是 `150`，而是“需要命中 gold evidence 的可评估题目数”。

当前 `evaluator_v2` 的判定规则是：

1. 如果 `minimum_gold_hits > 0`，该题进入分母
2. 或者该题存在 `gold_record_ids / gold_passage_ids`，该题进入分母

在当前 150 条 goldset 中，这个分母是 `120`。

对应关系可以粗略理解为：

1. non-refusal 题进入 retrieval 指标分母
2. refusal 题不进入 retrieval 指标分母

### 3.2 refusal 为什么全 0

`refusal` 类在当前报告里会出现：

1. `count = 30`
2. 所有 `fused_hit_at_k` 为 `0`
3. 所有 `rerank_hit_at_k` 为 `0`

这不是异常，也不是 retrieval 坏掉了。

它表示的是：

1. refusal 类样本在当前 goldset 口径下不要求命中 gold evidence
2. 因此它们不进入 Hit@K 的有效分母
3. 报告仍保留这 30 条，是为了让 `by_question_type` 结构完整
4. 当前 `0 / 0.0` 应读作“当前口径下不适用的占位值”，而不是“refusal 检索性能为零”

## 4. 字段定义

### 4.1 `top_k_values`

定义：

`top_k_values` 是当前 retrieval 诊断窗口的固定 K 集合。

当前冻结值为：

`[1, 3, 5, 10]`

它的含义不是：

1. 业务主链一定只看 top10
2. rerank 只保留 top10

它的含义是：

1. 报告层固定从这四个窗口观察 gold 是否进入候选前列
2. 这四个 K 值是后续对比 retrieval 优化前后的共同尺子

### 4.2 `aggregate.fused_hit_at_k`

定义：

在“融合候选阶段”观察 gold evidence 是否进入前 K。

统计规则：

1. 分母：当前所有可评估题，当前为 `120`
2. 分子：在某题的一个或多个 retrieval attempt 中，只要有一次 gold 的最优 rank `<= K`，该题就记为命中

注意：

1. 这是题级命中，不是候选条目级命中
2. 对 `general` / `comparison` 这种可能有多个 attempt 的题，按“任一 attempt 命中即可”统计

### 4.3 `aggregate.rerank_hit_at_k`

定义：

在“rerank 后阶段”观察 gold evidence 是否进入前 K。

统计规则与 `fused_hit_at_k` 一致，唯一差别是观察窗口换成 rerank 结果。

因此：

1. 它与 `fused_hit_at_k` 的分母相同
2. 它与 `fused_hit_at_k` 的可直接比较意义最强

### 4.4 `by_question_type`

定义：

按 `question_type` 切分后的 retrieval 统计。

当前固定题型为：

1. `source_lookup`
2. `meaning_explanation`
3. `general_overview`
4. `comparison`
5. `refusal`

读取时必须区分两个数字：

1. `count`
   - 这是该题型在 goldset 里的总题数
2. `fused_hit_at_k / rerank_hit_at_k`
   - 其分母是“该题型内部的可评估题数”，不是 `count`

这意味着：

1. `refusal.count = 30`
2. 但 refusal 的有效 retrieval 分母是 `0`

所以 `by_question_type` 应读成：

1. `count` 负责告诉我们题型规模
2. Hit@K 负责告诉我们该题型在“需要检索命中 gold”的部分表现如何

### 4.5 `rerank_delta_summary`

定义：

它衡量 rerank 相对 fused 阶段，对“best gold rank”到底是在改善还是在恶化。

逐题定义：

1. `best_gold_rank_before_rerank`：gold 在 fused 候选全列表中的最优 rank
2. `best_gold_rank_after_rerank`：gold 在 rerank 后候选全列表中的最优 rank
3. `rerank_rank_delta = best_after - best_before`

解释规则：

1. `delta < 0`：improved
2. `delta = 0`：unchanged
3. `delta > 0`：worsened

这里的“rank”用的是完整候选列表中的 rank，不只看 top10。

因此：

1. 某题即便 `rerank_hit_at_k[10] = false`
2. 仍然可能有 `best_gold_rank_after_rerank = 13`
3. 也就是 gold 还在列表里，只是掉出了 top10 诊断窗口

## 5. 怎么比较 fused 与 rerank

### 5.1 正确读法

读取 fused 与 rerank 的关系时，应回答两个问题：

1. rerank 是否把更多 gold 拉进更靠前的窗口
2. rerank 是否把原本已靠前的 gold 挤出了当前诊断窗口

如果 `rerank_hit_at_k` 低于 `fused_hit_at_k`，通常表示：

1. 在当前窗口定义下，rerank 对这批题整体是负贡献

但这仍然不自动等于：

1. 最终回答一定错误
2. 当前版本一定需要立刻改主链

因为最终回答还要经过 answer assembler、citation 选择和 v1 强校验。

### 5.2 当前报告的正式读法

当前全量结果可冻结为：

1. fused `Hit@10 = 119 / 120 = 0.9917`
2. rerank `Hit@10 = 117 / 120 = 0.9750`

这表示：

1. 在当前 top10 诊断窗口下，rerank 没有比 fused 更好
2. 至少有一部分题，gold 在 rerank 后被挤得更靠后

再看 `rerank_delta_summary`：

1. `improved_count = 19`
2. `unchanged_count = 71`
3. `worsened_count = 30`

正式解释是：

1. 共有 `120` 条可比较题在 fused 和 rerank 两个阶段都能定位到 gold 的 best rank
2. 其中 `19` 条 rank 变好
3. `71` 条不变
4. `30` 条变差

所以 `worsened_count = 30` 不应被读成“30 条答案失败”，而应被读成：

1. 在这 30 条题上，rerank 相对 fused 把 gold 排得更靠后
2. 它是下一轮 retrieval 优化必须优先复查的信号

## 6. 对当前失败样本的固定读法

### 6.1 `eval_seed_q001`

固定读法：

1. 这是 `source_lookup` 题
2. fused 阶段 `best_gold_rank_before_rerank = 1`
3. rerank 阶段 `best_gold_rank_after_rerank = 12`
4. 因此命中 `gold_miss_after_rerank`

它表示：

1. fused 本来已经把 gold 放到最佳位置
2. rerank 把 gold 挤出了 top10 诊断窗口

它不等于 v1 强失败，因为：

1. `mode_match = true`
2. `gold_citation_check.passed = true`
3. `unsupported_assertion_check.passed = true`

对 retrieval 优化的含义是：

1. 这类样本优先指向 rerank 负迁移问题，而不是 fused 检索问题

### 6.2 `eval_seed_q023`

固定读法：

1. 这是 `source_lookup` 题
2. fused 阶段 `best_gold_rank_before_rerank = 1`
3. rerank 阶段 `best_gold_rank_after_rerank = 14`
4. 因此同样命中 `gold_miss_after_rerank`

它与 `q001` 的语义一致：

1. 问题主要出在 rerank
2. fused 阶段已经足够好

它目前不等于 v1 强失败，原因也相同：

1. 最终 payload 没有模式回归
2. citation 仍命中 gold
3. unsupported assertion 没触发

### 6.3 `eval_seed_q095`

固定读法：

1. 这是 `general_overview` 题
2. 该题有 `2` 个 retrieval attempt
3. 在当前 top10 诊断窗口内，fused 与 rerank 都没命中 gold
4. 但完整候选列表中的 best rank 仍可定位为 `16 -> 13`

因此它会同时命中：

1. `gold_miss_in_fused_topk`
2. `gold_miss_after_rerank`

它的含义是：

1. 这不是“rerank 单独搞坏”的题
2. fused 阶段就已经没有把 gold 拉进 top10
3. rerank 虽然有轻微改善，但改善不足以进入 top10

它目前仍不等于 v1 强失败，因为：

1. 最终 payload 仍通过 mode/citation/unsupported assertion 强校验
2. 说明 gold 并不是完全不可达，而是没有进入当前冻结的 top10 诊断窗口

对下一步 retrieval 优化的意义是：

1. 这类样本优先指向 fused 检索召回不足
2. rerank 最多只是次级问题

## 7. 本轮冻结结论

本轮 retrieval 语义冻结后，后续任何 retrieval 优化都应按以下规则比较：

1. 先比较 `aggregate.fused_hit_at_k`
2. 再比较 `aggregate.rerank_hit_at_k`
3. 再比较 `by_question_type`
4. 再比较 `rerank_delta_summary`
5. 最后用典型失败样本解释变化来源

在下一轮 answer_text review 或 latency benchmark 开始前，不再改动这些 retrieval 指标的定义。
