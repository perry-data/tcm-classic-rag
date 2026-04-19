# multi 主锚 / 辅锚规则说明

本轮仅针对 `anchor_type = multi` 的单元做极小补丁，不改原有 `anchor_candidates`，只增补主锚/辅锚结构。

## 字段
- `primary_anchor_candidates`：当前离线层判断为主锚的 provisional anchors。
- `supporting_anchor_candidates`：补充性 provisional anchors。
- `anchor_priority_mode`：主辅锚判定模式。
- `primary_anchor_selection_reason`：主锚判定理由。
- `supporting_anchor_selection_reason`：辅锚判定理由。
- `multi_anchor_confidence`：本轮离线主辅锚判定置信度。

## 判定原则
1. **标题聚焦优先**：先看标题是否明确聚焦某一病机、证型、方名或证治中心。
2. **方名/证名优先**：若标题直接点出某一方名或证名，则优先以对应条文为主锚。
3. **原文顺序作 tie-break**：若多个候选都能支撑标题主论点，则以该教学单元中最先出现、承担主论点铺垫的条文为主锚。
4. **并列/鉴别簇不强判**：若标题本身覆盖多个并列主题、鉴别簇或批量变证，无法稳定区分唯一主锚，则标为 `unresolved_multi`。

## 本轮结果
- `title_focus_then_order`：标题主论点明确，按主论点 + 原文顺序确定 primary。
- `formula_focus_then_order`：标题直接点出方名/方证，按方名聚焦 + 原文顺序确定 primary。
- `unresolved_multi`：不强判唯一 primary，保留人工复核。
