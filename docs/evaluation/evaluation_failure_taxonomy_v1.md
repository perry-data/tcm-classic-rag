# 评估失败分类法 v1

- 文档版本：v1
- 文档日期：2026-04-09
- 适用范围：`evaluator_v2` 主骨架阶段
- 语义冻结参考：
  - `docs/evaluation/evaluator_v2_taxonomy_semantics_v1.md`
- 对应产物：
  - `scripts/run_evaluator_v2.py`
  - `artifacts/evaluation/evaluator_v2_report.json`
  - `artifacts/evaluation/evaluator_v2_report.md`

## 1. 文档定位

本分类法用于给 `evaluator_v2` 提供统一的失败语言，服务两类用途：

1. 给后续 retrieval / prompt 优化提供可统计、可追踪的诊断标签。
2. 给论文第 4 章中的失败分析与系统局限性分析提供结构化口径。

本分类法当前是“诊断层 artifact”，不是新的主链判错规则。

也就是说：

1. `summary.failure_count` 仍然沿用 `evaluator_v1` 的强校验口径。
2. `failure_taxonomy` 用于暴露更细粒度的问题信号。
3. taxonomy 中出现条目，不等价于本轮 replay 失败退出。
4. taxonomy 当前不影响 `--fail-on-evaluation-failure` 的退出逻辑。

## 2. 与 v1 强校验的关系

`evaluator_v2` 当前仍然保留并复用以下 v1 强校验：

1. `mode_match`
2. `citation_basic_pass`
3. `unsupported_assertion_check`
4. refusal 边界相关空字段检查

本分类法只是把这些已有检查和新增 retrieval 诊断，映射成更稳定的统计语言。

因此报告中允许出现这样的情况：

1. `summary.all_checks_passed = true`
2. 同时 `failure_taxonomy.items_with_failures > 0`

这代表：

1. 当前正式边界没有回归；
2. 但已经出现值得后续优化优先关注的诊断信号。

## 3. 计数规则

`failure_taxonomy` 统计遵守以下规则：

1. `category_counts`：按条目计数，不按题目计数。
2. `subcategory_counts`：按条目计数，不按题目计数。
3. `items_with_failures`：按题目去重计数，只统计“至少命中 1 个 taxonomy 条目”的样本数。
4. 同一题可同时命中多个 category / subcategory。

例：

如果同一题同时出现：

1. `gold_miss_in_fused_topk`
2. `gold_miss_after_rerank`

则：

1. `category_counts.retrieval_failure` 增加 `2`
2. `items_with_failures` 只增加 `1`

## 4. 一级分类定义

### 4.1 `retrieval_failure`

含义：

检索或 rerank 阶段未能把 gold evidence 放进预期观察窗口。

当前 v2 skeleton 已自动接入。

### 4.2 `citation_failure`

含义：

最终回答中的 citation 未命中 gold `record_id` 或 canonical `passage_id`。

当前 v2 skeleton 已自动接入。

### 4.3 `answer_mode_failure`

含义：

最终 `answer_mode` 与 gold 期望模式不一致。

当前 v2 skeleton 已自动接入。

### 4.4 `evidence_layering_failure`

含义：

在应为空、应拒答或应不输出证据的边界样本上，系统仍输出了不该出现的 evidence / citation / primary evidence。

当前 v2 skeleton 已自动接入。

### 4.5 `unsupported_assertion_failure`

含义：

当前输出触发了 v1 已有的 unsupported assertion 边界检查。

当前 v2 skeleton 已自动接入。

### 4.6 `answer_text_quality_issue`

含义：

回答文本在人评 rubric 下存在清晰度、结构或证据忠实度问题。

当前状态：

1. 类别已预留
2. 本轮不自动填充
3. 等待后续 answer_text review 轮次接入

### 4.7 `llm_runtime_issue`

含义：

LLM 调用、validator 或 fallback 过程中出现运行时问题。

