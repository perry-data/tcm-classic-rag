# formula_effect_short_tail_fragment_fix_v1

## 什么叫 short_tail_fragment_primary

- 指 `formula_effect_query` 已经给到 `strong`，但 `primary_context_clause` 只剩很短的动作尾巴或条件残片，像 `与`、`不瘥`、`若少气` 这类语境拿来直接回答“有什么作用”会很别扭。
- 这类问题多数不是 raw recall 缺料，而是同一条 primary 的 context clause 抽取过窄，或者把短而完整的直接语境误判成 short tail。

## 为什么它影响用户体感

- 用户第一眼看到的 answer 首句会直接退化成“用于与”“用于不瘥”“用于若少气”这类不自然短句。
- 即使 primary record_id 本身没错，只要 context clause 抽窄，整个 strong answer 的可信度和可读性都会立刻下降。
- baseline bulk audit 的 `after` 口径里，这类样本共有 `27` 个 query / `9` 个 formula；本轮回放后降到 `0` 个 query。

## 拟采用的最小修复策略

- 不改 raw retrieval candidate 生成，不扩 annotation / annotation_links，不碰 review-only 的升格逻辑。
- 在 `backend/answers/assembler.py` 的 `formula_effect` context clause 抽取里增加一层同-row 回退：如果 formula 前只剩 `与 / 可与 / 当 / 宜 / 更作` 这类动作残片，就回退到前一个更完整的症状片段；必要时拼回极短的条件尾巴，如 `不瘥`。
- 对 `少阴病，下利`、`发汗后，腹胀满`、`若少气` 这类短但完整的直接语境，改成更谨慎的 compact direct clause 判定，不再一律按“长度短”打成 short tail。
- 本轮回放后，`short_tail_fragment_primary` 本身共脱离 `27` 个 query、`9` 个 formula；其中 `21` 个 query 落回 `direct_context_main_selected`，另有 `6` 个 query 更准确地转入 `cross_chapter_bridge_primary`。

## 为什么本轮不顺手碰其他 pattern

- 不继续扩 `cross_chapter_bridge_primary`：它已有专门 patch，继续加 chapter 偏好会把 short-tail 和 bridge 两类规则重新缠在一起；当前 baseline 仍有 `60` 个 bridge query，后续应单独评估。
- 不碰 `review_only_should_remain_weak`：这类有 `77` 个 query，本来就应保持保守，不应借 short-tail patch 被误抬。
- 不碰 `raw_recall_missing_direct_context`：这类有 `28` 个 query，根因在 raw retrieval，不属于本轮允许范围。
- 不顺手改 `formula_title_or_composition_over_primary`：这类仍有 `15` 个 query，属于独立的 primary slot 问题，值得单独开一轮处理。
