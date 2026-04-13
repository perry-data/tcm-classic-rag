# formula_effect_bulk_audit_summary_v1

## 扫描设置

- 支持的 query 模板数：`3`
- 全书可识别方剂总数：`109`
- 生成 query 总数（全部 variant 合计）：`654`
- 当前系统口径：`after`（`TCM_ENABLE_FORMULA_EFFECT_PRIMARY_RULES_V1=1`）

## 当前系统全景（after）

- 批量覆盖的方剂总数：`109`
- 批量 query 总数：`327`
- strong / weak / refuse（query 级）：`222` / `105` / `0`
- strong / weak / refuse（formula 级）：`74` / `35` / `0`
- primary 合理的数量（query 级）：`111`
- primary 可疑的数量（query 级）：`111`
- review-only weak 的数量（query 级）：`77`
- raw recall 缺失的数量（query 级）：`28`
- weak 且更像 assembler 问题的数量（query 级）：`0`

## 方剂分组（after）

- 已经 strong 且 primary 合理：十枣汤方、四逆散方、大承气汤方、大陷胸汤方、大青龙汤方、小建中汤方、小柴胡汤方、小青龙汤方、当归四逆汤方、抵当丸方、抵当汤方、栀子乾姜汤方、栀子豉汤方、桂枝人参汤方、桂枝汤方、桂枝附子汤方、桃花汤方、炙甘草汤方、烧散方、牡蛎泽泻散方、猪苓汤方、甘草乾姜汤方、甘草汤方、甘草附子汤方、白头翁汤方、白散方、竹叶石膏汤方、芍药甘草附子汤方、苦酒汤方、茯苓桂枝白术甘草汤方、葛根汤方、蜜煎导方、附子汤方、麻赵本有子字仁丸方、麻黄连轺赤小豆汤方、麻黄附子细辛汤方、黄连阿胶汤方
- strong 但 primary 可疑（假强）：五苓散方、半夏散及汤方、吴茱萸汤方、四逆汤方、大柴胡汤方、大黄黄连泻心汤方、小承气汤方、小陷胸汤方、文蛤散方、枳实栀子豉汤方、柴胡桂枝汤方、栀子甘草豉汤方、栀子生姜豉汤方、桂枝二麻黄一汤方、桂枝加大黄汤方、桂枝加桂汤方、桂枝加芍药生姜人参新加汤方、桂枝加附子汤方、桂枝麻黄各半汤方、桔梗汤方、浓朴生姜甘草半夏人参汤方、猪肤汤方、理中丸方、瓜蒂散方、生姜泻心汤方、白虎加人参汤方、白虎汤方、白通汤方、芍药甘草汤方、茯苓甘草汤方、调胃承气汤方、通脉四逆汤方、附子泻心汤方、麻黄杏人甘草石膏汤方、麻黄汤方、黄芩加半夏生姜汤方、黄芩汤方
- weak 且更像 assembler 问题：_none_
- weak 且应视为 review-only：乌梅丸方、乾姜附子汤方、乾姜黄连黄芩人参汤方、半夏泻心汤方、四逆加人参汤方、旋复代赭石汤方、柴胡加芒硝汤方、柴胡加龙骨牡蛎汤方、柴胡桂枝乾姜汤方、栀子浓朴汤方、桂枝加浓朴杏子汤方、桂枝加芍药汤方、桂枝去芍药汤方、桂枝甘草龙骨牡蛎汤方、桃核承气汤方、甘草泻心汤方、白通加猪胆汁汤方、真武汤方、茯苓四逆汤方、茯苓桂枝甘草大枣汤方、茵陈蒿汤方、葛根加半夏汤方、葛根黄芩黄连汤方、赤石脂禹馀粮汤方、麻黄附子甘草汤方
- weak/refuse 且更像 raw recall 缺失：四赵本四上有当归二字逆加吴茱萸生姜汤方、四逆加猪胆汁汤方、大陷胸丸方、桂枝二越婢一汤方、桂枝去桂加茯苓白术汤方、桂枝去芍药加蜀漆龙骨牡蛎救逆汤方、桂枝去芍药加附子汤方、桂枝甘草汤方、麻黄升麻汤方
- weak 但模板间原因不完全一致：黄连汤方

## Failure Pattern 统计（after，query 级）

- `review_only_should_remain_weak`：`77`
- `cross_chapter_bridge_primary`：`60`
- `raw_recall_missing_direct_context`：`28`
- `short_tail_fragment_primary`：`27`
- `formula_title_or_composition_over_primary`：`15`
- `false_strong_without_direct_context`：`9`

## 最值得优先修的前 3 类问题

- `cross_chapter_bridge_primary`：`60`
- `short_tail_fragment_primary`：`27`
- `formula_title_or_composition_over_primary`：`15`

## Before / After 变化

- `primary_reasonable_query_count` delta：`21`
- `primary_suspicious_query_count` delta：`-21`
- `review_only_weak_query_count` delta：`0`
- `raw_recall_missing_query_count` delta：`0`
- `assembler_weak_query_count` delta：`0`
- 从可疑 strong 转为合理 strong 的方剂：小柴胡汤方、栀子豉汤方、桂枝汤方、猪苓汤方、甘草汤方、白头翁汤方、葛根汤方、附子汤方
- 从合理 strong 回退为可疑 strong 的方剂：麻黄汤方
