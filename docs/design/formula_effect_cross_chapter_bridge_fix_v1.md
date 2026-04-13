# formula_effect_cross_chapter_bridge_fix_v1

## 什么叫 cross_chapter_bridge_primary

- 指 formula_effect 查询已经给出 `strong`，但 `primary_evidence` 落在跨 chapter 的桥接/承接条文，而不是同公式正文 chapter 下更自然的直接使用语境。
- 它和 `short_tail_fragment_primary` 的区别是：这里的 primary 往往能回答问题，只是章节归属与正文锚点不够自然；短尾问题则更多是上下文本身残缺。

## 为什么它是当前最大可修问题

- baseline bulk audit 的 `after` 口径里，该模式共有 `60` 个 query，是本轮可修类里最大的单一 failure pattern。
- `review_only_should_remain_weak` 虽然更多（`77` 个 query），但按约束不应在 assembler 里硬抬成 strong。
- `raw_recall_missing_direct_context` 有 `28` 个 query，主因在 raw retrieval，不属于本轮允许改动范围。
- 其他可修类里，`short_tail_fragment_primary` 为 `27`，`formula_title_or_composition_over_primary` 为 `15`，规模都小于 cross-chapter bridge。

## 拟采用的最小修复策略

- 保留现有 formula_effect v1 的基础 context score，不重写 assembler 全局逻辑。
- 只在 support row ranking 内加入一个二阶段 chapter preference：若当前 top1 是跨章 bridge 且自身是 clean direct context，再检查是否存在同 formula chapter 的 clean direct context 候选。
- 只有当同章候选也满足 `main_passages + direct context + 非方题/组成 + 非短尾 + 基础分不为负` 时，才把 primary 切回同章候选。
- 这个门槛的目的是只修 `cross_chapter_bridge_primary`，不把 `short_tail_fragment_primary`、`formula_title_or_composition_over_primary` 也顺手卷进来。
- 本轮回放后，该策略实际修正 `3` 个 query、`1` 个 formula；`cross_chapter_bridge_primary` 从 `60` 降到 `57`。

## 为什么不顺手碰其他 pattern

- 不碰 `review_only_should_remain_weak`：这类样本本来就应保持保守，硬抬会直接违反本轮边界。
- 不碰 `raw_recall_missing_direct_context`：raw candidates 里没有正文直接语境时，assembler 没有足够素材可重排。
- 不碰 `annotation / annotation_links`：它们不属于这次 primary 失配的根因。
- 不碰 raw retrieval candidate 生成：当前修复只发生在 assembler 的 support row ranking / chapter preference 层。
- 不新开 family：仍沿用 `cross_chapter_bridge_primary` 这一路径，避免把本轮 patch 扩成多 pattern 联修。
