# definition_query_primary_prioritization_v1

## 1. 本轮要解决的问题

上一轮已经证明：某些 query-critical 解释性条目即使能进入 `raw_candidates` 或 `secondary_evidence`，也仍然会被无关但词面接近的 `main_passages` 占住 `primary_evidence`，最终 `answer_text` 继续走“主条直出”。

本轮不再继续对单个 query 打补丁，而是只做一个更小的 query family 实验：

- 当 query 本质上是在问“定义 / 术语 / 方义 / 归类”时
- 优先把直接回答该问法的定义句、解释句、方义句抬成 primary
- 不再让只共享局部词面的无关主条继续占 primary

## 2. 哪些 query 视为“定义 / 术语 / 方义解释类”

本轮只覆盖以下小类：

- `什么是X` / `X是什么`
- `X是什么意思` / `X什么意思`
- `X是Y吗`
- `X属于什么药` / `X是什么药`
- `X有什么作用`

说明：

- `X有什么作用` 这一支当前已有稳定的 `formula_effect_query` 路径，本轮主要把它当作同 family 的回归锚点，不重写其专用逻辑。
- `太阳病是什么` 这一支当前已有稳定的 `definition_outline_query` 路径，本轮同样保留既有专用逻辑，只把它作为 regression check。

## 3. 哪类 evidence 视为优先候选

本轮只优先以下“直接回答问法”的 evidence type：

- `exact_term_definition`
  - 典型形态：`X者，……也`、`X之为病，……`
  - 用于“X是什么 / X是什么意思”
- `exact_term_explanation`
  - 典型形态：句子直接以 `X` 起笔，对其义项、用法、条件做解释
  - 用于“X是什么 / X是什么意思”
- `term_membership_sentence`
  - 典型形态：`A者，X也`
  - 用于“什么是X”这类没有抽象定义句、但存在直接归类句的情况
- `subject_predicate_definition`
  - 典型形态：`A者，B也`
  - 用于 `A是B吗`
- `subject_category_definition`
  - 典型形态：`A者，某药也`
  - 用于 `A属于什么药`

实现边界：

- 仅允许 `main_passages` 与 `passages` 参与这一小类 query 的 primary 竞争
- `ambiguous_passages`、`annotations`、`annotation_links` 不得被提升为 primary

## 4. 哪类 evidence 不应继续错误占 primary

以下内容在本轮应继续被压到 secondary / review，或根本不参与该 family 的 primary 竞争：

- 只共享局部词面的泛条文
  - 例如 query 是“发汗药”，却被“可发汗 / 不可发汗 / 发汗后如何如何”的主条占住 primary
- 只能说明治疗语境、不能直接回答定义/归类问法的条文
- `ambiguous_passages`
- `annotations`
- `annotation_links`

换句话说，本轮目标不是“谁 rerank 分数最高谁进 primary”，而是“谁最直接回答当前问法谁优先”。

## 5. 本轮最小规则形态

规则采用配置化表达，而不是散落的 if/else：

- query pattern
  - 识别是 `what_is`、`what_means`、`category_membership_yesno`、`category_membership_open`
- evidence type preference
  - 为每个 family 指定优先 evidence type 顺序
- source gate
  - 只允许 `main_passages` / `passages`
- blocked sources
  - 明确屏蔽 `ambiguous_passages` / `annotations` / `annotation_links`

因此，本轮变化点落在 assembler 侧的“primary candidate prioritization / answer assembly input priority”，而不是重做 retrieval 主体。

## 6. 本轮规则边界

本轮只做：

- 最小 query family 识别
- 基于配置的 primary candidate prioritization
- 必要 debug 记录
- 非破坏性的 assembler 输入优先级调整

本轮明确不做：

- 不做 `发汗药` 特判
- 不做 `太阳病` 特判
- 不按 query id 打补丁
- 不恢复 `annotation`
- 不恢复 `annotation_links`
- 不大改 rerank 主体
- 不大改 answer assembler 全局逻辑
- 不扩大到所有 query 类型

## 7. 本轮可接受的实验性取舍

为了验证“primary bottleneck”是否真实存在，本轮允许在这一小类 query 中，把命中严格定义/归类模式的 `passages` 直接抬成 primary。

原因：

- 这类句子已经在 `raw_candidates` 中出现
- 它们直接回答了 query
- 当前问题的瓶颈恰恰是“进池了，但没有被裁成 primary”

这仍然比恢复 annotation 或大改 rerank 更小、更可控。

## 8. 预期结果

若规则生效，应看到：

- `raw_candidates` 基本不变
- 但 `primary_evidence` 从无关主条切换为定义句 / 解释句 / 方义句
- `answer_text` 从“主条直出”变为“基于依据解释”
- 已有稳定路径的 `definition_outline_query` 与 `formula_effect_query` 不发生明显回归
