# commentarial usecase matrix

本文件面向“下一轮接入前的最后准备”，用于指导 commentarial layer 的召回与展示策略。
默认前提不变：

- canonical layer 仍是默认主证据层
- commentarial layer 默认不得进入 primary_evidence
- commentarial layer 默认不参与 confidence gate
- commentarial layer 仅作为解释、比较、学习提示与名家视角层

## 用例 1：刘渡舟怎么看第141条？

- 意图类型：named_view / exact_commentator_view
- 优先 unit 类型：`exact`
- 优先 commentator：刘渡舟
- 优先标签：`passage_explanation`、`pathogenesis`、`formula_analysis`、`textual_relation`
- 降权标签：`edition_history`、宽主题 `theory_overview`
- 默认展示：允许
- 折叠展示：可选，不必默认折叠
- 备注：优先按 `PASSAGE_NO:141` 精确取 `cmu_liu_p141`

## 用例 2：郝万山怎么看桂枝汤？

- 意图类型：named_view / formula_theme_view
- 优先 unit 类型：`exact`、`multi`
- 优先 commentator：郝万山
- 优先标签：`formula_analysis`、`therapeutic_method`、`pathogenesis`
- 降权标签：`edition_history`
- 默认展示：允许，但多条结果宜卡片化
- 折叠展示：建议部分折叠
- 备注：对 `multi` 单元要注意“主条文+支持条文”结构，不要把所有 anchors 同权展示

## 用例 3：两家如何解释少阳病？

- 意图类型：comparison_view / commentator_comparison
- 优先 unit 类型：`theme`、`exact`、`multi`
- 优先标签：`comparison`、`theory_overview`、`pathogenesis`、`therapeutic_method`
- 降权标签：`edition_history`
- 默认展示：不宜直接长文展开
- 折叠展示：建议折叠并分栏
- 备注：先按主题定位，再抽对应条文解释单元补强

## 用例 4：名家是怎么讲这个条文的？

- 意图类型：assistive_commentarial_lookup
- 优先 unit 类型：`exact`、`excerpt`
- 优先标签：`passage_explanation`、`commentator_views`、`textual_relation`
- 降权标签：宽主题 `theme`
- 默认展示：允许，但宜在 canonical 之后作为“补充名家解读”
- 折叠展示：建议默认折叠

## 用例 5：怎么学《伤寒论》？

- 意图类型：meta_learning_view
- 优先 unit 类型：`theme`
- 优先标签：`study_method`、`theory_overview`
- 降权标签：`formula_analysis`、`clinical_application`
- 默认展示：允许
- 折叠展示：可不折叠
- 备注：优先召回郝万山相关 theme 单元，其次召回刘渡舟绪论与六经框架单元

## 用例 6：某个证候 / 方证两家有什么不同？

- 意图类型：comparison_view
- 优先 unit 类型：`multi`、`exact`、`theme`
- 优先标签：`comparison`、`pathogenesis`、`formula_analysis`、`textual_relation`
- 降权标签：`edition_history`
- 默认展示：不建议默认直接正文展开
- 折叠展示：建议折叠成“比较卡片”

## 用例 7：用户只问原文释义，但系统想补一句名家解读时，哪些 unit 适合参与？

- 意图类型：default_assistive_retrieval
- 允许参与的 unit：
  - `eligible_for_default_assistive_retrieval = true`
  - 且 `never_use_in_primary = true`
  - 且非 `low_confidence_commentarial_unit`
- 优先标签：`passage_explanation`、`pathogenesis`、`therapeutic_method`
- 不建议参与：宽主题 `theme`、`edition_history`、`study_method`
- 默认展示：只允许一句或短摘要，不允许压过 canonical layer
- 折叠展示：建议折叠为“名家补充解读”

## 用例 8：哪些情况绝不应让名家层进入默认回答正文？

- 用户只问原文出处、条文原文、证据溯源且未请求名家观点
- 当前 canonical 证据不足或 answer_mode 仍不稳
- 命中 commentarial unit 为宽主题 `theme`
- 命中 unit 被标为 `needs_manual_anchor_review` / `needs_manual_content_review`
- 命中 unit 仅适合 meta_learning，不适合条文解释
- 用户问题是严格证据型问句，而不是解释型、比较型、学习型问句
