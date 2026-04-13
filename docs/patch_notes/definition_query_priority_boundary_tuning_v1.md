# definition_query_priority_boundary_tuning_v1

## 1. 本轮范围

本轮只做 `definition_query_primary_prioritization_v1` 的小批量覆盖验证与边界收紧：

- 不新增 query family
- 不扩到 `formula_effect_query`
- 不碰 `annotation` / `annotation_links`
- 不改 raw retrieval candidate 生成
- 不做 assembler 全局重写

本轮验证集见：

- `artifacts/experiments/definition_query_priority_regression_set_v1.json`
- `artifacts/experiments/definition_query_priority_regression_report_v1.md`

## 2. 哪些 query 证明规则有效

本轮最稳定的正样本主要集中在两类前提都满足的 query：

- query 句式明确落在定义 / 释义 / 归类 family
- raw candidates 本身已经带回可直接回答问法的定义句、解释句或归类句

验证效果最明确的样本：

- `什么是发汗药`
  - `primary_evidence` 从无关“发汗语境主条”切到 `桂枝汤者，发汗药也`
  - `answer_text` 从主条直出变为基于依据解释
- `阳结是什么`
  - 证明 `what_is` 不只在“发汗药”上有效
  - 能稳定命中 `term_membership_sentence`
- `坏病是什么`
  - 证明 `what_is` 也能处理 `谓之X` 这类术语解释
- `发汗药是什么意思`
  - 稳定命中 `exact_term_explanation`
  - 从 weak 辅助材料提升到 strong 解释
- `阳结是什么意思`
  - 证明 `what_means` 在脉象类术语上也可工作
- `坏病是什么意思`
  - 证明 `what_means` 对 `谓之X` 类表达也可工作
- `桂枝汤是发汗药吗`
  - `category_membership_yesno` 能直接回到 `桂枝汤者，发汗药也`

结论：

- 规则已经证明不是“只在发汗药这一个点上有效”
- 但它的有效前提仍然很清楚：raw candidates 里必须先出现可直接回答问法的句子

## 3. 哪些 query 暂时不稳

当前不稳的点主要不是 assembler 抢错 primary，而是 raw recall 不足，导致 family 命中后只能 fallback：

- `承气汤是下药吗`
  - family 命中，但当前 raw candidates 没稳定带回 `承气汤者，下药也`
  - 因此只能保持 standard fallback
- `桂枝汤是什么药`
- `桂枝汤属于什么药`
- `承气汤是什么药`
- `神丹是什么药`
  - 这些 `category_membership_open` 问法都更像 retrieval coverage 问题
  - 现阶段不应把它误判成 assembler 排序还能继续救的场景
- `太阳病是什么意思`
  - 本轮已收紧到“不再被 definition priority 抢走”
  - 但当前仍只是回到 standard 路径，答案质量没有自动升级成理想的提纲式解释
  - 这说明它现在是“边界守住了，但还不是完整优化完成”

## 4. 哪些表达容易误判

本轮实际暴露出的易误判表达主要有两类：

- `X的组成是什么`
  - 词面上带 `是什么`，很容易被 `what_is` 吸进去
  - 但业务上它其实是组成/药味问题，不应进入当前 family
- `X是什么意思`
  - 其中天然包含更短的 `什么意思`
  - 若不做后缀消歧，`太阳病是什么意思` 会先被切成 `太阳病是 + 什么意思`
  - 这会绕过原本针对 outline-topic 的 guard，形成隐蔽误吸

需要单独记住的一条边界：

- 六经提纲主题如 `太阳病是什么意思`
  - 即使词面上是 `what_means`
  - 也不适合直接交给当前 generic definition priority 去抢 primary
  - 否则容易把“太阳病，发热无汗，反恶寒者，名曰刚痓”这类局部说明句误当主解释

## 5. 是否需要只调配置即可修正

可以只靠配置修正的部分：

- `X的组成是什么`
- `X的药味是什么`

本轮已经通过配置收紧：

- 在 `definition_query_priority_rules_v1.json` 的 `block_hints` 中新增：
  - `组成`
  - `药味`

不能只靠当前配置修正的部分：

- `是什么意思` / `什么意思` 的嵌套后缀歧义
- 六经提纲主题与 `what_means` 的冲突
- `category_membership_yesno` / `category_membership_open` 在若干 query 上的 raw recall 缺口

原因：

- 当前配置只能描述 query family、evidence type preference 和 block hints
- 它还不足以表达“短后缀不能吞掉长后缀的一部分”这类句法消歧
- 也不足以表达“某些 topic 已有专用稳定路径，应跳过 generic family”这类 topic-level guard

## 6. 本轮调了哪些边界

本轮实际落地了两类边界收紧：

### 6.1 配置收紧

文件：

- `config/controlled_replay/definition_query_priority_rules_v1.json`

调整：

- `block_hints` 新增 `组成`、`药味`

作用：

- 把 `发汗药的组成是什么` 这类问法挡在 family 外
- 避免 `what_is` 对组成类问法发生词面误吸

### 6.2 最小代码边界判断

文件：

- `backend/answers/assembler.py`

调整：

- 对 `what_means` 增加 outline-topic guard
  - 六经提纲主题不再进入 generic definition priority
- 对 suffix match 增加 `什么意思` / `是什么意思` 消歧
  - 短后缀不再错误吞掉长后缀的一部分

作用：

- `太阳病是什么意思` 不再被 `definition_priority:what_means` 抢走
- 本轮把重点落实在“验证和收紧”，没有顺手扩新 family

## 7. 本轮结论

可以确认的有效边界：

- 当 raw candidates 已带回直接定义句 / 解释句 / 归类句时，当前规则能稳定改善 primary 选择
- 改善点主要落在 assembler 侧 primary prioritization，而不是 retrieval 侧召回

当前仍需保留的风险判断：

- `category_membership_open` 还不能宣称稳定
- `承气汤是下药吗` 这类 yes/no 问法仍可能受 raw recall 限制
- `太阳病是什么意思` 目前属于“避免误吸成功，但未完成专题优化”

因此，本轮最准确的结论不是“全部 family 都已经稳定”，而是：

- `what_is` / `what_means` 已拿到可证明的正样本覆盖
- `category_membership_yesno` 已有明确正样本，但仍受个别 query 的 raw recall 约束
- `category_membership_open` 当前更多是在证明“没有乱抢 primary”，还不能证明“已稳定可答”
