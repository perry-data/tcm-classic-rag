# Answer_text Review Rubric v1

- 文档版本：v1
- 文档日期：2026-04-10
- 适用范围：`evaluator_v2` 的最小 sampled manual review
- 对应产物：
  - `artifacts/evaluation/answer_text_review_sample_v1.json`
  - `artifacts/evaluation/answer_text_review_report_v1.md`

## 1. Review 目标

本轮 answer_text review 的目标不是证明系统已经“回答得最好”，而是先把人工评价入口接进 `evaluator_v2` 体系，回答三个问题：

1. 当前 answer_text 可以按什么统一尺子来审。
2. 当前最值得先关注的是表达问题，还是系统边界问题。
3. 当前这组最小 review 结论，是否足以支撑下一步 prompt / 生成质量优化。

## 2. 适用范围

本轮 review 只覆盖“当前 `evaluator_v2` 已产出的正式 answer_text”，不做：

1. 150 条全量人工评审
2. baseline vs `qwen-plus` 双输出对照大评审
3. 双人一致性实验
4. 退出码接线

因此它的定位是：

1. 诊断层 artifact
2. prompt / 生成质量优化前的最小人工基线

## 3. 为什么本轮只抽样，不做 150 条全量人评

原因有四点：

1. 当前更缺的是“先把 review 回路接通”，不是一次性把人工工作量做满。
2. retrieval 指标与 taxonomy 语义刚冻结，先用小样本验证 rubric 是否可用更稳妥。
3. 150 条全量人评会显著增加标注成本，但对当前“能否指导下一步 prompt 优化”的边际收益不高。
4. 本轮目标是冻结入口、样本和报告落点，不是做论文终局版质量实验。

## 4. 本轮 sample 抽样规则

最小抽样集固定遵守以下规则：

1. 样本量保持小，只取能打通 review 回路的代表性子集。
2. 必须覆盖 `strong`、`weak_with_review_notice`、`refuse` 三种 answer_mode。
3. 必须覆盖至少 1 条 `general_overview`。
4. 必须覆盖至少 1 条 `source_lookup`。
5. 必须覆盖至少 1 条已出现 retrieval 诊断信号的样本。
6. 优先选取已经进入 `evaluator_v2_report.json` 的正式样本，避免另建平行数据源。

本轮实际抽样规模冻结为 `7` 条。

## 5. 评分维度

本轮 rubric 固定四个维度，并与 `evaluator_v2` schema 预留字段保持一致：

### 5.1 `clarity`

看点：

1. 回答是否直接回应用户问题
2. 语句是否清楚
3. 是否存在大量堆引文、但缺少解释的情况

### 5.2 `structure`

看点：

1. 结构是否有助于阅读
2. 是否按分支、比较项或结论顺序组织
3. 是否存在长段堆叠、编号无助于理解的情况

### 5.3 `evidence_faithfulness`

看点：

1. 回答是否忠于当前可见证据
2. 是否把“部分线索”说成“完整结论”
3. 是否在总括性问题上过度外推

### 5.4 `mode_boundary_preservation`

看点：

1. `strong / weak_with_review_notice / refuse` 的语气边界是否被保持
2. `weak` 是否明确提示“需核对”
3. `refuse` 是否干净拒答
4. `strong` 是否没有掺入与边界相冲突的保留语气

## 6. 评分档位

每个维度统一使用 `0 / 1 / 2` 三档：

1. `0`
   - 明显不满足
   - 该维度可视为 fail
2. `1`
   - 基本满足
   - 可用，但存在明显提升空间
3. `2`
   - 表现稳定
   - 该维度明显满足当前最小目标

## 7. 如何判定需要进 `answer_text_quality_issue`

本轮只冻结“判定规则”，不自动把人工 review 结果回写到 `failure_count` 或退出码。

当前最小规则如下：

1. 只要四个维度中任意一个维度得分为 `0`，该样本即可标记为 `answer_text_quality_issue candidate`。
2. 若 `0` 出现在 `clarity` 或 `structure`，优先视为“表达 / 组织问题”。
3. 若 `0` 出现在 `evidence_faithfulness` 或 `mode_boundary_preservation`，视为“可能影响系统边界的问题”。

对应 taxonomy 候选映射如下：

1. `clarity = 0` -> `clarity_low`
2. `structure = 0` -> `structure_low`
3. `evidence_faithfulness = 0` -> `evidence_faithfulness_low`
4. `mode_boundary_preservation = 0` -> `mode_boundary_broken`

## 8. 哪些问题只是文风问题，哪些可能影响系统边界

### 8.1 只属于文风 / 表达问题

通常包括：

1. 解释不够直白
2. 引文堆叠过多
3. 结构编号存在，但仍难以读懂
4. 总括性回答过长、分支组织不够收束

这类问题主要对应：

1. `clarity`
2. `structure`

### 8.2 可能影响系统边界的问题

通常包括：

1. 把弱证据说成强结论
2. 没有保住 `weak_with_review_notice` 的提示语气
3. `refuse` 没拒干净
4. 总括性回答把局部证据说成完整治法

这类问题主要对应：

1. `evidence_faithfulness`
2. `mode_boundary_preservation`

## 9. 与 evaluator_v2 的关系

本轮 review 与 `evaluator_v2` 的关系固定如下：

1. `answer_text_quality_review` 是诊断层 summary，不是强失败规则。
2. review 结果不影响 `summary.failure_count`。
3. review 结果不影响 `--fail-on-evaluation-failure`。
4. review 结果只用于指导后续 prompt / 生成质量优化与论文分析。

## 10. 本轮冻结结论

本轮之后，answer_text review 的最小入口已经冻结为：

1. 小样本人工 review
2. 四维 rubric
3. `0 / 1 / 2` 评分
4. `answer_text_quality_issue candidate` 判定规则

下一步若继续做 prompt / 生成质量优化，应在这套 rubric 上扩样本、做对照，而不是重新定义评价维度。
