# Answer_text Review Report v1

## 1. 本轮 review 目标

本轮只做 `evaluator_v2` 的最小 sampled manual review，目标是把 answer_text 的人工评价入口接进现有评估体系，而不是直接做 prompt 优化。

本轮结论是：

1. 当前 answer_text review 已能用统一 rubric 稳定审阅。
2. 当前主要问题集中在表达与组织，不集中在系统边界破坏。
3. 这组样本已经足以支撑下一步 prompt / 生成质量优化的方向判断，但还不足以支撑 150 条全量质量结论。

## 2. 为什么本轮只抽样，不做 150 条全量人评

原因有四点：

1. 本轮要先把 review 回路接通，而不是把人工标注规模一次性做满。
2. retrieval 指标和 taxonomy 刚刚冻结，先用小样本验证 rubric 是否可用更稳妥。
3. 150 条全量人评会显著增加工作量，但对当前“是否能指导下一步生成优化”的边际收益不高。
4. 本轮仍然属于诊断层建设，不是论文终局版人工评审。

## 3. 样本集

本轮共抽样 `7` 条，覆盖：

1. `strong`
2. `weak_with_review_notice`
3. `refuse`
4. `general_overview`
5. `source_lookup`
6. retrieval 诊断样本

抽样清单：

| question_id | question_type | mode | retrieval_diagnostic | 用途 |
| --- | --- | --- | --- | --- |
| `eval_seed_q001` | `source_lookup` | `strong` | yes | 观察 strong source_lookup 与 rerank 诊断并存时的文本表现 |
| `eval_seed_q002` | `meaning_explanation` | `weak_with_review_notice` | no | 观察弱答解释题的表达与边界 |
| `eval_seed_q003` | `general_overview` | `strong` | no | 观察强答总括题的结构组织 |
| `eval_seed_q005` | `general_overview` | `weak_with_review_notice` | no | 观察弱答总括题的表达压缩能力 |
| `eval_seed_q006` | `comparison` | `strong` | no | 观察比较题结构是否稳定 |
| `eval_seed_q008` | `refuse` | `refuse` | no | 观察拒答文本是否干净 |
| `eval_seed_q095` | `general_overview` | `strong` | yes | 观察 retrieval 诊断样本在总括题上的文本表现 |

## 4. Rubric 结果

评分档位：

1. `0` = fail
2. `1` = 基本可用，但有明显缺口
3. `2` = 稳定满足当前最小目标

逐样本结果：

| question_id | clarity | structure | evidence_faithfulness | mode_boundary_preservation | issue_candidate | issue_class |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `eval_seed_q001` | 2 | 2 | 2 | 2 | no | `none` |
| `eval_seed_q002` | 1 | 0 | 2 | 2 | yes | `style_only` |
| `eval_seed_q003` | 1 | 2 | 1 | 2 | no | `none` |
| `eval_seed_q005` | 0 | 1 | 2 | 2 | yes | `style_only` |
| `eval_seed_q006` | 2 | 2 | 2 | 2 | no | `none` |
| `eval_seed_q008` | 2 | 2 | 2 | 2 | no | `none` |
| `eval_seed_q095` | 1 | 2 | 1 | 2 | no | `none` |

## 5. 每条样本的正式读取说明

### `eval_seed_q001`

- 结论：文本表现稳定。
- 说明：source_lookup 强答直达题意，结构清楚，虽然 retrieval 层有 `gold_miss_after_rerank` 信号，但最终 answer_text 没表现出边界问题。

### `eval_seed_q002`

- 结论：`structure_low` 候选。
- 说明：弱答边界守住了，但正文更像直接贴辅助材料，缺少把“是什么意思”拆开的解释层。问题主要是表达组织，不是系统边界。

### `eval_seed_q003`

- 结论：可用，但 general_overview 仍偏长。
- 说明：分支结构有帮助，但“总括性问题”与“典型分支整理”之间还能再做一层归纳，当前更像结构可用、压缩不足。

### `eval_seed_q005`

- 结论：`clarity_low` 候选。
- 说明：弱答边界和证据边界都守住了，但对用户来说仍更像线索堆叠而不是“六经病应该怎么办”的可吸收答案，属于表达问题。

### `eval_seed_q006`

- 结论：本轮最稳定样本之一。
- 说明：比较结构明确，差异项组织清楚，结尾也保留继续核对的空间，当前可以作为后续 prompt 优化的正样本参考。

### `eval_seed_q008`

- 结论：拒答文本稳定。
- 说明：文本短而干净，没有越界解释，也没有假装提供内容，`refuse` 模式表现符合当前边界。

### `eval_seed_q095`

- 结论：文本可用，但 general_overview 仍偏“列分支”。
- 说明：这是 retrieval 诊断样本，但 answer_text 本身没有 mode 失守。当前不足主要在压缩和概括，不在边界。

## 6. 当前 answer_text 的主要问题集中在哪

当前问题主要集中在两类：

1. 弱答解释题仍偏“引用材料直贴”，缺少把材料翻译成用户可直接吸收语言的中间层。
2. 总括性问题虽然已有编号结构，但仍偏长、偏分支堆叠，尚未形成更凝练的总括表达。

相对更稳定的类型是：

1. source_lookup
2. comparison
3. refuse

## 7. 哪些只是文风问题，哪些可能影响系统边界

### 只是文风 / 表达问题

本轮样本里已出现的主要是：

1. `eval_seed_q002` 的 `structure_low`
2. `eval_seed_q005` 的 `clarity_low`

它们的共同点是：

1. 读起来仍然偏“引文堆叠”或“线索堆叠”
2. 但并没有把弱证据说成强结论
3. 也没有破坏 `weak_with_review_notice` / `refuse` 的边界

### 可能影响系统边界的问题

本轮样本里暂未观察到明显的：

1. `evidence_faithfulness = 0`
2. `mode_boundary_preservation = 0`

因此本轮结论是：

1. 当前主要问题在表达层
2. 暂未看到人工 review 层面的边界破坏样本

## 8. answer_text review 当前是否影响退出码

答案是：不影响。

本轮 answer_text review 仍然属于诊断层：

1. 不影响 `summary.failure_count`
2. 不影响 `--fail-on-evaluation-failure`
3. 不自动回写到 taxonomy 计数

## 9. 本轮结论是否足以支撑下一步 prompt / 生成质量优化

答案是：足以支撑“方向判断”，但不足以支撑“全量结论”。

可以支撑的下一步方向：

1. 优先优化 weak answer 的解释展开方式，减少“材料直贴”。
2. 优先优化 general_overview 的总括句和分支压缩方式，减少过长堆叠。
3. 保持 comparison / refuse 的现有结构，不要在这些类型上先做大改。

当前还不足以支撑的结论：

1. 不能据此宣称 150 条 answer_text 整体质量已经系统提升。
2. 不能据此替代后续更大样本的人评或 baseline-vs-LLM 对照评审。
