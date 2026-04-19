# theme display tier 规则说明

本轮为所有 `anchor_type = theme` 的单元新增 `theme_display_tier`。

## 枚举
- `tier_1_named_view_ok`：可用于 named view；默认仍不进 primary 正文中心位。
- `tier_2_fold_only`：只适合折叠展示或专题页，不建议默认展开。
- `tier_3_meta_learning_only`：仅用于学习方法 / 元学习视图。
- `tier_4_do_not_default_display`：作者、版本、沿革、附录等背景信息，默认不展示。

## 判定原则
1. **学习方法优先入 tier 3**：凡明确讨论“怎样学《伤寒论》/ 学习方法与要求”的主题，进入 `meta learning view`。
2. **作者与版本沿革优先入 tier 4**：作者背景、版本系统、流传史、附录类内容默认不进入正文。
3. **临床专题主题可入 tier 1**：与某经病、证候分类、治法、预后、禁忌强相关的主题，可供 named view 使用。
4. **宽泛概述归 tier 2**：广义理论总述、章节概述、框架性说明只宜折叠展示。
