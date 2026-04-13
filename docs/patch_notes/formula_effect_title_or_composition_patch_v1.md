# formula_effect_title_or_composition_patch_v1

## 修了哪些规则

- 收紧 `backend/answers/assembler.py` 里的 `_row_is_formula_composition_line`：不再因为普通正文里的 `合 / 两 / 升` 等字面就判成 composition，而是要求更像真正的剂量结构。
- 对带明显 direct usage marker 或症状语境的行取消 composition 判定，避免正文 direct context 被错打成组成条。
- 在 `_find_formula_effect_support_rows_v1` 中加入一层很小的 direct-context preference：仅当 top1 仍是 title/composition 且存在 clean main direct context 候选时，才让位给正文直接语境。
- 在 `_score_formula_effect_context_row_v1` 中补上 title/composition penalty，避免作用类 query 被方题/组成条抢占 primary。

## 改善规模

- `formula_title_or_composition_over_primary`：`15` -> `0`
- 脱离 title/composition 的 query 数：`15`
- 脱离 title/composition 的 formula 数：`5`
- 其中回到 `direct_context_main_selected`：`9` queries
- 其中转入 `cross_chapter_bridge_primary`：`6` queries
- 其中转入 `false_strong_without_direct_context`：`0` queries

## 是否有回退样本

- stable positive 回退 query 数：`0`
- stable positive 回退 formula 数：`0`
- review-only weak 误抬 query 数：`0`
- review-only weak 误抬 formula 数：`0`
- stable positive 回退公式：`_none_`
- review-only 误抬公式：`_none_`

## 下一轮是否还值得继续回头处理 cross_chapter_bridge_primary v2

- 建议：`是`。
- 原因：当前 `cross_chapter_bridge_primary` 仍有 `69` 个 query，而且本轮 title/composition 样本里又有 `6` 个 query 在去误判后重新暴露成 bridge，说明它仍是值得单独处理的剩余大类。
