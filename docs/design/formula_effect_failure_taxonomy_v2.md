# formula_effect_failure_taxonomy_v2

本 taxonomy 面向《伤寒论》全书级 formula_effect 批量审计，而不是个案解释。

## direct_context_main_selected

- 定义：primary 直接落在能表达使用语境的 `main_passages` 条文上，且不是方题、组成或短残片。
- 识别特征：`answer_mode=strong`，`whether_primary_contains_direct_context=true`，`whether_primary_is_formula_title_or_composition=false`，`whether_primary_looks_like_short_tail_fragment=false`，`whether_primary_is_cross_chapter_bridge=false`。
- 是否主要是 assembler 问题：否，这是当前理想状态。
- 是否主要是 raw recall 问题：否。
- 后续是否值得修：不作为失败项修复，只作为正样本基线。
- 本轮 query 计数：`111`

## short_tail_fragment_primary

- 定义：primary 虽然命中了提及该方的条文，但上下文只剩很短的承接片段，无法自然回答“有什么作用”。
- 识别特征：`answer_mode=strong`，`whether_primary_looks_like_short_tail_fragment=true`；常见于 `宜`、`与`、`当`、`欲解外` 这类尾部动作词残留。
- 是否主要是 assembler 问题：是，主要是 primary 选择和 context clause 抽取的问题。
- 是否主要是 raw recall 问题：通常不是，raw 里往往已经有更完整候选。
- 后续是否值得修：值得，高优先级。
- 本轮 query 计数：`27`

## cross_chapter_bridge_primary

- 定义：primary 选到跨章承接或桥接条文，形式上可回答，但不是该方最自然的直接使用语境。
- 识别特征：`answer_mode=strong` 且 `whether_primary_is_cross_chapter_bridge=true`。
- 是否主要是 assembler 问题：是，属于 chapter 偏好和 primary ranking 问题。
- 是否主要是 raw recall 问题：通常不是，raw/corpus 往往已经能找到同方正文语境。
- 后续是否值得修：值得，高优先级。
- 本轮 query 计数：`60`

## formula_title_or_composition_over_primary

- 定义：作用类 query 的 primary 被方题或组成条文抢占，答案退化成“方文/组成直出”。
- 识别特征：`whether_primary_is_formula_title_or_composition=true`。
- 是否主要是 assembler 问题：是，属于 evidence slot 选择错误。
- 是否主要是 raw recall 问题：通常不是。
- 后续是否值得修：值得，但优先级取决于出现频次。
- 本轮 query 计数：`15`

## review_only_should_remain_weak

- 定义：直接使用语境只稳定出现在 `passages` / `ambiguous_passages` 等 review 材料里，当前保持 weak 是正确保守行为。
- 识别特征：`answer_mode=weak_with_review_notice` 且 `whether_direct_context_exists_only_in_review=true`。
- 是否主要是 assembler 问题：不是，assembler 应保持保守，不应误抬成 strong。
- 是否主要是 raw recall 问题：也不完全是，更多是当前证据层级限制。
- 后续是否值得修：短期不建议在 assembler 层硬抬，除非未来允许更高等级证据来源。
- 本轮 query 计数：`77`

## raw_recall_missing_direct_context

- 定义：query 级 raw candidates 中根本没有直接使用语境，因此 assembler 没有足够素材组织 strong。
- 识别特征：`whether_direct_context_exists_in_raw_candidates=false`，对应 weak/refuse。
- 是否主要是 assembler 问题：否。
- 是否主要是 raw recall 问题：是，属于召回上限。
- 后续是否值得修：值得，但前提是允许改 raw retrieval；本轮约束下不应继续深挖。
- 本轮 query 计数：`28`

## false_strong_without_direct_context

- 定义：系统给出了 `strong`，但 primary 并不真正提供直接使用语境，因此属于“假 strong”。
- 识别特征：`answer_mode=strong` 且 `whether_primary_contains_direct_context=false`，同时又不属于更具体的方题/短尾/跨章标签。
- 是否主要是 assembler 问题：是。
- 是否主要是 raw recall 问题：通常不是。
- 后续是否值得修：值得，但应先看它是否能被更具体标签吸收。
- 本轮 query 计数：`9`

## stable_positive

- 定义：formula 级多模板结果稳定为 strong，且 primary 一直合理，可视为当前 formula_effect 的稳定正样本。
- 识别特征：formula 级 `strong_reasonable` 且模板结果一致。
- 是否主要是 assembler 问题：否。
- 是否主要是 raw recall 问题：否。
- 后续是否值得修：不作为失败项修复，应纳入回归基线。

## 补充模式：weak_main_direct_context_not_lifted

- 定义：query raw candidates 里已经能看到 `main_passages` 直接语境，但最终仍落成 weak。
- 识别特征：`answer_mode=weak_with_review_notice` 且 `raw_direct_context_main_candidate_ids` 非空。
- 是否主要是 assembler 问题：是，这是 weak 中最值得单独抽出来看的 assembler 失配类。
- 是否主要是 raw recall 问题：否，至少不是 query 级 raw recall 不足。
- 后续是否值得修：若计数显著，值得优先修。
- 本轮 query 计数：`0`