当前状态：

1. 类别已预留
2. 本轮不自动填充
3. 等待后续 live / review 扩展轮次接入

### 4.8 `latency_issue`

含义：

延迟超出约定阈值或性能表现异常。

当前状态：

1. 类别已预留
2. 本轮不自动填充
3. 等待 latency mini-benchmark 轮次接入

## 5. 二级分类定义

### 5.1 当前已启用的 subcategory

#### `gold_miss_in_fused_topk`

定义：

gold evidence 未进入 fused top `K`。

当前默认观察窗口：

`K = 10`

用途：

判断融合候选阶段是否已经丢失 gold。

#### `gold_miss_after_rerank`

定义：

gold evidence 在 rerank 后未进入 top `K`。

当前默认观察窗口：

`K = 10`

用途：

判断问题发生在 rerank 之后，还是更早之前已经丢失。

#### `citation_not_in_gold`

定义：

输出 citation 未匹配 gold `record_id` 或 canonical `passage_id`。

#### `expected_weak_but_actual_strong`

定义：

gold 期望是 `weak_with_review_notice`，但实际回答给成了 `strong`。

#### `expected_refuse_but_not_refuse`

定义：

gold 期望是 `refuse`，但实际没有拒答。

#### `mode_mismatch_other`

定义：

除上面两类之外的其他 `answer_mode` 错配。

#### `primary_should_be_empty`

定义：

当前样本要求 `primary_evidence` 为空，但输出中出现了内容。

#### `evidence_should_be_zero`

定义：

当前样本要求 evidence 槽位为空，但输出中出现了内容。

#### `citations_should_be_zero`

定义：

当前样本要求 citation 列表为空，但输出中出现了 citation。

#### `strong_without_gold_evidence`

定义：

回答给出了 `strong` 结论，但没有对应 gold evidence 支撑。

#### `mode_boundary_broken`

定义：

用于承接暂未细分命名、但已经确认属于 mode / boundary 破坏的兜底类问题。

### 5.2 已预留、暂未启用的 subcategory

以下 subcategory 已写入 schema / report 结构，但本轮不实际评分，只保留为后续扩展位：

1. `clarity_low`
2. `structure_low`
3. `evidence_faithfulness_low`
4. `llm_fallback_triggered`
5. `llm_validator_reject`
6. `latency_over_threshold`

## 6. 与 retrieval 指标的配合方式

`retrieval_failure` 不直接替代 `Hit@K` 指标，而是与它配套使用：

1. `retrieval_metrics.aggregate` 负责给出整体命中率
2. `retrieval_metrics.by_question_type` 负责给出题型切分
3. `retrieval_metrics.rerank_delta_summary` 负责给出 rerank 改善或恶化趋势
4. `failure_taxonomy` 负责把具体 miss 样本标出来

这意味着后续 retrieval 优化可以同时回答三件事：

1. 总体命中率是否上升
2. 哪类题受益最大
3. 仍然失败的是哪些题、失败在 fused 还是 rerank

## 7. v2 Skeleton 实际使用说明

在 `evaluator_v2` 主骨架轮次中，taxonomy 的推荐读取顺序为：

1. 先看 `summary`
2. 再看 `retrieval_metrics.aggregate`
3. 再看 `retrieval_metrics.by_question_type`
4. 最后看 `failure_taxonomy`

原因是：

1. `summary` 判断主链是否回归
2. retrieval 指标判断检索侧趋势
3. taxonomy 用于定位具体问题样本

不建议直接拿 `items_with_failures` 替代正式 pass/fail 结论。

## 8. 本轮边界

本分类法 v1 明确只覆盖 `evaluator_v2` 主骨架阶段，因此不包含：

1. answer_text 人工 rubric 的实际评分结果
2. latency threshold 的正式阈值结论
3. LLM runtime 故障树
4. 更细的根因推断或自动修复建议

这些内容留待后续评估优化轮次继续扩展。
