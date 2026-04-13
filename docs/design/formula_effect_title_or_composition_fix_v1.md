# formula_effect_title_or_composition_fix_v1

## 什么叫 formula_title_or_composition_over_primary

- 指作用类 query 的 `primary_evidence` 被方题或组成条误占，或者正文直接语境被当前 composition heuristic 误判成了“组成条”。
- 这一类里既有真的 title/composition 抢位，也有正文条文因为出现 `一升 / 三两 / 合病 / 数升` 之类词面而被错误贴上 composition 标签。

## 为什么它会让“作用类问法”退化成方文/组成直出

- 一旦 primary 被当成方题/组成条，`formula_effect` 的 strong answer 就会被判成“不是直接使用语境”，用户看到的回答要么偏方文直出，要么落到可疑 strong。
- 这类问题多数不是 raw recall 缺料，而是 assembler 在 primary slot 分析和 support row ranking 上把正文 direct context 误当成 composition。
- baseline bulk audit 的 `after` 口径里，这类样本共有 `15` 个 query / `5` 个 formula；本轮回放后降到 `0` 个 query。

## 拟采用的最小修复策略

- 收紧 `_row_is_formula_composition_line`：不再因为单个 `合 / 两 / 升` 字面就判成 composition，而是要求更像真正的剂量结构；同时对带明显 direct usage marker 或症状语境的行取消 composition 判定。
- 在 `formula_effect` support row ranking 里加入一个很小的 direct-context preference：只有当 top1 仍是 title/composition 且存在 clean main direct context 候选时，才优先正文直接语境。
- 不改 raw retrieval candidate 生成，不碰 annotation / annotation_links，不改 review-only weak 的证据层级。
- 本轮回放后，`formula_title_or_composition_over_primary` 共脱离 `15` 个 query、`5` 个 formula；其中 `9` 个 query 回到 `direct_context_main_selected`，另有 `6` 个 query 转入 `cross_chapter_bridge_primary`，`0` 个 query 转入 `false_strong_without_direct_context`。

## 为什么本轮不顺手碰其他 pattern

- 不继续扩 `cross_chapter_bridge_primary`：当前 baseline 还有 `60` 个 bridge query，本轮只允许把 title/composition 误占清掉，不继续加 chapter v2 偏好。
- 不碰 `review_only_should_remain_weak`：这类有 `77` 个 query，本来就应保持弱，不应因 title/composition patch 被误抬。
- 不碰 `raw_recall_missing_direct_context`：这类有 `28` 个 query，根因在 raw retrieval，不在本轮边界内。
- 不继续深挖 `short_tail_fragment_primary`：这类在上轮 patch 已单独处理过，当前剩余问题不应和 title/composition 联修。
