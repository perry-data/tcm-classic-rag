# formula_effect_short_tail_fragment_patch_v1

## 修了哪些规则

- 在 `backend/answers/assembler.py` 的 `_extract_formula_effect_context_clause_v1` 中加入同-row backtrack：当 formula 前只剩短动作残片时，回退到前一个更完整的症状片段。
- 对极短条件尾巴仅在必要时拼回，例如 `不瘥`，避免 answer_text 只剩一个动作词。
- 在 `_analyze_formula_effect_context_row_v1` 里加入 compact direct clause 判定，让 `少阴病，下利`、`发汗后，腹胀满` 这类短但完整的直接语境不再被误标为 short tail。
- 仅复用现有 formula_effect 逻辑做最小调整，没有改 raw retrieval、annotation 或 review-only weak 的证据边界。

## 改善规模

- `short_tail_fragment_primary`：`27` -> `0`
- 脱离 short-tail 的 query 数：`27`
- 脱离 short-tail 的 formula 数：`9`
- 其中回到 `direct_context_main_selected`：`21` queries
- 其中转入 `cross_chapter_bridge_primary`：`6` queries
- `primary_reasonable_query_count`：`111` -> `135`
- `primary_suspicious_query_count`：`111` -> `87`

## 是否有回退样本

- stable positive 回退 query 数：`0`
- stable positive 回退 formula 数：`0`
- review-only weak 误抬 query 数：`0`
- review-only weak 误抬 formula 数：`0`
- stable positive 回退公式：`_none_`
- review-only 误抬公式：`_none_`

## 下一轮是否还值得处理 formula_title_or_composition_over_primary

- 建议：`是`。
- 原因：当前 `formula_title_or_composition_over_primary` 仍有 `15` 个 query，且它与 short-tail 一样属于 assembler 内的 primary slot 失配。
